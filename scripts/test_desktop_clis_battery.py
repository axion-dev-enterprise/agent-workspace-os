#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria de Testes Automatizada: Disponibilização das CLIs Desktop (Codex, Antigravity, OpenCode)
Valida execução nativa, wrappers de PATH, ferramentas no tool_executor, rotas do Brain Server,
governança em AGENTS.md e skills operacionais.
"""

import os
import sys
import json
import unittest
import urllib.request
import urllib.error
from pathlib import Path

# Protege contra disparos acidentais ao CEO durante os testes
os.environ["AXION_TEST_MODE"] = "1"
os.environ["CI"] = "1"

SCRIPTS_DIR = Path(r"C:\workspace\scripts")
WORKSPACE_ROOT = Path(r"C:\workspace")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import tool_executor, autonomous_agent


class TestDesktopCLIsBattery(unittest.TestCase):

    def test_01_cli_binaries_and_wrappers_in_path(self):
        """Valida que todas as 3 CLIs estão no PATH e respondem a --version."""
        for cmd_name, expected_snippet in [
            ("codex.cmd --version", "codex-cli"),
            ("agy.exe --version", "1."),
            ("antigravity.cmd --version", "1."),
            ("opencode.cmd --version", "1.")
        ]:
            res = tool_executor.exec_command(cmd_name, timeout=10)
            self.assertTrue(res.get("success"), f"Falha executando {cmd_name}: {res}")
            out = res.get("output", "")
            self.assertIn(expected_snippet, out, f"Saída inesperada para {cmd_name}: {out}")

    def test_02_get_desktop_clis_status_tool(self):
        """Valida a ferramenta get_desktop_clis_status no tool_executor."""
        res = tool_executor.get_desktop_clis_status()
        self.assertTrue(res.get("success"))
        clis = res.get("clis", {})
        self.assertIn("codex", clis)
        self.assertIn("antigravity", clis)
        self.assertIn("opencode", clis)

        self.assertTrue(clis["codex"]["ready"])
        self.assertTrue(clis["antigravity"]["ready"])
        self.assertTrue(clis["opencode"]["ready"])

        self.assertIn("codex-cli", clis["codex"]["version"])
        self.assertIn("1.", clis["antigravity"]["version"])
        self.assertIn("1.", clis["opencode"]["version"])

        self.assertIn("Inventário e Status Operacional", res.get("summary", ""))

    def test_03_run_antigravity_cli_subcommands(self):
        """Testa execução de subcomandos do Google Antigravity (agy)."""
        res = tool_executor.run_antigravity_cli(subcommand="mcp", extra_args="list", timeout=15)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("agent"), "Antigravity")
        self.assertEqual(res.get("cli"), "agy")
        self.assertIn("No MCP servers configured", res.get("output", ""))

    def test_04_run_codex_cli_subcommands(self):
        """Testa execução de subcomandos do OpenAI Codex."""
        res = tool_executor.run_codex_cli(subcommand="doctor", extra_args="--summary", timeout=20)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("agent"), "Codex")
        self.assertEqual(res.get("cli"), "codex")
        self.assertIn("ok", res.get("output", "").lower())

    def test_05_run_opencode_cli_subcommands(self):
        """Testa execução de subcomandos do OpenCode."""
        res = tool_executor.run_opencode_cli(subcommand="stats", timeout=15)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("agent"), "OpenCode")
        self.assertEqual(res.get("cli"), "opencode")
        self.assertIn("OVERVIEW", res.get("output", "").upper())

    def test_06_tool_synonyms_and_aliasing(self):
        """Valida sinônimos difusos para despacho transparente de ferramentas."""
        synonyms = tool_executor.TOOL_SYNONYMS
        self.assertEqual(synonyms.get("codex"), "run_codex_cli")
        self.assertEqual(synonyms.get("codex_cli"), "run_codex_cli")
        self.assertEqual(synonyms.get("agy"), "run_antigravity_cli")
        self.assertEqual(synonyms.get("antigravity"), "run_antigravity_cli")
        self.assertEqual(synonyms.get("opencode"), "run_opencode_cli")
        self.assertEqual(synonyms.get("desktop_clis_status"), "get_desktop_clis_status")
        self.assertEqual(synonyms.get("status_clis"), "get_desktop_clis_status")

    def test_07_param_synonyms_mapping(self):
        """Valida que sinônimos de argumentos (instruction, message, cmd) são mapeados corretamente."""
        params = tool_executor.PARAM_SYNONYMS
        self.assertIn("run_codex_cli", params)
        self.assertEqual(params["run_codex_cli"].get("instruction"), "prompt")
        self.assertEqual(params["run_codex_cli"].get("action"), "subcommand")

        self.assertIn("run_antigravity_cli", params)
        self.assertEqual(params["run_antigravity_cli"].get("message"), "prompt")

        self.assertIn("run_opencode_cli", params)
        self.assertEqual(params["run_opencode_cli"].get("query"), "prompt")

    def test_08_execute_tool_dispatch(self):
        """Testa o despachador mestre execute_tool chamando os novos comandos."""
        # Status
        r1 = tool_executor.execute_tool("desktop_clis_status", {})
        self.assertTrue(r1.get("success"))
        self.assertIn("codex", r1.get("clis", {}))

        # Antigravity CLI via alias 'agy'
        r2 = tool_executor.execute_tool("agy", {"action": "mcp", "extra_args": "list"})
        self.assertTrue(r2.get("success"))
        self.assertEqual(r2.get("agent"), "Antigravity")

        # OpenCode CLI via alias 'opencode'
        r3 = tool_executor.execute_tool("opencode", {"cmd": "models"})
        self.assertTrue(r3.get("success"))
        self.assertEqual(r3.get("agent"), "OpenCode")

    def test_09_agents_md_rule_22_presence(self):
        """Valida que a Regra #22 está formalizada no documento canônico AGENTS.md."""
        agents_content = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Regra #22:", agents_content)
        self.assertIn("Disponibilidade e Orquestração das CLIs dos Agentes Desktop", agents_content)
        self.assertIn("run_codex_cli", agents_content)
        self.assertIn("run_antigravity_cli", agents_content)
        self.assertIn("run_opencode_cli", agents_content)
        self.assertIn("get_desktop_clis_status", agents_content)

    def test_10_desktop_agents_cli_skill_files(self):
        """Valida presença da skill canônica e seu espelhamento global."""
        local_skill = WORKSPACE_ROOT / ".agents" / "skills" / "desktop-agents-cli" / "SKILL.md"
        global_skill = Path(os.path.expanduser(r"~\.gemini\antigravity\skills\desktop-agents-cli\SKILL.md"))

        self.assertTrue(local_skill.exists(), f"Skill local ausente: {local_skill}")
        self.assertTrue(global_skill.exists(), f"Skill espelhada ausente: {global_skill}")

        skill_text = local_skill.read_text(encoding="utf-8")
        self.assertIn("name: desktop-agents-cli", skill_text)
        self.assertIn("run_codex_cli", skill_text)
        self.assertIn("run_antigravity_cli", skill_text)
        self.assertIn("run_opencode_cli", skill_text)

    def test_11_system_prompt_knowledge_of_desktop_clis(self):
        """Valida que o system prompt do agente autônomo descreve o acesso às 3 CLIs."""
        prompt = autonomous_agent.build_static_system_prompt()
        self.assertIn("CLIS DOS AGENTES DESKTOP DISPONÍVEIS NO AMBIENTE", prompt)
        self.assertIn("Google Antigravity CLI", prompt)
        self.assertIn("OpenAI Codex CLI", prompt)
        self.assertIn("OpenCode CLI", prompt)
        self.assertIn("get_desktop_clis_status", prompt)

    def test_12_brain_server_endpoints(self):
        """Valida os endpoints HTTP do Brain Server para inspeção e execução das CLIs."""
        # 1. GET /v1/desktop/clis
        req = urllib.request.Request("http://127.0.0.1:8765/v1/desktop/clis")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("success"))
                self.assertIn("codex", data.get("clis", {}))
                self.assertIn("antigravity", data.get("clis", {}))
                self.assertIn("opencode", data.get("clis", {}))
        except urllib.error.URLError as e:
            self.skipTest(f"Brain Server não está em execução: {e}")

        # 2. POST /v1/desktop/cli
        post_req = urllib.request.Request(
            "http://127.0.0.1:8765/v1/desktop/cli",
            data=json.dumps({"agent": "agy", "subcommand": "mcp", "extra_args": "list"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(post_req, timeout=15) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("success"))
                self.assertEqual(data.get("agent"), "Antigravity")
        except urllib.error.URLError as e:
            self.skipTest(f"Brain Server não respondeu no POST: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  INICIANDO BATERIA DE TESTES: CLIs DESKTOP PARA WHATSAPP")
    print("=" * 55 + "\n")
    unittest.main(verbosity=2)
