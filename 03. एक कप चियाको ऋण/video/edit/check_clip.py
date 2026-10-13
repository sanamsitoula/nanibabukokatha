"""Sanity-check generated clips: frame strip + loudness + Whisper transcript (Nepali).

Usage: py -3 check_clip.py <out_dir> clip1.mp4 [clip2.mp4 ...]
Writes <out_dir>/<clip>_strip.jpg and prints duration, mean volume and transcript per clip.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

FRAME_TIMES = (0.1, 2.6, 5.2, 7.8)
_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    return _model


def strip(clip, out_path):
    args, tags = [], ""
    for i, t in enumerate(FRAME_TIMES):
        args += ["-ss", str(t), "-i", str(clip)]
        tags += f"[{i}:v]scale=480:270[v{i}];"
    graph = tags + "".join(f"[v{i}]" for i in range(len(FRAME_TIMES))) + f"hstack=inputs={len(FRAME_TIMES)}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", graph, "-frames:v", "1", "-q:v", "4", str(out_path)], check=True)


def mean_volume(clip):
    res = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(clip), "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True)
    found = re.search(r"mean_volume: (-?[\d.]+) dB", res.stderr)
    return float(found.group(1)) if found else None


def decode_audio(clip):
    """Decode to 16 kHz mono float32 with ffmpeg (avoids faster-whisper's PyAV decoder)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


TRANSCRIPTS = Path(__file__).parent / "transcripts"


def transcript(clip):
    segments, _info = model().transcribe(decode_audio(clip), language="ne", vad_filter=True)
    segments = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
    TRANSCRIPTS.mkdir(exist_ok=True)
    (TRANSCRIPTS / f"{Path(clip).stem}.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1), encoding="utf-8")
    return " | ".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments)


def main(out_dir, clips):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for clip in map(Path, clips):
        strip(clip, out / f"{clip.stem}_strip.jpg")
        print(f"{clip.stem}: vol={mean_volume(clip)} dB :: {transcript(clip)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2:])
