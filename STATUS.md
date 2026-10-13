# नानीबाबुको कथा — production status

Last updated: 2026-10-12 21:47 NST. This file is the one home for project status; Subu-OS only links here.
Task list (left / done): `todo.md`.

## Episodes

| Episode | State |
|---|---|
| 1.1 दूधमा पानी, मनमा ढुङ्गा | Clips and a 2-minute condensed cut exist |
| 02 चौतारीमुनि गाडिएको चिठ्ठी | Final videos in `02. .../final/` (OpenArt Veo 3.1 lite pipeline) |
| 03 एक कप चियाको ऋण | Final videos in `03. .../final/` |
| 04 बूढो रूखको गुन | In production, two versions being compared (see below) |
| 05–44 | Story folders only |

## EP04 — what is being built

Two cuts of the same episode, to compare generators before choosing one for later episodes:

- **ToonBee cut (active):** storyboard images from Google Flow (Nano Banana Pro, 0 credits) → downloaded →
  uploaded to ToonBee → video generated there with the free Seedance 1 PRO model (silent, 864x480, 8 s).
  Voices come from edge-tts. Opens with a hook and ends with a hook.
- **Flow-only cut (paused):** clips generated directly in Flow with sound (12 credits each). Only 2 of 52 clips
  exist (`S1S1`, `S1S2`), made in the older account `info.onedexo@gmail.com`.

### Where things are

- Flow project: https://flow.google.com/u/0/project/d4273437-c5e9-4064-b74a-8121c12d9431
  (account `dokodocsnepal@gmail.com`, PRO, 1,050 credits, holds the 5 character sheets)
- ToonBee project: https://app.toonbee.ai/editor/145265
  (account `sanam.ctaula@gmail.com`, 129 credits, no PRO)
- Automation browser: Chrome with `--remote-debugging-port=9222` and profile `.browser_profile/` (git-ignored)
- Episode folder `04. बूढो रूखको गुन/`:
  - `keyframes/<id>.png` — Flow storyboard images
  - `video_toonbee/clips/<id>.mp4` — ToonBee clips
  - `video/clips/` — the 2 Flow-only clips
  - `video/edit/` — all scripts, narration, dialogue voices, logs
  - `final_toonbee/` — output of the ToonBee cut (holds only the draft so far)

### Scripts (`04. बूढो रूखको गुन/video/edit/`)

| Script | Job |
|---|---|
| `gen_keyframes.py` | One Flow storyboard image per shot; skips finished ones |
| `gen_toonbee.py` + `toonbee_client.py` | Upload image, generate the free clip, download; stops when quota is used |
| `gen_narration.py` | Narrator audio (edge-tts `ne-NP-SagarNeural`) |
| `gen_dialogue.py` | Character voices for all dialogue lines (two edge-tts voices, pitch per character) |
| `gen_narration_hooks.py` | Voices for the opening and ending hooks |
| `gen_dialogue_voicebox.py` | Same lines through the local Voicebox app (Kokoro Hindi voices), into `dialogue_voicebox/` |
| `build_toonbee.py` | Assembles the ToonBee cut: 16:9, 9:16, Reels/Shorts parts, SRT. Options: `--draft` (storyboard stills for missing clips), `--voices voicebox`, `--landscape-only` |
| `build_episode.py` | Assembles the Flow-only cut |

### Done so far (files present on 2026-10-10)

- Character sheets (5) uploaded to the Flow project.
- Storyboard images: 37 of 37 shots (`S9S1`, `S9S2` regenerated once to match the story).
- ToonBee clips: 13 of 52 (`S1S1` to `S3S2`), 0 credits spent by the scripts.
- Narration: 16 files. Dialogue voices: 39 segments. Hook voices: `HOOK.mp3`, `OUTRO.mp3`.
- Hooks written:
  - Opening (before the channel bumper): fast cuts of the landslide with
    "सबैले रूख काटे... एउटाले काटेन। आज त्यही बूढो रूखले कसको ज्यान बचाउँछ? अन्तिमसम्म हेर्नुहोस्।"
  - Ending (after the moral): "तपाईंको गाउँमा पनि यस्तो बूढो रूख छ? कमेन्टमा भन्नुहोस्।
    अर्को कथा — अन्धो ग्राहकको आँखा। हेर्न नबिर्सनुहोस्।"
- Assembly script `build_toonbee.py` ran for the first time on 2026-10-11 as a draft:
  `final_toonbee/EP04_बूढो_रूखको_गुन_ToonBee_DRAFT_16x9_YouTube_Facebook.mp4` (8 min 57 s, 1920x1080,
  -14.3 LUFS, true peak -1.3 dBFS) plus its SRT. Hook, bumper, story, moral, ending hook, music and captions
  are in; 37 shots are storyboard stills because their clips do not exist yet.

### State on 2026-10-11 12:40 NST

- ToonBee clips: 15 of 52 on disk (`S1S1` to `S3S3`). `S4S1` is finished on ToonBee but not downloaded.
- `py -3 -u gen_toonbee.py > toonbee_run8.log` is running. The free quota is 0 until 16:49 NST, because 19
  free videos were made elsewhere on the account. About 25 clips are possible in the evening and the last 11
  after about 01:00 NST on 2026-10-12.
- `gen_toonbee.py` now retries a segment 6 times and picks up a clip that was already requested, so a laptop
  sleep no longer stops the batch or wastes a free slot.
- ToonBee credits: 122 before and after every run of the scripts on 2026-10-11.
- Voicebox (local app, v0.5.0): it has no Nepali voice. Its Kokoro Hindi voices give more distinct characters
  but mispronounce Nepali word endings (a Whisper check heard "आउँदैछ" as "आउन्दैच" and "म" as "मैं"). The
  edge-tts Nepali voices stay the default; the Voicebox set is ready in `dialogue_voicebox/` for a comparison
  build with `--voices voicebox`.

### State on 2026-10-12 21:47 NST

- ToonBee clips: still 15 of 52 on disk. No batch and no automation Chrome were running; `toonbee_run9.log`
  ends on 2026-10-11 13:40 NST while waiting for quota.
- Automation Chrome restarted (port 9222, ToonBee EP04 tab, still signed in) and
  `py -3 -u gen_toonbee.py > toonbee_run10.log` started at 21:47 NST.
- ToonBee changed the free limit: the API now reports 20 videos per rolling 24 hours (it was 25 per 8 hours).
  20 of 20 are used, none of them by the EP04 scripts, so the first free slot is 2026-10-13 01:56 NST.
- With 36 clips to generate and 1 to download (`S4S1`), the earliest finish is about 2026-10-14 02:00 NST,
  and only if no other free ToonBee video is made on the account before then.
- ToonBee credits: 122.

### Clip review on 2026-10-12 22:10 NST (all 15 clips, 3 frames each)

- 13 clips are usable.
- `S3S2b` rejected: at 5 s the shot cuts and the boy becomes an unknown bald man in a blue shirt. The file is
  kept as `video_toonbee/rejected/S3S2b_v1.mp4`, its entry was removed from `toonbee_slides.json`, and the
  batch makes it again first.
- `S1S2` is wrong and still in `clips/`: its storyboard image `keyframes/S1S2.png` shows the landslide from
  outside, but the script is the inside of Arjun's house (Sunita wakes Arjun). The clip cuts to the room
  after 2 s and shows two Arjuns with a full beard. It needs a new Flow storyboard image before a new clip.
- Continuity between shots: in `S3S1` the child is a shirtless toddler and Baje wears a white topi; in `S3S2`
  the child is older and dressed and Baje wears a Dhaka topi. Both come from the storyboard images.
- `motion_prompt()` in `gen_toonbee.py` now also asks for one continuous shot, no scene cut, no new
  characters. It applies to every clip made from now on.
- Batch restarted as `toonbee_run11.log`; 14 clips on disk, 37 to generate, 1 to download.

### Left

1. ToonBee clips for 37 segments (`S4S1` onward); the running batch sleeps while the free quota is used up
   and continues by itself.
2. Final run of `py -3 build_toonbee.py` when all 52 clips exist (16:9, 9:16, Reels/Shorts parts, SRT).
3. Review of the final videos, then the comparison with the Flow-only cut.
4. Flow-only cut: 50 clips missing; needs a decision on whether to finish it (about 600 Flow credits).
5. Publishing: not started; nothing is uploaded anywhere.

### Blockers and limits

- Both batches were killed once on 2026-10-10 10:12 NST when the computer ran low on memory; restarted 11:43 NST.
  The ToonBee batch was killed again on 2026-10-11 (533 MB free of 16 GB) and restarted at 12:31 NST.
- Closing the laptop lid puts it to sleep (three times on 2026-10-11 morning) and drops the browser connection.
- ToonBee free model: 20 videos per rolling 24 hours for the whole account since 2026-10-12 (25 per 8 hours
  before), so free videos made in other ToonBee projects delay EP04. On 2026-10-10 the quota was full until
  14:36 NST.
- Flow got slow (12 to 16 minutes per image) late in the batch; one frozen Flow tab blocked the browser
  connection and had to be closed.
- The computer must stay awake and the automation Chrome must stay open with both project tabs.
- Free ToonBee clips are silent and 480p, so the ToonBee cut has TTS voices and no lip-synced speech.
  Sound models cost 7 to 8 credits per clip; 129 credits cover about 17 clips.
- One 7-credit ToonBee generation on 2026-10-10 07:50 NST did not come from the scripts.

### Open decisions for Sanam

- Dialogue audio: keep free silent clips with TTS voices, or pay for a sound model on key dialogue clips.
- Hook wording: the lines above are a proposal.
- Subu-OS rule conflict: `config/browser_profiles.toml` says never automate Google Flow, but this pipeline
  drives Flow through the automation browser on request. Tracked in Subu-OS `USER_SETUP.md` S36.
