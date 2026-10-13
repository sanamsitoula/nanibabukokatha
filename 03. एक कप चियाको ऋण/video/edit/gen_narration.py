"""Generate Nepali narration audio (edge-tts) for every segment in segments.json that has `narration`.

Writes narration/<id>.mp3 plus narration/_durations.json (id -> seconds). Existing files are kept.
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

HERE = Path(__file__).parent
OUT = HERE / "narration"
VOICE = "ne-NP-SagarNeural"
MAX_ATTEMPTS = 5
RETRY_DELAY_S = 3
STYLES = {
    "narrator": {"rate": "-8%", "pitch": "-2Hz"},
    "baje": {"rate": "-18%", "pitch": "-14Hz"},
    "moral": {"rate": "-13%", "pitch": "-4Hz"},
}
EXTRA = [
    {"id": "INTRO", "narration": "एक कप चिया... एउटा भोकाएको बूढो... र एउटा ठूलो रहस्य। सुरु गरौँ आजको कथा — एक कप चियाको ऋण।"},
]


def style_for(segment):
    if segment.get("moral"):
        return STYLES["moral"]
    return STYLES[segment.get("voice", "narrator")]


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()), 3)


async def synth(segment):
    target = OUT / f"{segment['id']}.mp3"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if target.exists() and target.stat().st_size > 0:
            break
        try:
            await edge_tts.Communicate(segment["narration"], VOICE, **style_for(segment)).save(str(target))
        except Exception as exc:  # network drops are common; retry, then surface the failure
            target.unlink(missing_ok=True)
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"TTS failed for {segment['id']} after {MAX_ATTEMPTS} attempts") from exc
            await asyncio.sleep(RETRY_DELAY_S * attempt)
    return segment["id"], duration(target)


async def main():
    OUT.mkdir(exist_ok=True)
    segments = json.loads((HERE / "segments.json").read_text(encoding="utf-8")) + EXTRA
    durations = dict([await synth(s) for s in segments if s.get("narration")])
    (OUT / "_durations.json").write_text(json.dumps(durations, indent=1), encoding="utf-8")
    print(durations)


if __name__ == "__main__":
    asyncio.run(main())
