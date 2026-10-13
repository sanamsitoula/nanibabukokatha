"""Generate the EP04 character / location reference sheets in Flow and save them to <episode>/character/."""
import json
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from flow_client import chat_tail, download, flow_page, media_ids, to_grid

EDIT = Path(__file__).parent
OUT = EDIT.parent.parent / "character"
IDS = EDIT / "characters.json"
IMAGE_TIMEOUT_S = 180
SHEET = ("Generate exactly one 16:9 image with Nano Banana 2 (only 1 output). Character reference sheet, high-quality 2D "
         "Nepali cartoon animation style, clean bold outlines, flat warm colors, expressive large eyes, plain light beige "
         "background, no text or labels. Full-body figures standing side by side, front view. ")
SHEETS = {
    "KIDS": SHEET + "LEFT: Ravi, a 10-year-old Nepali village boy, thin, short black hair, curious lively eyes, brown "
            "school shirt, short pants, barefoot. RIGHT: Dipa, a 7-year-old Nepali girl, round face, two small braids, "
            "big eyes, yellow frock, barefoot.",
    "MUK_MAILA": SHEET + "LEFT: Mukhiya Dhanbahadur, a 58-year-old Nepali village headman, heavyset, thick grey moustache, "
                 "stern face, brown coat, black Nepali topi, wooden walking stick in hand. RIGHT: Maila, a 35-year-old "
                 "thin Nepali woodcutter with a light stubble beard, playful clever face, patched brown tunic, Dhaka topi.",
    # a sheet that paired Govinda with a young boy was blocked by Flow's content filter; keep him alone
    "BAJE": SHEET + "One figure only: Govinda, an 80-year-old Nepali village grandfather, long white beard, calm kind "
            "eyes, white Nepali topi, old cream kurta and a grey shawl, leaning on a wooden stick.",
    "RIDGE": ("Generate exactly one 16:9 image with Nano Banana 2 (only 1 output). Location reference, high-quality 2D "
              "Nepali cartoon animation style, clean bold outlines, soft hand-painted background, warm daylight, no "
              "people, no text. A Nepali hill village: one single huge ancient banyan-like tree with thick exposed roots "
              "standing alone on top of a bare ridge covered in tree stumps; just below it a small stone-and-mud house "
              "with a slate roof and a wooden cowshed; more slate-roof houses and terraced fields further down the slope."),
}


def generate_image(page: Page, prompt: str) -> str:
    to_grid(page)
    before = set(media_ids(page))
    box = page.locator("[contenteditable=true]:visible, textarea:visible").last
    box.click(timeout=8000)
    page.keyboard.insert_text(prompt)
    page.get_by_role("button", name="Start generation").click()
    deadline = time.time() + IMAGE_TIMEOUT_S
    while time.time() < deadline:
        page.wait_for_timeout(4000)
        fresh = [m for m in media_ids(page) if m not in before]
        if fresh:
            return fresh[0]
    raise TimeoutError("no image appeared: " + chat_tail(page))


def main() -> None:
    known = json.loads(IDS.read_text(encoding="utf-8")) if IDS.exists() else {}
    with sync_playwright() as playwright:
        page = flow_page(playwright)
        for name, prompt in SHEETS.items():
            if name in known:
                continue
            media_id = generate_image(page, prompt)
            download(page, media_id, OUT / f"{name}.png")
            known = {**known, name: media_id}
            IDS.write_text(json.dumps(known, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
