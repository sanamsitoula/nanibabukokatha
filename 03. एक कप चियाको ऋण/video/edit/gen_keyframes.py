"""Generate stylized 1920x1080 keyframe illustrations for each story segment in Episode 03.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
KEYFRAMES_DIR = HERE.parent.parent / "keyframes"
KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS_FILE = HERE / "segments.json"
segments = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))

WIDTH, HEIGHT = 1920, 1080

# Color palettes by mood
PALETTES = {
    "mysterious": ("#1A1C29", "#2E3856", "#C89D7C", "#F4E3B2"),
    "suspense": ("#1E2022", "#393E46", "#F2A365", "#ECECEC"),
    "sad": ("#2B2E4A", "#53354A", "#903749", "#E84545"),
    "emotional": ("#222831", "#393E46", "#00ADB5", "#EEEEEE"),
    "warm": ("#2D132C", "#801336", "#C72C41", "#EE4540"),
    "tense": ("#1B1A17", "#3E2C41", "#E45826", "#F0A500"),
    "epic": ("#0F1026", "#1F293D", "#E09F3E", "#FFF3B0"),
    "uplifting": ("#14213D", "#FCA311", "#E5E5E5", "#FFFFFF"),
    "cheerful": ("#003049", "#D62828", "#F77F00", "#FCBF49"),
    "moral": ("#1E1B18", "#5A3D31", "#DDA15E", "#FEFAE0"),
}


def create_gradient_bg(width: int, height: int, c1_hex: str, c2_hex: str) -> Image.Image:
    im = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(im)

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    r1, g1, b1 = hex_to_rgb(c1_hex)
    r2, g2, b2 = hex_to_rgb(c2_hex)

    for y in range(height):
        t = y / height
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return im


def generate_segment_keyframe(seg: dict) -> None:
    seg_id = seg["id"]
    title = seg.get("title", "")
    mood = seg.get("mood", "warm")
    c1, c2, accent1, accent2 = PALETTES.get(mood, PALETTES["warm"])

    img = create_gradient_bg(WIDTH, HEIGHT, c1, c2)
    draw = ImageDraw.Draw(img)

    # Hill silhouette layers for Nepali village backdrop
    for i in range(3):
        hill_color = (15 + i * 15, 20 + i * 20, 30 + i * 25, 200 - i * 40)
        points = [(0, HEIGHT)]
        for x in range(0, WIDTH + 40, 40):
            y_base = HEIGHT * 0.55 + i * 110
            y_offset = math.sin((x + i * 300) * 0.003) * (80 + i * 30)
            points.append((x, int(y_base + y_offset)))
        points.append((WIDTH, HEIGHT))
        draw.polygon(points, fill=hill_color)

    # Chautari / Pipal Tree silhouette on right
    tree_base_x = WIDTH * 0.82
    tree_base_y = HEIGHT * 0.75
    draw.ellipse(
        [tree_base_x - 180, tree_base_y - 280, tree_base_x + 180, tree_base_y + 40],
        fill=(10, 15, 25, 220),
    )
    draw.rectangle(
        [tree_base_x - 20, tree_base_y - 80, tree_base_x + 20, HEIGHT],
        fill=(8, 12, 20, 240),
    )
    # Chautari stone platform
    draw.rounded_rectangle(
        [tree_base_x - 140, tree_base_y + 60, tree_base_x + 140, tree_base_y + 130],
        radius=12,
        fill=(35, 40, 50, 255),
        outline=(60, 70, 85, 255),
        width=3,
    )

    # Teashop silhouette on left
    shop_x = WIDTH * 0.2
    shop_y = HEIGHT * 0.65
    draw.rectangle([shop_x - 160, shop_y, shop_x + 160, HEIGHT], fill=(20, 25, 35, 240))
    # Tin roof slope
    draw.polygon(
        [
            (shop_x - 200, shop_y),
            (shop_x + 200, shop_y),
            (shop_x + 160, shop_y - 70),
            (shop_x - 160, shop_y - 70),
        ],
        fill=(40, 48, 60, 255),
    )
    # Glowing lantern / tea stall light
    lantern_x = shop_x + 80
    lantern_y = shop_y + 30
    draw.ellipse(
        [lantern_x - 35, lantern_y - 35, lantern_x + 35, lantern_y + 35],
        fill=(255, 200, 100, 180),
    )
    draw.ellipse(
        [lantern_x - 15, lantern_y - 15, lantern_x + 15, lantern_y + 15],
        fill=(255, 240, 180, 255),
    )

    # Frame Vignette & decorative border
    draw.rectangle(
        [30, 30, WIDTH - 30, HEIGHT - 30],
        outline=(255, 215, 0, 90),
        width=4,
    )

    # Episode Header Card
    header_w, header_h = 750, 110
    header_x = (WIDTH - header_w) // 2
    header_y = 70
    draw.rounded_rectangle(
        [header_x, header_y, header_x + header_w, header_y + header_h],
        radius=25,
        fill=(10, 15, 25, 210),
        outline=(255, 195, 0, 200),
        width=3,
    )

    # Subtitle / Scene Name Banner at bottom
    banner_w, banner_h = 950, 90
    banner_x = (WIDTH - banner_w) // 2
    banner_y = HEIGHT - 150
    draw.rounded_rectangle(
        [banner_x, banner_y, banner_x + banner_w, banner_y + banner_h],
        radius=20,
        fill=(15, 20, 30, 220),
        outline=(255, 255, 255, 120),
        width=2,
    )

    # Save Keyframe
    out_path = KEYFRAMES_DIR / f"{seg_id}.png"
    img.convert("RGB").save(out_path, quality=95)
    print(f"Rendered keyframe: {out_path.name}")


def main():
    print(f"Generating {len(segments)} keyframes in {KEYFRAMES_DIR}...")
    for s in segments:
        generate_segment_keyframe(s)
    print("[OK] All keyframes generated successfully!")


if __name__ == "__main__":
    main()
