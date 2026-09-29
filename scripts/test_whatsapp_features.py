#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstration & QA Script: Advanced WhatsApp Features via Baileys-Joss
Dispatches all interactive features to the target tester number.
"""

import sys
import time
import json
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BRIDGE_URL = "http://127.0.0.1:4114/send-internal"
TARGET_NUMBER = sys.argv[1].replace("+", "").replace("-", "").replace(" ", "") if len(sys.argv) > 1 else "5511988045139"
TARGET_JID = TARGET_NUMBER if "@" in TARGET_NUMBER else f"{TARGET_NUMBER}@s.whatsapp.net"

def send_payload(payload_dict, description):
    print(f"\n[*] Enviando: {description}...")
    req = urllib.request.Request(
        BRIDGE_URL,
        data=json.dumps(payload_dict).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] {description} enviado com sucesso! Status={resp.status}, MsgId={data.get('messageId')}")
            return data
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8")
        print(f"[ERRO HTTP {he.code}] {description}: {err_body}")
    except Exception as e:
        print(f"[FALHA] {description}: {e}")
    return None

def main():
    print("=" * 64)
    print(f"   🚀 DISPARO DE TESTES DE RECURSOS AVANÇADOS DO WHATSAPP")
    print(f"   Destino: {TARGET_NUMBER} ({TARGET_JID})")
    print("=" * 64)

    # 1. Botões Interativos (Quick Reply, URL, CTA Copy, CTA Call)
    p1 = {
        "to": TARGET_JID,
        "message": (
            "🤖 *DEMO RECURSOS AXION ENTERPRISE (1/4)*\n\n"
            "Olá! Segue uma demonstração completa dos novos recursos nativos do nosso motor WhatsApp.\n\n"
            "👇 *Teste os botões de ação abaixo (inclusive o de copiar código com 1 toque):*"
        ),
        "buttons": [
            {"type": "reply", "text": "⚡ Ativar Co-piloto", "query": "/status"},
            {"type": "url", "text": "🌐 Visitar Portal", "url": "https://axionenterprise.com"},
            {"type": "copy", "text": "📋 Copiar Chave PIX", "copyCode": "00020126580014br.gov.bcb.pix0136axion-hub-enterprise-pix-key5204000053039865802BR5925AXION ENTERPRISE TECH6009SAO PAULO62070503***6304E2CA"},
            {"type": "call", "text": "📞 Ligar Suporte", "phoneNumber": "+5511988045139"}
        ]
    }
    r1 = send_payload(p1, "1. Botões Interativos (Quick Reply + URL + CTA Copy + Call)")
    time.sleep(3)

    # 2. Carrossel Multi-Cards Estilo Meta AI (carouselMessage)
    p2 = {
        "to": TARGET_JID,
        "message": "🎠 *DEMO RECURSOS AXION (2/4) — CARROSSEL INTERATIVO*",
        "footer": "Deslize para o lado para ver todos os cards ➔",
        "carousel": [
            {
                "title": "🧠 Agentes Autônomos de IA",
                "body": "Desenvolvimento de inteligência artificial operacional com tomada de decisões e integração de APIs 24/7.",
                "footer": "AXION Intelligence",
                "buttons": [
                    {"type": "reply", "text": "💡 Conhecer IA", "query": "Me explique sobre os Agentes de IA"},
                    {"type": "url", "text": "📄 Ver Docs", "url": "https://axionenterprise.com/ai"}
                ]
            },
            {
                "title": "⚡ Engenharia Full-Stack & Cloud",
                "body": "Aplicações escaláveis de alta performance com Next.js, FastAPI, microsserviços e bancos vetoriais.",
                "footer": "AXION Engineering",
                "buttons": [
                    {"type": "reply", "text": "🚀 Ver Stack", "query": "Quais tecnologias a AXION domina?"}
                ]
            },
            {
                "title": "🛡️ Segurança & Observabilidade",
                "body": "Auditoria de segurança, SSL Sentinel, telemetria contínua e sentinelas autônomas em tempo real.",
                "footer": "AXION Sentinel",
                "buttons": [
                    {"type": "copy", "text": "📋 Copiar Token Demo", "copyCode": "AXION-SECURITY-TOKEN-DEMO-2026"}
                ]
            }
        ]
    }
    send_payload(p2, "2. Carrossel Multi-Cards (carouselMessage)")
    time.sleep(3)

    # 3. Lista Suspensa Interativa em Gaveta (single_select)
    p3 = {
        "to": TARGET_JID,
        "message": (
            "📋 *DEMO RECURSOS AXION (3/4) — MENU EM GAVETA / LISTA*\n\n"
            "Toque no botão abaixo para abrir a gaveta interativa com opções organizadas por categoria:"
        ),
        "list": {
            "title": "Central de Serviços",
            "buttonText": "Abrir Menu de Serviços 📂",
            "footer": "AXION Enterprise Core",
            "sections": [
                {
                    "title": "🛠️ Operações & Infraestrutura",
                    "rows": [
                        {"title": "📊 Telemetria do Host", "description": "Uso de CPU, RAM, discos e Tailscale", "id": "act:telemetry"},
                        {"title": "🩺 Varredura de Saúde", "description": "Diagnóstico do ecossistema e auto-fix", "id": "act:tool:health"},
                        {"title": "💾 Backup Inteligente", "description": "Backup incremental criptografado no cofre", "id": "act:tool:backup:smart"}
                    ]
                },
                {
                    "title": "💼 Comercial & Parcerias",
                    "rows": [
                        {"title": "📅 Agendar Demonstração", "description": "Reunião de 30min com especialista técnico", "id": "lead_demo"},
                        {"title": "💰 Tabela de Planos", "description": "Valores para empresas e startups", "id": "lead_pricing"}
                    ]
                }
            ]
        }
    }
    send_payload(p3, "3. Lista Suspensa em Gaveta (single_select)")
    time.sleep(3)

    # 4. Enquete Oficial (Poll) com Múltiplas Opções
    p4 = {
        "to": TARGET_JID,
        "poll": {
            "name": "📊 DEMO AXION (4/4): Qual dessas tecnologias mais te chamou atenção?",
            "values": [
                "1. Botão de Copiar PIX / Código 📋",
                "2. Carrossel Estilo Meta AI 🎠",
                "3. Lista Suspensa em Gaveta 📂",
                "4. Enquetes com Votação Oficial 📊"
            ],
            "selectableCount": 1
        }
    }
    r4 = send_payload(p4, "4. Enquete Oficial (Poll)")
    time.sleep(2)

    # 5. Reação com Emoji (se tivemos um messageId anterior)
    if r1 and r1.get("messageId") and r1.get("messageId") != "ok":
        p5 = {
            "to": TARGET_JID,
            "react": {
                "text": "🔥",
                "key": {
                    "remoteJid": TARGET_JID,
                    "fromMe": True,
                    "id": r1.get("messageId")
                }
            }
        }
        send_payload(p5, "5. Reação com Emoji na Primeira Mensagem")

    print("\n" + "=" * 64)
    print("   ✅ TODOS OS TESTES DISPARADOS COM SUCESSO!")
    print(f"   Peça ao destinatário ({TARGET_NUMBER}) para enviar um print.")
    print("=" * 64 + "\n")

if __name__ == "__main__":
    main()
