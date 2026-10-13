"""Assemble the ToonBee cut of Episode 04 for comparison with the Flow cut.

ToonBee clips are silent, so every dialogue line is voiced by gen_dialogue.py and laid under its clip here.
This cut also opens with a cold-open hook (before the channel bumper) and closes with a question and a
next-episode tease (before the closing bumper). Everything else reuses build_episode.py.

Run: py -3 gen_narration_hooks.py, py -3 gen_dialogue.py, then py -3 build_toonbee.py
Outputs go to <episode>/final_toonbee/.
"""
import json
import shutil

import build_episode as be

EDIT = be.EDIT
RAW_CLIPS = be.EPISODE / "video_toonbee" / "clips"
DIALOGUE = EDIT / "dialogue"
HOOKS = EDIT / "narration_hooks"

be.CLIPS = EDIT / "work_toonbee" / "clips"
be.WORK = EDIT / "work_toonbee"
be.FONTS = be.WORK / "fonts"
be.FINAL = be.EPISODE / "final_toonbee"
be.TRANSCRIPTS = be.WORK / "transcripts"
be.NAME = "EP04_बूढो_रूखको_गुन_ToonBee"

HOOK_TEXT = "सबैले रूख काटे... एउटाले काटेन। आज त्यही बूढो रूखले कसको ज्यान बचाउँछ? अन्तिमसम्म हेर्नुहोस्।"
HOOK_TITLE = "यो रूखले कसलाई बचाउँछ?"
HOOK_SHOTS = (("S1S1", 4.5), ("S7S1", 3.0), ("S8S1", 4.0), ("S1S4", 4.0))
OUTRO_TEXT = ("तपाईंको गाउँमा पनि यस्तो बूढो रूख छ? कमेन्टमा भन्नुहोस्। "
              "अर्को कथा — अन्धो ग्राहकको आँखा। हेर्न नबिर्सनुहोस्।")
OUTRO_TITLE = "तपाईंको गाउँमा यस्तो रूख छ?"
OUTRO_SMALL = "अर्को कथा: अन्धो ग्राहकको आँखा"
OUTRO_SHOTS = (("S11S4", 0.0),)
HOOK_SHOT_S = 2.2
MAX_DIALOGUE_SLOWDOWN = 2.0


def prepare_clip(seg: dict, timings: dict) -> None:
    """Give a silent ToonBee clip an audio track: the voiced lines for dialogue, silence otherwise."""
    source, out = RAW_CLIPS / f"{seg['id']}.mp4", be.CLIPS / f"{seg['id']}.mp4"
    if not source.exists() or out.exists():
        return
    length = be.probe_duration(source)
    spoken = timings.get(seg["id"])
    if not spoken:
        be.run(["-i", source, "-f", "lavfi", "-i", f"anullsrc=r={be.AR}:cl=stereo", "-c:v", "copy", *be.AAC,
                "-t", f"{length:.3f}", out])
        return
    total = max(length, spoken["dur"])
    speed = min(MAX_DIALOGUE_SLOWDOWN, total / length)  # slow the picture a little when the lines run long
    graph = (f"[0:v]setpts={speed:.4f}*PTS,fps={be.FPS},tpad=stop_mode=clone:stop_duration={total:.3f},"
             f"trim=0:{total:.3f},setpts=PTS-STARTPTS[v];[1:a]apad,atrim=0:{total:.3f}[a]")
    be.run(["-i", source, "-i", DIALOGUE / f"{seg['id']}.wav", "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
            *be.X264, *be.AAC, "-t", f"{total:.3f}", out])
    (be.TRANSCRIPTS / f"{seg['id']}.json").write_text(json.dumps(spoken["lines"]), encoding="utf-8")


def render_montage(item: dict, out) -> None:
    """Quick cuts from the most dramatic clips under the hook narration."""
    args, parts = [], []
    for i, (sid, start) in enumerate(item["shots"]):
        args += ["-ss", start, "-t", HOOK_SHOT_S, "-i", be.CLIPS / f"{sid}.mp4"]
        parts.append(f"[{i}:v]scale={be.W}:{be.H}:flags=lanczos,fps={be.FPS},setpts=PTS-STARTPTS[v{i}]")
    count, dur = len(item["shots"]), item["dur"]
    args += ["-i", item["audio"]]
    graph = (";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(count)) + f"concat=n={count}:v=1:a=0[cv];"
             f"[cv]tpad=stop_mode=clone:stop_duration={dur:.3f},trim=0:{dur:.3f},setpts=PTS-STARTPTS"
             f"{be.fades(dur, item)}[v];"
             f"[{count}:a]aresample={be.AR},adelay={int(be.NAR_LEAD * 1000)}:all=1,apad,atrim=0:{dur:.3f},"
             f"aformat=channel_layouts=stereo[a]")
    be.run([*args, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *be.X264, *be.AAC, "-t", f"{dur:.3f}", out])


def render_bumper_item(item: dict, out) -> None:
    be.render_bumper(item["source"], out)


def hook_item(kind: str, text: str, audio, shots, scene: int) -> dict:
    spoken = be.probe_duration(audio)
    dur = max(len(shots) * HOOK_SHOT_S, be.NAR_LEAD + spoken + 0.8)
    return {"kind": kind, "id": kind.upper(), "scene": scene, "dur": dur, "audio": audio, "shots": shots,
            "subs": be.caption_events(text, be.NAR_LEAD, be.NAR_LEAD + spoken)}


def bumper_item(name: str, source, scene: int) -> dict:
    return {"kind": "bumper", "id": name, "scene": scene, "dur": 0.0, "source": source, "subs": []}


def timeline(segments: list, nar_dur: dict) -> list:
    story = be.build_items(segments, nar_dur)
    last_scene = story[-1]["scene"]
    items = [hook_item("hook", HOOK_TEXT, HOOKS / "HOOK.mp3", HOOK_SHOTS, -2),
             bumper_item("ENTRY", be.COMMON / "0.0_Entry_Scene_202608010943.mp4", -1),
             *story,
             hook_item("outro", OUTRO_TEXT, HOOKS / "OUTRO.mp3", OUTRO_SHOTS, last_scene + 1),
             bumper_item("LAST", be.COMMON / "0.1_Last_Scene_202608010943.mp4", last_scene + 2)]
    for i, item in enumerate(items):
        item["fade_in"] = i == 0 or item["scene"] != items[i - 1]["scene"]
        item["fade_out"] = i == len(items) - 1 or item["scene"] != items[i + 1]["scene"]
    return items


def render_program(items: list):
    renderers = {"intro": be.render_intro, "finale": be.render_finale, "still": be.render_still,
                 "hook": render_montage, "outro": render_montage, "bumper": render_bumper_item}
    pieces = []
    for i, item in enumerate(items):
        out = be.WORK / f"{i:03d}_{item['id']}.mp4"
        renderers.get(item["kind"], be.render_clip_item)(item, out)
        item["dur"] = be.probe_duration(out)
        pieces.append(out)
        print(f"rendered {out.name} {item['dur']:.2f}s", flush=True)
    concat_list = be.WORK / "concat.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    program = be.WORK / "program.mp4"
    be.run(["-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", program])
    return program


def hook_overlays(items: list, offsets: list) -> list:
    overlays = []
    for item, start in zip(items, offsets):
        end = start + item["dur"] - 0.2
        if item["kind"] == "hook":
            overlays.append(("Title", start + 0.4, end, HOOK_TITLE))
        if item["kind"] == "outro":
            overlays += [("Title", start + 0.4, end, OUTRO_TITLE), ("Card", start + 4.0, end, OUTRO_SMALL)]
    return overlays


def music_sections(items: list, offsets: list) -> list:
    sections = []
    for item, start in zip(items, offsets):
        mood = be.SCENE_MOOD.get(item["scene"], "tense" if item["kind"] == "hook" else "warm")
        if sections and sections[-1]["mood"] == mood:
            sections[-1]["end"] = start + item["dur"]
        else:
            sections.append({"start": start, "end": start + item["dur"], "mood": mood})
    return sections


def render_outputs(clean, items: list, offsets: list, total: float) -> list:
    subs, overlays = be.program_events(items, offsets)
    overlays += hook_overlays(items, offsets)
    be.write_srt(be.FINAL / f"{be.NAME}_nepali_captions.srt", subs)
    land_ass = be.WORK / "land.ass"
    be.write_ass(land_ass, be.LAND, subs, overlays, captions=False)
    be.burn_landscape(clean, land_ass, be.FINAL / f"{be.NAME}_16x9_YouTube_Facebook.mp4")

    header = [("Small", 0, total, "नानीबाबुको कथा"), ("Handle", 0, total, be.HANDLE)]
    vert_ass = be.WORK / "vert_full.ass"
    be.write_ass(vert_ass, be.VERT, subs, overlays + header)
    be.render_vertical(clean, vert_ass, be.FINAL / f"{be.NAME}_9x16_TikTok_Facebook.mp4")

    parts = be.split_points(items, offsets, total)
    for n, (a, b) in enumerate(parts, 1):
        label = [("Small", a, b, f"नानीबाबुको कथा • भाग {n}/{len(parts)}"), ("Handle", a, b, be.HANDLE)]
        if n < len(parts):
            label.append(("Card", b - 3.0, b, f"भाग {n + 1} मा जारी... ▶"))
        part_ass = be.WORK / f"vert_part{n}.ass"
        be.write_ass(part_ass, be.VERT, subs, overlays + label, shift=a, end=b)
        be.render_vertical(clean, part_ass, be.FINAL / f"{be.NAME}_9x16_part{n}of{len(parts)}_Reels_Shorts.mp4", a, b)
    return parts


def main() -> None:
    for folder in (be.FONTS, be.FINAL, be.CLIPS, be.TRANSCRIPTS):
        folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(be.SYSTEM_FONT, be.FONTS / be.SYSTEM_FONT.name)
    segments = json.loads((EDIT / "segments.json").read_text(encoding="utf-8"))
    timings = json.loads((DIALOGUE / "_timings.json").read_text(encoding="utf-8"))
    missing = [s["id"] for s in segments if not s.get("still") and s["id"] != "S12S1"
               and not (RAW_CLIPS / f"{s['id']}.mp4").exists()]
    if missing:
        raise SystemExit(f"ToonBee clips still missing: {' '.join(missing)}")
    for seg in segments:
        prepare_clip(seg, timings)
    nar_dur = json.loads((be.NARRATION / "_durations.json").read_text(encoding="utf-8"))
    items = timeline(segments, nar_dur)

    program = render_program(items)
    offsets, at = [], 0.0
    for item in items:
        offsets.append(at)
        at += item["dur"]
    total = be.probe_duration(program)
    music = be.WORK / "music.wav"
    be.render_score(music_sections(items, offsets), total, music)
    clean = be.WORK / "clean_master.mp4"
    be.mix_master(program, music, clean)
    parts = render_outputs(clean, items, offsets, total)
    print(json.dumps({"total_s": round(total, 2), "parts": [(round(a, 1), round(b, 1)) for a, b in parts]}))


if __name__ == "__main__":
    main()
