---
name: neural-speech-audio
description: >-
  Operational engineering skill for neural voice synthesis (TTS), speech-to-text (STT) transcription,
  voice cloning, acoustic noise reduction, and speaker diarization via ElevenLabs API, OpenAI Whisper,
  and local neural audio models.
---

# Neural Speech & Audio Engineering — Master Skill

Skill operacional canonica para processamento de voz, sintese neural de fala (TTS) e transcricao de audio (STT). Unifica pipelines de producao de audio em tempo real, dublagem automatica de avatares e geracao de legendas sincronizadas.

---

## 1. Arquitetura de Voz: TTS vs STT

| Modalidade | Motor Principal | Formato Canônico | Latência Alvo |
| :--- | :--- | :--- | :--- |
| **Síntese Neural (TTS)** | ElevenLabs API / Piper TTS | MP3 / PCM 24kHz Mono | < 300ms (Streaming WS) |
| **Transcrição & Diarização (STT)**| OpenAI Whisper (faster-whisper) | 16kHz WAV Mono | < 1.0x Real-Time Factor |
| **Sincronização de Legendas** | Phoneme Timestamp Aligner | JSON / SRT / WebVTT | N/A (Offline) |

---

## 2. Text-to-Speech (TTS) com ElevenLabs API

### 2.1 Parâmetros Críticos de Síntese
- **Model ID**: `eleven_multilingual_v2` para suporte nativo em Português do Brasil com entonação coloquial.
- **Voice Settings**:
  - `stability: 0.50` (Valores entre 0.40 e 0.60 oferecem balanço ótimo entre expressividade emocional e estabilidade).
  - `similarity_boost: 0.80` (Aderência tímbrica à voz original clonada).
  - `style: 0.15` (Intensidade estilística da voz).
- **Format**: `mp3_44100_128` para assets finais ou `pcm_24000` para buffers de streaming de ultra baixa latência.

---

## 3. Speech-to-Text (STT) com OpenAI Whisper

### 3.1 Normalização Pré-Transcrição Obrigatória
O Whisper opera com máxima acurácia quando o áudio de entrada e normalizado para **16.000 Hz, 16-bit mono**:
```bash
# Normalizacao via FFmpeg nativo
ffmpeg -i input_audio.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 clean_audio.wav
```

### 3.2 Transcrição com Segmentação de Palavras (Word-Level Timestamps)
```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe("clean_audio.wav", word_timestamps=True, language="pt")

captions = []
for segment in segments:
    for word in segment.words:
        captions.append({
            "word": word.word.strip(),
            "start": round(word.start, 3),
            "end": round(word.end, 3),
            "confidence": round(word.probability, 2)
        })
```

---

## 4. O Utilitário CLI Standalone (`scripts/speech_pipeline.py`)

A skill inclui um utilitário CLI em Python stdlib para inspecionar, sintetizar e normalizar arquivos de áudio:

```bash
# Normalizar audio para 16kHz mono pronto para Whisper
python .agents/skills/neural-speech-audio/scripts/speech_pipeline.py --normalize audio.mp3 --out audio_16k.wav

# Inspecionar duracao, taxa de amostragem e canais de audio
python .agents/skills/neural-speech-audio/scripts/speech_pipeline.py --info audio.wav

# Sintetizar texto para voz via ElevenLabs API
python .agents/skills/neural-speech-audio/scripts/speech_pipeline.py --tts "Ola, bem-vindo ao AXION" --voice-id <ID> --out fala.mp3
```

---

## 5. Portão de Verificação (Verification Gate)

1. Para TTS: O áudio MP3 retornado deve ter tamanho > 10KB e bitrate constante.
2. Para STT: A transcrição gerada deve ter confiança média > 0.85 sem repetição cíclica de tokens (*hallucination loop*).