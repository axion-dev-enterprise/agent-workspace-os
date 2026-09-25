---
name: whisper-stt-neural-voice
description: >-
  Operational skill for speech-to-text audio processing using Whisper models, speaker diarization, chunked audio processing, and subtitle generation.
---

# Whisper Audio & Speech-to-Text Skill

Skill operacional para transcrição automatizada de chamadas, reuniões e notas de voz com Whisper.

## 1. Processamento de Áudio
- **Normalização**: Converter áudio de entrada para 16kHz mono WAV antes da inferência para máxima precisão e velocidade.
- **Divisão em Janelas**: Arquivos maiores que 25MB devem ser divididos em chunks de 30 segundos em pausas de silêncio (usando `pydub` ou `ffmpeg`).
