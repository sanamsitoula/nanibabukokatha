"""Call ToonBee's editor API from the signed-in editor tab (Chrome started with --remote-debugging-port=9222)."""
import base64
import json
from pathlib import Path

from playwright.sync_api import Page

CDP = "http://127.0.0.1:9222"
PROJECT_ID = 145265
FREE_MODEL_ID = 30  # Seedance 1 PRO: 0 credits, silent, 25 clips per 8 hours

# fetch from inside the page so the session cookie and Laravel XSRF token are used
CALL_JS = """async ({path, method, body, image}) => {
  const xsrf = decodeURIComponent((document.cookie.match(/XSRF-TOKEN=([^;]+)/) || [])[1] || '');
  const headers = {Accept: 'application/json', 'X-XSRF-TOKEN': xsrf, 'X-Requested-With': 'XMLHttpRequest'};
  let payload;
  if (image) {
    const bytes = Uint8Array.from(atob(image.data), c => c.charCodeAt(0));
    payload = new FormData();
    payload.append('image', new File([bytes], image.name, {type: 'image/jpeg'}));
  } else if (body) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  const response = await fetch('/api' + path, {method, headers, body: payload, credentials: 'include'});
  return {status: response.status, text: await response.text()};
}"""


def editor_page(playwright) -> Page:
    browser = playwright.chromium.connect_over_cdp(CDP)
    return next(pg for pg in browser.contexts[0].pages if f"toonbee.ai/editor/{PROJECT_ID}" in pg.url)


def call(page: Page, method: str, path: str, body: dict | None = None, image: dict | None = None):
    result = page.evaluate(CALL_JS, {"path": path, "method": method, "body": body, "image": image})
    if result["status"] >= 400:
        raise RuntimeError(f"{method} {path} -> {result['status']}: {result['text'][:300]}")
    return json.loads(result["text"]) if result["text"] else None


def upload_image_file(page: Page, slide_id: int, jpeg: Path) -> None:
    data = base64.b64encode(jpeg.read_bytes()).decode()
    call(page, "POST", f"/slides/{slide_id}/upload-image", image={"name": jpeg.name, "data": data})


def upload_image_url(page: Page, slide_id: int, url: str) -> None:
    call(page, "POST", f"/slides/{slide_id}/upload-image", body={"image_url": url})


def free_quota(page: Page) -> dict:
    models = call(page, "GET", "/credit-costs")["video_models"]
    return next(m for m in models if m["id"] == FREE_MODEL_ID)


def status(page: Page) -> dict:
    return call(page, "GET", f"/projects/{PROJECT_ID}/status")
