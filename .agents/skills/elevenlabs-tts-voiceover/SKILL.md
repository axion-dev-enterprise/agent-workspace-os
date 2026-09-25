---
name: elevenlabs-tts-voiceover
description: >-
  Operational skill for realistic neural voice synthesis using ElevenLabs API, voice cloning, latency-optimized audio streaming, and SSML tags.
---

# ElevenLabs Neural Voice Synthesis Skill

Skill operacional para geração de locuções hiper-realistas, clones de voz corporativos e streaming de áudio.

## 1. Melhores Práticas
- **Streaming de Baixa Latência**: Usar endpoints de WebSockets ou chunked HTTP para tocar áudio em tempo real enquanto o texto ainda está sendo gerado.
- **Modelos**: Usar `eleven_multilingual_v2` para português com entonação natural e clareza fonética.
