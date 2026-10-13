"""Assemble Episode 03 (एक कप चियाको ऋण) from Veo clips, TTS narration and a generated score.

Outputs (in <episode>/final/):
  ..._16x9_YouTube_Facebook.mp4         1920x1080, title/cards/moral burned in, captions as sidecar .srt
  ..._nepali_captions.srt               upload as CC on YouTube / Facebook
  ..._9x16_TikTok_Facebook.mp4          1080x1920 full story, burned-in Nepali captions
  ..._9x16_partNofM_Reels_Shorts.mp4    <= 3 min parts for Instagram Reels / YouTube Shorts

Run: py -3 build_episode.py
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

from gen_music import render_score

EDIT = Path(__file__).parent
EPISODE = EDIT.parent.parent
CLIPS = EDIT.parent / "clips"
KEYFRAMES = EPISODE / "keyframes"
NARRATION = EDIT / "narration"
TRANSCRIPTS = EDIT / "transcripts"
WORK = EDIT / "work"
FONTS = WORK / "fonts"
FINAL = EPISODE / "final"
COMMON = EPISODE.parent / "common"
SYSTEM_FONT = Path(r"C:\Windows\Fonts\Nirmala.ttc")

W, H, FPS, AR = 1920, 1080, 24, 48000
CLIP_S = 8.0
NAR_LEAD, NAR_TAIL = 0.5, 0.7
MAX_SLOWDOWN = 1.6
SCENE_FADE = 0.3
AMBIENT_UNDER_NARRATION = 0.45
MUSIC_GAIN = 0.32
PART_MAX_S = 178.0
MIN_PART_S = 30.0
TITLE = "एक कप चियाको ऋण"
NAME = "EP03_एक_कप_चियाको_ऋण"
EPISODE_LABEL = "नानीबाबुको कथा • एपिसोड ०३"
HANDLE = "@nanibabukokatha"
SCENE_MOOD = {1: "tense", 2: "sad", 3: "sad", 4: "warm", 5: "tense", 6: "mystery", 7: "mystery",
              8: "sad", 9: "hopeful", 10: "warm", 11: "joyful", 12: "warm"}
INTRO_TEXT = "एक कप चिया... एउटा भोकाएको बूढो... र एउटा ठूलो रहस्य। सुरु गरौँ आजको कथा — एक कप चियाको ऋण।"
INTRO_SHOTS = (("S1S1", 0.5), ("S3S2", 1.0), ("S5S1", 2.0), ("S7S2", 3.0), ("S9S3", 0.5))
INTRO_SHOT_S = 2.3
ZOOM_PER_FRAME = 0.0006
X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "48"]
AAC = ["-c:a", "aac", "-b:a", "192k", "-ar", str(AR), "-ac", "2"]


# ---------------------------------------------------------------- helpers
def run(args, cwd=None):
    """Run ffmpeg; `cwd` lets subtitles= use relative paths (Windows drive colons break filter parsing)."""
    res = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], capture_output=True, text=True,
                         encoding="utf-8", cwd=cwd)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(map(str, args))[:400]}\n{res.stderr[-2000:]}")


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def scene_of(seg_id):
    return int(re.match(r"S(\d+)S", seg_id).group(1))


def ts_ass(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ts_srt(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def chunk_text(text, max_chars=46):
    """Split text into caption-sized pieces on natural breaks."""
    parts = [p.strip() for p in re.split(r"(?<=[।?!])\s+|\s+—\s+|(?<=\.\.\.)\s+", text) if p.strip()]
    chunks = []
    for part in parts:
        words = part.split()
        pieces = -(-len(part) // max_chars)  # ceil: balanced pieces instead of greedy wrap orphans
        target = len(part) / pieces
        line = ""
        for word in words:
            if line and len(line) + 1 + len(word) > target + 6:
                chunks.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            chunks.append(line)
    return chunks


def spread(chunks, start, end):
    """Give each chunk a time window proportional to its length."""
    total = sum(len(c) for c in chunks) or 1
    events, t = [], start
    for c in chunks:
        d = (end - start) * len(c) / total
        events.append((t, t + d, c))
        t += d
    return events


def caption_events(text, start, end, speaker=""):
    return [{"start": a, "end": b, "speaker": speaker if i == 0 else "", "text": c}
            for i, (a, b, c) in enumerate(spread(chunk_text(text), start, end))]


# ---------------------------------------------------------------- timeline
def dialogue_events(seg):
    """Place each spoken line using Whisper timings when the segment count matches the script."""
    lines = seg["lines"]
    path = TRANSCRIPTS / f"{seg['id']}.json"
    heard = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    limit = clip_len(seg["id"]) or CLIP_S
    if len(heard) == len(lines):
        windows = [(h["start"], min(limit, h["end"] + 0.3)) for h in heard]
    else:
        start = heard[0]["start"] if heard else 0.3
        end = min(limit - 0.2, heard[-1]["end"] + 0.3) if heard else limit - 0.3
        windows = [(a, b) for a, b, _ in spread([t for _, t in lines], start, end)]
    events = []
    for (speaker, text), (a, b) in zip(lines, windows):
        events += caption_events(text, a, b, speaker)
    return events


def clip_len(seg_id):
    clip = CLIPS / f"{seg_id}.mp4"
    return probe_duration(clip) if clip.exists() else None


def build_items(segments, nar_dur):
    by_id = {s["id"]: s for s in segments}
    intro_len = max(len(INTRO_SHOTS) * INTRO_SHOT_S, NAR_LEAD + nar_dur["INTRO"] + 1.0)
    items = [{"kind": "intro", "id": "INTRO", "dur": intro_len, "scene": 0,
              "subs": caption_events(INTRO_TEXT, NAR_LEAD, NAR_LEAD + nar_dur["INTRO"])}]
    for seg in segments:
        sid = seg["id"]
        if seg.get("still"):
            continue  # the moral still is rendered inside the finale item
        item = {"id": sid, "scene": scene_of(sid), "card": seg.get("card")}
        if sid == "S12S1":
            moral = by_id["S12S2"]
            n1, n2 = nar_dur["S12S1"], nar_dur["S12S2"]
            moral_at = NAR_LEAD + n1 + 1.2
            item.update(kind="finale", speed=1.0, n1=n1, dur=moral_at + n2 + 2.5, moral_at=moral_at, moral_len=n2,
                        subs=caption_events(seg["narration"], NAR_LEAD, NAR_LEAD + n1),
                        moral=[s.strip() for s in re.split(r"(?<=[।])\s*", moral["narration"]) if s.strip()])
        elif seg.get("narration"):
            n = nar_dur[sid]
            src = clip_len(sid)
            dur = max(src or 0.0, round(NAR_LEAD + n + NAR_TAIL, 2))
            item.update(kind="narration" if src else "still", dur=dur, src_len=src,
                        speed=min(MAX_SLOWDOWN, dur / src) if src else 1.0,
                        subs=caption_events(seg["narration"], NAR_LEAD, NAR_LEAD + n, seg.get("speaker", "")))
        elif seg.get("lines"):
            item.update(kind="dialogue", dur=clip_len(sid), speed=1.0, subs=dialogue_events(seg))
        else:
            item.update(kind="ambient", dur=clip_len(sid), speed=1.0, subs=[])
        items.append(item)
    for i, item in enumerate(items):
        item["fade_in"] = i == 0 or item["scene"] != items[i - 1]["scene"]
        item["fade_out"] = i == len(items) - 1 or item["scene"] != items[i + 1]["scene"]
    return items


# ---------------------------------------------------------------- per-item render
def fades(dur, item):
    f = []
    if item.get("fade_in"):
        f.append(f"fade=t=in:st=0:d={SCENE_FADE}")
    if item.get("fade_out"):
        f.append(f"fade=t=out:st={dur - SCENE_FADE:.3f}:d={SCENE_FADE}")
    return ("," + ",".join(f)) if f else ""


def video_chain(speed, dur, zoom=False):
    """Stretch, pad by cloning the last frame, and optionally push in slowly so held frames still move."""
    stretch = f"setpts={speed:.4f}*PTS," if speed > 1.001 else ""
    push = (f",zoompan=z='min(1+{ZOOM_PER_FRAME}*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s={W}x{H}:fps={FPS}") if zoom else ""
    return (f"{stretch}scale={W}:{H}:flags=lanczos,fps={FPS},"
            f"tpad=stop_mode=clone:stop_duration={dur:.3f},trim=0:{dur:.3f},setpts=PTS-STARTPTS{push}")


def audio_tempo(speed):
    return f"atempo={1 / speed:.4f}," if speed > 1.001 else ""


def render_clip_item(item, out):
    dur, speed = item["dur"], item["speed"]
    held = item["kind"] == "narration" and item["src_len"] * speed < dur - 0.5
    vf = video_chain(speed, dur, zoom=held) + fades(dur, item)
    args = ["-i", CLIPS / f"{item['id']}.mp4"]
    if item["kind"] == "narration":
        args += ["-i", NARRATION / f"{item['id']}.mp3"]
        graph = (f"[0:v]{vf}[v];"
                 f"[0:a]{audio_tempo(speed)}volume={AMBIENT_UNDER_NARRATION},apad,atrim=0:{dur:.3f}[amb];"
                 f"[1:a]aresample={AR},adelay={int(NAR_LEAD * 1000)}:all=1,apad,atrim=0:{dur:.3f}[nar];"
                 f"[amb][nar]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo[a]")
    else:
        graph = f"[0:v]{vf}[v];[0:a]aresample={AR},apad,atrim=0:{dur:.3f},aformat=channel_layouts=stereo[a]"
    run([*args, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *X264, *AAC, "-t", f"{dur:.3f}", out])


def render_intro(item, out):
    args, parts = [], []
    for i, (sid, ss) in enumerate(INTRO_SHOTS):
        args += ["-ss", ss, "-t", INTRO_SHOT_S, "-i", CLIPS / f"{sid}.mp4"]
        parts.append(f"[{i}:v]scale={W}:{H}:flags=lanczos,fps={FPS},setpts=PTS-STARTPTS[v{i}];"
                     f"[{i}:a]aresample={AR},volume=0.25,aformat=channel_layouts=stereo[a{i}]")
    n, dur = len(INTRO_SHOTS), item["dur"]
    args += ["-i", NARRATION / "INTRO.mp3"]
    concat = "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]"
    graph = (";".join(parts) + ";" + concat + ";"
             f"[cv]tpad=stop_mode=clone:stop_duration={dur:.3f},trim=0:{dur:.3f},setpts=PTS-STARTPTS{fades(dur, item)}[v];"
             f"[{n}:a]aresample={AR},adelay={int(NAR_LEAD * 1000)}:all=1[nar];"
             f"[ca]apad,atrim=0:{dur:.3f}[amb];[amb][nar]amix=inputs=2:normalize=0,apad,atrim=0:{dur:.3f}[a]")
    run([*args, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *X264, *AAC, "-t", f"{dur:.3f}", out])


def render_finale(item, out):
    """S12S1 clip slowed, cross-fading into a slow push-in on the moral still (S12S2)."""
    dur = item["dur"]
    first_len = NAR_LEAD + item["n1"] + 0.6
    still_len = dur - first_len + 1.0
    graph = (f"[0:v]{ken_burns(first_len)},format=yuv420p[c];"
             f"[1:v]{ken_burns(still_len)},format=yuv420p[s];"
             f"[c][s]xfade=transition=fade:duration=1:offset={first_len - 1:.3f}{fades(dur, item)}[v];"
             f"anullsrc=r={AR}:cl=stereo,atrim=0:{dur:.3f}[amb];"
             f"[2:a]aresample={AR},adelay={int(NAR_LEAD * 1000)}:all=1[n1];"
             f"[3:a]aresample={AR},adelay={int(item['moral_at'] * 1000)}:all=1[n2];"
             f"[amb][n1][n2]amix=inputs=3:normalize=0,apad,atrim=0:{dur:.3f},aformat=channel_layouts=stereo[a]")
    run(["-loop", "1", "-i", KEYFRAMES / "S12S1.png", "-loop", "1", "-i", KEYFRAMES / "S12S2.png",
         "-i", NARRATION / "S12S1.mp3", "-i", NARRATION / "S12S2.mp3",
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *X264, *AAC, "-t", f"{dur:.3f}", out])


def ken_burns(seconds):
    return (f"scale=3840:2160,zoompan=z='min(1.0+{ZOOM_PER_FRAME}*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={int(seconds * FPS) + 1}:s={W}x{H}:fps={FPS},trim=0:{seconds:.3f},setpts=PTS-STARTPTS")


def render_still(item, out):
    """Narration over a slow push-in on the keyframe (scenes without a generated clip)."""
    dur = item["dur"]
    graph = (f"[0:v]{ken_burns(dur)},format=yuv420p{fades(dur, item)}[v];"
             f"[1:a]aresample={AR},adelay={int(NAR_LEAD * 1000)}:all=1,apad,atrim=0:{dur:.3f},"
             f"aformat=channel_layouts=stereo[a]")
    run(["-loop", "1", "-i", KEYFRAMES / f"{item['id']}.png", "-i", NARRATION / f"{item['id']}.mp3",
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *X264, *AAC, "-t", f"{dur:.3f}", out])


def render_bumper(src, out):
    graph = (f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},setpts=PTS-STARTPTS[v];"
             f"[0:a]aresample={AR},aformat=channel_layouts=stereo[a]")
    run(["-i", src, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *X264, *AAC, out])


# ---------------------------------------------------------------- captions
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Nirmala UI,{sub},&H00FFFFFF,&H00FFFFFF,&H00392F8C,&H96000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,{subv},1
Style: Card,Nirmala UI,{card},&H0005B7F2,&H00FFFFFF,&H00392F8C,&H96000000,1,0,0,0,100,100,0,0,1,5,3,8,60,60,{cardv},1
Style: Title,Nirmala UI,{title},&H0005B7F2,&H00FFFFFF,&H00392F8C,&H96000000,1,0,0,0,100,100,0,0,1,6,3,8,60,60,{titlev},1
Style: Small,Nirmala UI,{small},&H00E9F6FF,&H00FFFFFF,&H00392F8C,&H96000000,1,0,0,0,100,100,0,0,1,4,2,8,60,60,{smallv},1
Style: Moral,Nirmala UI,{moral},&H0005B7F2,&H00FFFFFF,&H00392F8C,&H96000000,1,0,0,0,100,100,0,0,1,5,3,8,90,90,{moralv},1
Style: Handle,Nirmala UI,{small},&H00E9F6FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,1,2,60,60,{handlev},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# Colours are &HBBGGRR: gold #F2B705 text, maroon #8C2F39 outline (brand_guidelines.md)
LAND = dict(w=W, h=H, sub=54, subv=50, card=70, cardv=70, title=96, titlev=420, small=46, smallv=340,
            moral=56, moralv=110, moralrow=95, handlev=30)
VERT = dict(w=1080, h=1920, sub=54, subv=560, card=58, cardv=1420, title=74, titlev=250, small=42, smallv=170,
            moral=44, moralv=1290, moralrow=150, handlev=110)


def program_events(items, offsets):
    """All timed text in program time: captions (subs) and overlays (cards, title, moral)."""
    subs, overlays = [], []
    for item, t0 in zip(items, offsets):
        subs += [{**e, "start": t0 + e["start"], "end": t0 + e["end"]} for e in item.get("subs", [])]
        if item.get("card"):
            overlays.append(("Card", t0 + 0.3, t0 + 3.0, item["card"]))
        if item["kind"] == "intro":
            end = t0 + item["dur"]
            overlays += [("Small", end - 5.2, end - 0.2, EPISODE_LABEL),
                         ("Title", end - 5.0, end - 0.2, TITLE)]
        if item["kind"] == "finale":
            start = t0 + item["moral_at"]
            for row, (a, _b, text) in enumerate(spread(item["moral"], start, start + item["moral_len"])):
                overlays.append(("Moral", a, t0 + item["dur"] - 0.3, text, row))
    return subs, overlays


def write_ass(path, geom, subs, overlays, shift=0.0, end=None, captions=True):
    lines = [ASS_HEAD.format(**geom)]
    for style, a, b, text, *row in overlays:
        if end is not None and (b < shift or a > end):
            continue
        margin = geom["moralv"] + row[0] * geom["moralrow"] if row else 0
        lines.append(f"Dialogue: 1,{ts_ass(a - shift)},{ts_ass(b - shift)},{style},,0,0,{margin},,{{\\fad(400,300)}}{text}")
    for e in subs if captions else []:
        if end is not None and (e["end"] < shift or e["start"] > end):
            continue
        who = f"{{\\c&H05B7F2&}}{e['speaker']}:{{\\c&HFFFFFF&}} " if e["speaker"] else ""
        lines.append(f"Dialogue: 0,{ts_ass(e['start'] - shift)},{ts_ass(e['end'] - shift)},Sub,,0,0,0,,{who}{e['text']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def write_srt(path, subs):
    rows = []
    for i, e in enumerate(sorted(subs, key=lambda s: s["start"]), 1):
        who = f"{e['speaker']}: " if e["speaker"] else ""
        rows.append(f"{i}\n{ts_srt(e['start'])} --> {ts_srt(e['end'])}\n{who}{e['text']}\n")
    path.write_text("\n".join(rows), encoding="utf-8")


# ---------------------------------------------------------------- final outputs
def mix_master(program, music, out):
    graph = ("[0:a]asplit=2[voice][key];"
             f"[1:a]volume={MUSIC_GAIN}[m];"
             "[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck];"
             "[voice][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    run(["-i", program, "-i", music, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", *AAC, out])


def burn_landscape(clean, ass_path, out):
    run(["-i", clean, "-vf", f"subtitles={ass_path.name}:fontsdir=fonts", *X264, "-c:a", "copy",
         "-movflags", "+faststart", out], cwd=WORK)


def render_vertical(clean, ass_path, out, start=None, end=None):
    seek = ["-ss", f"{start:.3f}", "-to", f"{end:.3f}"] if start is not None else []
    graph = ("[0:v]split[a][b];"
             "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,eq=brightness=-0.18[bg];"
             "[b]scale=1080:-2:flags=lanczos[fg];"
             f"[bg][fg]overlay=0:620,subtitles={ass_path.name}:fontsdir=fonts[v]")
    run([*seek, "-i", clean, "-filter_complex", graph, "-map", "[v]", "-map", "0:a",
         *X264, *AAC, "-movflags", "+faststart", out], cwd=WORK)


def split_points(items, offsets, total):
    """Cut at scene starts so each vertical part is <= PART_MAX_S."""
    bounds = sorted({t for item, t in zip(items, offsets) if item["fade_in"]} | {total})
    parts, start = [], 0.0
    while total - start > 0.5:
        if total - start <= PART_MAX_S:
            parts.append((start, total))
            break
        fits = [b for b in bounds if start + MIN_PART_S < b <= start + PART_MAX_S]
        stop = max(fits) if fits else start + PART_MAX_S
        parts.append((start, stop))
        start = stop
    return parts


def render_program(items):
    pieces = [WORK / "000_entry.mp4"]
    render_bumper(COMMON / "0.0_Entry_Scene_202608010943.mp4", pieces[0])
    renderers = {"intro": render_intro, "finale": render_finale, "still": render_still}
    for i, item in enumerate(items, 1):
        out = WORK / f"{i:03d}_{item['id']}.mp4"
        renderers.get(item["kind"], render_clip_item)(item, out)
        item["dur"] = probe_duration(out)
        pieces.append(out)
        print(f"rendered {out.name} {item['dur']:.2f}s", flush=True)
    pieces.append(WORK / "999_last.mp4")
    render_bumper(COMMON / "0.1_Last_Scene_202608010943.mp4", pieces[-1])
    concat_list = WORK / "concat.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    program = WORK / "program.mp4"
    run(["-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", program])
    return program, probe_duration(pieces[0])


def main():
    FONTS.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(exist_ok=True)
    shutil.copy2(SYSTEM_FONT, FONTS / SYSTEM_FONT.name)
    segments = json.loads((EDIT / "segments.json").read_text(encoding="utf-8"))
    nar_dur = json.loads((NARRATION / "_durations.json").read_text(encoding="utf-8"))
    items = build_items(segments, nar_dur)

    program, entry_len = render_program(items)
    offsets, t = [], entry_len
    for item in items:
        offsets.append(t)
        t += item["dur"]
    total = probe_duration(program)

    sections = []
    for item, off in zip(items, offsets):
        mood = SCENE_MOOD.get(item["scene"], "mystery")
        if sections and sections[-1]["mood"] == mood:
            sections[-1]["end"] = off + item["dur"]
        else:
            sections.append({"start": off, "end": off + item["dur"], "mood": mood})
    music = WORK / "music.wav"
    render_score(sections, total, music)
    clean = WORK / "clean_master.mp4"
    mix_master(program, music, clean)

    subs, overlays = program_events(items, offsets)
    write_srt(FINAL / f"{NAME}_nepali_captions.srt", subs)
    land_ass = WORK / "land.ass"
    write_ass(land_ass, LAND, subs, overlays, captions=False)
    burn_landscape(clean, land_ass, FINAL / f"{NAME}_16x9_YouTube_Facebook.mp4")

    header = [("Small", 0, total, "नानीबाबुको कथा"), ("Title", 0, total, TITLE), ("Handle", 0, total, HANDLE)]
    vert_ass = WORK / "vert_full.ass"
    write_ass(vert_ass, VERT, subs, overlays + header)
    render_vertical(clean, vert_ass, FINAL / f"{NAME}_9x16_TikTok_Facebook.mp4")

    parts = split_points(items, offsets, total)
    for n, (a, b) in enumerate(parts, 1):
        label = [("Small", a, b, f"नानीबाबुको कथा • भाग {n}/{len(parts)}"), ("Title", a, b, TITLE),
                 ("Handle", a, b, HANDLE)]
        if n < len(parts):
            label.append(("Card", b - 3.0, b, f"भाग {n + 1} मा जारी... ▶"))
        part_ass = WORK / f"vert_part{n}.ass"
        write_ass(part_ass, VERT, subs, overlays + label, shift=a, end=b)
        render_vertical(clean, part_ass, FINAL / f"{NAME}_9x16_part{n}of{len(parts)}_Reels_Shorts.mp4", a, b)
    print(json.dumps({"total_s": round(total, 2), "parts": [(round(a, 1), round(b, 1)) for a, b in parts]}))


if __name__ == "__main__":
    main()
