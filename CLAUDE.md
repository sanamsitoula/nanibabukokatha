# नानीबाबुको कथा — rules for Claude

Project status, accounts, scripts and what is left: see `STATUS.md`.

## Golden rule: ToonBee video model

On ToonBee (app.toonbee.ai), generate video **only** with **Seedance 1 PRO – FREE**
(`video_model_id` 30, 0 credits).

- Never request any other ToonBee video model: not the paid Seedance 1 PRO variant (id -30), not
  Seedance 2 Mini, Grok Imagine, VEO 3.1, Kling, PixVerse or Seedance 2.0.
- Never spend ToonBee credits on video. The credit balance before and after a batch must be equal.
- The free model allows 25 videos per rolling 8 hours for the whole account. When the quota is used up,
  wait for the next slot. Do not switch to a paid model to go faster, and do not offer it as a shortcut.
- Free clips are silent. Voices come from edge-tts in the assembly step.
- Only Sanam can change this rule, by saying so explicitly.

## Pipeline for ToonBee episodes

1. Storyboard images in Google Flow (Nano Banana Pro, 0 credits), saved to `<episode>/keyframes/`.
2. Upload each image to the ToonBee project and generate the clip with the free model.
3. Download clips to `<episode>/video_toonbee/clips/`, then assemble locally with ffmpeg.
4. Every episode opens with a hook and ends with a hook.
