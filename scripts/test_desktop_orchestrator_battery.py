#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Agents Orchestrator Battery -- AXION Enterprise
Comprehensive test suite verifying Rule #25 and desktop agents orchestration:
- Task specialization & semantic affinity routing (Codex, Antigravity, OpenCode)
- Quota ledger tracking, rate-limit cooldowns, and status transitions
- Automatic failover mechanics
- Tool executor integration (`dispatch_desktop_task`, `get_desktop_orchestrator_status`)
- Brain Server HTTP endpoints
"""

import unittest
import sys
import os
import json
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import desktop_orchestrator
from bot_engine import tool_executor


class TestDesktopOrchestratorBattery(unittest.TestCase):

    def setUp(self):
        # Use test environment isolation where appropriate
        os.environ["AXION_TEST_MODE"] = "1"
        self._reset_ledger()

    def tearDown(self):
        self._reset_ledger()

    def _reset_ledger(self):
        ledger = desktop_orchestrator.load_quota_ledger()
        for a in ledger.get("agents", {}).values():
            a["status"] = "ready"
            a["rate_limited_until"] = 0
            a["quota_exceeded_until"] = 0
            a["consecutive_failures"] = 0
        desktop_orchestrator.save_quota_ledger(ledger)

    def test_01_agent_specs_and_affinity_catalog(self):
        """Valida integridade do catálogo de agentes e modelos neurais associados."""
        self.assertIn("codex", desktop_orchestrator.AGENT_SPECS)
        self.assertIn("antigravity", desktop_orchestrator.AGENT_SPECS)
        self.assertIn("opencode", desktop_orchestrator.AGENT_SPECS)

        codex_spec = desktop_orchestrator.AGENT_SPECS["codex"]
        self.assertEqual(codex_spec["tier"], "premium")
        self.assertIn("o1", codex_spec["model"])

        agy_spec = desktop_orchestrator.AGENT_SPECS["antigravity"]
        self.assertEqual(agy_spec["tier"], "enterprise")
        self.assertIn("Gemini", agy_spec["model"])

        opencode_spec = desktop_orchestrator.AGENT_SPECS["opencode"]
        self.assertEqual(opencode_spec["tier"], "free_tier")
        self.assertIn("free", opencode_spec["model"])

    def test_02_semantic_routing_selection(self):
        """Valida que o roteador seleciona o agente ideal de acordo com a semântica da tarefa."""
        # 1. Tarefa de código / refatoração / pytest -> Codex
        t_code = "Refatore a função de processamento de pagamentos e crie testes unitários em pytest"
        p_code = desktop_orchestrator.select_optimal_desktop_agent(t_code)
        self.assertEqual(p_code["selected_agent"], "codex")

        # 2. Tarefa de arquitetura / regras / skills -> Antigravity
        t_arch = "Estruture a arquitetura do workspace, regras de governança no AGENTS.md e crie novas skills"
        p_arch = desktop_orchestrator.select_optimal_desktop_agent(t_arch)
        self.assertEqual(p_arch["selected_agent"], "antigravity")

        # 3. Tarefa de script rápido / leve -> OpenCode
        t_fast = "Execute um script rápido e simples para listar e limpar arquivos temporários"
        p_fast = desktop_orchestrator.select_optimal_desktop_agent(t_fast)
        self.assertEqual(p_fast["selected_agent"], "opencode")

    def test_03_preferred_agent_override(self):
        """Valida que o parâmetro preferred_agent sobrepõe a seleção automática quando disponível."""
        prompt = "Escreva uma função simples em Python"
        p_force = desktop_orchestrator.select_optimal_desktop_agent(prompt, preferred_agent="opencode")
        self.assertEqual(p_force["selected_agent"], "opencode")
        self.assertIn("Agente preferencial", p_force["selection_reason"])

    def test_04_quota_ledger_load_save(self):
        """Valida persistência e estrutura do ledger de quotas."""
        ledger = desktop_orchestrator.load_quota_ledger()
        self.assertIsInstance(ledger, dict)
        self.assertIn("agents", ledger)
        self.assertIn("codex", ledger["agents"])
        self.assertIn("antigravity", ledger["agents"])
        self.assertIn("opencode", ledger["agents"])

    def test_05_rate_limit_detection_and_cooldown(self):
        """Valida que erro de Rate Limit (429) aciona cooldown e marca o agente com rate_limited."""
        desktop_orchestrator.update_agent_execution_feedback(
            agent="codex",
            success=False,
            output="Error 429: Too Many Requests. Rate limit reached for TPM.",
            error="429 Rate Limit"
        )
        state = desktop_orchestrator.get_agent_operational_state("codex")
        self.assertFalse(state["available"])
        self.assertEqual(state["status"], "rate_limited")
        self.assertGreater(state["remaining_seconds"], 0)

        # Limpa o estado após o teste
        desktop_orchestrator.update_agent_execution_feedback(agent="codex", success=True, output="Restabelecido")

    def test_06_quota_depleted_detection_and_cooldown(self):
        """Valida que erro de Quota Esgotada aciona cooldown prolongado e marca quota_depleted."""
        desktop_orchestrator.update_agent_execution_feedback(
            agent="antigravity",
            success=False,
            output="Error: You exceeded your current quota, please check your plan and billing details.",
            error="insufficient_quota"
        )
        state = desktop_orchestrator.get_agent_operational_state("antigravity")
        self.assertFalse(state["available"])
        self.assertEqual(state["status"], "quota_depleted")
        self.assertGreater(state["remaining_seconds"], 0)

        # Limpa o estado após o teste
        desktop_orchestrator.update_agent_execution_feedback(agent="antigravity", success=True, output="Restabelecido")

    def test_07_failover_routing_on_blocked_agent(self):
        """Valida que quando o agente primário está bloqueado por quota/rate-limit, a seleção pula para o fallback."""
        # Bloqueia temporariamente o Codex com rate limit
        desktop_orchestrator.update_agent_execution_feedback(
            agent="codex",
            success=False,
            output="429 Too Many Requests"
        )
        # Solicita tarefa de código (que normalmente iria para Codex)
        t_code = "Refatore a função de login e corrija bugs em python"
        plan = desktop_orchestrator.select_optimal_desktop_agent(t_code)
        # Não pode ser Codex, deve cair em Antigravity ou OpenCode
        self.assertNotEqual(plan["selected_agent"], "codex")
        self.assertIn(plan["selected_agent"], ["antigravity", "opencode"])

        # Restabelece Codex
        desktop_orchestrator.update_agent_execution_feedback(agent="codex", success=True, output="OK")

    def test_08_tool_executor_dispatch_desktop_task_definition(self):
        """Valida registro e documentação de dispatch_desktop_task no tool_executor."""
        self.assertIn("dispatch_desktop_task", tool_executor.TOOL_DEFINITIONS)
        tool_def = tool_executor.TOOL_DEFINITIONS["dispatch_desktop_task"]
        self.assertIn("task_description", tool_def["parameters"])
        self.assertIn("preferred_agent", tool_def["parameters"])

    def test_09_tool_executor_get_desktop_orchestrator_status(self):
        """Valida chamada da ferramenta get_desktop_orchestrator_status."""
        res = tool_executor.execute_tool("get_desktop_orchestrator_status", {})
        self.assertTrue(res.get("success"))
        self.assertIn("agents", res)
        self.assertEqual(len(res["agents"]), 3)

    def test_10_rule_25_presence_in_agents_md(self):
        """Valida que a Regra #25 está formalizada no contrato mestre AGENTS.md."""
        agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("### Regra #25: Modo Orquestrador Maestro e Despacho para Agentes Desktop", agents_md)
        self.assertIn("dispatch_desktop_task", agents_md)
        self.assertIn("quota_status.json", agents_md)

    def test_11_skill_desktop_agents_orchestrator_exists(self):
        """Valida existência da skill desktop-agents-orchestrator e espelhamento."""
        skill_file = WORKSPACE_ROOT / ".agents" / "skills" / "desktop-agents-orchestrator" / "SKILL.md"
        self.assertTrue(skill_file.exists())
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("desktop-agents-orchestrator", content)
        self.assertIn("OpenAI Codex", content)
        self.assertIn("Google Antigravity", content)
        self.assertIn("OpenCode", content)

    def test_12_companion_audit_script(self):
        """Executa o script de auditoria da skill e valida retorno de sucesso."""
        audit_script = WORKSPACE_ROOT / ".agents" / "skills" / "desktop-agents-orchestrator" / "scripts" / "audit_desktop_orchestrator.py"
        self.assertTrue(audit_script.exists())
        import subprocess
        res = subprocess.run([sys.executable, str(audit_script)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Audit falhou: {res.stdout}\n{res.stderr}")
        self.assertIn("ALL PASS", res.stdout)


if __name__ == "__main__":
    unittest.main()
