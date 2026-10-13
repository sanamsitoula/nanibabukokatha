"""Turn story_segments_raw.json into segments.json: one entry per 8-second clip.

Dialogue that will not fit in one clip is split at sentence breaks into follow-up clips (S2S2, S2S2b, S2S2c).
"""
import json
import re
from pathlib import Path

EDIT = Path(__file__).parent
MAX_CLIP_CHARS = 82  # Omni 1.1 Flash spoke ~72 Nepali characters in 6.2 s on the S1S2 test
SUFFIXES = ("", "b", "c", "d")
CARDS = {"S2S1": "दुई वर्षअघि...", "S9S1": "बिहान...", "S11S1": "भोलिपल्ट..."}
FINALE = "साथीहरू... अर्जुनले काटेनन् एउटा मात्र रूख — तर त्यो एउटा रूखले सिंगो परिवारको ज्यान बचायो। रूखको जरा जति गहिरो जान्छ, रूख उत्तिकै बलियो हुन्छ — र त्यही जराले माटोलाई पनि बलियो बनाउँछ।"
MORAL = "प्रकृतिलाई जोगाए प्रकृतिले हामीलाई जोगाउँछ। एउटा रूख काट्नुअघि सोच्नुहोस् — त्यो केवल दाउरा होइन, त्यो हाम्रो भविष्यको जरा हो।"


def pack(pieces: list[str]) -> list[str]:
    """Greedily join neighbouring pieces while they stay under the per-clip limit."""
    packed: list[str] = []
    for piece in pieces:
        if packed and len(packed[-1]) + 1 + len(piece) <= MAX_CLIP_CHARS:
            packed = [*packed[:-1], f"{packed[-1]} {piece}"]
        else:
            packed = [*packed, piece]
    return packed


def clip_groups(lines: list[list[str]]) -> list[list[list[str]]]:
    units = [[who, part] for who, text in lines for part in pack(re.split(r"(?<=[।!?])\s+", text))]
    groups: list[list[list[str]]] = []
    for unit in units:
        used = sum(len(text) for _, text in groups[-1]) if groups else MAX_CLIP_CHARS
        if used + len(unit[1]) <= MAX_CLIP_CHARS:
            groups = [*groups[:-1], [*groups[-1], unit]]
        else:
            groups = [*groups, [unit]]
    return groups


def build(raw: list[dict]) -> list[dict]:
    segments = []
    for seg in raw:
        base = {"prompt": seg["prompt"], "sfx": seg["sfx"]}
        if seg["id"] == "S12S1":
            segments.append({"id": "S12S1", **base, "narration": FINALE})
        elif seg["id"] == "S12S2":
            segments.append({"id": "S12S2", **base, "narration": MORAL, "still": True, "moral": True})
        elif seg["lines"]:
            for suffix, group in zip(SUFFIXES, clip_groups(seg["lines"]), strict=False):
                segments.append({"id": seg["id"] + suffix, **base, "lines": group, "part": SUFFIXES.index(suffix)})
        else:
            card = {"card": CARDS[seg["id"]]} if seg["id"] in CARDS else {}
            segments.append({"id": seg["id"], **base, "narration": seg["narration"], **card})
    return segments


if __name__ == "__main__":
    built = build(json.loads((EDIT / "story_segments_raw.json").read_text(encoding="utf-8")))
    (EDIT / "segments.json").write_text(json.dumps(built, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(built), "segments;", sum("lines" in s for s in built), "dialogue clips")
    print(" ".join(f"{s['id']}:{sum(len(t) for _, t in s['lines'])}" for s in built if "lines" in s))
