import os
import shutil
import asyncio
import edge_tts
from pathlib import Path
from PIL import Image

BASE_DIR = Path(r"c:\workspace\apps\breno-english")
PUBLIC_DIR = BASE_DIR / "public"
AUDIO_DIR = PUBLIC_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 1. Update Breno's Portrait
source_portrait = Path(r"C:\Users\AXION\.gemini\antigravity\brain\68ae4830-2ed7-4785-a4e1-df7a5d6685cb\breno_portrait_1790704003580.jpg")
target_portrait = PUBLIC_DIR / "breno-portrait.png"

if source_portrait.exists():
    print(f"[*] Processing portrait from: {source_portrait}")
    with Image.open(source_portrait) as img:
        img.save(target_portrait, "PNG", quality=95)
    print(f"[OK] Saved high-res portrait to: {target_portrait}")
else:
    print(f"[!] Source portrait not found: {source_portrait}")

# 2. Generate Studio-Quality Neural Audio for Conversation Scenarios
scenarios = [
    {
        "filename": "interview.mp3",
        "text": "Could you walk me through your decision-making process during that architectural migration?",
        "voice": "en-US-ChristopherNeural"  # Professional, confident, articulate
    },
    {
        "filename": "negotiation.mp3",
        "text": "Given the scope of this role and market benchmarks, I'm targeting a base compensation of 110k.",
        "voice": "en-US-GuyNeural"  # Assertive, warm business tone
    },
    {
        "filename": "meeting.mp3",
        "text": "Let's circle back to this point once we review the analytics report by Friday.",
        "voice": "en-US-ChristopherNeural"
    },
    {
        "filename": "travel.mp3",
        "text": "Excuse me, could you let me know if this express train connects directly to downtown?",
        "voice": "en-US-GuyNeural"
    }
]

async def generate_all_audio():
    for s in scenarios:
        out_path = AUDIO_DIR / s["filename"]
        print(f"[*] Generating neural audio: {s['filename']} with {s['voice']}...")
        communicate = edge_tts.Communicate(s["text"], s["voice"], rate="-3%")
        await communicate.save(str(out_path))
        print(f"[OK] Generated: {out_path} ({out_path.stat().st_size} bytes)")

asyncio.run(generate_all_audio())

# 3. Clean up test file
test_file = BASE_DIR / "test.mp3"
if test_file.exists():
    test_file.unlink()

print("[DONE] All visual and neural audio assets successfully generated and deployed to public/!")
