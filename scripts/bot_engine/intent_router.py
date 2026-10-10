#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic Intent Router & Fast Response Engine — AXION Enterprise
Catches common user and lead intents (demo, pricing, support, services)
returning instant, high-quality pre-formatted responses with quick action buttons.
Zero LLM latency (< 2ms) and 100% immune to file crawling hallucinations.
"""

import os
import re
import unicodedata
from typing import Optional, Tuple, Dict, Any, List

def normalize_text(text: str) -> str:
    """Normalizes string for robust intent matching: lowercase, accents removed, trimmed."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return ' '.join(text.split())

# ── Pre-formatted Intent Knowledge Base ──────────────────────────────
SUPPORT_PHONE = os.environ.get("WHATSAPP_SUPPORT_NUMBER", os.environ.get("WHATSAPP_ADMIN_NUMBER", "+5511999999999"))

_INTENT_RESPONSES = {
    "demo": {
        "text": (
            "📅 *Agendamento de Demonstração — Agent Workspace OS*\n\n"
            "Ficamos felizes com seu interesse em conhecer nosso ecossistema de soluções e agentes autônomos de IA!\n\n"
            "Nossas sessões de demonstração duram **30 minutos** e cobrem:\n"
            "• 🧠 Arquitetura de agentes autônomos 24/7 integrados aos seus canais\n"
            "• ⚡ Integrações com WhatsApp, Telegram, bancos vetoriais e APIs\n"
            "• 🎯 Diagnóstico e casos de uso específicos para o seu negócio\n\n"
            "👉 *Selecione uma opção abaixo para avançar:*"
        ),
        "buttons": [
            {"type": "reply", "text": "💬 Falar com Especialista", "query": "Gostaria de agendar um horário com um especialista técnico"},
            {"type": "reply", "text": "💰 Ver Tabela de Planos", "query": "lead_pricing"},
            {"type": "call", "text": "📞 Ligar Agora", "phoneNumber": SUPPORT_PHONE}
        ]
    },
    "pricing": {
        "text": (
            "💰 *Condição Especial de Lançamento — AXION Autoatendimento IA*\n\n"
            "Liberamos o ecossistema completo com **30 DIAS 100% GRATUITOS** para você testar no seu negócio!\n\n"
            "🟢 *Opção 1 — Com seu Próprio WhatsApp:*\n"
            "• **R$ 0,00 nos primeiros 30 dias** (100% Free)\n"
            "• Conexão instantânea via QR Code\n"
            "• **Zero taxas da Meta:** Não precisa de API oficial nem paga por conversa\n\n"
            "🔵 *Opção 2 — Com Número Dedicado AXION:*\n"
            "• **Apenas R$ 50,00 / mês** (custo exclusivo da linha/chip virtual)\n"
            "• Número novo e exclusivo pronto para uso imediato\n\n"
            "🎯 *Bônus Especial de Tráfego Pago:*\n"
            "Basta cadastrar seu **Pixel ID** ou token da **CAPI (API de Conversão)**: o agente classifica seus leads e envia eventos automáticos direto pro Gerenciador de Anúncios!\n\n"
            "👉 *Selecione uma opção abaixo para ativar seu teste:*"
        ),
        "buttons": [
            {"type": "reply", "text": "🚀 Ativar 30 Dias Grátis", "query": "Gostaria de ativar o teste gratuito de 30 dias do Autoatendimento IA"},
            {"type": "reply", "text": "🎯 Dúvidas sobre Pixel/CAPI", "query": "Como funciona a integração com Pixel do Facebook e CAPI?"},
            {"type": "call", "text": "📞 Falar com Consultor", "phoneNumber": SUPPORT_PHONE}
        ]
    },
    "support": {
        "text": (
            "🛠️ *Canal de Suporte & Operações*\n\n"
            "Nosso time de engenharia e observabilidade monitora os sistemas 24 horas por dia.\n\n"
            "• Para dúvidas gerais ou solicitações de rotina, descreva seu pedido aqui.\n"
            "• Para incidentes críticos em produção, acione o canal telefônico direto.\n\n"
            "👉 *Opções de ação rápida:*"
        ),
        "buttons": [
            {"type": "reply", "text": "📊 Status dos Servidores", "query": "/status"},
            {"type": "call", "text": "📞 Suporte de Emergência", "phoneNumber": SUPPORT_PHONE}
        ]
    },
    "services": {
        "text": (
            "✨ *Autoatendimento Inteligente & Agentes de IA*\n\n"
            "Aumente a conversão do seu negócio com agentes autônomos de alta velocidade:\n\n"
            "• ⚡ *Respostas Instantâneas (< 1s):* Atendimento 24/7 humanizado com botões rápidos.\n"
            "• 📱 *Zero Taxa da Meta:* Funciona direto no WhatsApp sem pagar por mensagem.\n"
            "• 🎯 *Integração Pixel & CAPI:* Otimização de tráfego pago com disparo automático de eventos.\n"
            "• 🔒 *30 Dias Grátis:* Teste completo no seu próprio número ou com chip dedicado.\n\n"
            "👉 *Como você prefere começar?*"
        ),
        "buttons": [
            {"type": "reply", "text": "💰 Ver Planos & Valores", "query": "lead_pricing"},
            {"type": "reply", "text": "🚀 Ativar 30 Dias Grátis", "query": "Gostaria de ativar os 30 dias grátis do sistema"},
            {"type": "call", "text": "📞 Falar com Especialista", "phoneNumber": SUPPORT_PHONE}
        ]
    }
}

# ── Pattern Rules ────────────────────────────────────────────────────
_INTENT_PATTERNS = [
    # Demo / Agendamento
    ("demo", re.compile(r'\b(lead_demo|demo|agendar|agendamento|reuniao|apresentacao|demonstracao|marcar conversa|call)\b', re.IGNORECASE)),
    # Pricing / Planos / Valores
    ("pricing", re.compile(r'\b(lead_pricing|lead_plans|preco|precos|valor|valores|plano|planos|quanto custa|tabela de preco|orcamento|proposta)\b', re.IGNORECASE)),
    # Suporte / Ajuda
    ("support", re.compile(r'\b(lead_support|suporte|ajuda|socorro|problema|bug|fora do ar|offline)\b', re.IGNORECASE)),
    # Serviços / O que faz
    ("services", re.compile(r'\b(lead_services|servico|servicos|solucao|solucoes|o que voces fazem|o que a axion faz|portfolio|tecnologias)\b', re.IGNORECASE)),
]

def match_fast_intent(raw_text: str) -> Optional[Tuple[str, str, List[Dict[str, Any]]]]:
    """
    Evaluates raw incoming text or button ID.
    Returns: (intent_name, response_text, buttons_list) if matched, else None.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    clean = raw_text.strip()

    # 1. Exact ID checks (from button clicks)
    if clean in ("lead_demo", "act:lead:demo", "flow:demo"):
        item = _INTENT_RESPONSES["demo"]
        return ("demo", item["text"], item["buttons"])
    elif clean in ("lead_pricing", "lead_plans", "act:lead:pricing", "flow:pricing"):
        item = _INTENT_RESPONSES["pricing"]
        return ("pricing", item["text"], item["buttons"])
    elif clean in ("lead_support", "act:lead:support", "flow:support"):
        item = _INTENT_RESPONSES["support"]
        return ("support", item["text"], item["buttons"])
    elif clean in ("lead_services", "act:lead:services", "flow:services"):
        item = _INTENT_RESPONSES["services"]
        return ("services", item["text"], item["buttons"])

    # Only exact button IDs are intercepted deterministically.
    # All natural language text goes directly to the LLM with first content streaming.
    return None

if __name__ == "__main__":
    test_cases = [
        "lead_demo",
        "Gostaria de agendar uma reunião",
        "Quanto custa o plano?",
        "Qual o suporte técnico de vocês?",
        "O que a AXION faz?",
        "Quero ver os backups do host"
    ]
    for tc in test_cases:
        m = match_fast_intent(tc)
        print(f"Query: '{tc}' -> Match: {m[0] if m else 'None (delegates to agent)'}")
