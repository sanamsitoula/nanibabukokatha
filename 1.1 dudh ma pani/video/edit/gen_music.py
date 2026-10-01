import numpy as np
from scipy.io import wavfile

SR = 48000
DURATION = 377.903
N = int(SR * DURATION)
t = np.arange(N) / SR

rng = np.random.default_rng(42)

# D minor pentatonic, low register for a warm bansuri/flute-adjacent tone
SCALE = {
    "D3": 146.83, "F3": 174.61, "G3": 196.00, "A3": 220.00, "C4": 261.63,
    "D4": 293.66, "F4": 349.23, "G4": 392.00, "A4": 440.00,
}


def env_note(n_samples, attack=0.15, release=0.35):
    """Raised-cosine attack/release envelope, sustain in between."""
    e = np.ones(n_samples)
    a = int(SR * attack)
    r = int(SR * release)
    a = min(a, n_samples // 2)
    r = min(r, n_samples // 2)
    if a > 0:
        e[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r > 0:
        e[-r:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(r) / r)
    return e


def tone(freq, n_samples, vibrato_hz=4.5, vibrato_depth=0.004, harmonics=(1.0, 0.5, 0.15)):
    tt = np.arange(n_samples) / SR
    vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_hz * tt)
    phase = 2 * np.pi * freq * np.cumsum(vibrato) / SR
    sig = np.zeros(n_samples)
    for h_idx, h_amp in enumerate(harmonics, start=1):
        sig += h_amp * np.sin(h_idx * phase)
    sig /= sum(harmonics)
    return sig


# ---- Drone bed: root + fifth, slow breathing amplitude ----
drone = 0.5 * np.sin(2 * np.pi * SCALE["D3"] * t) + 0.35 * np.sin(2 * np.pi * SCALE["A3"] * t)
breathing = 0.7 + 0.3 * np.sin(2 * np.pi * (1 / 9.0) * t)
drone = drone * breathing
drone *= 0.045

# ---- Sparse pentatonic melody, three loose dynamic sections ----
melody = np.zeros(N)
notes = list(SCALE.values())
mid_notes = notes[2:7]  # central register for the melodic line

cursor = 6.0  # start a few seconds in
section_bounds = (0.0, DURATION * 0.35, DURATION * 0.75, DURATION)
section_amp = (0.055, 0.075, 0.05)  # calm open, gentle build mid-story, soft resolve

while cursor < DURATION - 2.0:
    sec_idx = 0
    if cursor >= section_bounds[2]:
        sec_idx = 2
    elif cursor >= section_bounds[1]:
        sec_idx = 1
    amp = section_amp[sec_idx]

    freq = float(rng.choice(mid_notes))
    note_len = float(rng.uniform(1.6, 3.0))
    n_samp = int(note_len * SR)
    start_samp = int(cursor * SR)
    end_samp = min(start_samp + n_samp, N)
    seg_len = end_samp - start_samp
    if seg_len <= 0:
        break

    note = tone(freq, seg_len) * env_note(seg_len) * amp
    melody[start_samp:end_samp] += note

    cursor += note_len + float(rng.uniform(0.8, 2.2))

mix = drone + melody

# gentle stereo width: tiny delay + level diff between channels
delay_samples = int(0.012 * SR)
right = np.concatenate([np.zeros(delay_samples), mix[:-delay_samples]]) * 0.98
left = mix

stereo = np.stack([left, right], axis=1)

# overall fade in/out
fade_len = int(3.0 * SR)
fade_in = 0.5 - 0.5 * np.cos(np.pi * np.arange(fade_len) / fade_len)
fade_out = fade_in[::-1]
stereo[:fade_len] *= fade_in[:, None]
stereo[-fade_len:] *= fade_out[:, None]

peak = np.max(np.abs(stereo))
if peak > 0:
    stereo = stereo / peak * 0.9

out_path = r"D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video/edit/music_bed.wav"
wavfile.write(out_path, SR, (stereo * 32767).astype(np.int16))
print("wrote", out_path, "duration", N / SR)
