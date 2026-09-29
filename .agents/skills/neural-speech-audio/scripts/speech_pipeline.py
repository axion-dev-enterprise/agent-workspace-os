#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neural Speech & Audio CLI Pipeline -- AXION Enterprise
Utility for inspecting, normalizing, and synthesizing neural speech.
Runs on Python 3 standard library.
"""

import os
import sys
import json
import argparse
import subprocess
import urllib.request
from pathlib import Path

def inspect_audio(file_path: Path):
    if not file_path.exists():
        print(f"Error: File {file_path} not found.", file=sys.stderr)
        return False
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels,duration", "-of", "json", str(file_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        stream = data.get("streams", [{}])[0]
        print(f"File:        {file_path.name}")
        print(f"Codec:       {stream.get('codec_name')}")
        print(f"Sample Rate: {stream.get('sample_rate')} Hz")
        print(f"Channels:    {stream.get('channels')}")
        print(f"Duration:    {round(float(stream.get('duration', 0)), 2)}s")
        return True
    except Exception as e:
        print(f"Error inspecting with ffprobe: {e}", file=sys.stderr)
        return False

def normalize_audio(in_file: Path, out_file: Path):
    cmd = ["ffmpeg", "-y", "-i", str(in_file), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(out_file)]
    print(f"Normalizing audio to 16kHz mono: {out_file}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        print("[OK] Audio normalized successfully.")
        return True
    print(f"Error normalizing audio: {res.stderr.decode()}", file=sys.stderr)
    return False

def synthesize_elevenlabs(text: str, voice_id: str, out_file: Path, api_key: str):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    payload = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        print(f"Synthesizing speech via ElevenLabs...")
        with urllib.request.urlopen(req) as resp:
            audio_bytes = resp.read()
            out_file.write_bytes(audio_bytes)
        print(f"[OK] Saved {len(audio_bytes)} bytes to {out_file}")
        return True
    except Exception as e:
        print(f"Error calling ElevenLabs API: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Neural Speech & Audio Pipeline")
    parser.add_argument("--info", help="Path to audio file to inspect")
    parser.add_argument("--normalize", help="Input audio to normalize to 16kHz mono WAV")
    parser.add_argument("--out", "-o", help="Output file path")
    parser.add_argument("--tts", help="Text to synthesize")
    parser.add_argument("--voice-id", default="21m00Tcm4TlvDq8ikWAM", help="ElevenLabs Voice ID")
    parser.add_argument("--api-key", help="ElevenLabs API Key (or ELEVENLABS_API_KEY env)")

    args = parser.parse_args()

    if args.info:
        inspect_audio(Path(args.info))
        sys.exit(0)

    if args.normalize:
        out = Path(args.out or "normalized_16k.wav")
        success = normalize_audio(Path(args.normalize), out)
        sys.exit(0 if success else 1)

    if args.tts:
        out = Path(args.out or "synthesized_voice.mp3")
        key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            print("Error: ElevenLabs API Key is required via --api-key or ELEVENLABS_API_KEY env.", file=sys.stderr)
            sys.exit(1)
        success = synthesize_elevenlabs(args.tts, args.voice_id, out, key)
        sys.exit(0 if success else 1)

    parser.print_help()

if __name__ == "__main__":
    main()