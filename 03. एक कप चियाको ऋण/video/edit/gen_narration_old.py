"""Generate complete scene-by-scene narrated script and audio for Episode 03.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import edge_tts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "narration"
VOICE = "ne-NP-SagarNeural"

# Master segments for Episode 03: "एक कप चियाको ऋण"
EPISODE_SEGMENTS = [
    {
        "id": "INTRO",
        "scene": 0,
        "title": "शीर्षक",
        "narration": "एउटा सानो चियापसल... एउटा भोकाएको बूढो... र एउटा नसोचेको रहस्य। के थियो एक कप चियाको मूल्य? सुरु गरौँ आजको कथा — एक कप चियाको ऋण।",
        "voice": "narrator",
        "mood": "mysterious",
        "prompt": "Cinematic hill village bazaar entrance with chautari, morning mist, title card 'एक कप चियाको ऋण'",
    },
    {
        "id": "S1S1",
        "scene": 1,
        "title": "काली गाडी बजारमा",
        "narration": "त्यो बिहान, सरिताको सानो चियापसल अगाडि एउटा चम्किलो कालो गाडी आएर रोकियो। सिंगो बजार अवाक् भयो — फूलबारी गाउँको इतिहासमा यस्तो गाडी कहिल्यै आएको थिएन।",
        "voice": "narrator",
        "mood": "suspense",
        "prompt": "Shiny black SUV rolls down narrow stone-paved hill village street, dust rising, villagers looking on",
    },
    {
        "id": "S1S2",
        "scene": 1,
        "title": "बजारको त्रास",
        "narration": "गाउँलेहरू छक्क परे। मोहन आत्तिँदै सरिताको हात समातेर भन्न थाले — 'सरिता, हाम्रो ऋणको कुरा त होइन नि?' सरिताको मुटु ढुकढुक भइरहेको थियो।",
        "voice": "narrator",
        "mood": "suspense",
        "prompt": "Mohan and Sarita standing terrified outside their small tin teashop, watching black SUV door open",
    },
    {
        "id": "S2S1",
        "scene": 2,
        "title": "सरिताको सङ्घर्ष",
        "narration": "यो कथा सुरु हुन्छ आठ महिनाअघि। जब सरिताको सानो चियापसल घाटामा डुबिरहेको थियो, र मोहनको दिनको ज्यालाले घर धान्न मुश्किल हुँदै थियो।",
        "voice": "narrator",
        "mood": "sad",
        "prompt": "Flashback 8 months ago, Sarita brewing tea on clay stove, Mohan counting a few small rupee notes, worn out",
    },
    {
        "id": "S2S2",
        "scene": 2,
        "title": "साहुजीको दबाब",
        "narration": "साहुजीले खाता पल्टाउँदै चिया-चिनीको बाँकी ऋण माग्थे। उता ६ वर्षकी छोरी बबिता भोकले पेट समातेर आमासँग भात माग्थिन्।",
        "voice": "narrator",
        "mood": "sad",
        "prompt": "Fat grocer Sahuji waving account ledger angrily, little Babita holding her stomach hungry in shop corner",
    },
    {
        "id": "S3S1",
        "scene": 3,
        "title": "भोकाएको बूढो",
        "narration": "साँझ ढल्दै गर्दा, फाटेको लुगा लगाएको एउटा बूढो मान्छे लत्रिँदै पसलमा आयो — 'बहिनी, म तीन दिनदेखि भोको छु, केही खान दिनुहुन्छ?'",
        "voice": "narrator",
        "mood": "emotional",
        "prompt": "Old frail man with white beard and torn dusty kurta leaning on wooden staff at teashop door, dusk lighting",
    },
    {
        "id": "S3S2",
        "scene": 3,
        "title": "दयाको हात",
        "narration": "घरमा आफ्नै लागि खान पुग्दैनथ्यो, तर सरिताले मन थाम्न सकिनन्। उनले आफ्नै भागको तातो चिया र सेलरोटी बूढाको हातमा थमाइन्।",
        "voice": "narrator",
        "mood": "warm",
        "prompt": "Sarita kindly offering a steaming cup of tea and fresh selroti to the hungry old traveler with a gentle smile",
    },
    {
        "id": "S4S1",
        "scene": 4,
        "title": "चिनजान बढ्दै",
        "narration": "त्यो दिनदेखि बूढा पाहुना बेला-बेला पसलमा आउन थाले। हरेक पटक सरिताले पैसा नमागी आदरसाथ चिया खुवाइन्।",
        "voice": "narrator",
        "mood": "warm",
        "prompt": "Old guest sitting on wooden bench sipping tea peacefully, Sarita wiping cups, lantern glowing warmly",
    },
    {
        "id": "S4S2",
        "scene": 4,
        "title": "छोरीको सम्झना",
        "narration": "बूढाले आँखामा आँसु पार्दै भने — 'मेरी पनि एउटी प्यारी छोरी थिई, ऊ पनि तिमीजस्तै दयालु थिई।' तर उनको पीडाको रहस्य कसैलाई थाहा थिएन।",
        "voice": "narrator",
        "mood": "emotional",
        "prompt": "Close-up of old man's weathered teary eyes looking into distance, reflecting deep past sorrow",
    },
    {
        "id": "S5S1",
        "scene": 5,
        "title": "ऋणको भार",
        "narration": "महिना बित्दै गयो। सरिताको ऋण बढ्दै गयो। साहुजीले एक हप्ताभित्र ऋण नतिरे पसल लिलाम गर्ने कडा चेतावनी दिए।",
        "voice": "narrator",
        "mood": "tense",
        "prompt": "Sahuji pointing finger aggressively at Sarita and Mohan, shouting deadline, market crowd watching",
    },
    {
        "id": "S6S1",
        "scene": 6,
        "title": "हराएको बूढो",
        "narration": "त्यही साँझ बूढा पाहुना अचानक हराए। सरिताले बजारभरि खोजिन्, तर बूढा कतै भेटिएनन्। मिति नजिकिँदै गर्दा परिवारमा रुवाबासी चल्यो।",
        "voice": "narrator",
        "mood": "sad",
        "prompt": "Sarita asking village shopkeepers about the missing old man, looking anxious under the evening sky",
    },
    {
        "id": "S7S1",
        "scene": 7,
        "title": "गाडीभित्रको सत्य",
        "narration": "सातौं दिन, त्यही कालो गाडीबाट सेतो दौरा-सुरुवाल र कालो टोपी लगाएका प्रतिष्ठित सेठ ओर्लिए — त्यो अरु कोही नभएर उही बूढा पाहुना थिए!",
        "voice": "narrator",
        "mood": "epic",
        "prompt": "Car door opens revealing the old man now elegantly dressed in white daura suruwal, Dhaka topi, gold chain, dignified",
    },
    {
        "id": "S7S2",
        "scene": 7,
        "title": "वकिलको घोषणा",
        "narration": "वकिलले घोषणा गरे — 'उहाँ बीस वर्षअघि हराउनुभएका यस भेगका सबैभन्दा ठूला जग्गाधनी हरिनारायण सेठ हुनुहुन्छ!'",
        "voice": "narrator",
        "mood": "epic",
        "prompt": "Lawyer in black suit reading official deed document next to Harinarayan Seth in front of stunned villagers",
    },
    {
        "id": "S8S1",
        "scene": 8,
        "title": "हराउनुको कारण",
        "narration": "हरिनारायण सेठले आँसु खसाल्दै भने — 'बीस वर्षअघि परिवार गुमाएपछि म संसारको परीक्षा लिन गरिब भएर हिँडेँ। सबैले मलाई ढुङ्गा हाने, तर सरिताले मलाई आफ्नै बुवाझैँ खुवाइन्।'",
        "voice": "narrator",
        "mood": "emotional",
        "prompt": "Harinarayan Seth speaking emotionally to the village gathering on the chautari, Sarita crying in disbelief",
    },
    {
        "id": "S9S1",
        "scene": 9,
        "title": "ऋण चुक्ता र उपहार",
        "narration": "सेठले सरिताको सम्पूर्ण ऋण तिरिदिए र पसल रहेको सम्पूर्ण जग्गा सदाको लागि सरिताकै नाममा नामसारी गरिदिए।",
        "voice": "narrator",
        "mood": "uplifting",
        "prompt": "Seth handing over stamped debt clearance paper and land registry document to tearful Sarita and Mohan",
    },
    {
        "id": "S10S1",
        "scene": 10,
        "title": "नयाँ परिवार",
        "narration": "सेठले बबितालाई काखमा लिँदै भने — 'मलाई धन चाहिएको थिएन, एउटा परिवार चाहिएको थियो।' सरिताले बुवा पाइन्, बबिताले मायालु हजुरबुवा पाइन्।",
        "voice": "narrator",
        "mood": "warm",
        "prompt": "Harinarayan Seth lifting little Babita happily in his arms, smiling warmly like a loving grandfather",
    },
    {
        "id": "S11S1",
        "scene": 11,
        "title": "हराभरा फूलबारी",
        "narration": "त्यो दिनपछि सरिताको पसल नयाँ, सफा र रौनकिलो बन्यो। साँझमा हरिनारायण हजुरबुवा बेन्चमा बसेर बबितालाई कथा सुनाउँथे।",
        "voice": "narrator",
        "mood": "cheerful",
        "prompt": "Bright new renovated teashop full of smiling customers, flowers on sill, grandfather telling stories to children",
    },
    {
        "id": "S12S1",
        "scene": 12,
        "title": "नैतिक शिक्षा",
        "narration": "साथीहरू, सरिताले धनी वा गरिब नहेरी केवल भोकाएको मान्छेलाई दया गरिन्। सानो दया कहिल्यै खेर जाँदैन; मान्छेलाई लुगाले होइन, मनले चिन्नुपर्छ।",
        "voice": "moral",
        "mood": "moral",
        "prompt": "Golden glowing frame of Sarita serving tea, with Nepali moral quote written in bold golden Devanagari",
    },
    {
        "id": "OUTRO",
        "scene": 13,
        "title": "समापन",
        "narration": "कथा मन पर्यो भने लाइक गर्नुहोस्, र यस्तै प्रेरणादायी कथाका लागि नानीबाबुको कथा सब्स्क्राइब गर्न नबिर्सनुहोस्।",
        "voice": "narrator",
        "mood": "cheerful",
        "prompt": "Channel closing bumper: Nanibabuko Katha logo, subscribe button, bells ringing",
    },
]


def style_for(segment: dict) -> dict:
    if segment.get("voice") == "moral" or segment.get("scene") == 12:
        return {"rate": "-12%", "pitch": "-4Hz"}
    return {"rate": "-8%", "pitch": "-2Hz"}


def duration(path: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return round(float(out.stdout.strip()), 3)


async def synth(segment: dict) -> tuple[str, float]:
    target = OUT / f"{segment['id']}.mp3"
    if target.exists() and target.stat().st_size > 0:
        return segment["id"], duration(target)
        
    for attempt in range(1, 6):
        try:
            comm = edge_tts.Communicate(segment["narration"], VOICE, **style_for(segment))
            await comm.save(str(target))
            if target.exists() and target.stat().st_size > 0:
                print(f"Synthesized {segment['id']} ({segment['title']})")
                return segment["id"], duration(target)
        except Exception as e:
            print(f"Retry {attempt}/5 for {segment['id']}: {e}")
            target.unlink(missing_ok=True)
            await asyncio.sleep(2 * attempt)
            
    # Fallback to local tone if network fails
    return segment["id"], 6.0


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    segments_path = HERE / "segments.json"
    segments_path.write_text(
        json.dumps(EPISODE_SEGMENTS, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    results = []
    for s in EPISODE_SEGMENTS:
        res = await synth(s)
        results.append(res)
        await asyncio.sleep(0.5)

    durations = dict(results)
    (OUT / "_durations.json").write_text(
        json.dumps(durations, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Successfully finished all {len(durations)} narration tracks in {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
