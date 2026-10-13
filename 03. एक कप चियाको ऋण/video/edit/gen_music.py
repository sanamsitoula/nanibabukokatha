"""Procedural Nepali-folk-flavoured background score (bansuri-like lead, harmonium drone, madal hits).

render_score(sections, total_s, out_wav) writes a 48 kHz stereo WAV. `sections` is a list of
{"start": s, "end": s, "mood": name}; time outside every section stays silent (used for bumpers).
"""
import numpy as np
from scipy.io import wavfile

SR = 48000
XFADE_S = 2.0
D3 = 146.83

# Semitone offsets from D for each scale
MINOR_PENTA = (0, 3, 5, 7, 10)
MAJOR_PENTA = (0, 2, 4, 7, 9)

MOODS = {
    #           scale        drone  lead   note_len     gap         octave  pulse_s  madal
    "tense":   (MINOR_PENTA, 0.060, 0.030, (1.4, 2.6), (0.6, 1.6), 1.0, 1.05, False),
    "sad":     (MINOR_PENTA, 0.050, 0.040, (1.8, 3.2), (0.8, 2.0), 1.0, None, False),
    "mystery": (MINOR_PENTA, 0.045, 0.025, (2.2, 3.6), (1.0, 2.2), 2.0, 1.6, False),
    "hopeful": (MAJOR_PENTA, 0.045, 0.040, (1.0, 2.0), (0.4, 1.2), 2.0, None, False),
    "joyful":  (MAJOR_PENTA, 0.040, 0.045, (0.35, 0.7), (0.05, 0.3), 2.0, None, True),
    "warm":    (MAJOR_PENTA, 0.050, 0.040, (1.6, 2.8), (0.6, 1.6), 1.0, None, False),
}


def envelope(n, attack=0.12, release=0.4):
    env = np.ones(n, dtype=np.float32)
    a, r = min(int(SR * attack), n // 2), min(int(SR * release), n // 2)
    if a:
        env[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r:
        env[-r:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(r) / r)
    return env


def bansuri(freq, n, rng):
    """Breathy flute: fundamental + weak harmonics, delayed vibrato, band-limited breath noise."""
    t = np.arange(n) / SR
    vib_depth = 0.006 * np.clip(t / 0.5, 0, 1)
    phase = 2 * np.pi * freq * np.cumsum(1 + vib_depth * np.sin(2 * np.pi * 5.0 * t)) / SR
    tone = np.sin(phase) + 0.18 * np.sin(2 * phase) + 0.06 * np.sin(3 * phase)
    breath = np.convolve(rng.normal(0, 1, n), np.ones(24) / 24, mode="same") * 0.08
    return ((tone + breath) * envelope(n)).astype(np.float32)


def drone(n, scale_major, t0):
    """Harmonium-like root+fifth pad with slow breathing."""
    t = (np.arange(n) + t0) / SR
    third = 2 ** ((4 if scale_major else 3) / 12)
    sig = np.zeros(n, dtype=np.float32)
    for ratio, amp in ((0.5, 0.5), (1.0, 0.45), (1.5, 0.35), (third, 0.12)):
        f = D3 * ratio
        sig += amp * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t))
    return sig * (0.8 + 0.2 * np.sin(2 * np.pi * t / 7.0))


def thump(n_len=0.45, freq=55.0, decay=10.0):
    t = np.arange(int(SR * n_len)) / SR
    return (np.sin(2 * np.pi * freq * t) * np.exp(-t * decay)).astype(np.float32)


def madal_hit(rng, low):
    t = np.arange(int(SR * (0.35 if low else 0.15))) / SR
    if low:
        body = np.sin(2 * np.pi * 95 * t * (1 + 0.4 * np.exp(-t * 30))) * np.exp(-t * 9)
        return (body + rng.normal(0, 0.15, t.size) * np.exp(-t * 60)).astype(np.float32)
    ring = np.sin(2 * np.pi * 320 * t) * np.exp(-t * 35)
    return (0.6 * ring + rng.normal(0, 0.35, t.size) * np.exp(-t * 45)).astype(np.float32)


def add_at(buf, start, sig):
    end = min(buf.size, start + sig.size)
    if start < end:
        buf[start:end] += sig[: end - start]


def section_audio(dur_s, mood, rng, t0):
    scale, drone_amp, lead_amp, note_len, gap, octave, pulse_s, madal = MOODS[mood]
    n = int(dur_s * SR)
    out = drone(n, scale is MAJOR_PENTA, t0) * drone_amp
    notes = [D3 * octave * 2 ** (s / 12) for s in scale] + [D3 * octave * 2 * 2 ** (s / 12) for s in scale[:3]]
    cursor = rng.uniform(0.5, 1.5)
    idx = rng.integers(0, len(notes))
    while cursor < dur_s - 1.0:
        idx = int(np.clip(idx + rng.choice((-2, -1, -1, 1, 1, 2)), 0, len(notes) - 1))  # stepwise melody
        length = rng.uniform(*note_len)
        add_at(out, int(cursor * SR), bansuri(notes[idx], int(length * SR), rng) * lead_amp)
        cursor += length + rng.uniform(*gap)
    if pulse_s:
        beat = thump() * 0.09
        for k in np.arange(0.3, dur_s, pulse_s):
            add_at(out, int(k * SR), beat)
    if madal:
        beat_s = 60 / 104
        pattern = (True, False, False, True, False, True, False, False)  # dha . . dha . tin-heavy groove
        for i, k in enumerate(np.arange(0.0, dur_s, beat_s / 2)):
            add_at(out, int(k * SR), madal_hit(rng, pattern[i % len(pattern)]) * 0.08)
    return out


def render_score(sections, total_s, out_wav, seed=7):
    rng = np.random.default_rng(seed)
    total = int(total_s * SR)
    mix = np.zeros(total, dtype=np.float32)
    fade = int(XFADE_S * SR)
    for sec in sections:
        start = int(sec["start"] * SR)
        body = section_audio(sec["end"] - sec["start"] + XFADE_S, sec["mood"], rng, start)
        ramp = np.ones(body.size, dtype=np.float32)
        ramp[:fade] = np.linspace(0, 1, fade)
        ramp[-fade:] = np.linspace(1, 0, fade)
        add_at(mix, max(0, start - fade // 2), body * ramp)
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.7
    delay = int(0.012 * SR)  # Haas widening
    right = np.concatenate([np.zeros(delay, dtype=np.float32), mix[:-delay]])
    wavfile.write(out_wav, SR, (np.stack([mix, right], axis=1) * 32767).astype(np.int16))
