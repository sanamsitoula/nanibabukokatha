"""Voice the opening hook and the closing question of the ToonBee cut (edge-tts). Writes narration_hooks/*.mp3."""
import asyncio

import edge_tts

from build_toonbee import HOOKS, HOOK_TEXT, OUTRO_TEXT
from gen_narration import MAX_ATTEMPTS, RETRY_DELAY_S, VOICE

STYLE = {"rate": "-4%", "pitch": "-2Hz"}  # a little faster than story narration: a hook has to grab


async def synth(name: str, text: str) -> None:
    target = HOOKS / f"{name}.mp3"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await edge_tts.Communicate(text, VOICE, **STYLE).save(str(target))
            return
        except Exception as exc:  # network drops are common; retry, then surface the failure
            target.unlink(missing_ok=True)
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"TTS failed for {name}") from exc
            await asyncio.sleep(RETRY_DELAY_S * attempt)


async def main() -> None:
    HOOKS.mkdir(exist_ok=True)
    await synth("HOOK", HOOK_TEXT)
    await synth("OUTRO", OUTRO_TEXT)


if __name__ == "__main__":
    asyncio.run(main())
