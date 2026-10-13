"""Generate every EP04 clip in Google Flow (Omni 1.1 Flash) and download it to ../clips/<id>.mp4.

Resumable: video_ids.json records submitted clips, failed_clips.json the refusals. Run again to continue.
Usage: py -3 gen_clips.py [id ...]     (no ids = every segment that still needs a clip)
"""
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from flow_client import approve, close_overlays, download, flow_page, to_grid

EDIT = Path(__file__).parent
CLIPS = EDIT.parent / "clips"
IDS = EDIT / "video_ids.json"
FAILED = EDIT / "failed_clips.json"
EXPECTED_COST = "costing 12 credits"
REPLY_TIMEOUT_S = 120
DOWNLOAD_ATTEMPTS = 4
DOWNLOAD_RETRY_S = 45
NO_CLIP = {"S12S1", "S12S2"}  # finale and moral are built from stills
STYLE = ("High-quality cinematic 2D Nepali cartoon animation, clean bold outlines, soft hand-painted Nepali hill-village "
         "backgrounds, warm natural colors, expressive large eyes.")
CAST = {
    "अर्जुन": ("Arjun", "deep, firm, caring adult male voice"),
    "सुनिता": ("Sunita", "soft, worried adult female voice"),
    "रवि": ("Ravi", "excited 10-year-old boy voice"),
    "दिपा": ("Dipa", "sweet 7-year-old girl voice"),
    "माइला दाजु": ("Maila", "playful, clever village man voice"),
    "मुखिया धनबहादुर": ("Mukhiya Dhanbahadur", "authoritative, impatient older male voice"),
    "हजुरबा गोविन्द": ("Grandfather Govinda", "calm, deep, very old male voice"),
    "सानो अर्जुन": ("the small boy", "innocent little boy voice"),
    "गाउँले १": ("the village farmer", "rough middle-aged village man voice"),
}
REFERENCES = ("Use the character reference sheet images already in this project (Arjun and Sunita; Ravi and Dipa; Mukhiya "
              "Dhanbahadur and Maila; Grandfather Govinda) and the ridge location image so every character and the "
              "ancient tree look exactly the same as in those images.")


def english(text: str) -> str:
    """Replace the story's bracketed Devanagari tags with the English names used on the reference sheets."""
    for nepali, (name, _voice) in CAST.items():
        text = text.replace(f"[{nepali}]", name)
    return re.sub(r"\[STYLE\]\s*", "", text).replace('"काफलडाँडा"', "Kaphaldanda")


def video_prompt(seg: dict) -> str:
    scene = english(seg["prompt"])
    if seg.get("lines"):
        spoken = " Then ".join(f'{CAST[who][0]} says in Nepali, in a {CAST[who][1]}: "{text}"' for who, text in seg["lines"])
        focus = " This is a continuation of the same conversation: frame the speaker in a closer shot." if seg.get("part") else ""
        audio = f"{spoken}. Spoken language must be Nepali, lips moving only for the speaker. Background sound: natural ambience."
    else:
        focus = ""
        audio = "No speech and no voice-over at all; only natural ambient sound effects that fit the scene."
    return (f"Generate one 8-second 16:9 video with Omni 1.1 Flash, with sound. {REFERENCES} {STYLE} {scene}{focus} "
            f"{audio} No on-screen text, no titles, no subtitles, no captions.")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def reply_to(page: Page, prompt: str) -> str:
    """Wait for the agent's answer to this prompt (text after the prompt's own tail in the chat)."""
    marker = prompt[-40:]
    deadline = time.time() + REPLY_TIMEOUT_S
    reply = ""
    while time.time() < deadline:
        page.wait_for_timeout(3000)
        body = page.inner_text("body")
        reply = body[body.rfind(marker) + len(marker):]
        if "Approve" in reply or len(reply.split("What do you want to create?")[0].strip(" /\n")) > 60:
            return reply
    return reply


def submit(page: Page, prompt: str) -> str:
    to_grid(page)
    box = page.locator("[contenteditable=true]:visible, textarea:visible").last
    box.click(timeout=8000)
    page.keyboard.insert_text(prompt)
    page.get_by_role("button", name="Start generation").click()
    reply = reply_to(page, prompt)
    if EXPECTED_COST not in reply:
        if "Approve" in reply:  # an unexpected price: never spend it
            page.get_by_text("Reject", exact=True).last.click(timeout=8000)
        raise RuntimeError("not offered at 12 credits: " + " ".join(reply.split())[:300])
    return approve(page)[0]


def fetch(page: Page, seg_id: str, media_id: str) -> bool:
    for _ in range(DOWNLOAD_ATTEMPTS):
        try:
            download(page, media_id, CLIPS / f"{seg_id}.mp4")
            return True
        except Exception as exc:  # still rendering, or the tile is not on screen yet
            print(f"{seg_id}: download retry ({type(exc).__name__})", flush=True)
            close_overlays(page)
            page.wait_for_timeout(DOWNLOAD_RETRY_S * 1000)
    return False


def main(wanted: list[str]) -> None:
    segments = json.loads((EDIT / "segments.json").read_text(encoding="utf-8"))
    todo = [s for s in segments if s["id"] not in NO_CLIP and (not wanted or s["id"] in wanted)]
    with sync_playwright() as playwright:
        for seg in todo:
            sid = seg["id"]
            if (CLIPS / f"{sid}.mp4").exists():
                continue
            ids, failed = load(IDS), load(FAILED)
            try:
                page = flow_page(playwright)
                if sid not in ids:
                    ids = {**ids, sid: submit(page, video_prompt(seg))}
                    save(IDS, ids)
                    print(f"{sid}: submitted {ids[sid]}", flush=True)
                if not fetch(page, sid, ids[sid]):
                    raise RuntimeError("download failed")
                save(FAILED, {k: v for k, v in failed.items() if k != sid})
            except Exception as exc:
                save(FAILED, {**failed, sid: str(exc)[:400]})
                print(f"{sid}: FAILED {str(exc)[:200]}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
