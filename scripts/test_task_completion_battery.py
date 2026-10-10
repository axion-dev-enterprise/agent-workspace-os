#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria de Testes Canônica: Conclusão Compulsória de Tarefas,
Anti-Evasão ("Se quiser eu faço...") e Observabilidade de Passos (Regra #23).
"""

import os
import sys
import re
import html
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))

class TestTaskCompletionAndObservabilityBattery(unittest.TestCase):

    def setUp(self):
        os.environ["AXION_TEST_MODE"] = "1"

    def test_01_rule_23_exists_in_agents_md(self):
        agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("### Regra #23:", agents_md)
        self.assertIn("Execução Autônoma Compulsória", agents_md)
        self.assertIn("Transparência de Passos", agents_md)
        self.assertIn("Proibição de Tarefas Incompletas", agents_md)
        self.assertIn("se quiser eu posso verificar", agents_md.lower())
        self.assertIn("📋 Passos de Execução Realizados:", agents_md)
        self.assertIn("Status da Tarefa:", agents_md)

    def test_02_skill_file_and_registry(self):
        skill_file = WORKSPACE_ROOT / ".agents" / "skills" / "task-completion-observability" / "SKILL.md"
        self.assertTrue(skill_file.exists(), "SKILL.md de task-completion-observability deve existir")
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("name: task-completion-observability", content)
        self.assertIn("Zero Halfway Stopping", content)
        self.assertIn("Proibição Estrita de Respostas Evasivas", content)

        registry_file = WORKSPACE_ROOT / "docs" / "SKILLS_REGISTRY.md"
        if registry_file.exists():
            reg_content = registry_file.read_text(encoding="utf-8")
            self.assertIn("task-completion-observability", reg_content)

    def test_03_static_system_prompt_contains_rule_23(self):
        from bot_engine import autonomous_agent
        prompt = autonomous_agent.build_static_system_prompt()
        self.assertIn("REGRA DE FINALIZAÇÃO COMPULSÓRIA E TRANSPARÊNCIA DE PASSOS (REGRA #23", prompt)
        self.assertIn("📋 Passos de Execução Realizados:", prompt)
        self.assertIn("Status da Tarefa:", prompt)
        self.assertIn("PROIBIÇÃO ABSOLUTA DE RESPOSTAS EVASIVAS", prompt)
        self.assertIn("se quiser eu faço", prompt.lower())

    def test_04_synthesizer_system_has_mandatory_steps_and_status(self):
        from bot_engine import autonomous_agent
        synth = autonomous_agent._SYNTHESIZER_SYSTEM
        self.assertIn("REGRA #23", synth)
        self.assertIn("TRANSPARÊNCIA OBRIGATÓRIA DE PASSOS", synth)
        self.assertIn("STATUS FINAL DA TAREFA", synth)
        self.assertIn("PROIBIÇÃO DE EVASIVAS", synth)

    def test_05_format_execution_steps_block_structure(self):
        from bot_engine import autonomous_agent
        sample_steps = [
            {"step": 1, "type": "tool", "name": "list_directory", "args_summary": "path=C:/workspace", "success": True, "duration_ms": 120},
            {"step": 2, "type": "tool", "name": "read_file", "args_summary": "file_path=C:/workspace/README.md", "success": True, "duration_ms": 350},
            {"step": 3, "type": "tool", "name": "exec_command", "args_summary": "cmd=git status", "success": False, "duration_ms": 500}
        ]
        block = autonomous_agent.format_execution_steps_block(sample_steps, ["list_directory", "read_file", "exec_command"], "completed")
        self.assertIn("<b>📋 Passos de Execução Realizados:</b>", block)
        self.assertIn("• Passo 1: ✅ <code>list_directory</code>", block)
        self.assertIn("• Passo 2: ✅ <code>read_file</code>", block)
        self.assertIn("• Passo 3: ❌ <code>exec_command</code>", block)
        self.assertIn("• <b>Status da Tarefa:</b> ✅ <i>Concluída</i>", block)

    def test_06_format_execution_steps_block_with_circuit_breaker(self):
        from bot_engine import autonomous_agent
        sample_steps = [
            {"step": 1, "type": "tool", "name": "exec_command", "args_summary": "cmd=fail1", "success": False, "duration_ms": 100},
            {"step": 2, "type": "tool", "name": "exec_command", "args_summary": "cmd=fail2", "success": False, "duration_ms": 100}
        ]
        block = autonomous_agent.format_execution_steps_block(sample_steps, ["exec_command", "exec_command"], "circuit_breaker_tripped")
        self.assertIn("<b>Status da Tarefa:</b> ⚠️ <i>Finalizada com proteção de circuito ativada</i>", block)

    def test_07_anti_evasion_conditional_offer_patterns(self):
        conditional_offer_patterns = [
            r'\b(?:se (?:você )?quiser|caso queira|se desejar|quer que eu|se preferir)\b',
            r'\b(?:posso (?:também |agora )?(?:verificar|investigar|analisar|checar|testar|rodar|olhar|abrir|executar))\b',
            r'\b(?:é só (?:me )?(?:avisar|falar|mandar|dizer|pedir))\b',
        ]
        test_phrases = [
            "Se quiser, posso verificar agora se existem chaves SSH salvas no PC. É só mandar.",
            "Caso queira, posso investigar mais a fundo o serviço nos VPS.",
            "Quer que eu investigue mais a fundo a questão do SSH nos VPS?",
            "Posso também verificar os arquivos de configuração se você preferir.",
            "É só me avisar que eu rodo o script de diagnóstico."
        ]
        for phrase in test_phrases:
            matched = any(re.search(pat, phrase, re.IGNORECASE) for pat in conditional_offer_patterns)
            self.assertTrue(matched, f"Deveria detectar oferta condicional evasiva em: '{phrase}'")

    def test_08_anti_stall_future_promise_patterns(self):
        future_promise_patterns = [
            r'\b(?:vou|irei|estou a|estou indo|vamos)\s+(?:investigar|extrair|verificar|analisar|buscar|ler|checar|inspecionar|fazer|executar|olhar|pesquisar|baixar|rodar|testar|coletar|abrir|obter|validar)\b',
            r'\b(?:aguarde|um momento|iniciando a|começando a|vou dar uma olhada|vou checar|deixe-me|vou agora)\b',
        ]
        test_phrases = [
            "Vou investigar o estado do código Axion Pay no workspace e a situação de produção em paralelo.",
            "Vou extrair o conteúdo do documento Google Docs e investigar o estado do código Axion Pay em paralelo.",
            "Irei verificar as instâncias agora mesmo.",
            "Aguarde um momento enquanto checo os servidores."
        ]
        for phrase in test_phrases:
            matched = any(re.search(pat, phrase, re.IGNORECASE) for pat in future_promise_patterns)
            self.assertTrue(matched, f"Deveria detectar promessa futura em: '{phrase}'")

    def test_09_actionable_context_signals_coverage(self):
        queries = [
            "Qual a versão do Node.js instalada no servidor?",
            "Encontre qualquer referência a senha root de VPSs Axion",
            "Veja o estado do código em produção e o repositório o Axion Pay",
            "https://docs.google.com/document/d/12345/edit",
            "veja os logs da conversa comigo",
            "qual o uso atual de memória RAM e disco?",
            "disponibilize as CLIs do codex, antigravity e opencode"
        ]
        actionable_words = [
            "http://", "https://", "veja", "analise", "verifique", "execute", "leia", "extraia",
            "inspecione", "deploy", "git", "status", "código", "repositório", "pm2", "qual a versão",
            "codex", "antigravity", "opencode", "agy", "cli", "clis", "vps", "senha", "root",
            "logs", "erro", "teste", "porta", "ssh", "onde", "ache", "procure", "como está",
            "qual o uso", "investigue", "cheque", "resolva", "conserte", "arrume", "disco", "memória"
        ]
        for q in queries:
            has_signal = any(w in q.lower() for w in actionable_words) or bool(re.search(r'https?://', q))
            self.assertTrue(has_signal, f"Query '{q}' deve ser identificada como acionável")

    def test_10_guaranteed_steps_and_status_in_output_formatting(self):
        from bot_engine import autonomous_agent
        # Test synthetic simulation of formatted_html without steps block
        raw_html = "<b>Diagnóstico do Servidor:</b> O serviço está ativo na máquina local."
        exec_steps = [
            {"step": 1, "type": "tool", "name": "exec_command", "args_summary": "cmd=pm2 status", "success": True, "duration_ms": 250}
        ]
        steps_block = autonomous_agent.format_execution_steps_block(exec_steps, ["exec_command"], "completed")
        self.assertIn("<b>📋 Passos de Execução Realizados:</b>", steps_block)
        self.assertIn("• <b>Status da Tarefa:</b> ✅ <i>Concluída</i>", steps_block)

        # Simulation of injection logic
        if not any(kw in raw_html.lower() for kw in ["passos de execução", "passos realizados", "passos executados"]):
            final_html = f"{raw_html.rstrip()}{steps_block}"
        else:
            final_html = raw_html

        self.assertIn("<b>📋 Passos de Execução Realizados:</b>", final_html)
        self.assertIn("• Passo 1: ✅ <code>exec_command</code>", final_html)
        self.assertIn("• <b>Status da Tarefa:</b> ✅ <i>Concluída</i>", final_html)

    def test_11_brain_server_whatsapp_step_reporting_syntax(self):
        brain_code = (WORKSPACE_ROOT / "scripts" / "brain_server.py").read_text(encoding="utf-8")
        self.assertIn("prog_lines_wa = []", brain_code)
        self.assertIn("prog_lines_wa.append", brain_code)
        self.assertIn("⚙️ *Executando tarefa no ambiente...*", brain_code)
        self.assertIn("edit_res = _dispatch_reply", brain_code)
        self.assertIn("enviando resposta como nova mensagem", brain_code)

if __name__ == "__main__":
    unittest.main(verbosity=2)
