#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
desktop_watcher_cli.py — CLI Operacional do Desktop Agents Watcher
Part of desktop-agents-watcher skill — AXION Enterprise
Permite varreduras manuais, auditoria de tarefas desktop e registro de conclusões.
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import json
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPTS_DIR = Path(r"C:\workspace\scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def run_status() -> dict:
    """Verifica e retorna o status atual do daemon watcher."""
    try:
        from bot_engine import desktop_watcher
        return desktop_watcher.get_desktop_watcher_status()
    except Exception as e:
        return {"status": "error", "message": f"Erro ao acessar desktop_watcher: {e}"}


def run_sweep(notify: bool = False) -> dict:
    """Dispara uma varredura manual de tarefas dos agentes desktop."""
    try:
        from bot_engine import desktop_watcher
        # Scan tasks
        result = desktop_watcher.scan_and_notify_finished_tasks(send_fn=None if not notify else None)
        return {
            "status": "success",
            "sweep_result": result,
            "message": "Varredura executada com sucesso."
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro na varredura: {e}"}


def run_record(agent: str, task_id: str, title: str, result_summary: str) -> dict:
    """Registra a conclusão de uma tarefa de agente desktop manualmente."""
    try:
        from bot_engine import desktop_watcher
        entry = desktop_watcher.record_desktop_task_completion(
            agent=agent,
            task_id=task_id,
            title=title,
            status="completed",
            result=result_summary
        )
        return {"status": "success", "recorded_entry": entry}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao registrar: {e}"}


def main():
    parser = argparse.ArgumentParser(description="CLI de Observabilidade para Agentes Desktop (Antigravity, Codex, OpenCode)")
    parser.add_argument("--status", action="store_true", help="Exibe status da supervisão e últimos alertas")
    parser.add_argument("--sweep", action="store_true", help="Executa varredura manual de tarefas pendentes/concluídas")
    parser.add_argument("--record", action="store_true", help="Registra conclusão de tarefa manualmente")
    parser.add_argument("--agent", default="antigravity", choices=["antigravity", "codex", "opencode"], help="Nome do agente")
    parser.add_argument("--task-id", help="Identificador único da tarefa")
    parser.add_argument("--title", help="Título descritivo da tarefa")
    parser.add_argument("--result", help="Resumo do resultado da entrega")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON estruturado")
    args = parser.parse_args()

    if args.record:
        if not args.task_id or not args.title:
            print("❌ --task-id e --title são obrigatórios para registrar conclusão.")
            sys.exit(1)
        res = run_record(args.agent, args.task_id, args.title, args.result or "Tarefa concluída.")
    elif args.sweep:
        res = run_sweep()
    else:
        res = run_status()

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("\n═════════════════════════════════════════════════════════════════════")
        print("          AXION DESKTOP AGENTS WATCHER — CLI DE AUDITORIA            ")
        print("═════════════════════════════════════════════════════════════════════")
        print(f"Status do Sentinel : {res.get('status', 'unknown').upper()}")
        if "total_monitored_finished" in res:
            print(f"Total Monitoradas  : {res['total_monitored_finished']}")
        if "recent_alerts" in res and res["recent_alerts"]:
            print("\n[Alertas Recentes]")
            for a in res["recent_alerts"]:
                print(f"  • [{a.get('agent')}] {a.get('title')} ({a.get('status')}) - {a.get('notified_at')}")
        if "message" in res:
            print(f"\nMensagem: {res['message']}")
        print("═════════════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
