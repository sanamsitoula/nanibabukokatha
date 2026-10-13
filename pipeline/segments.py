"""story.md -> production/segments.json: one record per 10-second segment.

    python pipeline/segments.py "10. मास्टर सापको फाटेको जुत्ता"
    python pipeline/segments.py --check        parse every story folder and report counts
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_HEADING = re.compile(r"^#{1,3}\s.*10-(SECOND|सेकेन्ड)", re.I)
SCENE_HEADING = re.compile(r"SCENE\s*\d+|दृश्य\s*[\d०-९]+", re.I)
SEGMENT_HEADING = re.compile(r"^#{2,4}\s.*?SCENE\s*(\d+).*?SEGMENT\s*(\d+)", re.I)
FIELD = re.compile(r"^\*\*([^*:]+):\*\*\s*(.*)$")
STAGE_DIRECTION = re.compile(r"\*\([^)]*\)\*|\([^)]*\)")
QUOTED = re.compile(r"[\"“]([^\"”]+)[\"”]")
SPEAKER_QUOTE = re.compile(r"([^\"“”:*]+):\**\s*[\"“]([^\"”]+)[\"”]")
STYLE_BLOCK = re.compile(r"^\[[^\]]{80,}\]\s*")
NARRATOR = "narrator"
FIELDS = {
    "duration": "duration", "video prompt": "prompt", "character consistency": "consistency",
    "narration": "narration", "narration (voiceover)": "narration", "dialogue": "dialogue",
    "voice direction": "voice_direction", "sound effects": "sfx", "music": "music", "ending hook": "hook",
}


def spoken(text):
    """The words to be voiced: what is inside quotes, without stage directions."""
    text = STAGE_DIRECTION.sub(" ", text)
    quoted = QUOTED.findall(text)
    return " ".join(part.strip() for part in quoted) if quoted else text.strip().strip("*").strip()


def utterances(text):
    """Dialogue text -> (speaker, words) pairs. One line may hold several speakers."""
    text = STAGE_DIRECTION.sub(" ", text)
    pairs = [(speaker.strip(" *—-"), words.strip()) for speaker, words in SPEAKER_QUOTE.findall(text)]
    if pairs:
        return [{"speaker": speaker or NARRATOR, "text": words} for speaker, words in pairs]
    words = spoken(text)
    return [{"speaker": NARRATOR, "text": words}] if words else []


def parse(story_md):
    lines = story_md.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if PROMPTS_HEADING.match(line)), None)
    if start is None:
        raise ValueError(f"No '10-SECOND ... VIDEO PROMPTS' heading in {story_md}")
    segments, current, field = [], None, None
    for line in lines[start + 1:]:
        heading = SEGMENT_HEADING.match(line)
        if heading:
            scene, number = int(heading.group(1)), int(heading.group(2))
            current = {"id": f"s{scene:02d}g{number:02d}", "scene": scene, "segment": number, "lines": []}
            segments.append(current)
            field = None
            continue
        if line.startswith("#") and current:      # next scene heading or the end of the prompt section
            if not SCENE_HEADING.search(line):
                break
            current, field = None, None
            continue
        if current is None or not line.strip() or line.strip() == "---":
            continue
        match = FIELD.match(line)
        label = match.group(1).strip().lower() if match else None
        if label in FIELDS:
            field, value = FIELDS[label], match.group(2).strip()
            if field == "narration" and value:
                current["lines"].append({"speaker": NARRATOR, "text": spoken(value)})
            elif field == "dialogue" and value:
                current["lines"].extend(utterances(value))
            elif field != "dialogue" and value:
                current[field] = STYLE_BLOCK.sub("", value) if field == "prompt" else value
        elif field in ("dialogue", "narration"):      # **राजु:** "..."
            current["lines"].extend(utterances(line))
    return [s for s in segments if s.get("prompt")]


def story_dir(name):
    path = ROOT / name
    if not (path / "story.md").is_file():
        raise SystemExit(f"No story.md in {path}")
    return path


def write(name):
    folder = story_dir(name)
    segments = parse(folder / "story.md")
    out = folder / "production"
    out.mkdir(exist_ok=True)
    (out / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1), encoding="utf-8")
    cast = out / "cast.json"
    speakers = sorted({line["speaker"] for s in segments for line in s["lines"]})
    known = json.loads(cast.read_text(encoding="utf-8")) if cast.is_file() else {}
    merged = {speaker: known.get(speaker, "") for speaker in speakers}
    cast.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    unset = [speaker for speaker, role in merged.items() if not role]
    print(f"{len(segments)} segments, {sum(len(s['lines']) for s in segments)} spoken lines -> {out / 'segments.json'}")
    if unset:
        print("Set a voice role in cast.json for: " + ", ".join(unset))


def check():
    for folder in sorted(p for p in ROOT.iterdir() if (p / "story.md").is_file()):
        try:
            segments = parse(folder / "story.md")
            silent = sum(1 for s in segments if not s["lines"])
            print(f"{folder.name[:3]} segments={len(segments):2d} scenes={len({s['scene'] for s in segments}):2d} "
                  f"lines={sum(len(s['lines']) for s in segments):3d} silent={silent}")
        except ValueError as error:
            print(f"{folder.name[:3]} FAILED: {error}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    check() if sys.argv[1] == "--check" else write(sys.argv[1])
