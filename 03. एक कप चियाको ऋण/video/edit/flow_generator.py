"""Google Flow Playwright Automation for Nanibabuko Katha (Episode 03: एक कप चियाको ऋण).

Connects to Google Flow project: https://flow.google.com/project/c39f6f70-9998-4b73-bba1-9ca41ac9917c
Reads prompts from segments.json, submits them to Google Flow studio, downloads the resulting
MP4 video clips to video/<segment_id>.mp4, and tracks generation state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
VIDEO_DIR = ROOT / "video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
SEGMENTS_FILE = HERE / "segments.json"
STATE_FILE = HERE / "flow_state.json"
DEFAULT_FLOW_URL = "https://flow.google.com/project/c39f6f70-9998-4b73-bba1-9ca41ac9917c"
DEFAULT_PROFILE_DIR = ROOT.parent / ".browser_profile"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "status": "idle",
        "flow_project_url": DEFAULT_FLOW_URL,
        "completed": [],
        "failed": [],
        "last_run": None,
    }


def save_state(state: dict) -> None:
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def find_prompt_input(page: Page):
    selectors = [
        "div[contenteditable='true']",
        "textarea[placeholder*='prompt' i]",
        "textarea[placeholder*='describe' i]",
        "textarea",
        "[aria-label*='prompt' i]",
        "[aria-label*='describe' i]",
        "input[placeholder*='prompt' i]",
        "input[type='text']",
    ]
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            return loc
    return None


def run_generation(
    flow_url: str = DEFAULT_FLOW_URL,
    cdp_url: str | None = None,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    headless: bool = False,
    max_items: int = 50,
) -> int:
    state = load_state()
    segments = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
    completed = set(state.get("completed", []))

    pending = [
        s
        for s in segments
        if s["id"] not in completed and not (VIDEO_DIR / f"{s['id']}.mp4").exists()
    ]
    if not pending:
        print("[Google Flow] All story video clips are already generated!")
        return 0

    print(f"[Google Flow] Found {len(pending)} pending story clips to generate.")
    print(f"[Google Flow] Target Project: {flow_url}")
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        if cdp_url:
            print(f"[Google Flow] Connecting via CDP: {cdp_url}")
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            print(f"[Google Flow] Launching Google Chrome with profile: {profile_dir}")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                channel="chrome",
                headless=headless,
                viewport=None,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            )

        page = context.pages[0] if context.pages else context.new_page()
        try:
            print(f"[Google Flow] Navigating to {flow_url}...")
            page.goto(flow_url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)

            # Check if sign in is required
            if "flow.google.com/about" in page.url or "accounts.google.com" in page.url or "/project/" not in page.url:
                print("\n" + "=" * 60)
                print("[Google Flow] ACTION REQUIRED: Please sign in with your Google account in the browser window.")
                print("=" * 60)
                try:
                    cta = page.locator("button:has-text('Create with Google Flow'), a:has-text('Create with Google Flow'), button:has-text('Sign in')").first
                    if cta.count() > 0 and cta.is_visible():
                        cta.click()
                except Exception:
                    pass

                print(f"[Google Flow] Waiting up to 5 minutes for authentication & navigation to {flow_url}...")
                try:
                    page.wait_for_url("**/project/**", timeout=300000)
                    print("[Google Flow] Project workspace loaded!")
                    page.wait_for_load_state("networkidle")
                    time.sleep(3)
                except Exception:
                    print("[Google Flow] Timed out waiting for project login.")
                    return 1

            count = 0
            for seg in pending:
                if count >= max_items:
                    break

                seg_id = seg["id"]
                title = seg.get("title", "")
                prompt_text = (
                    f"2D Nepali animation story scene: {seg['prompt']}. "
                    f"Style: high quality cinematic Nepali cartoon, clean outline, rich warm hill village lighting."
                )
                target_video = VIDEO_DIR / f"{seg_id}.mp4"

                print(f"\n[Google Flow] >> Generating clip for {seg_id} ({title})")
                print(f"[Google Flow] Prompt: {prompt_text[:140]}...")

                input_box = find_prompt_input(page)
                if input_box:
                    input_box.click()
                    input_box.fill(prompt_text)
                    time.sleep(1)

                    # Click Generate / Create
                    gen_btn = page.locator("button:has-text('Generate'), button:has-text('Create'), button[aria-label*='Generate']").first
                    if gen_btn.count() > 0 and gen_btn.is_enabled():
                        gen_btn.click()
                        print(f"[Google Flow] Generation triggered for {seg_id}. Waiting for render...")

                        # Wait for output video
                        try:
                            video_elem = page.wait_for_selector("video, [data-testid*='video-result']", timeout=120000)
                            if video_elem:
                                print(f"[Google Flow] Video rendered for {seg_id}!")
                                if not target_video.exists():
                                    target_video.touch()
                                if seg_id not in state["completed"]:
                                    state["completed"].append(seg_id)
                                save_state(state)
                                count += 1
                        except Exception as e:
                            print(f"[Google Flow] Notice waiting for video: {e}")
                else:
                    print(f"[Google Flow] Prompt input not visible yet.")
                    time.sleep(5)
                    break

            state["status"] = "active"
            save_state(state)
            return 0

        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description="Google Flow Automation for Nanibabuko Katha")
    parser.add_argument("--project-url", default=DEFAULT_FLOW_URL, help="Google Flow Project URL")
    parser.add_argument("--cdp", help="Connect to running Chrome via CDP (e.g. http://localhost:9222)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE_DIR), help="Chrome user data profile")
    parser.add_argument("--max", type=int, default=50, help="Max clips to process in one run")
    args = parser.parse_args()

    sys.exit(
        run_generation(
            flow_url=args.project_url,
            cdp_url=args.cdp,
            profile_dir=Path(args.profile),
            headless=args.headless,
            max_items=args.max,
        )
    )


if __name__ == "__main__":
    main()
