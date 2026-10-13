"""production/segments.json + cast.json -> production/voice/<segment>-<n>.mp3 and voice.json (timings).

    python pipeline/voice.py "10. मास्टर सापको फाटेको जुत्ता"

Free Microsoft Edge voices (needs internet, no key). Only two Nepali voices exist, so each role in
cast.json is one of them with its own pitch and speed. A line that already has its file is skipped.
"""
import asyncio
import json
import subprocess
import sys

import edge_tts

from segments import story_dir

WOMAN, MAN = "ne-NP-HemkalaNeural", "ne-NP-SagarNeural"
ROLES = {                       # role: (voice, rate, pitch)
    "narrator": (WOMAN, "-6%", "-2Hz"),
    "woman": (WOMAN, "+0%", "+4Hz"),
    "girl": (WOMAN, "+6%", "+28Hz"),
    "boy": (WOMAN, "+8%", "+14Hz"),
    "man": (MAN, "+0%", "+0Hz"),
    "old_man": (MAN, "-10%", "-12Hz"),
}
CLIP_SECONDS = 10.0
PAUSE_SECONDS = 0.35            # gap between two lines of one segment


def seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()), 2)


async def speak(text, role, path):
    voice, rate, pitch = ROLES[role]
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path))


async def main(name):
    production = story_dir(name) / "production"
    segments = json.loads((production / "segments.json").read_text(encoding="utf-8"))
    cast = json.loads((production / "cast.json").read_text(encoding="utf-8"))
    unknown = sorted({line["speaker"] for s in segments for line in s["lines"] if cast.get(line["speaker"]) not in ROLES})
    if unknown:
        raise SystemExit("cast.json needs one of " + ", ".join(ROLES) + " for: " + ", ".join(unknown))
    voice_dir = production / "voice"
    voice_dir.mkdir(exist_ok=True)
    timings = []
    for segment in segments:
        files = []
        for index, line in enumerate(segment["lines"], start=1):
            path = voice_dir / f"{segment['id']}-{index}.mp3"
            if not path.is_file() or path.stat().st_size == 0:
                await speak(line["text"], cast[line["speaker"]], path)
            files.append({"file": path.name, "speaker": line["speaker"], "text": line["text"], "seconds": seconds(path)})
        spoken = round(sum(f["seconds"] for f in files) + PAUSE_SECONDS * max(len(files) - 1, 0), 2)
        timings.append({"id": segment["id"], "spoken_seconds": spoken, "lines": files})
    (production / "voice.json").write_text(json.dumps(timings, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(t["spoken_seconds"] for t in timings)
    over = [f"{t['id']} {t['spoken_seconds']}s" for t in timings if t["spoken_seconds"] > CLIP_SECONDS]
    print(f"{sum(len(t['lines']) for t in timings)} lines, {total:.0f} s of speech over {len(timings)} segments")
    print("Longer than one 10-second clip: " + (", ".join(over) if over else "none"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    asyncio.run(main(sys.argv[1]))
