"""Extract the 10-second segment breakdown of story.md into story_segments_raw.json."""
import json
import re
from pathlib import Path

EDIT = Path(__file__).parent
STORY = EDIT.parent.parent / "story.md"
OUT = EDIT / "story_segments_raw.json"
SEGMENT = re.compile(r"###\s*SCENE\s*(\d+)\s*—\s*SEGMENT\s*(\d+)([\s\S]+?)(?=\n###\s|\n##\s|\n#\s|\Z)")
LINE = re.compile(r"\*\*([^*:]+):\*\*\s*(?:\*\([^)]*\)\*\s*)?\"([^\"]+)\"")


def field(body: str, name: str) -> str:
    found = re.search(rf"\*\*{name}:\*\*\s*(.+)", body)
    return found.group(1).strip() if found else ""


def parse(text: str) -> list[dict]:
    segments = []
    for scene, number, body in SEGMENT.findall(text):
        segments.append({
            "id": f"S{scene}S{number}",
            "prompt": field(body, "Video Prompt"),
            "narration": field(body, "Narration").strip('"'),
            "lines": [[who.strip(), said.strip()] for who, said in LINE.findall(field(body, "Dialogue"))],
            "voice": field(body, "Voice Direction"),
            "sfx": field(body, "Sound Effects"),
            "music": field(body, "Music"),
        })
    return segments


if __name__ == "__main__":
    parsed = parse(STORY.read_text(encoding="utf-8"))
    OUT.write_text(json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(parsed), "segments;", sum(bool(s["lines"]) for s in parsed), "with dialogue;",
          sum(bool(s["narration"]) for s in parsed), "with narration;",
          sum(not s["lines"] and not s["narration"] for s in parsed), "silent")
