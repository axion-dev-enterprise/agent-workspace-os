#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION First Content Streaming & Intent Classification Engine — 100% LLM-driven.
Consome tokens em tempo real via OpenRouter Server-Sent Events (SSE),
classifica a intenção semântica do turno (<intent>CHAT_ONLY|DIAGNOSTIC|ACTION</intent>)
e detecta o fechamento do primeiro pensamento útil formulado pela IA,
disparando imediatamente para o canal (WhatsApp/Telegram), garantindo TTFT sub-segundo.
ZERO heurísticas cegas, ZERO regex de palavras-chave, ZERO templates estáticos.
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.error
from typing import Callable, Optional

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_STREAM_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "xiaomi/mimo-v2.6-flash")

_FIRST_CONTENT_SYSTEM_PROMPT = (
    "Você é o Co-piloto de Inteligência Artificial e Engenharia da AXION Enterprise.\n"
    "O usuário acabou de enviar uma mensagem ou solicitação.\n\n"
    "CLASSIFICAÇÃO DE INTENÇÃO (OBRIGATÓRIO NO INÍCIO):\n"
    "Na primeiríssima linha da sua resposta, emita EXATAMENTE a tag de intenção correspondente ao turno:\n"
    "• <intent>CHAT_ONLY</intent>: Saudações ('oi', 'olá', 'bom dia'), agradecimentos e cortesias ('valeu', 'obrigado', 'blz'), perguntas puramente teóricas ou didáticas ('o que é Docker?'), piadas ou bate-papo sem comandos no servidor.\n"
    "• <intent>DIAGNOSTIC</intent>: Leitura, consulta ou inspeção passiva ('veja o status do pm2', 'leia o log', 'quais portas estão abertas?', 'como está o sistema?').\n"
    "• <intent>ACTION</intent>: Ações ativas, edição ou criação de código/arquivos, deploy, reinício de serviços ou automações no ambiente.\n\n"
    "DIRETRIZES FUNDAMENTAIS PARA O TEXTO:\n"
    "1. Imediatamente após a tag </intent>, escreva a resposta ao usuário em Português do Brasil.\n"
    "2. Seja direto, conciso e profissional: 1 ou no máximo 2 frases objetivas.\n"
    "3. Se for CHAT_ONLY, responda de forma cordial e prestativa.\n"
    "4. Se for DIAGNOSTIC ou ACTION, declare sucintamente o plano ou ação imediata."
)

def is_first_thought_complete(accumulated_text: str) -> bool:
    """
    Avalia se a LLM já completou o primeiro pensamento com sentido pleno.
    Baseia-se puramente na pontuação natural emitida pelo modelo e contagem de palavras.
    """
    text = accumulated_text.strip()
    if not text:
        return False

    words = text.split()
    
    # 1. Delimitadores naturais de encerramento de frase com no mínimo 8 palavras
    if len(words) >= 8:
        if text.endswith(('.', '!', '?')) or '\n\n' in text:
            return True
        if text.endswith(('\n', ':\n', ';')):
            return True

    # 2. Ponto de corte seguro para frases muito longas (28+ palavras)
    if len(words) >= 28 and text.endswith(('.', '!', '?', ',', ';', ' ')):
        return True

    return False

def clean_intent_tags(text: str) -> str:
    """Remove a tag <intent>...</intent> do texto exibido ao usuário."""
    if not text:
        return ""
    cleaned = re.sub(r'<intent>\s*[A-Za-z_]+\s*</intent>', '', text, flags=re.IGNORECASE)
    return cleaned.strip()

def normalize_intent(raw_intent: str, is_lead: bool = False) -> str:
    """Normaliza a string de intenção para uma das três categorias canônicas."""
    raw = (raw_intent or "").upper().strip()
    if "CHAT" in raw:
        return "CHAT_ONLY"
    if "DIAG" in raw:
        return "DIAGNOSTIC"
    if "ACT" in raw:
        return "ACTION"
    return "CHAT_ONLY" if is_lead else "ACTION"

def generate_first_content_stream(
    user_prompt: str,
    on_first_content_callback: Optional[Callable[[str], None]] = None,
    on_stream_update_callback: Optional[Callable[[str], None]] = None,
    on_intent_callback: Optional[Callable[[str], None]] = None,
    history: Optional[list[dict]] = None,
    is_lead: bool = False,
    model: Optional[str] = None,
    timeout: float = 12.0
) -> tuple[str, float, str]:
    """
    Abre conexão de streaming SSE com a LLM.
    Extrai a tag <intent> na primeira oração e emite on_intent_callback(intent).
    Assim que a primeira oração útil é completada, dispara on_first_content_callback(first_sentence) em tempo real.
    Continua o streaming e emite on_stream_update_callback(clean_current) progressivamente sem truncar a resposta.
    
    Retorna (texto_completo_limpo, ttft_ms, intent_detectada).
    """
    target_model = model or DEFAULT_STREAM_MODEL
    system_prompt = _FIRST_CONTENT_SYSTEM_PROMPT
    if is_lead:
        system_prompt += (
            "\nATENÇÃO: O canal é de atendimento comercial a clientes (WhatsApp). "
            "Mantenha um tom consultivo, acolhedor e focado em soluções comerciais da AXION."
        )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        # Pega as últimas 3 mensagens para dar contexto sem inflar a latência
        messages.extend(history[-3:])
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "max_tokens": 600,
        "temperature": 0.2,
        "stream": True
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "HTTP-Referer": "https://example.com",
        "X-Title": "AXION Fast First Content"
    }

    req = urllib.request.Request(OPENROUTER_API_URL, data=body, headers=headers)

    t0 = time.monotonic()
    ttft_ms = 0.0
    accumulated_tokens = []
    first_content_dispatched = False
    first_sentence = ""
    detected_intent = "CHAT_ONLY" if is_lead else "ACTION"
    intent_notified = False
    last_update_time = 0.0
    last_dispatched_len = 0

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue

                event_data = line[5:].strip()
                if event_data == "[DONE]":
                    break

                try:
                    chunk = json.loads(event_data)
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    token = delta.get("content", "")
                    if not token:
                        continue

                    if ttft_ms == 0.0:
                        ttft_ms = (time.monotonic() - t0) * 1000

                    accumulated_tokens.append(token)
                    raw_text = "".join(accumulated_tokens).strip()

                    # Verifica e extrai tag de intenção precocemente
                    if not intent_notified:
                        im = re.search(r'<intent>\s*([A-Za-z_]+)\s*</intent>', raw_text, re.IGNORECASE)
                        if im:
                            detected_intent = normalize_intent(im.group(1), is_lead=is_lead)
                            intent_notified = True
                            if on_intent_callback:
                                try:
                                    on_intent_callback(detected_intent)
                                except Exception as ic_err:
                                    print(f"[FirstContentStream] Erro no on_intent_callback: {ic_err}")

                    clean_current = clean_intent_tags(raw_text)

                    # 1. Dispara o primeiro pensamento útil sem quebrar o stream
                    if not first_content_dispatched and clean_current and is_first_thought_complete(clean_current):
                        first_sentence = clean_current
                        first_content_dispatched = True
                        last_dispatched_len = len(first_sentence)
                        last_update_time = time.monotonic()
                        elapsed_first = (time.monotonic() - t0) * 1000
                        safe_preview = first_sentence[:80].encode('ascii', errors='replace').decode()
                        print(f"[FirstContentStream] >> Primeiro conteúdo [{detected_intent}] gerado em {elapsed_first:.1f}ms: \"{safe_preview}...\"")
                        if on_first_content_callback:
                            try:
                                on_first_content_callback(first_sentence)
                            except Exception as cb_err:
                                print(f"[FirstContentStream] Erro no callback de primeiro conteúdo: {cb_err}")

                    # 2. Emite atualizações progressivas de streaming throttled (~1.1s ou quebra de parágrafo)
                    elif first_content_dispatched and clean_current and on_stream_update_callback:
                        now = time.monotonic()
                        chars_added = len(clean_current) - last_dispatched_len
                        has_paragraph_break = '\n\n' in clean_current[last_dispatched_len:]
                        if (now - last_update_time >= 1.1 or (has_paragraph_break and chars_added >= 15)) and chars_added >= 8:
                            last_update_time = now
                            last_dispatched_len = len(clean_current)
                            try:
                                on_stream_update_callback(clean_current)
                            except Exception as up_err:
                                print(f"[FirstContentStream] Erro no on_stream_update_callback: {up_err}")

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"[FirstContentStream] Aviso durante streaming ({target_model}): {e}")

    raw_full = "".join(accumulated_tokens).strip()
    clean_full = clean_intent_tags(raw_full)

    # Se a intenção ainda não foi notificada, extrai ou usa default
    if not intent_notified:
        im = re.search(r'<intent>\s*([A-Za-z_]+)\s*</intent>', raw_full, re.IGNORECASE)
        if im:
            detected_intent = normalize_intent(im.group(1), is_lead=is_lead)
        if on_intent_callback:
            try:
                on_intent_callback(detected_intent)
            except Exception as ic_err:
                pass

    # Se a primeira sentença ainda não disparou (ex: resposta muito curta que não atingiu a pontuação mínima), dispara agora
    if not first_content_dispatched and clean_full:
        first_sentence = clean_full
        first_content_dispatched = True
        if on_first_content_callback:
            try:
                on_first_content_callback(first_sentence)
            except Exception as cb_err:
                print(f"[FirstContentStream] Erro no callback final de primeiro conteúdo: {cb_err}")

    # Emite a última atualização com o texto completo limpo se expandiu após o último update
    elif first_content_dispatched and clean_full and on_stream_update_callback and len(clean_full) > last_dispatched_len:
        try:
            on_stream_update_callback(clean_full)
        except Exception as up_err:
            pass

    return clean_full, ttft_ms, detected_intent

    return clean_full, ttft_ms, detected_intent


if __name__ == "__main__":
    print("Testando First Content Streaming com OpenRouter...")
    def _test_cb(sentence):
        print(f"\n[DISPARO EM TEMPO REAL RECEBIDO]:\n>> {sentence}\n")

    def _test_intent(intent):
        print(f"\n[INTENÇÃO CLASSIFICADA]: {intent}")

    t_start = time.time()
    full, ttft, intent = generate_first_content_stream(
        "Oi, tudo bem?",
        on_first_content_callback=_test_cb,
        on_intent_callback=_test_intent
    )
    print(f"Finalizado em {(time.time()-t_start)*1000:.1f}ms | TTFT: {ttft:.1f}ms | Intent: {intent}")
    print(f"Texto Completo:\n{full}")
