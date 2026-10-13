"""Voice every dialogue line with edge-tts for the ToonBee cut, whose clips are silent.

Writes dialogue/<segment id>.wav (all lines of the segment in order, with pauses) and
dialogue/_timings.json (segment id -> {"dur": seconds, "lines": [{"start", "end"}, ...]}) for caption timing.
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

from gen_narration import MAX_ATTEMPTS, RETRY_DELAY_S, duration

HERE = Path(__file__).parent
OUT = HERE / "dialogue"
LINES = OUT / "lines"
MALE, FEMALE = "ne-NP-SagarNeural", "ne-NP-HemkalaNeural"
# edge-tts has one Nepali voice per gender, so characters are told apart by pitch and pace
VOICES = {
    "अर्जुन": (MALE, "-4%", "-6Hz"),
    "सुनिता": (FEMALE, "+0%", "-2Hz"),
    "रवि": (MALE, "+10%", "+38Hz"),
    "दिपा": (FEMALE, "+6%", "+28Hz"),
    "माइला दाजु": (MALE, "+8%", "+10Hz"),
    "मुखिया धनबहादुर": (MALE, "-8%", "-20Hz"),
    "हजुरबा गोविन्द": (MALE, "-18%", "-14Hz"),
    "सानो अर्जुन": (FEMALE, "+8%", "+45Hz"),
    "गाउँले १": (MALE, "+0%", "-10Hz"),
}
LEAD_S = 0.4
GAP_S = 0.35
TAIL_S = 0.5
SAMPLE_RATE = 48000


async def synth(target: Path, speaker: str, text: str) -> float:
    voice, rate, pitch = VOICES[speaker]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if target.exists() and target.stat().st_size > 0:
            break
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(target))
        except Exception as exc:  # network drops are common; retry, then surface the failure
            target.unlink(missing_ok=True)
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"TTS failed for {target.name}") from exc
            await asyncio.sleep(RETRY_DELAY_S * attempt)
    return duration(target)


def mix(segment_id: str, files: list[Path], starts: list[float], total: float) -> None:
    inputs = [arg for f in files for arg in ("-i", str(f))]
    delayed = ";".join(f"[{i}:a]aresample={SAMPLE_RATE},adelay={int(s * 1000)}:all=1[a{i}]" for i, s in enumerate(starts))
    graph = (f"{delayed};{''.join(f'[a{i}]' for i in range(len(files)))}amix=inputs={len(files)}:normalize=0,"
             f"apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[a]",
                    str(OUT / f"{segment_id}.wav")], check=True)


async def main() -> None:
    LINES.mkdir(parents=True, exist_ok=True)
    timings = {}
    for seg in json.loads((HERE / "segments.json").read_text(encoding="utf-8")):
        if not seg.get("lines"):
            continue
        files, starts, windows, at = [], [], [], LEAD_S
        for index, (speaker, text) in enumerate(seg["lines"]):
            target = LINES / f"{seg['id']}_{index}.mp3"
            length = await synth(target, speaker, text)
            files.append(target)
            starts.append(at)
            windows.append({"start": round(at, 3), "end": round(at + length, 3)})
            at += length + GAP_S
        total = round(at - GAP_S + TAIL_S, 3)
        mix(seg["id"], files, starts, total)
        timings[seg["id"]] = {"dur": total, "lines": windows}
        print(seg["id"], total, flush=True)
    (OUT / "_timings.json").write_text(json.dumps(timings, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
