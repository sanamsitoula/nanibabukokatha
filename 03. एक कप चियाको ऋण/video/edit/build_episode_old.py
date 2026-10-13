"""Assemble Episode 03 (एक कप चियाको ऋण) from keyframe scenes, narration, and Nepali background score.

Outputs (in <episode>/final/):
  ..._16x9_YouTube_Facebook.mp4         1920x1080, title/cards/moral, captions
  ..._nepali_captions.srt               upload as CC on YouTube/Facebook
  ..._9x16_TikTok_Facebook.mp4          1080x1920 full story, burned-in Nepali captions
  ..._9x16_partNofM_Reels_Shorts.mp4    <= 3 min parts for Instagram Reels / Shorts
  ..._thumbnail_1280x720.jpg            YouTube / Facebook thumbnail
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FINAL_DIR = ROOT / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
WORK_DIR = HERE / "work"
WORK_DIR.mkdir(parents=True, exist_ok=True)
KEYFRAMES_DIR = ROOT / "keyframes"
NARRATION_DIR = HERE / "narration"
COMMON_DIR = ROOT.parent / "common"

SEGMENTS_FILE = HERE / "segments.json"
segments = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))

DURATIONS_FILE = NARRATION_DIR / "_durations.json"
durations = (
    json.loads(DURATIONS_FILE.read_text(encoding="utf-8"))
    if DURATIONS_FILE.exists()
    else {}
)


def make_thumbnail():
    thumb_path = FINAL_DIR / "EP03_thumbnail_1280x720.jpg"
    im = Image.new("RGB", (1280, 720), "#1A1A24")
    draw = ImageDraw.Draw(im)

    # Gradient glow
    for y in range(720):
        t = y / 720
        r = int(30 + t * 40)
        g = int(20 + t * 15)
        b = int(45 + t * 20)
        draw.line([(0, y), (1280, y)], fill=(r, g, b))

    # Border frame
    draw.rectangle([20, 20, 1260, 700], outline="#F2B705", width=6)

    # Title Card
    draw.rounded_rectangle(
        [140, 220, 1140, 480], radius=30, fill=(10, 12, 18), outline="#F2B705", width=4
    )

    im.save(thumb_path, quality=95)
    print(f"[Thumbnail] Created {thumb_path.name}")


def generate_srt(subs: list[dict], out_path: Path):
    lines = []

    def fmt_time(s: float) -> str:
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        ms = int(round((s - int(s)) * 1000))
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    for i, sub in enumerate(subs, 1):
        lines.append(f"{i}")
        lines.append(f"{fmt_time(sub['start'])} --> {fmt_time(sub['end'])}")
        lines.append(sub["text"])
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SRT] Generated subtitles at {out_path.name}")


def render_segments_and_concat():
    seg_video_files = []
    current_time = 0.0
    subtitle_events = []

    print("[Build] Rendering segment clips...")
    for idx, seg in enumerate(segments):
        seg_id = seg["id"]
        audio_file = NARRATION_DIR / f"{seg_id}.mp3"
        image_file = KEYFRAMES_DIR / f"{seg_id}.png"

        # Calculate duration from audio + 1.2s padding
        aud_dur = durations.get(seg_id, 8.0)
        seg_dur = max(6.0, aud_dur + 1.2)

        out_clip = WORK_DIR / f"clip_{idx:02d}_{seg_id}.mp4"

        # Zoom / pan motion filter on 1920x1080 keyframe
        zoom_direction = "in" if idx % 2 == 0 else "out"
        z_expr = (
            f"min(zoom+0.0008,1.15)"
            if zoom_direction == "in"
            else f"if(eq(on,1),1.15,max(1.0,zoom-0.0008))"
        )
        vf = f"scale=8000:-1,zoompan=z='{z_expr}':d={int(seg_dur*30)}:s=1920x1080:fps=30"

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_file),
            "-i",
            str(audio_file) if audio_file.exists() else str(image_file),
            "-t",
            str(seg_dur),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_clip),
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        seg_video_files.append(out_clip)

        subtitle_events.append({
            "start": current_time,
            "end": current_time + seg_dur,
            "text": seg["narration"],
        })
        current_time += seg_dur

    # Save SRT
    srt_file = FINAL_DIR / "EP03_एक_कप_चियाको_ऋण_nepali_captions.srt"
    generate_srt(subtitle_events, srt_file)

    # Concat list
    concat_txt = WORK_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for v in seg_video_files:
            p_str = str(v.resolve()).replace("\\", "/")
            f.write(f"file '{p_str}'\n")

    # Master 16:9 Video
    out_16x9 = FINAL_DIR / "EP03_एक_कप_चियाको_ऋण_16x9_YouTube_Facebook.mp4"
    print(f"[Build] Concatenating 16:9 Master Video -> {out_16x9.name}")
    cmd_16x9 = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_txt),
        "-c",
        "copy",
        str(out_16x9),
    ]
    subprocess.run(cmd_16x9, capture_output=True, check=True)

    # Vertical 9:16 Video (1080x1920) for TikTok/Reels
    out_9x16 = FINAL_DIR / "EP03_एक_कप_चियाको_ऋण_9x16_TikTok_Facebook.mp4"
    print(f"[Build] Rendering 9:16 Vertical Full Video -> {out_9x16.name}")
    # Crop & format for 9:16 with background blur / vertical pillarbox
    cmd_9x16 = [
        "ffmpeg",
        "-y",
        "-i",
        str(out_16x9),
        "-vf",
        "split[original][copy];[copy]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[blurred];[original]scale=1080:-1[scaled];[blurred][scaled]overlay=(W-w)/2:(H-h)/2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(out_9x16),
    ]
    subprocess.run(cmd_9x16, capture_output=True, check=True)

    # Vertical Split Parts (Part 1 and Part 2 under 3 minutes each)
    half_time = current_time / 2.0
    out_p1 = FINAL_DIR / "EP03_एक_कप_चियाको_ऋण_9x16_part1of2_Reels_Shorts.mp4"
    out_p2 = FINAL_DIR / "EP03_एक_कप_चियाको_ऋण_9x16_part2of2_Reels_Shorts.mp4"

    print(f"[Build] Creating Split Reels Part 1 & Part 2...")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(out_9x16),
            "-t",
            str(half_time),
            "-c",
            "copy",
            str(out_p1),
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(half_time),
            "-i",
            str(out_9x16),
            "-c",
            "copy",
            str(out_p2),
        ],
        capture_output=True,
        check=True,
    )

    make_thumbnail()
    print("\n[SUCCESS] All Episode 03 videos and assets rendered successfully!")


def main():
    render_segments_and_concat()


if __name__ == "__main__":
    main()
