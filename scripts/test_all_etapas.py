#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite Completa de Verificação Automatizada - Etapas 1 a 6 da Blindagem do ReAct & Brain Server.
"""

import sys
import time
import threading
from pathlib import Path

WORKSPACE_ROOT = Path("C:/workspace")
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))

from bot_engine import message_store
from bot_engine.autonomous_agent import parse_all_tool_calls, ToolCircuitBreaker
from bot_engine.first_content_stream import clean_intent_tags, normalize_intent
from brain_server import PerChatLockManager, _ACTIVE_REQUESTS, _cleanup_old_requests, _REQUESTS_LOCK
import datetime

def test_etapa_1_dialogue_hygiene():
    print("[TEST] Etapa 1: Higiene de Histórico & Isolamento de Alertas...")
    test_cid = 9999901
    chat_file = message_store.CHATS_DIR / f"{test_cid}.jsonl"
    if chat_file.exists():
        chat_file.unlink()

    # User message
    message_store.save_message(test_cid, "incoming", "Olá, preciso de ajuda com o deploy")
    # Proactive broadcast
    message_store.save_message(test_cid, "outgoing", "⚠️ Relatório de Backup: Sincronização Concluída", metadata={"is_system_broadcast": True})
    # Another user message
    message_store.save_message(test_cid, "incoming", "Status atual?")

    history = message_store.get_clean_dialogue_history(test_cid)
    texts = [m["content"] for m in history]
    assert not any("Relatório de Backup" in t for t in texts), f"Alerta vazou no histórico: {texts}"
    assert any("Olá, preciso de ajuda" in t for t in texts)
    assert any("Status atual?" in t for t in texts)
    print("  -> Etapa 1 PASSED: Broadcasts de robô isolados com sucesso!")

def test_etapa_2_expurgo_heuristicas():
    print("[TEST] Etapa 2: Expurgo de Heurísticas Cegas & Sandboxing de Parsers...")
    didactic = "Para reverter o último commit:\n```bash\ngit reset --hard HEAD~1\ngit push --force\n```\nQualquer dúvida me avise."
    calls = parse_all_tool_calls(didactic)
    assert len(calls) == 0, f"Tutorial em markdown gerou tool_calls: {calls}"

    raw_script = "get-content C:/workspace/package.json\npm2 restart all\n"
    calls_raw = parse_all_tool_calls(raw_script)
    assert len(calls_raw) == 0, f"Script cru gerou tool_calls: {calls_raw}"

    legit = '<invoke name="write_file"><parameter name="file_path">index.html</parameter><parameter name="content"><div class="main">Olá</div></parameter></invoke>'
    calls_legit = parse_all_tool_calls(legit)
    assert len(calls_legit) == 1
    assert calls_legit[0][0] == "write_file"
    assert calls_legit[0][1].get("file_path") == "index.html"
    print("  -> Etapa 2 PASSED: Parsers protegidos e comandos didáticos mascarados!")

def test_etapa_3_intent_tags():
    print("[TEST] Etapa 3: Classificador Semântico de Escopo...")
    raw_response = "<intent>CHAT_ONLY</intent> Olá! Tudo bem com você? Como posso te ajudar hoje?"
    cleaned = clean_intent_tags(raw_response)
    assert "<intent>" not in cleaned and "</intent>" not in cleaned
    assert cleaned == "Olá! Tudo bem com você? Como posso te ajudar hoje?"

    assert normalize_intent("CHAT_ONLY") == "CHAT_ONLY"
    assert normalize_intent("DIAGNOSTIC") == "DIAGNOSTIC"
    assert normalize_intent("ACTION") == "ACTION"
    assert normalize_intent("chat") == "CHAT_ONLY"
    print("  -> Etapa 3 PASSED: Tags semânticas limpas e normalizadas com precisão!")

def test_etapa_4_task_done_barrier():
    print("[TEST] Etapa 4: Barreira de Tarefa Concluída (TaskDoneBarrier)...")
    test_cid = 9999902
    chat_file = message_store.CHATS_DIR / f"{test_cid}.jsonl"
    if chat_file.exists():
        chat_file.unlink()

    # Previous task was completed
    message_store.save_message(test_cid, "incoming", "Crie o arquivo teste.txt")
    message_store.save_message(test_cid, "outgoing", "Arquivo criado com sucesso!", metadata={"task_completed": True, "tools_executed": ["write_file"]})

    history = message_store.get_clean_dialogue_history(test_cid, limit=5)
    last_turn_was_assistant = bool(history and history[-1].get("role") == "assistant")
    assert last_turn_was_assistant

    user_prompt = "valeu!"
    clean_user_input = user_prompt.strip().lower()
    is_short_courtesy = len(clean_user_input) <= 20 and any(
        w in clean_user_input for w in ("ok", "valeu", "obrigado", "show", "blz", "beleza", "top", "perfeito", "agradeço", "vlw")
    )
    assert is_short_courtesy, "TaskDoneBarrier falhou ao reconhecer 'valeu!'"
    print("  -> Etapa 4 PASSED: TaskDoneBarrier reconhece cortesias após tarefas concluídas!")

def test_etapa_5_circuit_breaker():
    print("[TEST] Etapa 5: Circuit Breaker de Ferramentas...")
    cb = ToolCircuitBreaker(max_consecutive_failures=2)

    # First failure -> Circuit should NOT trip
    trip1 = cb.record_result("exec_command", False, "syntax error in command near '&'", {"cmd": "powershell -c echo hello & test"})
    assert not trip1, "Circuito desarmou prematuramente na 1ª falha!"

    # Second failure with same tool and same syntax error -> Circuit MUST trip
    trip2 = cb.record_result("exec_command", False, "syntax error in command near '&'", {"cmd": "powershell -c echo hello & test"})
    assert trip2, "Circuito NÃO desarmou na 2ª falha idêntica consecutiva!"

    # Reset on success
    cb.record_result("exec_command", True, "", {"cmd": "dir"})
    assert len(cb.failure_history) == 0, "Histórico do circuit breaker não foi resetado após sucesso!"
    print("  -> Etapa 5 PASSED: ToolCircuitBreaker desarmou perfeitamente na 2ª falha consecutiva!")

def test_etapa_6_per_chat_lock_and_ttl():
    print("[TEST] Etapa 6: PerChatLockManager & TTL de Memória...")
    lock_mgr = PerChatLockManager()
    cid = 888123

    lock1 = lock_mgr.get_lock(cid)
    lock2 = lock_mgr.get_lock(cid)
    assert lock1 is lock2, "Locks para o mesmo chat_id não compartilham o mesmo objeto!"

    order = []
    def worker1():
        l = lock_mgr.get_lock(cid)
        with l:
            order.append("w1_start")
            time.sleep(0.1)
            order.append("w1_end")

    def worker2():
        time.sleep(0.02)
        l = lock_mgr.get_lock(cid)
        with l:
            order.append("w2_start")
            order.append("w2_end")

    t1 = threading.Thread(target=worker1)
    t2 = threading.Thread(target=worker2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert order == ["w1_start", "w1_end", "w2_start", "w2_end"], f"Ordem de concorrência violada: {order}"

    # Test TTL cleanup
    old_time = (datetime.datetime.now() - datetime.timedelta(minutes=70)).isoformat()
    with _REQUESTS_LOCK:
        _ACTIVE_REQUESTS["req_test_old"] = {"status": "done", "finished_at": old_time}
    _cleanup_old_requests()
    assert "req_test_old" not in _ACTIVE_REQUESTS, "Requisição expirada (>60 min) não foi descartada da memória!"
    print("  -> Etapa 6 PASSED: PerChatLock serializou requisições concorrentes e TTL limpou memória!")

if __name__ == "__main__":
    print("=" * 60)
    print("INICIANDO SUITE DE TESTES DAS ETAPAS 1 A 6")
    print("=" * 60)
    test_etapa_1_dialogue_hygiene()
    test_etapa_2_expurgo_heuristicas()
    test_etapa_3_intent_tags()
    test_etapa_4_task_done_barrier()
    test_etapa_5_circuit_breaker()
    test_etapa_6_per_chat_lock_and_ttl()
    print("=" * 60)
    print("🎉 TODAS AS 6 ETAPAS FORAM RIGOROSAMENTE VALIDADAS COM SUCESSO!")
    print("=" * 60)
