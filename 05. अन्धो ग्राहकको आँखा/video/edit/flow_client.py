"""Drive Google Flow's agent chat over CDP (Chrome started with --remote-debugging-port=9222).

Usage:
  py -3 flow_client.py ask "<prompt>"            send a prompt, print the agent's reply (cost question)
  py -3 flow_client.py approve                   approve the pending generation, wait for new media
  py -3 flow_client.py list                      print media ids currently in the project grid
  py -3 flow_client.py get <media_id> <out>      download an image (.png) or video (.mp4) by id
"""
import re
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

CDP = "http://127.0.0.1:9222"
MEDIA = "img[src*='flow-content.google/image/'], img[src*='flow.google.com/asb/']"
# videos show a flow-content thumbnail keyed by uuid; generated images are served from /asb/<token>
MEDIA_ID = re.compile(r"flow-content\.google/(?:image|video)/([0-9a-f-]{36})|/asb/([\w-]{24})")
REPLY_WAIT_MS = 2000
REPLY_TIMEOUT_S = 90
MEDIA_TIMEOUT_S = 600


def flow_page(playwright) -> Page:
    browser = playwright.chromium.connect_over_cdp(CDP)
    page = next(pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url and "/project/" in pg.url)
    page.bring_to_front()
    return page


def close_overlays(page: Page) -> None:
    """Angular CDK menus (account, settings) swallow every click until their backdrop is dismissed."""
    backdrop = page.locator(".cdk-overlay-backdrop")
    if backdrop.count():
        backdrop.first.click(force=True, position={"x": 5, "y": 5})
        page.wait_for_timeout(800)


def credits(page: Page) -> str:
    close_overlays(page)
    page.locator("[aria-label='Account details']").first.click(force=True)
    page.wait_for_timeout(2000)
    found = re.search(r"([\d,]+) Google Flow credits", page.inner_text(".cdk-overlay-container"))
    close_overlays(page)
    return found.group(1) if found else "unknown"


def to_grid(page: Page) -> None:
    """Leave the clip editor (its URL contains /edit/) and return to the project grid."""
    close_overlays(page)
    if "/edit/" in page.url:
        page.get_by_role("button", name="Back button to go to previous page").click()
        page.wait_for_timeout(REPLY_WAIT_MS)


def media_ids(page: Page) -> list[str]:
    srcs = page.eval_on_selector_all(MEDIA, "els => els.map(e => e.src)")
    return list(dict.fromkeys(m.group(1) or m.group(2) for m in map(MEDIA_ID.search, srcs) if m))


def chat_tail(page: Page, chars: int = 500) -> str:
    return page.inner_text("body")[-chars:].replace("\n", " / ")


def ask(page: Page, prompt: str) -> str:
    to_grid(page)
    box = page.locator("[contenteditable=true]:visible, textarea:visible").last
    box.click(timeout=8000)
    page.keyboard.insert_text(prompt)
    page.get_by_role("button", name="Start generation").click()
    deadline = time.time() + REPLY_TIMEOUT_S
    while time.time() < deadline:
        page.wait_for_timeout(REPLY_WAIT_MS)
        tail = chat_tail(page)
        if "Approve" in tail and "credit" in tail:
            return tail
    return chat_tail(page, 900)


def approve(page: Page) -> list[str]:
    before = set(media_ids(page))
    page.get_by_text("Approve", exact=True).last.click(timeout=8000)  # earlier turns leave stale buttons
    deadline = time.time() + MEDIA_TIMEOUT_S
    while time.time() < deadline:
        page.wait_for_timeout(5000)
        fresh = [m for m in media_ids(page) if m not in before]
        if fresh and "generating" not in chat_tail(page).lower():
            page.wait_for_timeout(5000)
            return [m for m in media_ids(page) if m not in before]
    raise TimeoutError("no new media appeared: " + chat_tail(page))


def download(page: Page, media_id: str, out: Path) -> None:
    """Images use the grid thumbnail URL; videos need the signed URL the editor requests."""
    to_grid(page)
    tile = page.locator(f"img[src*='{media_id}']").first
    url = tile.get_attribute("src")
    if out.suffix.lower() == ".mp4":
        with page.expect_response(lambda r: f"/video/{media_id}" in r.url, timeout=30000) as found:
            tile.click()
        url = found.value.url
        page.wait_for_timeout(1500)
        to_grid(page)
    out.parent.mkdir(parents=True, exist_ok=True)
    if "/asb/" in url:
        out.write_bytes(page.context.request.get(url).body())  # needs the signed-in session cookies
    else:
        urllib.request.urlretrieve(url, out)
    print(out.name, out.stat().st_size)


def main(argv: list[str]) -> None:
    command = argv[0]
    with sync_playwright() as playwright:
        page = flow_page(playwright)
        if command == "ask":
            print(ask(page, argv[1]))
        elif command == "approve":
            print("NEW", approve(page))
        elif command == "credits":
            print(credits(page))
        elif command == "list":
            to_grid(page)
            print(media_ids(page))
        elif command == "get":
            download(page, argv[1], Path(argv[2]))
        else:
            raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
