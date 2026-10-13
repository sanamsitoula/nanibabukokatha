# नानीबाबुको कथा — to do

Last updated: 2026-10-12 21:47 NST. Background, accounts, URLs and scripts: `STATUS.md`. Rules: `CLAUDE.md`.

## EP04 बूढो रूखको गुन — ToonBee cut

### Left

- [ ] **ToonBee clips: 37 of 52 still to make** (free model only, now 20 videos per rolling 24 hours).
      `gen_toonbee.py` was restarted on 2026-10-12 21:47 NST (`toonbee_run10.log`) and waits for free slots by
      itself. First slot 2026-10-13 01:56 NST; earliest finish about 2026-10-14 02:00 NST.
  - [ ] Scene 1 redo: `S1S2` (wrong storyboard image; needs a new Flow image of the house interior first)
  - [ ] Scene 3 redo: `S3S2b` (boy turned into another man; queued first in `toonbee_run11.log`)
  - [x] Scene 3: `S3S3`
  - [ ] Scene 4 (`S4S1` is finished on ToonBee, not downloaded): `S4S1` `S4S1b` `S4S2` `S4S3`
  - [ ] Scene 5: `S5S1` `S5S1b` `S5S2` `S5S2b` `S5S3`
  - [ ] Scene 6: `S6S1` `S6S1b` `S6S2` `S6S3`
  - [ ] Scene 7: `S7S1` `S7S2` `S7S2b` `S7S2c` `S7S3`
  - [ ] Scene 8: `S8S1` `S8S2` `S8S3`
  - [ ] Scene 9: `S9S1` `S9S2` `S9S2b` `S9S3`
  - [ ] Scene 10: `S10S1` `S10S2` `S10S3` `S10S3b` `S10S3c`
  - [ ] Scene 11: `S11S1` `S11S1b` `S11S2` `S11S2b` `S11S2c` `S11S3` `S11S4`
- [ ] Look at every new clip (contact sheet); regenerate any with broken characters or motion.
- [x] First run of `build_toonbee.py` as a draft on 2026-10-11 (16:9, 9:16, 4 Reels/Shorts parts, SRT; 37 shots
      are storyboard stills).
- [ ] Final run of `py -3 build_toonbee.py` when all 52 clips exist.
- [ ] Check the final videos: opening hook, ending hook, voices in sync with captions, music level, moral card.
- [ ] Outputs present in `04. बूढो रूखको गुन/final_toonbee/`: 16:9 video, 9:16 video, Reels/Shorts parts, SRT.

### Needs Sanam

- [ ] Keep the laptop awake and the automation Chrome open with the Flow tab and the ToonBee EP04 tab.
- [ ] Avoid free ToonBee videos in other projects until EP04 is done; each one delays EP04 by one clip.
- [ ] Approve or change the hook lines (opening and ending) in `STATUS.md`.
- [ ] Voices: accept edge-tts character voices for the silent clips, or name another free voice source.
- [ ] Subu-OS rule conflict on automating Google Flow (`USER_SETUP.md` S36): keep the rule or allow this account.
- [ ] Watch the finished ToonBee cut and say what to fix.

### Done

- [x] Flow project with 5 character sheets (`dokodocsnepal@gmail.com`).
- [x] Storyboard images from Flow: 37 of 37 in `keyframes/` (0 credits).
- [x] ToonBee project `editor/145265` created.
- [x] ToonBee clips: 13 of 52 (`S1S1` `S1S2` `S1S3` `S1S4` `S2S1` `S2S2` `S2S2b` `S2S2c` `S2S3` `S3S1`
      `S3S1b` `S3S1c` `S3S2`), 0 credits.
- [x] Narration audio: 16 files.
- [x] Character voices for all 39 dialogue segments.
- [x] Hook lines written and voiced (`HOOK.mp3`, `OUTRO.mp3`).
- [x] Scripts: `gen_keyframes.py`, `gen_toonbee.py`, `toonbee_client.py`, `gen_dialogue.py`,
      `gen_narration_hooks.py`, `build_toonbee.py`.
- [x] Golden rule in `CLAUDE.md`: ToonBee video only with Seedance 1 PRO – FREE.
- [x] Status recorded in Subu-OS (signpost, project registry, `USER_SETUP.md` S34–S36).

## EP04 — Flow-only cut and comparison

- [ ] Decide whether to finish the Flow-only cut: 2 of 52 clips exist (`S1S1`, `S1S2`); 50 more cost about
      600 Flow credits (1,050 available).
- [ ] If yes: generate the 50 clips, run `build_episode.py`.
- [ ] Compare the two cuts (picture quality, character consistency, voices, cost, time) and pick the
      generator for later episodes.

## After EP04

- [ ] Publish EP04 (nothing is uploaded anywhere yet; needs Sanam's go).
- [ ] Commit the work: the repository has many untracked folders (EP02, EP03, EP04 assets and scripts).
- [ ] EP05 अन्धो ग्राहकको आँखा (named in the EP04 ending hook) and episodes 06–44: story folders only.
