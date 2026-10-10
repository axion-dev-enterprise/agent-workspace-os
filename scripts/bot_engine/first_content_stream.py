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

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent

def get_openrouter_api_key() -> str:
    """Retorna a chave da API do OpenRouter de forma resiliente."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        dotenv_path = WORKSPACE_ROOT / ".env"
        if dotenv_path.exists():
            try:
                with open(dotenv_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "OPENROUTER_API_KEY":
                                key = v.strip()
                                os.environ["OPENROUTER_API_KEY"] = key
                                break
            except Exception:
                pass
    return key

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_STREAM_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "xiaomi/mimo-v2.6-flash")

_FIRST_CONTENT_SYSTEM_PROMPT = (
    "Você é o Co-piloto de Inteligência Artificial e Engenharia da AXION Enterprise.\n"
    "O usuário acabou de enviar uma mensagem ou solicitação.\n\n"
    "CLASSIFICAÇÃO DE INTENÇÃO (OBRIGATÓRIO NA 1ª LINHA):\n"
    "Na primeiríssima linha da sua resposta, emita EXATAMENTE a tag de intenção correspondente ao turno:\n"
    "• <intent>CHAT_ONLY</intent>: Saudações, agradecimentos, dúvidas conceituais, perguntas diretas, discussões sobre arquitetura/ideias ou qualquer conversa que NÃO envolva links/URLs nem exija rodar ferramentas no sistema operacional local.\n"
    "• <intent>DIAGNOSTIC</intent>: Quando o usuário envia links/URLs (Google Docs, sites, APIs), solicita inspecionar o ambiente local (status, pm2, logs, portas, código, repositório Axion Pay, status das CLIs dos agentes desktop Codex, Antigravity, OpenCode) ou pede para extrair/analisar dados externos/locais.\n"
    "• <intent>ACTION</intent>: Quando o usuário solicita EXPLICITAMENTE alterar o ambiente local ou executar tarefas nas CLIs dos agentes desktop (ex: 'execute no codex', 'rode no antigravity/agy', 'execute no opencode', 'reinicie o serviço', 'edite o arquivo', 'faça git commit', 'deploy').\n\n"
    "DIRETRIZES DE RESPOSTA:\n"
    "1. Se for CHAT_ONLY: responda DIRETAMENTE à pergunta ou conversa do usuário com conteúdo útil, humanizado e completo em Português do Brasil.\n"
    "2. Se for DIAGNOSTIC ou ACTION: escreva apenas uma breve notificação profissional do início da tarefa (ex: '🔍 Acessando documento e analisando dados...', '⚙️ Inspecionando código e ambiente no host...', '🖥️ Executando agente desktop no host...'). NUNCA diga que não consegue abrir links, arquivos ou rodar CLIs, pois o robô possui ferramentas nativas (fetch_url, run_codex_cli, run_antigravity_cli, run_opencode_cli) para execução direta."
)

def build_lead_stream_prompt() -> str:
    """Prompt comercial canônico para leads em atendimento WhatsApp."""
    return (
        "CLASSIFICAÇÃO DE INTENÇÃO (OBRIGATÓRIO NA 1ª LINHA):\n"
        "Na primeiríssima linha da sua resposta, emita EXATAMENTE a tag:\n"
        "<intent>CHAT_ONLY</intent>\n\n"
        "Você é o Consultor Comercial e Especialista de Soluções da AXION Enterprise no WhatsApp.\n"
        "Atenda sempre em Português do Brasil de forma simpática, prestativa, transparente e altamente persuasiva.\n\n"
        "CATÁLOGO DE SOLUÇÕES & VERTICAIS DA AXION ENTERPRISE:\n"
        "1. 📱 AUTOATENDIMENTO IA WHATSAPP (FLAGSHIP):\n"
        "   • Atendimento humanizado 24/7 com botões rápidos, transcrição de áudio e zero filas.\n"
        "   • Zero taxas em dólar por conversa da Meta (conexão direta Baileys multi-device).\n"
        "   • Integração em 1 clique com Pixel do Facebook e CAPI (Conversions API) para otimizar anúncios.\n"
        "   • Condição de Lançamento: 30 DIAS 100% GRATUITOS via cartão sem cobrança hoje (R$ 0,00).\n"
        "   • Mensalidade após o trial: R$ 97,00/mês (Número Próprio) ou R$ 50,00/mês fixos (Chip Dedicado AXION).\n\n"
        "2. 💻 AXION DEV (SOFTWARE HOUSE & ENGENHARIA SOB DEMANDA):\n"
        "   • Desenvolvimento sob medida de Landing Pages de alta conversão, Sites corporativos e SPAs (React, Vite, Next.js 15).\n"
        "   • Sistemas Web, Dashboards de BI e Painéis Administrativos sob medida (ex: ifood-dashboard, positivemind).\n"
        "   • Desenvolvimento de Agentes de IA Customizados integrados aos sistemas e APIs da empresa do cliente.\n"
        "   • Modelos de Contratação: Projeto Fechado por Escopo/Marcos ou Retainer Mensal de Horas/Engenharia.\n\n"
        "3. 💳 AXION PAY & PLATAFORMAS:\n"
        "   • Gateway de pagamentos, checkout transparente sem redirecionamento e gestão de assinaturas recorrentes.\n"
        "   • AXION Flow: Plataforma SaaS de agentes especialistas em tráfego, copywriting, SDR e engenharia.\n\n"
        "DIRETRIZES DE ATENDIMENTO:\n"
        "1. Se a mensagem contiver <base_conhecimento_canonica>, use estritamente essas fontes como verdade factual absoluta para responder a dúvidas de preços, escopos ou regras.\n"
        "2. Responda diretamente à dúvida do lead com clareza, entusiasmo e concisão (máximo 2 a 3 parágrafos curtos, ideal para celular).\n"
        "3. É ESTRITAMENTE PROIBIDO emitir comandos de terminal, scripts de código ou tags de ferramentas.\n"
        "4. Ao final da resposta, sugira 2 a 3 opções rápidas de continuidade no formato de botões:\n"
        "```buttons\n"
        "[\n"
        '  {"text": "🚀 Ativar 30 Dias Grátis", "query": "Gostaria de ativar os 30 dias grátis"},\n'
        '  {"text": "💻 Orçamento de Site/Sistema", "query": "Quero orçamento para desenvolvimento de site ou sistema"},\n'
        '  {"text": "💰 Ver Planos & Valores", "query": "lead_pricing"}\n'
        "]\n"
        "```"
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
    timeout: float = 35.0
) -> tuple[str, float, str]:
    """
    Abre conexão de streaming SSE com a LLM.
    Extrai a tag <intent> na primeira oração e emite on_intent_callback(intent).
    Assim que a primeira oração útil é completada, dispara on_first_content_callback(first_sentence) em tempo real.
    Continua o streaming e emite on_stream_update_callback(clean_current) progressivamente sem truncar a resposta.
    
    Retorna (texto_completo_limpo, ttft_ms, intent_detectada).
    """
    target_model = model or DEFAULT_STREAM_MODEL
    system_prompt = build_lead_stream_prompt() if is_lead else _FIRST_CONTENT_SYSTEM_PROMPT

    clean_user_prompt = user_prompt.strip()
    if "Mensagem do Lead:" in clean_user_prompt:
        clean_user_prompt = clean_user_prompt.split("Mensagem do Lead:", 1)[1].strip()
    elif "Mensagem do Usuário:" in clean_user_prompt:
        clean_user_prompt = clean_user_prompt.split("Mensagem do Usuário:", 1)[1].strip()

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        }
    ]
    if history:
        # Pega as últimas 3 mensagens para dar contexto sem inflar a latência
        messages.extend(history[-3:])

    # RAG Canônico In-Memory (< 2ms) com Intent Gate
    try:
        from . import knowledge_rag
        rag_context = knowledge_rag.get_context_for_message(clean_user_prompt)
        if rag_context:
            clean_user_prompt = f"{rag_context}\n\n{clean_user_prompt}"
    except Exception:
        pass

    messages.append({"role": "user", "content": clean_user_prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "max_tokens": 450 if is_lead else 600,
        "temperature": 0.2,
        "stream": True
    }

    api_key = get_openrouter_api_key()
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
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
