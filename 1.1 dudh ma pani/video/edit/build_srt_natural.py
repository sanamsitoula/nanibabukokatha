import json
import re
from pathlib import Path

edit_dir = Path(r"D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video/edit")
transcripts_dir = edit_dir / "transcripts"
edl = json.loads((edit_dir / "edl_trimmed.json").read_text(encoding="utf-8"))

PUNCT_BREAK = set(".,!?;:।")  # danda '।' is the Devanagari full stop
SILENCE_BREAK = 0.5  # seconds
MAX_WORDS = 7


def srt_ts(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    h, rem = divmod(total_ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


entries = []
seg_offset = 0.0

for r in edl["ranges"]:
    name = r["source"]
    seg_start = float(r["start"])
    seg_end = float(r["end"])
    seg_dur = seg_end - seg_start

    tpath = transcripts_dir / f"{name}.json"
    words = json.loads(tpath.read_text(encoding="utf-8"))["words"]
    words = [w for w in words if w.get("type") == "word"
             and w.get("start") is not None and w.get("end") is not None
             and seg_start <= w["start"] < seg_end]

    chunks = []
    current = []
    prev_end = None
    for w in words:
        gap = (w["start"] - prev_end) if prev_end is not None else 0.0
        if current and (gap >= SILENCE_BREAK or len(current) >= MAX_WORDS):
            chunks.append(current)
            current = []
        current.append(w)
        text = (w.get("text") or "").strip()
        if text and text[-1] in PUNCT_BREAK:
            chunks.append(current)
            current = []
        prev_end = w["end"]
    if current:
        chunks.append(current)

    for chunk in chunks:
        c_start = max(seg_start, chunk[0]["start"])
        c_end = min(seg_end, chunk[-1]["end"])
        out_start = max(0.0, c_start - seg_start) + seg_offset
        out_end = max(0.0, c_end - seg_start) + seg_offset
        if out_end <= out_start:
            out_end = out_start + 0.4
        text = " ".join((w.get("text") or "").strip() for w in chunk)
        text = re.sub(r"\s+", " ", text).strip()
        entries.append((out_start, out_end, text))

    seg_offset += seg_dur

entries.sort(key=lambda e: e[0])
lines = []
for i, (a, b, t) in enumerate(entries, start=1):
    lines.append(str(i))
    lines.append(f"{srt_ts(a)} --> {srt_ts(b)}")
    lines.append(t)
    lines.append("")

out_path = edit_dir / "master_natural.srt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out_path} ({len(entries)} cues), total_duration={seg_offset:.2f}s")
