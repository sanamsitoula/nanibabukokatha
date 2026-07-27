# दूधमा पानी, मनमा ढुङ्गा — 2-Minute Condensed Cut (Design)

## Goal

Produce a ~2:00 YouTube (16:9) condensed cut of the full 12-scene story
"दूधमा पानी, मनमा ढुङ्गा", built in DaVinci Resolve from existing rendered
footage. One representative shot per scene, hard cuts, using each clip's
embedded Nepali dialogue/narration audio. Title card at open, moral text
card at close. No music/SFX, no subtitles, no color grading in this pass —
those are explicitly deferred to a later iteration.

## Source Material

- Footage: `1.1 dudh ma pani/video/` — 46 clips named `S{scene}S{shot}.mp4`
  (e.g. `S1S1`, `S1S2`... `S12S2`), covering Scenes 1–12, 2–5 shot variants
  per scene.
- Each clip: ~10s (one clip is 8s), 1280×720, 24fps, H.264 video + AAC
  audio. Audio is baked-in dialogue/narration per shot — no separate
  voiceover files exist.
- Script: `1.1 dudh ma pani/prompt2-dudhma_pani_full_script.md` — full
  12-scene script with Narration, Dialogue, Animation Direction, and Scene
  Ending Hook for each scene.
- Character stills: `1.1 dudh ma pani/character/` — reference images only,
  not used as video source in this cut.
- Output destination: `1.1 dudh ma pani/video_davi/` (currently empty).

## Shot Selection

For each of the 12 scenes, select exactly one shot to represent it in the
condensed cut, chosen by cross-referencing the available shot options
against that scene's Dialogue, Animation Direction, and Scene Ending Hook
text — picking whichever shot carries the scene's strongest emotional beat
or cliffhanger. Where the filename alone doesn't make the right shot
obvious, pull a still frame to confirm before committing.

This is a per-scene editorial judgment call made during implementation, not
a fixed rule (e.g. not simply "always shot 1" or "always the last shot").

## Timeline Structure

1. Title card (story title, ~2–3s)
2. 12 selected clips, one per scene, in scene order S1 → S12 (~10s each,
   ≈120s total)
3. End card (final moral line from Scene 12, ~4–5s)

Total runtime: ~2:05–2:10. This is treated as acceptable for a "2-minute"
cut; if the user wants strictly under 2:00, individual clips can be
trimmed slightly during review.

## Technical Settings

- New DaVinci Resolve project (name: `dudh-ma-pani-2min`).
- Timeline format matches source: 1280×720, 24fps — avoids any transcode
  or quality loss versus the source media.
- Source clips are only referenced into the timeline; nothing in
  `1.1 dudh ma pani/video/` is modified, transcoded, or replaced.
- Title/end cards built as Resolve title/text clips (e.g. Fusion Title or
  Text+), not burned into or replacing any source clip.
- Render output: single mp4 delivered to `1.1 dudh ma pani/video_davi/`.

## Explicitly Out of Scope (this pass)

- Subtitles/captions (Nepali or English)
- Background music / SFX layering
- Color grading / look development
- Transitions beyond hard cuts

## Open Risk

Shot selection is subjective — the chosen shot per scene may not match
what the user has in mind once they see the assembled cut. First render
should be treated as a draft for review, not a final delivery.
