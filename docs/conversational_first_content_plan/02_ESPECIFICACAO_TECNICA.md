# 02 — Especificação Técnica: Leitor SSE de Streaming & First Sentence Buffering

---

## 1. Contrato da API OpenRouter com Streaming

A chamada deve utilizar o protocolo Server-Sent Events (SSE) nativo da OpenAI/OpenRouter:

```python
payload = {
    "model": OPENROUTER_FALLBACK_MODEL,  # xiaomi/mimo-v2.6-flash (alta velocidade)
    "messages": messages,
    "max_tokens": 150,
    "temperature": 0.2,
    "stream": True
}
```

### Cabeçalhos Necessários:
```http
Authorization: Bearer <OPENROUTER_API_KEY>
Content-Type: application/json
Accept: text/event-stream
HTTP-Referer: https://example.com
X-Title: AXION Fast Content Streamer
```

---

## 2. Algoritmo de First Sentence Buffering

O leitor SSE acumula os deltas de texto emitidos em `choices[0].delta.content`.  
O critério para corte do **First Content** é a detecção do fechamento do primeiro pensamento ou oração gerada pela IA, respeitando os seguintes limites naturais:

```python
def is_first_sentence_complete(accumulated_text: str) -> bool:
    """
    Verifica se a LLM finalizou o primeiro pensamento com sentido completo.
    Não usa regex heurístico de assunto — apenas delimitadores naturais de linguagem.
    """
    text = accumulated_text.strip()
    words = text.split()
    
    # 1. Delimitadores naturais de frase (. ! ? ou quebra de linha dupla) com no mínimo 6 palavras
    if len(words) >= 6 and any(text.endswith(punct) for punct in ['.', '!', '?', '\n\n']):
        return True
        
    # 2. Limite superior de conforto para o leitor: se a frase for longa e atingir 22 palavras
    if len(words) >= 22:
        return True
        
    return False
```

---

## 3. Estrutura do Módulo `scripts/bot_engine/first_content_stream.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION First Content Streaming Engine — 100% LLM-driven.
Lê tokens em tempo real via SSE e despacha a primeira oração útil no WhatsApp/Telegram.
"""

import os
import json
import time
import urllib.request
from typing import Callable, Optional

def stream_first_content(
    messages: list[dict],
    on_first_content: Callable[[str], None],
    model: str = "xiaomi/mimo-v2.6-flash",
    timeout: float = 6.0
) -> str:
    """
    Consome o stream SSE da LLM e chama on_first_content(sentence)
    imediatamente ao concluir o primeiro pensamento (~800ms).
    Retorna o texto acumulado completo.
    """
    ...
```

---

## 4. Gestão de Threads e Não-Bloqueio

O `stream_first_content` deve rodar em uma thread desacoplada ou como primeiro estágio no `_process_chat_request`:
- O `on_first_content` recebe a frase e já chama o `_dispatch_reply` de forma assíncrona.
- O ReAct principal pode continuar a execução das ferramentas logo em seguida, aproveitando que o usuário já está consumindo a contextualização inicial.
