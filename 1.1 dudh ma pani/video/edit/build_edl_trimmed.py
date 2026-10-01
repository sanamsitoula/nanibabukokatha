import json
from pathlib import Path

base = r"D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video"
edit_dir = Path(base) / "edit"
transcripts_dir = edit_dir / "transcripts"

order = [
    "S1S1_202607231152", "S1S2_202607231158", "S1S3_202607231159", "S1S4_202607231159",
    "S2S1_202607231159", "S2S2_202607231200", "S2S3_202607231201",
    "S3S1_202607231409", "S3S2_202607241201", "S3S3_202607231416", "S3S4_202607231416",
    "S4S1_202607231417", "S4S2_202607262042", "S4S3_202607262043",
    "S5S1_202607262050", "S5S2_202607262022", "S5S3_202607262020", "S5S4_202607262107",
    "S6S1_202607262108", "S6S2_202607262108", "S6S3_202607241203", "S6S4_202607241202",
    "S7S1_202607262016", "S7S2_202607241202", "S7S3---_202607241202", "S7S4_202607241202",
    "S8S1_202607241200", "S8S2_202607241201", "S8S3_202607241201", "S8S4_202607262119",
    "S9S1_202607241202", "S9S2_202607241201", "S9S3_202607262123", "S9S4_202607262128",
    "S10S1_202607262132", "S10S2_202607262136", "S10S3_202607262139", "S10S4_202607262149", "S10S5_202607262015",
    "S11S1_202607262014", "S11S2_202607262014", "S11S3_202607262014", "S11S4_202607262153",
    "S12S1_202607262035", "S12S2_202607262035",
]

durations = {
    "S10S1_202607262132": 10.005, "S10S2_202607262136": 10.005, "S10S3_202607262139": 10.005,
    "S10S4_202607262149": 10.005, "S10S5_202607262015": 10.005, "S11S1_202607262014": 10.005,
    "S11S2_202607262014": 10.005, "S11S3_202607262014": 8.000, "S11S4_202607262153": 10.005,
    "S12S1_202607262035": 10.005, "S12S2_202607262035": 10.005, "S1S1_202607231152": 10.005,
    "S1S2_202607231158": 10.005, "S1S3_202607231159": 10.005, "S1S4_202607231159": 10.005,
    "S2S1_202607231159": 10.005, "S2S2_202607231200": 10.005, "S2S3_202607231201": 10.005,
    "S3S1_202607231409": 10.005, "S3S2_202607241201": 10.005, "S3S3_202607231416": 10.005,
    "S3S4_202607231416": 10.005, "S4S1_202607231417": 10.005, "S4S2_202607262042": 10.005,
    "S4S3_202607262043": 10.005, "S5S1_202607262050": 10.005, "S5S2_202607262022": 10.005,
    "S5S3_202607262020": 10.005, "S5S4_202607262107": 10.005, "S6S1_202607262108": 10.005,
    "S6S2_202607262108": 10.005, "S6S3_202607241203": 10.005, "S6S4_202607241202": 10.005,
    "S7S1_202607262016": 10.005, "S7S2_202607241202": 10.005, "S7S3---_202607241202": 10.005,
    "S7S4_202607241202": 10.005, "S8S1_202607241200": 10.005, "S8S2_202607241201": 10.005,
    "S8S3_202607241201": 10.005, "S8S4_202607262119": 10.005, "S9S1_202607241202": 10.005,
    "S9S2_202607241201": 10.005, "S9S3_202607262123": 10.005, "S9S4_202607262128": 10.005,
}

LEAD_PAD = 0.05   # 50ms before first word
TAIL_PAD = 0.15   # 150ms after last word

sources = {name: f"{base}/{name}.mp4" for name in order}
ranges = []
total = 0.0
for name in order:
    dur = durations[name]
    tpath = transcripts_dir / f"{name}.json"
    words = json.loads(tpath.read_text(encoding="utf-8"))["words"]
    words = [w for w in words if w.get("type") == "word" and w.get("start") is not None]
    if not words:
        start, end = 0.0, dur
    else:
        first_start = words[0]["start"]
        last_end = words[-1]["end"]
        start = max(0.0, first_start - LEAD_PAD)
        end = min(dur, last_end + TAIL_PAD)
        if end - start < 1.0:  # safety floor
            start, end = 0.0, dur
    seg_dur = end - start
    ranges.append({
        "source": name, "start": round(start, 3), "end": round(end, 3),
        "beat": name, "quote": "", "reason": "trimmed dead air (lead 50ms / tail 150ms pad)",
    })
    total += seg_dur

edl = {
    "version": 1,
    "sources": sources,
    "ranges": ranges,
    "grade": "none",
    "overlays": [],
    "subtitles": None,
    "total_duration_s": round(total, 3),
}

out = edit_dir / "edl_trimmed.json"
out.write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", out, "total_duration_s=", edl["total_duration_s"], "(was 448.22, saved", round(448.22 - total, 2), "s)")
