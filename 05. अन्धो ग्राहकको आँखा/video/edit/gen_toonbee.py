"""Turn Flow keyframes into ToonBee clips with the free Seedance 1 PRO model (silent, 8 s).

Usage:
  py -3 gen_toonbee.py            every segment that has no clip yet, in story order; sleeps while the free quota is used up
  py -3 gen_toonbee.py S1S1 S1S2  only these segments

A first segment of a shot starts from keyframes/<id>.png. Continuation segments (part 1, 2) start from the last
frame of the previous clip so the conversation plays as one unbroken shot. Only the free model is ever requested.
"""
import io
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

import toonbee_client as tb
from gen_clips import CAST, NO_CLIP, english

EDIT = Path(__file__).parent
EPISODE = EDIT.parents[1]
KEYFRAMES = EPISODE / "keyframes"
CLIPS = EPISODE / "video_toonbee" / "clips"
SLIDES = EDIT / "toonbee_slides.json"  # segment id -> ToonBee slide id
DURATION_S = 8
POLL_S = 15
QUOTA_MARGIN_S = 90
FETCH_ATTEMPTS = 4
KEYFRAME_WAIT_S = 1500
CLIP_TIMEOUT_S = 900
JPEG_QUALITY = 92
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/155.0 Safari/537.36"
RUNNING = {"generating", "processing", "queued", "pending"}


def motion_prompt(seg: dict) -> str:
    scene = english(seg["prompt"])
    if seg.get("lines"):
        speakers = list(dict.fromkeys(CAST[who][0] for who, _text in seg["lines"]))
        acting = (f" {' then '.join(speakers)} talk{'s' if len(speakers) == 1 else ''} with clear mouth movement and "
                  "natural hand gestures; the listener reacts.")
    else:
        acting = " Nobody speaks."
    return (f"2D cartoon animation. {scene}{acting} Keep the exact character designs, clothes and art style of the "
            "image. Smooth natural motion. No text, no captions, no subtitles.")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def slide_state(page: Page, slide_id: int) -> dict:
    return next(s for s in tb.status(page)["slides"] if s["id"] == slide_id)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # the asset host rejects the default agent
    for attempt in range(FETCH_ATTEMPTS):
        try:
            return urllib.request.urlopen(request, timeout=120).read()
        except OSError:  # the connection to the asset host times out now and then
            if attempt == FETCH_ATTEMPTS - 1:
                raise
            time.sleep(POLL_S)


def set_start_image(page: Page, slide_id: int, seg: dict, previous_slide: int | None) -> None:
    jpeg = EDIT / "_upload.jpg"
    if seg.get("part"):
        if previous_slide is None:
            raise RuntimeError("previous clip of this shot is missing")
        video = slide_state(page, previous_slide)["current_video_version"]["video_asset"]
        jpeg.write_bytes(fetch(video["last_frame_url"]))  # ToonBee only accepts library images by URL, so upload the file
    else:
        Image.open(KEYFRAMES / f"{seg['id']}.png").convert("RGB").save(jpeg, "JPEG", quality=JPEG_QUALITY)
    tb.upload_image_file(page, slide_id, jpeg)
    jpeg.unlink()


def wait_for_clip(page: Page, slide_id: int) -> str:
    deadline = time.time() + CLIP_TIMEOUT_S
    while time.time() < deadline:
        time.sleep(POLL_S)
        state = slide_state(page, slide_id)
        if state["video_status"] == "completed" and state["current_video_version"]:
            return state["current_video_version"]["video_asset"]["url"]
        if state["video_status"] not in RUNNING:
            raise RuntimeError(f"video {state['video_status']}: {state['video_error']}")
    raise TimeoutError("clip not finished")


def download(url: str, seg: dict) -> Path:
    out = CLIPS / f"{seg['id']}.mp4"
    out.write_bytes(fetch(url))
    return out


def generate(page: Page, seg: dict, slides: dict) -> Path:
    slide_id = slides.get(seg["id"]) or tb.call(page, "POST", f"/projects/{tb.PROJECT_ID}/slides", {"text": ""})["id"]
    slides[seg["id"]] = slide_id
    SLIDES.write_text(json.dumps(slides, indent=1), encoding="utf-8")
    done = slide_state(page, slide_id)
    if done["video_status"] == "completed" and done["current_video_version"]:  # finished in an earlier, interrupted run
        return download(done["current_video_version"]["video_asset"]["url"], seg)
    set_start_image(page, slide_id, seg, slides.get(seg.get("_previous")))
    tb.call(page, "POST", f"/slides/{slide_id}/generate-video", {
        "video_model_id": tb.FREE_MODEL_ID, "duration": DURATION_S,
        "prompt": motion_prompt(seg), "use_simple_video_prompt": True})
    return download(wait_for_clip(page, slide_id), seg)


def wait_for_quota(playwright, segment_id: str) -> Page:
    """The free quota is a rolling 8-hour window: sleep until the oldest clip leaves it, then go on."""
    while True:
        page = tb.editor_page(playwright)  # reconnect: the handle does not survive hours of sleep
        quota = tb.free_quota(page)
        if quota["throttle_remaining"]:
            return page
        reset = datetime.fromisoformat(quota["throttle_reset_at"])
        wait = max(60.0, (reset - datetime.now(timezone.utc)).total_seconds() + QUOTA_MARGIN_S)
        print(f"{segment_id} waiting {wait / 60:.0f} min: free quota used, next slot {quota['throttle_reset_at']}", flush=True)
        time.sleep(wait)


def main(only: list[str]) -> None:
    segments = [s for s in json.loads((EDIT / "segments.json").read_text(encoding="utf-8")) if s["id"] not in NO_CLIP]
    for previous, seg in zip([None] + segments, segments):
        seg["_previous"] = previous["id"] if previous else None
    todo = [s for s in segments if not (CLIPS / f"{s['id']}.mp4").exists() and (not only or s["id"] in only)]
    slides = load(SLIDES)
    CLIPS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        page = tb.editor_page(playwright)
        balance = tb.status(page)["credit_balance"]
        for seg in todo:
            keyframe = KEYFRAMES / f"{seg['id']}.png"
            waited = 0
            while not seg.get("part") and not keyframe.exists() and waited < KEYFRAME_WAIT_S:  # Flow batch still running
                time.sleep(POLL_S)
                waited += POLL_S
            if not seg.get("part") and not keyframe.exists():
                print(f"{seg['id']} stop: keyframe not ready", flush=True)
                break
            page = wait_for_quota(playwright, seg["id"])
            started = time.time()
            try:
                out = generate(page, seg, slides)
            except Exception as error:  # stop here: later parts of the shot need this clip's last frame
                print(f"{seg['id']} FAILED {str(error)[:300]}", flush=True)
                break
            print(f"{seg['id']} ok {out.stat().st_size} bytes {time.time() - started:.0f}s", flush=True)
        print(f"credits before {balance}, after {tb.status(page)['credit_balance']}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
