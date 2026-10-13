"""Generate one opening keyframe per shot in Google Flow (Nano Banana Pro) for the ToonBee image-to-video pass.

Usage:
  py -3 gen_keyframes.py            every shot that has no keyframe yet
  py -3 gen_keyframes.py S2S1 S4S2  only these shots

Continuation segments (part 1, 2) reuse the last frame of the previous clip, so they get no keyframe.
"""
import io
import json
import re
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import Error as PlaywrightError, Page, sync_playwright

from flow_client import chat_tail, flow_page, media_ids, to_grid
from gen_clips import REFERENCES, STYLE, english

EDIT = Path(__file__).parent
KEYFRAMES = EDIT.parents[1] / "keyframes"
FAILED = EDIT / "failed_keyframes.json"
MAX_PAID_CREDITS = 0
TURN_TIMEOUT_S = 300
NUDGES = 2
POLL_S = 5
IDLE_POLLS_BEFORE_NUDGE = 3
NUDGE = "Continue. Generate that one 16:9 still image now with Nano Banana Pro."
COST = re.compile(r"(\d+)\s+credits?", re.I)


def image_prompt(seg: dict) -> str:
    scene = re.sub(r"bold Devanagari moral text appearing on screen\.?", "", english(seg["prompt"]))
    return (f"Generate one 16:9 still image with Nano Banana Pro now, without asking me to confirm. {REFERENCES} {STYLE} "
            f"{scene} This still is the first frame of a video shot: show the moment just before the action starts. "
            "No on-screen text, no titles, no subtitles, no captions, no watermark.")


def send(page: Page, text: str) -> None:
    to_grid(page)
    box = page.locator("[contenteditable=true]:visible, textarea:visible").last
    box.click(timeout=8000)
    page.keyboard.insert_text(text)
    page.get_by_role("button", name="Start generation").click()


def approve_if_free(page: Page) -> None:
    """The agent sometimes asks for approval; only accept when the quoted cost is within the budget."""
    tail = chat_tail(page, 400)
    if "Approve" not in tail:
        return
    costs = [int(c) for c in COST.findall(tail)]
    if costs and max(costs) > MAX_PAID_CREDITS:
        raise PlaywrightError(f"agent asks for {max(costs)} credits: {tail}")
    page.get_by_text("Approve", exact=True).last.click(timeout=8000)


def poll(page: Page, before: set[str]) -> tuple[list[str], bool]:
    fresh = [m for m in media_ids(page) if m not in before]
    busy = page.get_by_role("button", name="Stop").count() > 0
    if not fresh and not busy:
        approve_if_free(page)
    return fresh, busy


def wait_for_image(playwright, before: set[str]) -> str | None:
    deadline = time.time() + TURN_TIMEOUT_S
    idle_polls = 0
    page = flow_page(playwright)
    time.sleep(8)
    while time.time() < deadline:
        try:
            fresh, busy = poll(page, before)
        except PlaywrightError as error:
            if "credits" in str(error):
                raise
            page = flow_page(playwright)  # the CDP handle sometimes closes mid-turn; the tab itself stays open
            fresh, busy = [], True
        if fresh and not busy:
            return fresh[-1]
        idle_polls = 0 if busy else idle_polls + 1
        if idle_polls >= IDLE_POLLS_BEFORE_NUDGE:
            return None
        time.sleep(POLL_S)
    return None


def save_png(page: Page, media_id: str, out: Path) -> None:
    url = page.locator(f"img[src*='{media_id}']").first.get_attribute("src")
    Image.open(io.BytesIO(page.context.request.get(url).body())).convert("RGB").save(out, "PNG")


def generate(playwright, seg: dict) -> Path:
    page = flow_page(playwright)
    before = set(media_ids(page))
    send(page, image_prompt(seg))
    media_id = wait_for_image(playwright, before)
    for _ in range(NUDGES):
        if media_id:
            break
        send(flow_page(playwright), NUDGE)
        media_id = wait_for_image(playwright, before)
    page = flow_page(playwright)
    if not media_id:
        raise RuntimeError("no image: " + chat_tail(page, 300))
    out = KEYFRAMES / f"{seg['id']}.png"
    save_png(page, media_id, out)
    return out


def main(only: list[str]) -> None:
    segments = json.loads((EDIT / "segments.json").read_text(encoding="utf-8"))
    todo = [s for s in segments if not s.get("part") and not (KEYFRAMES / f"{s['id']}.png").exists()
            and (not only or s["id"] in only)]
    failed: dict[str, str] = {}
    KEYFRAMES.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        for seg in todo:
            started = time.time()
            try:
                out = generate(playwright, seg)
                print(f"{seg['id']} ok {out.stat().st_size} bytes {time.time() - started:.0f}s", flush=True)
            except Exception as error:  # one bad shot must not stop the batch; it is logged and retried later
                failed[seg["id"]] = str(error)[:300]
                print(f"{seg['id']} FAILED {failed[seg['id']]}", flush=True)
                if "credits" in str(error):
                    break
    FAILED.write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"done {len(todo) - len(failed)}/{len(todo)}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
