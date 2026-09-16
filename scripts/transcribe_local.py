#!/usr/bin/env python3
"""
Local Whisper Transcription Service — Agent Workspace OS
Zero-cloud, privacy-first local audio transcription using faster-whisper.
Features:
- Serial execution queue / file lock preventing race conditions on model download and GPU/CPU VRAM allocations
- Automatic language detection or Portuguese default
- Warm-up & clean JSON stdout output
"""

import sys
import os
import argparse
import json
import time

sys.stdout.reconfigure(encoding="utf-8")

LOCK_FILE = os.path.join(os.path.dirname(__file__), ".transcribe.lock")
_model_cache = {}

def acquire_lock():
    """File-based lock for cross-process concurrency control."""
    start_time = time.time()
    while time.time() - start_time < 120:  # 2 minutes max wait
        try:
            if os.name == "nt":
                lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return lock_fd
            else:
                import fcntl
                lock_fd = open(LOCK_FILE, "w")
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
        except (OSError, IOError):
            time.sleep(0.25)
    return None

def release_lock(lock_fd):
    """Release and clean up file lock."""
    if lock_fd is not None:
        try:
            if os.name == "nt":
                os.close(lock_fd)
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            else:
                import fcntl
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
        except Exception:
            pass

def get_whisper_model(model_size="base", device="cpu", compute_type="int8"):
    cache_key = f"{model_size}_{device}_{compute_type}"
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    _model_cache[cache_key] = model
    return model

def transcribe(audio_path, language="pt", model_size="base"):
    if not os.path.exists(audio_path):
        return {"ok": False, "error": f"Arquivo de áudio não encontrado: {audio_path}"}

    lock_fd = acquire_lock()
    if lock_fd is None:
        return {"ok": False, "error": "Timeout aguardando lock serial de transcrição."}

    start_t = time.time()
    try:
        model = get_whisper_model(model_size=model_size)
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts).strip()
        elapsed = time.time() - start_t

        return {
            "ok": True,
            "text": full_text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "elapsed_seconds": round(elapsed, 2),
            "engine": f"faster-whisper ({model_size})"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        release_lock(lock_fd)

def main():
    parser = argparse.ArgumentParser(description="Local Whisper Transcription Service")
    parser.add_argument("--audio", required=True, help="Path to input audio file")
    parser.add_argument("--language", default="pt", help="Audio language code (default: pt)")
    parser.add_argument("--model", default="base", help="Model size: tiny, base, small, medium")
    args = parser.parse_args()

    result = transcribe(args.audio, language=args.language, model_size=args.model)
    print(json.dumps(result, ensure_ascii=False))
    if not result.get("ok"):
        sys.exit(1)

if __name__ == "__main__":
    main()
