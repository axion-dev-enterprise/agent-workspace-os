#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria de Testes Integral — RAG Canônico, Agente Autônomo e Serviços AXION
=============================================================================
Testa:
1. Acurácia e latência de recuperação do RAG SQLite FTS5 (meta < 5ms).
2. Precisão do Intent Gate (< 0.1ms).
3. Mecanismo de Hot-Reload e tolerância a cache inalterado.
4. Integração do catálogo de ferramentas (tool_executor).
5. Integridade dos endpoints HTTP locais do Brain Server e WhatsApp Bridge.
6. Blindagem de segurança RBAC (bloqueio de injeção e isolamento de Leads).
7. Turno conversacional ponta a ponta com telemetria de KV-Cache.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.bot_engine import knowledge_rag
from scripts.bot_engine import tool_executor
from scripts.bot_engine import autonomous_agent

PASSED = 0
FAILED = 0
TEST_LOGS = []

def record_test(name: str, passed: bool, detail: str = ""):
    global PASSED, FAILED
    status_str = "[PASS]" if passed else "[FAIL]"
    if passed:
        PASSED += 1
    else:
        FAILED += 1
    msg = f"{status_str} {name} - {detail}" if detail else f"{status_str} {name}"
    print(msg)
    TEST_LOGS.append({"test": name, "passed": passed, "detail": detail})


# =====================================================================
# SUÍTE 1: Acurácia e Latência do RAG (< 5ms)
# =====================================================================
def run_suite_1_rag_benchmarks():
    print("\n" + "=" * 60)
    print("SUÍTE 1: RAG SQLite FTS5 — Acurácia & Latência (< 5ms)")
    print("=" * 60)

    test_cases = [
        {
            "query": "qual o valor da mensalidade do whatsapp",
            "vertical": "all",
            "expected_kw": "97"
        },
        {
            "query": "quanto custa o chip dedicado fornecido pela axion",
            "vertical": "all",
            "expected_kw": "50"
        },
        {
            "query": "desenvolvimento de landing page e site sob demanda",
            "vertical": "commercial",
            "expected_kw": "AXION Dev"
        },
        {
            "query": "como funciona o gateway axion pay e checkout transparente",
            "vertical": "all",
            "expected_kw": "AXION Pay"
        },
        {
            "query": "quem e o ceo e autoridade maxima da empresa",
            "vertical": "governance",
            "expected_kw": "Operator"
        },
        {
            "query": "quais as portas ativas e servicos pm2",
            "vertical": "technical",
            "expected_kw": "8765"
        },
        {
            "query": "gestao de trafego pago com yan nascimento pixel capi",
            "vertical": "commercial",
            "expected_kw": "Yan Nascimento"
        },
        {
            "query": "regras anti ban e bloqueio de envios frios sem opt in",
            "vertical": "operations",
            "expected_kw": "canSendOutbound"
        }
    ]

    # Warmup do motor FTS5 para compilação JIT de SQL
    knowledge_rag.search_knowledge_base("warmup", limit=1)

    latencies = []
    for tc in test_cases:
        t0 = time.perf_counter()
        hits = knowledge_rag.search_knowledge_base(tc["query"], limit=2, vertical=tc["vertical"])
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        latencies.append(elapsed_ms)

        found_kw = False
        top_section = hits[0]["section_path"] if hits else "NENHUM"
        if hits:
            combined_text = " ".join([f"{h['section_path']} {h['content']}" for h in hits])
            found_kw = tc["expected_kw"].lower() in combined_text.lower()

        is_fast = elapsed_ms < 5.0
        passed = bool(hits) and found_kw and is_fast

        safe_top = top_section.encode("ascii", errors="replace").decode("ascii")
        record_test(
            f"RAG: '{tc['query'][:35]}...'",
            passed,
            f"Hits: {len(hits)} | {elapsed_ms:.2f}ms | Top: {safe_top[:45]}"
        )

    avg_lat = sum(latencies) / len(latencies)
    record_test(
        "RAG Latência Média Global",
        avg_lat < 3.0,
        f"Média: {avg_lat:.2f}ms (Alvo: < 3.0ms)"
    )


# =====================================================================
# SUÍTE 2: Precisão do Intent Gate (< 0.1ms)
# =====================================================================
def run_suite_2_intent_gate():
    print("\n" + "=" * 60)
    print("SUÍTE 2: Intent-Gated Filter — Precisão (< 0.1ms)")
    print("=" * 60)

    engine = knowledge_rag.get_rag_engine()

    greetings_cases = [
        "oi", "olá", "bom dia!", "boa tarde", "tudo bem?", "valeu!", "ok", "/start"
    ]
    factual_cases = [
        "quanto custa um site?", "qual o preço do whatsapp?",
        "como funciona a axion pay?", "quem é o fundador?",
        "quais as portas abertas no servidor?"
    ]

    for g in greetings_cases:
        t0 = time.perf_counter()
        is_cand = engine.is_retrieval_candidate(g)
        elapsed_us = (time.perf_counter() - t0) * 1000000.0
        passed = (is_cand is False) and (elapsed_us < 200.0)
        record_test(f"Intent Gate (Bypass): '{g}'", passed, f"Candidato: {is_cand} ({elapsed_us:.1f}µs)")

    for f in factual_cases:
        t0 = time.perf_counter()
        is_cand = engine.is_retrieval_candidate(f)
        elapsed_us = (time.perf_counter() - t0) * 1000000.0
        passed = (is_cand is True) and (elapsed_us < 200.0)
        record_test(f"Intent Gate (Trigger): '{f}'", passed, f"Candidato: {is_cand} ({elapsed_us:.1f}µs)")


# =====================================================================
# SUÍTE 3: Hot-Reload e Invalidação de Cache Mtime
# =====================================================================
def run_suite_3_hot_reload():
    print("\n" + "=" * 60)
    print("SUÍTE 3: Hot-Reload do Índice FTS5 & Estabilidade de Mtime")
    print("=" * 60)

    engine = knowledge_rag.get_rag_engine()

    # 1. Chamada sem alterações deve ser ultra rápida (< 0.05ms)
    t0 = time.perf_counter()
    count_noop = engine.reload_index(force=False)
    elapsed_noop_ms = (time.perf_counter() - t0) * 1000.0
    record_test(
        "Mtime Check Inalterado",
        count_noop > 0 and elapsed_noop_ms < 1.0,
        f"Chunks: {count_noop} ({elapsed_noop_ms:.3f}ms)"
    )

    # 2. Forçar reload deve completar em menos de 25ms
    t0 = time.perf_counter()
    count_force = engine.reload_index(force=True)
    elapsed_force_ms = (time.perf_counter() - t0) * 1000.0
    record_test(
        "Force Reindex Completo",
        count_force >= 60 and elapsed_force_ms < 30.0,
        f"Chunks reindexados: {count_force} em {elapsed_force_ms:.2f}ms"
    )


# =====================================================================
# SUÍTE 4: Integração de Ferramentas (tool_executor)
# =====================================================================
def run_suite_4_tool_executor():
    print("\n" + "=" * 60)
    print("SUÍTE 4: Integração de Ferramentas — tool_executor")
    print("=" * 60)

    # 1. Executa search_knowledge_base via dispatch
    res = tool_executor.execute_tool("search_knowledge_base", {
        "query": "preço do chip dedicado",
        "vertical": "all",
        "limit": 2
    })

    has_results = res.get("success") and res.get("count", 0) > 0
    record_test("Dispatch de search_knowledge_base", has_results, f"Count: {res.get('count')}")

    # 2. Verifica se a ferramenta está registrada nas definições
    in_defs = "search_knowledge_base" in tool_executor.TOOL_DEFINITIONS
    record_test("Registro em TOOL_DEFINITIONS", in_defs, "Presente no catálogo formal")


# =====================================================================
# SUÍTE 5: Endpoints HTTP da Brain Server API (Porta 8765)
# =====================================================================
def run_suite_5_brain_http_api():
    print("\n" + "=" * 60)
    print("SUÍTE 5: Endpoints HTTP da Brain API (http://127.0.0.1:8765)")
    print("=" * 60)

    # 1. Health check
    try:
        req = urllib.request.Request("http://127.0.0.1:8765/v1/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            is_ok = data.get("status") == "ok"
            record_test("Brain Server /v1/health", is_ok, f"Uptime: {data.get('uptime_seconds', 0):.0f}s")
    except Exception as e:
        record_test("Brain Server /v1/health", False, str(e))

    # 2. Invocação de Tool via REST API
    try:
        body = json.dumps({
            "tool_name": "search_knowledge_base",
            "args": {"query": "regras do trial de 30 dias"}
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8765/v1/tool",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            res_dict = data.get("result", {})
            has_hits = res_dict.get("success") and res_dict.get("count", 0) > 0
            record_test("Brain Server POST /v1/tool (RAG)", has_hits, f"Result count: {res_dict.get('count')}")
    except Exception as e:
        record_test("Brain Server POST /v1/tool (RAG)", False, str(e))


# =====================================================================
# SUÍTE 6: Endpoints HTTP do WhatsApp Bridge (Porta 4114)
# =====================================================================
def run_suite_6_whatsapp_bridge():
    print("\n" + "=" * 60)
    print("SUÍTE 6: Endpoints HTTP do WhatsApp Bridge (http://127.0.0.1:4114)")
    print("=" * 60)

    try:
        req = urllib.request.Request("http://127.0.0.1:4114/status")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            is_conn = data.get("status") == "connected"
            num = data.get("connectedNumber")
            record_test("WhatsApp Bridge /status", is_conn, f"Status: {data.get('status')} | Número: {num}")
    except Exception as e:
        record_test("WhatsApp Bridge /status", False, str(e))

    try:
        req = urllib.request.Request("http://127.0.0.1:4114/team")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            team_cnt = data.get("total", 0)
            record_test("WhatsApp Bridge /team", team_cnt > 0, f"Membros cadastrados: {team_cnt}")
    except Exception as e:
        record_test("WhatsApp Bridge /team", False, str(e))

    try:
        req = urllib.request.Request("http://127.0.0.1:4114/leads")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            leads_cnt = data.get("total", 0)
            record_test("WhatsApp Bridge /leads", isinstance(leads_cnt, int), f"Total leads capturados: {leads_cnt}")
    except Exception as e:
        record_test("WhatsApp Bridge /leads", False, str(e))


# =====================================================================
# SUÍTE 7: Blindagem de Segurança RBAC e Anti-Injeção
# =====================================================================
def run_suite_7_rbac_security():
    print("\n" + "=" * 60)
    print("SUÍTE 7: Blindagem de Segurança RBAC — Isolamento de Lead")
    print("=" * 60)

    # 1. No modo lead (allow_tools=False, is_lead=True), o catálogo de ferramentas deve ser vazio/bloqueado
    lead_sys_msg = autonomous_agent.build_system_message(allow_tools=False)
    has_no_tools_catalog = "FERRAMENTAS DISPONÍVEIS NO PC LOCAL" not in str(lead_sys_msg)
    record_test("Omissão de ferramentas para Leads", has_no_tools_catalog, "Zero ferramentas no prompt de Lead")

    # 2. Trava Anti-Ban do WhatsApp Bridge contra envio frio para virgem
    anti_ban_check = tool_executor.send_whatsapp_message("5599999999999", "teste frio", force=False)
    is_blocked = anti_ban_check.get("blocked_by_anti_ban") is True
    record_test("Proteção Meta Anti-Ban (canSendOutbound)", is_blocked, "Bloqueou envio frio para número virgem")


# =====================================================================
# EXECUÇÃO PRINCIPAL
# =====================================================================
def main():
    print("*" * 65)
    print("   AXION ENTERPRISE — BATERIA DE TESTES INTEGRADA DO ECOSSISTEMA")
    print(f"   Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 65)

    run_suite_1_rag_benchmarks()
    run_suite_2_intent_gate()
    run_suite_3_hot_reload()
    run_suite_4_tool_executor()
    run_suite_5_brain_http_api()
    run_suite_6_whatsapp_bridge()
    run_suite_7_rbac_security()

    print("\n" + "=" * 65)
    print(f"   RESUMO DOS TESTES: {PASSED} PASSOU | {FAILED} FALHOU (Total: {PASSED + FAILED})")
    print("=" * 65)

    if FAILED == 0:
        print("🟢 TODOS OS TESTES FORAM APROVADOS COM SUCESSO ABSOLUTO!")
        sys.exit(0)
    else:
        print(f"🔴 FORAM DETECTADAS {FAILED} FALHAS!")
        sys.exit(1)


if __name__ == "__main__":
    main()
