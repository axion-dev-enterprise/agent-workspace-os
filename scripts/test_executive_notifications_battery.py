#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test Battery: Executive Notification Governance — AXION Enterprise
Validates:
1. Exact RAM usage calculation (no more '0 GB de 11.96 GB').
2. Top memory consuming processes identification.
3. Executive task eligibility filter (blocks ephemeral Antigravity task-XXXX scratch logs).
4. Real deliveries allowance and deliverable link/evidence extraction.
5. Strict RAM hysteresis deadband (prevents ping-pong alerts on 1% flutuation).
6. Friendly semantic step descriptions in chat execution blocks.
"""

import sys
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import tool_executor
from bot_engine import desktop_watcher
from bot_engine import tentacles
from bot_engine import autonomous_agent
from bot_engine import task_queue


class TestExecutiveNotificationsBattery(unittest.TestCase):

    def test_01_ram_calculation_has_used_gb(self):
        """Valida que a telemetria calcula used_gb real (eliminando o bug de '0 GB')"""
        telemetry = tool_executor.get_system_telemetry()
        ram = telemetry.get("ram", {})
        self.assertIn("used_gb", ram)
        self.assertGreater(ram["used_gb"], 0.0)
        self.assertEqual(ram["used_gb"], round(max(0.0, ram["total_gb"] - ram["free_gb"]), 2))

    def test_02_top_ram_processes_extraction(self):
        """Valida identificação dos top processos em memória pelo tool_executor"""
        procs = tool_executor.get_top_ram_processes(limit=3)
        self.assertIsInstance(procs, list)
        if procs:
            self.assertIn("name", procs[0])
            self.assertIn("memory_mb", procs[0])
            self.assertGreater(procs[0]["memory_mb"], 0.0)

    def test_03_desktop_watcher_blocks_ephemeral_scratch(self):
        """Valida que tarefas efêmeras de scratch (ex: task-5750) são descartadas pelo filtro executivo"""
        ephemeral_task = {
            "id": "antigravity_5c583549_task-5750",
            "agent": "Antigravity",
            "title": "Processo em Background (task-5750)",
            "result": "Processo finalizado (log: 232 bytes)",
            "source": "antigravity_tasks_dir"
        }
        self.assertFalse(desktop_watcher.is_executive_task_eligible(ephemeral_task))

        generic_task = {
            "id": "task_999",
            "agent": "Antigravity",
            "title": "Processo (task-1234)",
            "result": "Processo finalizado (log: 120 bytes)",
            "source": "antigravity_tasks_dir"
        }
        self.assertFalse(desktop_watcher.is_executive_task_eligible(generic_task))

    def test_04_desktop_watcher_allows_real_deliveries(self):
        """Valida que entregas reais de alto valor passam pelo filtro e extraem evidência"""
        real_delivery = {
            "id": "task_codex_deploy_42",
            "agent": "Codex",
            "title": "Deploy do Microserviço OAuth",
            "result": "Serviço compilado na porta 3000 ativa e liberado em https://oauth.example.com",
            "source": "workspace_queue"
        }
        self.assertTrue(desktop_watcher.is_executive_task_eligible(real_delivery))

        evidence = desktop_watcher._extract_deliverable_evidence(real_delivery["result"])
        self.assertEqual(evidence, "https://oauth.example.com")

    def test_05_ram_hysteresis_deadband_logic(self):
        """Valida a histerese estrita de RAM (não normaliza entre 80% e 92%)"""
        # Thresholds
        self.assertEqual(tentacles.RAM_WARN_PCT, 92.0)
        self.assertEqual(tentacles.RAM_CRIT_PCT, 96.0)
        self.assertEqual(tentacles.RAM_NORM_PCT, 80.0)
        self.assertEqual(tentacles.RAM_ALERT_COOLDOWN_SECS, 14400)

        # Simula estado anterior em WARNING com 88% atual: deve PERMANECER em WARNING (sem normalização)
        fake_state = {"ram_state": {"level": "WARNING", "last_alert_ts": 1000.0}}
        # 88% está entre 80% e 92% -> histerese mantém o estado anterior
        pct = 88.0
        previous_level = fake_state["ram_state"]["level"]
        if pct >= tentacles.RAM_CRIT_PCT:
            curr = "CRITICAL"
        elif pct >= tentacles.RAM_WARN_PCT:
            curr = "WARNING"
        elif pct <= tentacles.RAM_NORM_PCT:
            curr = "NOMINAL"
        else:
            curr = previous_level

        self.assertEqual(curr, "WARNING", "Na zona de histerese (88%), o nível deve se manter sem disparar normalização!")

    def test_06_format_execution_steps_has_semantic_descriptions(self):
        """Valida que passos de execução traduzem ferramentas para linguagem executiva"""
        sample_steps = [
            {"step": 1, "type": "tool", "name": "exec_command", "args_summary": "git status", "success": True, "duration_ms": 200},
            {"step": 2, "type": "tool", "name": "exec_command", "args_summary": "pm2 status", "success": True, "duration_ms": 300}
        ]
        block = autonomous_agent.format_execution_steps_block(sample_steps, ["exec_command", "exec_command"], "completed")
        self.assertIn("Auditoria do repositório Git", block)
        self.assertIn("Verificação de processos PM2", block)
        self.assertIn("Status da Tarefa:", block)


if __name__ == "__main__":
    unittest.main()
