# Cheap video pipeline for the story folders (10 onward)

Written 2026-10-13. Worked example: `10. मास्टर सापको फाटेको जुत्ता` (42 segments of 10 s, about 7 minutes).

## Which generator is cheapest

| Tool | Free allowance | Cost of one 42-clip story | Output | Verdict |
|---|---|---|---|---|
| **ToonBee** (Seedance 1 PRO, model 30) | 20 clips and 30 images per rolling 8 hours (20 since 2026-10-12) | 0, spread over 3 windows (about one day) | 864×480, 5–12 s, silent | **Main clip generator** |
| **Google Flow** images | Free image model, free 1080p upscale | 0 | Stills with character reference | **All stills and references** |
| **Google Flow** video (Omni 1.1 Flash) | About 1050 credits a month per account; 53 left on 2026-10-12 | 15 credits × 42 = 630 credits, 60% of a month | 720p → free 1080p, with sound | **Hero shots only** (hook, climax) |
| **OpenArt** | 40 one-time trial credits; reviews put a video clip near 100 credits | Not possible free; paid from $14 a month for about 40 clips | Many models | **Skip**: no free path, no bot written |
| **Flow Music** | Bot exists (`subu/musicvideo/flowmusic.py`); its credit cost is not checked | Unknown | WAV + stems | Channel music beds, made once |
| Local music (`1.1 dudh ma pani/video/edit/gen_music.py`) | Unlimited | 0 | Synth flute bed | Fallback |

ToonBee and Flow figures come from `subu-os/config/musicvideo.toml`, `subu-os/docs/musicvideo.md` and
`subu-os/data/musicvideo/credits.jsonl`. OpenArt figures are from third-party reviews, not its pricing page.

## The flow

```
story.md
  └─ 1 parse ─────────► production/segments.json, cast.json        plain code   (built)
        ├─ 2 references ► production/reference/<character>.jpg     Flow image   free
        ├─ 3 stills ────► production/storyboard/<segment>.jpg      Flow image   free
        │     └─ 4 clips ► production/clips/<segment>.mp4          ToonBee      free, 20 per 8 h
        │           └─ 5 enhance ► 1728×960                        Video2X      local
        ├─ 6 voice ─────► production/voice/<segment>-<n>.mp3       see "Voice"
        └─ 7 music ─────► production/music/bed.wav                 Flow Music or gen_music.py
  8 assemble ─► out/<story>.mp4  (bookends from common/, subtitles, music ducked)   ffmpeg
  9 shorts ───► out/<story>-teaser.mp4  (60 s, 9:16)                               ffmpeg
```

| Stage | Detail |
|---|---|
| 1 parse | `python pipeline/segments.py "<folder>"`. Reads every story 02–50 (`--check` lists them). Drops the repeated style block from each prompt and splits narration and dialogue by speaker. |
| 2 references | One image per character from the story's CHARACTER REFERENCE SHEET, plus the style block. These keep faces and clothes the same in every clip. |
| 3 stills | One still per segment from its video prompt, with the character references attached. Flow's image model costs no credits; its daily limit is not checked. |
| 4 clips | ToonBee image-to-video from each still, 10 s. The existing bot (`subu/musicvideo/toonbee.py`) already uploads a Flow still and animates it. |
| 5 enhance | Existing `[enhance]` setting (Video2X, Anime4K, ×2). Flow clips skip this. |
| 6 voice | One file per spoken line, timings in `voice.json`. A segment whose speech runs past 10 s holds its last frame. |
| 7 music | Three or four mood beds for the whole channel (playful, tense, sad, warm), reused in every story. |
| 8 assemble | Same method as `1.1 dudh ma pani/video/edit/` and `video_davi/build_2min.sh`: clip + voice per segment, music lowered under speech, Nepali subtitles with Nirmala UI. |
| 9 shorts | Scene 1 hook plus the cliffhanger, cropped to 9:16. |

## Saving clips

- Establishing shots with nobody acting do not need a video model: pan and zoom the still in ffmpeg. Story 10 has 5 segments with no speech; with those and other scenery shots a story drops from 42 to about 30 animated clips, two ToonBee windows instead of three.
- Spend Flow credits only on Scene 1 (the hook) and the climax, about 6 clips = 90 credits.
- The ToonBee account is shared with Gokul Kirtan and 10 Seconds Home Fix. Whichever job runs first takes the window.

## Voice

ToonBee clips are silent, so the voice has to be added.

| Route | Cost | State |
|---|---|---|
| Microsoft Edge voices (`pipeline/voice.py`, `ne-NP-Hemkala`, `ne-NP-Sagar`) | Free, online | **Refused today**: the service answers 403 with the newest `edge-tts` (7.2.8). Script is written, not proven. |
| OmniVoice in `voice_studio` | Free, offline | Supports Nepali and voice cloning. Not installed: 3.3 GB download, and this PC has no graphics card, so it will be slow. |
| Flow video with sound for talking shots | Flow credits | How episode 1.1 got its voices. Too dear for a whole story. |

Only VibeVoice weights are on disk in `voice_studio` today, and it does not list Nepali.

## What not to use for this

- **OpenMontage**: its pipelines call paid provider APIs for the pictures. Useful ideas, not a free path.
- **Bhrikuty**: builds explainer videos from infographic cards and a voiceover. Wrong shape for character animation; its platform-text step could later write the per-platform captions.
- **Wan2.1** (`wanvideo/Wan2.1`): free and unlimited, but it needs an NVIDIA card with 8 GB or more. This PC has only Intel UHD 750 graphics, no model weights are downloaded, and its environment has CPU-only PyTorch, so it cannot run here. On a PC with an NVIDIA card it would replace ToonBee's quota: the 1.3B model makes 480p text-to-video in 8 GB; image-to-video from our stills needs the 14B model and 16–24 GB.
- **Remotion**: only worth it for animated title and moral cards. ffmpeg with subtitle cards already does the static ones.

## Built so far

- `pipeline/segments.py`: done, run on all 49 stories.
- `10. .../production/segments.json` and `cast.json`: done (42 segments, 47 spoken lines, 12 speakers).
- `pipeline/voice.py`: written, blocked by the 403 above.
- Stages 2–5 and 7–9: not built. They are an adaptation of `subu/musicvideo` (stills, ToonBee, enhance) and of the 1.1 edit scripts.
