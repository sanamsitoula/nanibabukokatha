"""Voice every dialogue line with the local Voicebox app (Kokoro voices) as an alternative to gen_dialogue.py.

Voicebox has no Nepali language, so the lines are read by its Hindi voices: more distinct characters than the two
edge-tts voices, but Hindi pronunciation of Nepali word endings. Start the server first:
  "C:\\Program Files\\Voicebox\\voicebox-server.exe" --port 17493 --data-dir %APPDATA%\\sh.voicebox.app
Writes dialogue_voicebox/<segment id>.wav and dialogue_voicebox/_timings.json in the same layout as dialogue/.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import gen_dialogue as gd
from gen_narration import duration

HERE = Path(__file__).parent
OUT = HERE / "dialogue_voicebox"
LINES = OUT / "lines"
API = "http://127.0.0.1:17493"
ENGINE, LANGUAGE = "kokoro", "hi"
PROFILE_PREFIX = "nbk_"
POLL_S = 1
TIMEOUT_S = 300
# character -> (Kokoro Hindi voice, pitch shift in semitones, tempo)
VOICES = {
    "अर्जुन": ("hm_omega", 0, 1.0),
    "सुनिता": ("hf_alpha", 0, 1.0),
    "रवि": ("hf_beta", 3, 1.06),
    "दिपा": ("hf_alpha", 4, 1.05),
    "माइला दाजु": ("hm_psi", 1, 1.05),
    "मुखिया धनबहादुर": ("hm_psi", -3, 0.93),
    "हजुरबा गोविन्द": ("hm_omega", -4, 0.85),
    "सानो अर्जुन": ("hf_beta", 5, 1.05),
    "गाउँले १": ("hm_omega", 2, 1.0),
}


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=TIMEOUT_S).read())


def profile_ids() -> dict:
    """Voicebox profile id for every Kokoro voice in VOICES; missing profiles are created."""
    known = {p["name"]: p["id"] for p in call("GET", "/profiles")}
    ids = {}
    for voice in {voice for voice, _pitch, _tempo in VOICES.values()}:
        name = PROFILE_PREFIX + voice
        ids[voice] = known.get(name) or call("POST", "/profiles", {
            "name": name, "language": LANGUAGE, "voice_type": "preset", "preset_engine": ENGINE,
            "preset_voice_id": voice, "default_engine": ENGINE})["id"]
    return ids


def synth(target: Path, speaker: str, text: str, profiles: dict) -> float:
    if not (target.exists() and target.stat().st_size > 0):
        voice, pitch, tempo = VOICES[speaker]
        effects = [{"type": "pitch_shift", "params": {"semitones": pitch}}] if pitch else None
        generation = call("POST", "/generate", {"profile_id": profiles[voice], "text": text, "language": LANGUAGE,
                                                "engine": ENGINE, "effects_chain": effects})
        deadline = time.time() + TIMEOUT_S
        while generation["status"] not in ("completed", "failed"):
            if time.time() > deadline:
                raise TimeoutError(f"Voicebox did not finish {target.name}")
            time.sleep(POLL_S)
            generation = call("GET", f"/history/{generation['id']}")
        if generation["status"] == "failed":
            raise RuntimeError(f"Voicebox failed for {target.name}: {generation.get('error')}")
        raw = target.with_suffix(".raw.wav")
        raw.write_bytes(urllib.request.urlopen(f"{API}/audio/{generation['id']}", timeout=TIMEOUT_S).read())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"atempo={tempo}", str(target)], check=True)
        raw.unlink()
    return duration(target)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    LINES.mkdir(parents=True, exist_ok=True)
    gd.OUT = OUT  # gd.mix writes the mixed segment next to our lines
    profiles = profile_ids()
    timings = {}
    for seg in json.loads((HERE / "segments.json").read_text(encoding="utf-8")):
        if not seg.get("lines"):
            continue
        files, starts, windows, at = [], [], [], gd.LEAD_S
        for index, (speaker, text) in enumerate(seg["lines"]):
            target = LINES / f"{seg['id']}_{index}.wav"
            length = synth(target, speaker, text, profiles)
            files.append(target)
            starts.append(at)
            windows.append({"start": round(at, 3), "end": round(at + length, 3)})
            at += length + gd.GAP_S
        total = round(at - gd.GAP_S + gd.TAIL_S, 3)
        gd.mix(seg["id"], files, starts, total)
        timings[seg["id"]] = {"dur": total, "lines": windows}
        print(seg["id"], total, flush=True)
    (OUT / "_timings.json").write_text(json.dumps(timings, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
