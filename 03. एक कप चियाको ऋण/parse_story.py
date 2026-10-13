import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
STORY_FILE = HERE / "story.md"
OUT_FILE = HERE / "video" / "edit" / "segments.json"

text = STORY_FILE.read_text(encoding="utf-8")

# Parse 10-second segment breakdown
seg_pattern = re.compile(
    r"###\s*SCENE\s*(\d+)\s*—\s*SEGMENT\s*(\d+)([\s\S]+?)(?=###\s*SCENE|\Z)",
    re.IGNORECASE,
)
matches = list(seg_pattern.finditer(text))

segments = []
for m in matches:
    scene_num = int(m.group(1))
    seg_num = int(m.group(2))
    content = m.group(3)
    seg_id = f"S{scene_num}S{seg_num}"

    # Narration
    narr_m = re.search(r"\*\*Narration:\*\*\s*\"?([^\n\"]+)\"?", content)
    narr = narr_m.group(1).strip() if narr_m else ""

    # Prompt
    prompt_m = re.search(r"\*\*Video Prompt:\*\*\s*([\s\S]+?)(?=\n\*\*|\Z)", content)
    prompt = prompt_m.group(1).strip() if prompt_m else ""

    # SFX
    sfx_m = re.search(r"\*\*Sound Effects:\*\*\s*([^\n]+)", content)
    sfx = sfx_m.group(1).strip() if sfx_m else ""

    # Music
    music_m = re.search(r"\*\*Music:\*\*\s*([^\n]+)", content)
    music = music_m.group(1).strip() if music_m else ""

    # Voice / Role
    voice = "narrator"
    if scene_num == 12:
        voice = "moral"

    segments.append({
        "id": seg_id,
        "scene": scene_num,
        "segment": seg_num,
        "narration": narr,
        "prompt": prompt,
        "sfx": sfx,
        "music": music,
        "voice": voice,
        "duration": 10.0,
    })

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(segments, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Successfully extracted {len(segments)} segments into {OUT_FILE}")
