#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Agent Engine (Xiaomi Mimo) — AXION Enterprise
Handles multi-turn conversational reasoning, autonomous PC tool execution (ReAct loop),
dynamic button generation, live RAG telemetry, and goal-driven termination.
"""

import os
import sys
import json
import time
import re
import html
import uuid
import threading
import urllib.request
import urllib.parse
import urllib.error
import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import tool_executor
from bot_engine import dynamic_keyboard
from bot_engine import message_store
from bot_engine import task_queue
from bot_engine import telemetry
from bot_engine import error_handlers

DOTENV_PATH = WORKSPACE_ROOT / ".env"

def load_env():
    if DOTENV_PATH.exists():
        try:
            with open(DOTENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env()

OPENROUTER_API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL      = os.environ.get("OPENROUTER_MODEL", "xiaomi/mimo-v2.6-pro")
OPENROUTER_FALLBACK_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "xiaomi/mimo-v2.6-flash")
OPENROUTER_API_URL    = "https://openrouter.ai/api/v1/chat/completions"

# ---------------------------------------------------------------------------
# Watcher integration (optional — imported lazily so missing module is silent)
# ---------------------------------------------------------------------------
_watcher = None
try:
    from bot_engine import watcher as _watcher
except ImportError:
    _watcher = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_data_file(filename: str) -> Path:
    p1 = WORKSPACE_ROOT / "memory" / "infrastructure" / filename
    if p1.exists():
        return p1
    p2 = WORKSPACE_ROOT / "workspace" / filename
    if p2.exists():
        return p2
    return p1

# ---------------------------------------------------------------------------
# Live context (unchanged)
# ---------------------------------------------------------------------------

def get_live_system_context() -> str:
    """Builds unified live infrastructure context for the LLM"""
    health_file = find_data_file("health_telemetry.json")
    ssl_file    = find_data_file("ssl_telemetry.json")
    audit_file  = Path(r"E:\backups\axion_enterprise\retention_audit.json")

    health = {}
    if health_file.exists():
        try:
            with open(health_file, "r", encoding="utf-8") as f:
                health = json.load(f)
        except Exception:
            pass

    ssl = {}
    if ssl_file.exists():
        try:
            with open(ssl_file, "r", encoding="utf-8") as f:
                ssl = json.load(f)
        except Exception:
            pass

    backup = {}
    if audit_file.exists():
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                backup = json.load(f)
        except Exception:
            pass

    tasks = task_queue.list_tasks(limit=5)
    pending_tasks_count = len([t for t in tasks if t.get("status") == "pending"])

    telemetry = tool_executor.get_system_telemetry()
    ram     = telemetry.get("ram", {})
    c_drive = telemetry.get("c_drive", {})
    e_drive = telemetry.get("e_backup_drive", {})

    lines = [
        "TELEMETRIA EM TEMPO REAL — AXION ENTERPRISE:",
        f"- Timestamp Atual: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"- PC Local: Windows 10 (desktop-1t1e46h) | RAM: {ram.get('free_gb')} GB livres de {ram.get('total_gb')} GB ({ram.get('percent_used')}% em uso)",
        f"- Armazenamento C: (SSD SO): {c_drive.get('free_gb')} GB livres ({c_drive.get('percent_free')}%)",
        f"- Armazenamento E: (Cofre Frio): {e_drive.get('free_gb')} GB livres ({e_drive.get('percent_free')}%)",
        f"- Rede Tailscale Mesh: {telemetry.get('tailscale_summary')} (vps-node-01: 100.64.0.1, debian-2vcpu: 100.64.0.2)",
        "- Nós Descomissionados: juliana-vps (100.81.231.111), juliana.example.com e proxionmidia.com (100% descomissionados em 25/09/2026, dados em cofre permanente E:\\)",
        f"- Certificados SSL: {ssl.get('total_audited', 16)} auditados e saudáveis",
        f"- Fila de Tarefas do Workspace: {len(tasks)} registradas ({pending_tasks_count} pendentes)"
    ]
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Sanitizer (unchanged)
# ---------------------------------------------------------------------------

def sanitize_and_convert_to_tg_html(text: str) -> str:
    """Converts LLM markdown formatting to Telegram-compliant HTML and removes internal XML tags"""
    if not text:
        return ""

    # Strip internal execution and goal tags
    text = re.sub(r'<invoke\s+name=[\'">[^\'"]+[\'"]>[\s\S]*?</invoke>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<function(?:[=:].*?|\s+name=.*?)>[\s\S]*?</function>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?(?:invoke|parameter|tool_call|function_call|function)[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<goal_achieved>.*?</goal_achieved>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Replace markdown bold **text** or __text__ with <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text, flags=re.DOTALL)

    # Replace markdown italic *text*
    text = re.sub(r'(?<!\w)\*([^\*\n]+?)\*(?!\w)', r'<i>\1</i>', text)

    # Replace code blocks ```lang\ncode\n``` with <pre><code>code</code></pre>
    def replace_code_block(match):
        code_content = match.group(2)
        code_content = code_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre><code>{code_content}</code></pre>"
    text = re.sub(r'```([a-zA-Z0-9_\-]*)\n?(.*?)```', replace_code_block, text, flags=re.DOTALL)

    # Replace inline `code` with <code>code</code>
    def replace_inline_code(match):
        code_content = match.group(1)
        code_content = code_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<code>{code_content}</code>"
    text = re.sub(r'`([^`\n]+?)`', replace_inline_code, text)

    # Replace markdown headers ### Header with <b>Header</b>
    text = re.sub(r'^(#{1,6})\s*(.+)$', r'<b>\2</b>', text, flags=re.MULTILINE)

    # Convert list asterisks or dashes to bullets
    text = re.sub(r'^\s*[\*\-]\s+', r'• ', text, flags=re.MULTILINE)

    return text.strip()

# ---------------------------------------------------------------------------
# System prompt (always loads AGENTS.md dynamically from disk)
# ---------------------------------------------------------------------------

def load_agents_markdown() -> str:
    """Loads canonical AGENTS.md governance rules directly from the workspace root."""
    agents_path = WORKSPACE_ROOT / "AGENTS.md"
    if agents_path.exists():
        try:
            return agents_path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as e:
            return f"[Aviso: Erro ao carregar AGENTS.md: {e}]"
    return "[Aviso: Arquivo AGENTS.md não encontrado na raiz do workspace]"

def build_system_prompt() -> str:
    live_ctx     = get_live_system_context()
    tools_desc   = json.dumps(tool_executor.TOOL_DEFINITIONS, indent=2, ensure_ascii=False)
    agents_rules = load_agents_markdown()

    return (
        "Você é o Co-piloto Autônomo e Assistente de Infraestrutura da AXION Enterprise, "
        "motorizado pelo modelo neural Xiaomi Mimo.\n"
        "Você opera com AUTONOMIA TOTAL no PC local (C:\\workspace), servidores na Tailnet, "
        "borda Cloudflare, Vercel e sistemas de backup.\n\n"
        "======================================================================\n"
        "REGRAS CANÔNICAS DE GOVERNANÇA DO WORKSPACE (AGENTS.md):\n"
        "As diretrizes abaixo são mandatórias e regem todas as suas ações, ferramentas, caminhos e código:\n"
        "======================================================================\n"
        f"{agents_rules}\n"
        "======================================================================\n\n"
        f"{live_ctx}\n\n"
        "FERRAMENTAS DISPONÍVEIS NO PC LOCAL:\n"
        f"{tools_desc}\n\n"
        "COMANDOS CANÔNICOS DA CLI ANTIGRAVITY (AGY):\n"
        "• agy : Iniciar a sessão interativa TUI\n"
        "• agy -c : Continuar a conversa mais recente\n"
        "• agy -p \"<prompt>\" : Executar um prompt direto sem entrar no modo interativo (headless)\n"
        "• agy models : Listar modelos disponíveis\n"
        "• agy mcp list : Listar e gerenciar servidores MCP\n"
        "• agy update : Atualizar a CLI para a versão mais recente\n\n"
        "COMO CHAMAR FERRAMENTAS:\n"
        "Se o usuário pedir um diagnóstico, execução de comando, teste de rotas, verificação de status, "
        "ou se você precisar de dados para responder, você DEVE invocar a ferramenta correspondente.\n\n"
        "SAUDAÇÕES E CONVERSAS SOCIAIS (SEM FERRAMENTAS):\n"
        "Se o usuário enviar apenas uma saudação, cumprimento ou pergunta social informal (ex: 'oi', 'olá', 'bom dia', 'boa tarde', 'tudo bem?', 'e aí'), "
        "você NÃO DEVE chamar nenhuma ferramenta nem executar comandos. Responda imediatamente de forma calorosa, prestativa e concisa, perguntando em que pode ajudar.\n\n"
        "SINTAXE DE CHAMADA (suporta JSON ou XML):\n"
        "Formato JSON:\n"
        "```tool_call\n"
        "{\n"
        '  "tool": "exec_command",\n'
        '  "args": {"cmd": "comando powershell"}\n'
        "}\n"
        "```\n"
        "OU Formato XML:\n"
        '<invoke name="exec_command">\n'
        '<parameter name="cmd">comando powershell</parameter>\n'
        '</invoke>\n\n'
        "REGRA CRÍTICA DE EXECUÇÃO:\n"
        "1. NUNCA escreva scripts de PowerShell soltos no texto da mensagem dizendo 'vou executar agora'.\n"
        "   Se você precisa testar ou executar algo, você DEVE emitir a chamada de ferramenta `<invoke name=...>` "
        "ou ````tool_call { ... } ````. O bot executará no PC e fornecerá a saída real para você sintetizar o relatório.\n"
        "2. CAMINHOS NO WINDOWS: Use SEMPRE barras normais `/` (ex: `C:/workspace/scripts`), pois a contrabarra `\\` é caractere de escape em JSON/Python.\n"
        "3. COMANDOS HEADLESS: NUNCA execute comandos que aguardem confirmação interativa (`[y/n]`, editores ou senhas). Use sempre `-y`, `--yes` ou `--no-input`.\n"
        "4. EDIÇÃO CIRÚRGICA: Prefira usar `replace_in_file` para alterar trechos pontuais de código existente, sem reescrever o arquivo todo.\n\n"
        "AUTONOMIA COM ARQUIVOS E PASTAS LOCAIS (PC WINDOWS):\n"
        "1. Você opera DIRETAMENTE no computador da AXION (C:\\workspace). Você NÃO é um chatbot isolado em nuvem.\n"
        "2. Se o usuário fornecer um caminho de pasta/arquivo (ex: 'C:\\workspace\\apps\\projeto-exemplo') ou pedir 'analise a pasta enviada', "
        "você DEVE chamar 'list_directory' ou 'read_file' IMEDIATAMENTE para ler os dados do disco.\n"
        "3. É ESTRITAMENTE PROIBIDO pedir ao usuário para 'enviar arquivo ZIP', 'subir a pasta' ou 'colar código no chat'. "
        "Você tem acesso total ao disco rígido local e DEVE usar suas ferramentas 'list_directory' e 'read_file' autonomamente.\n\n"
        "REGRA DE DEPLOY (CRÍTICA — NUNCA IGNORE):\n"
        "Quando o usuário pedir para criar E hospedar/publicar/deploiar um site:\n"
        "1. Você DEVE usar a ferramenta `vercel_deploy` passando o HTML COMPLETO no parâmetro `html_content`.\n"
        "2. NUNCA mostre o HTML como texto no chat e diga 'vou deployar agora' — execute imediatamente.\n"
        "3. Após o deploy, retorne SOMENTE a URL pública do Vercel para o usuário.\n"
        "Exemplo de uso:\n"
        "```tool_call\n"
        "{\n"
        '  "tool": "vercel_deploy",\n'
        '  "args": {\n'
        '    "project_name": "nome-do-projeto",\n'
        '    "html_content": "<!DOCTYPE html><html>...conteúdo completo...</html>"\n'
        "  }\n"
        "}\n"
        "```\n\n"
        "BOTÕES DINÂMICOS SUGERIDOS:\n"
        "Ao final da sua resposta conclusiva, sugira de 1 a 4 botões dinâmicos de continuidade:\n"
        "```buttons\n"
        "[\n"
        '  {"text": "Texto do Botão", "query": "Pergunta de continuidade"},\n'
        '  {"text": "Executar Ação", "action": "tool:nome_da_tool"}\n'
        "]\n"
        "```\n\n"
        "GERENCIAMENTO DE TAREFAS E PROCESSOS LONGOS (SEM TIMEOUT ESTÁTICO):\n"
        "• Não existem timeouts estáticos rígidos que matam tarefas de forma arbitrária.\n"
        "• Quando uma operação (build, deploy, instalação de pacotes, script demorado) atinge o limite do checkpoint, a ferramenta retorna os logs parciais, o PID e status `running: true`.\n"
        "• Ao receber um processo em execução com checkpoint atingido:\n"
        "  1. Inspecione atentamente os logs parciais fornecidos.\n"
        "  2. Se os logs indicarem que o processo está avançando normalmente (ex: download em progresso, arquivos sendo compilados, upload do Vercel), chame a ferramenta `wait_command(pid=..., wait_seconds=30)` para continuar acompanhando.\n"
        "  3. Se os logs mostrarem travamento definitivo (aguardando input interativo no terminal, erro fatal não recuperável ou sem nenhuma atividade), chame `kill_command(pid=...)` para encerrar o processo e decida se deve reiniciar com parâmetros corrigidos ou seguir outra abordagem.\n\n"
        "FORMATO DE RESPOSTA:\n"
        "1. Responda em Português do Brasil com clareza, precisão técnica e brevidade.\n"
        "2. Formate SEMPRE em HTML válido do Telegram (<b>, <i>, <code>, <pre>). Nunca use Markdown cru.\n"
        "3. Nunca invente dados divergentes da telemetria real.\n\n"
        "REGRA ANTI-ECHO (CRÍTICA — NUNCA QUEBRE):\n"
        "• NUNCA copie strings de comandos PowerShell, bash ou shell na sua resposta ao usuário.\n"
        "• NUNCA inclua campos internos das ferramentas (returncode, command, elapsed_seconds) na resposta.\n"
        "• Após receber [RESULTADO DA TOOL 'exec_command'], você deve INTERPRETAR o output e apresentar "
        "os dados em linguagem natural humana — NÃO copiar o comando nem o output bruto.\n"
        "• Se o output for um número solto (ex: '30'), interprete o contexto: '30 linhas no arquivo de log' "
        "ou '30 tarefas registradas' — NUNCA apresente o número solto sem contexto.\n"
        "• Exemplo ERRADO: 'Get-Content \"C:/workspace/memory/daily_logs/2026-09-26.md\" -ErrorAction SilentlyContinue\\n30'\n"
        "• Exemplo CORRETO: 'O log de hoje contém 30 entradas. As tarefas realizadas foram: ...'\n\n"
        "VERIFICAÇÃO DE OBJETIVO (CRÍTICO — NUNCA IGNORE):\n"
        "Após receber os resultados de uma ou mais ferramentas, você DEVE verificar se o objetivo do usuário "
        "foi plenamente alcançado.\n"
        "• Se o objetivo FOI alcançado: responda com <goal_achieved>YES</goal_achieved> seguido da resposta final "
        "completa e conclusiva em HTML para o usuário.\n"
        "• Se o objetivo NÃO foi alcançado ainda: continue raciocinando e emita a próxima chamada de ferramenta.\n"
        "• NUNCA pare após uma única ferramenta sem verificar se o objetivo foi atingido.\n"
        "• NUNCA emita <goal_achieved>YES</goal_achieved> sem ter os dados reais para responder o objetivo."
    )

def build_lead_system_prompt() -> str:
    """Dedicated prompt for customer service and lead conversations (fast, polite, tool-free)."""
    return (
        "Você é o Consultor Comercial e Especialista de Soluções da AXION Enterprise no WhatsApp.\n"
        "Atenda sempre em Português do Brasil de forma simpática, prestativa, transparente e altamente persuasiva.\n\n"
        "PRODUTO PRINCIPAL: Sistema de Autoatendimento com Inteligência Artificial para WhatsApp.\n"
        "• 🤖 Atendimento e qualificação de clientes 24/7 com inteligência humanizada e botões interativos.\n"
        "• ⚡ Respostas instantâneas (< 1s) para eliminar o tempo de espera do cliente.\n"
        "• 📱 SEM TAXAS DA META: Não precisa integrar com a API oficial da Meta nem pagar tarifas por conversa ao Facebook.\n"
        "• 🎯 INTEGRAÇÃO COM PIXEL DO FACEBOOK & CAPI: Basta o cliente informar o Pixel ID ou token da CAPI. "
        "O agente classifica os contatos e dispara eventos automáticos de conversão para o Gerenciador de Anúncios, otimizando as campanhas de tráfego pago.\n\n"
        "OFERTA & MODELO COMERCIAL (CONDIÇÃO DE LANÇAMENTO):\n"
        "• 🎁 30 DIAS 100% GRATUITOS para o cliente testar na empresa dele.\n"
        "• Opção 1 (WhatsApp Próprio): R$ 0,00 nos primeiros 30 dias (conecta direto por QR Code).\n"
        "• Opção 2 (Número Dedicado AXION): Apenas R$ 50,00/mês referente ao chip/linha virtual que fornecemos.\n"
        "• Ativação simples via cartão de crédito para liberar os 30 dias grátis sem cobrança antecipada.\n\n"
        "DIRETRIZES DE ATENDIMENTO:\n"
        "1. Responda diretamente à dúvida do lead com entusiasmo, clareza e objetividade (máximo 2 a 3 parágrafos).\n"
        "2. Sempre incentive o lead a aproveitar os 30 dias grátis ou tirar dúvidas sobre o Pixel/CAPI.\n"
        "3. É ESTRITAMENTE PROIBIDO emitir comandos de terminal, scripts de código ou tags de ferramentas.\n"
        "4. Ao final da resposta, sugira de 2 a 3 opções rápidas de continuidade no formato de botões:\n"
        "```buttons\n"
        "[\n"
        '  {"text": "🚀 Ativar 30 Dias Grátis", "query": "Gostaria de ativar os 30 dias grátis"},\n'
        '  {"text": "💰 Ver Planos & Valores", "query": "lead_pricing"},\n'
        '  {"text": "🎯 Dúvidas sobre Pixel/CAPI", "query": "Como funciona o rastreamento com Pixel e CAPI?"}\n'
        "]\n"
        "```"
    )

# ---------------------------------------------------------------------------
# OpenRouter API call (unchanged)
# ---------------------------------------------------------------------------

def call_openrouter_api(messages: list, model: str = None, timeout: int = 90, max_tokens: int = 4000) -> dict:
    target_model = model or OPENROUTER_MODEL
    payload = {
        "model": target_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "AXION Autonomous Telegram Agent"
    }
    body = json.dumps(payload).encode("utf-8")

    def _execute():
        req = urllib.request.Request(OPENROUTER_API_URL, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    t0 = time.monotonic()
    try:
        res = error_handlers.retry_with_backoff(
            _execute,
            max_retries=2,
            initial_delay=1.5,
            service_name="openrouter_api",
            circuit=error_handlers.OPENROUTER_CIRCUIT
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        telemetry.record_llm_metric(target_model, duration_ms, success=True)
        return res
    except Exception as e:
        duration_ms = int((time.monotonic() - t0) * 1000)
        telemetry.record_llm_metric(target_model, duration_ms, success=False, error=str(e))
        raise


class ToolCircuitBreaker:
    """
    Monitors consecutive failures of tools within the ReAct loop.
    If the same tool fails 2 consecutive times with the same error category or same arguments,
    it trips the circuit breaker to prevent token blowups and infinite retry loops.
    """
    def __init__(self, max_consecutive_failures: int = 2):
        self.max_failures = max_consecutive_failures
        self.failure_history: list[tuple[str, str, int]] = []

    def _categorize_error(self, err_msg: str) -> str:
        err = (err_msg or "").lower()
        if "syntax" in err or "parse" in err:
            return "SYNTAX_ERROR"
        if "not found" in err or "não encontrado" in err or "enoent" in err:
            return "NOT_FOUND"
        if "permission" in err or "acesso negado" in err:
            return "PERMISSION_DENIED"
        if "timeout" in err:
            return "TIMEOUT"
        return err[:40]

    def record_result(self, tool_name: str, success: bool, error_msg: str, args: dict) -> bool:
        """Returns True if the circuit breaker trips (abort ReAct loop immediately)."""
        if success:
            self.failure_history.clear()
            return False

        err_cat = self._categorize_error(error_msg)
        try:
            args_signature = hash(json.dumps(args, sort_keys=True, default=str))
        except Exception:
            args_signature = hash(str(args))

        self.failure_history.append((tool_name, err_cat, args_signature))

        if len(self.failure_history) >= self.max_failures:
            last_two = self.failure_history[-2:]
            same_tool = (last_two[0][0] == last_two[1][0])
            same_error_or_args = (last_two[0][1] == last_two[1][1] or last_two[0][2] == last_two[1][2])
            if same_tool and same_error_or_args:
                return True

        return False



def repair_json(raw_str: str) -> dict:
    """
    Robust Auto-Fix parser for imperfect JSON produced by LLMs.
    Handles trailing commas, single quotes, unquoted keys, unescaped backslashes,
    unclosed brackets/braces, and extracts valid dictionary objects.
    """
    if not raw_str or not raw_str.strip():
        return {}

    cleaned = raw_str.strip()

    # Try standard json parse first
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Extract JSON object substring if surrounded by markdown or extra text
    obj_match = re.search(r'\{[\s\S]*\}', cleaned)
    if obj_match:
        cleaned = obj_match.group(0)

    # 1. Normalize unescaped Windows backslashes in paths
    cleaned = re.sub(r'([A-Za-z]:)\\([^\s"\'<>`]+)', lambda m: m.group(1) + '/' + m.group(2).replace('\\', '/'), cleaned)

    # 2. Normalize quotes
    if '"' not in cleaned and "'" in cleaned:
        cleaned = cleaned.replace("'", '"')
    else:
        cleaned = re.sub(r"'([a-zA-Z0-9_\-]+)'\s*:", r'"\1":', cleaned)
        cleaned = re.sub(r':\s*\'([^\']*?)\'', r': "\1"', cleaned)

    # 3. Quote unquoted keys: {key: "val"} -> {"key": "val"}
    cleaned = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)

    # 4. Quote unquoted bareword string values: {"tool": exec_command} -> {"tool": "exec_command"}
    def quote_bareword(m):
        val = m.group(1).strip()
        if val.lower() in ("true", "false", "null") or val.isdigit():
            return f': {val}'
        return f': "{val}"'
    cleaned = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_./\\-]*)\s*(?=[,}])', quote_bareword, cleaned)

    # 5. Remove trailing commas before } or ]
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    # 6. Fix unclosed braces/brackets
    open_braces = cleaned.count('{') - cleaned.count('}')
    if open_braces > 0:
        cleaned += '}' * open_braces
    open_brackets = cleaned.count('[') - cleaned.count(']')
    if open_brackets > 0:
        cleaned += ']' * open_brackets

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 6. Fallback regex extractor for key: value pairs if JSON parser still fails
    fallback_dict = {}
    for kv_match in re.finditer(r'["\']?([a-zA-Z0-9_\-]+)["\']?\s*[:=]\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s,}]+))', cleaned):
        k = kv_match.group(1)
        v = kv_match.group(2) or kv_match.group(3) or kv_match.group(4) or ""
        v = v.strip().strip('"\'')
        if v.isdigit():
            fallback_dict[k] = int(v)
        elif v.lower() == 'true':
            fallback_dict[k] = True
        elif v.lower() == 'false':
            fallback_dict[k] = False
        else:
            fallback_dict[k] = v

    return fallback_dict

def normalize_tool_call(tool_name: str, args: dict) -> tuple[str, dict]:
    """
    Auto-fixes and normalizes tool names and arguments:
    - Normalizes synonyms: run_cmd -> exec_command, list_dir -> list_directory, cat -> read_file
    - Normalizes parameter names: dir -> path, command -> cmd, file -> file_path
    - Fixes Windows backslashes in paths
    """
    clean_name = tool_name.strip().lower()

    # Tool synonym mapping
    synonyms = {
        "run_command": "exec_command",
        "execute_command": "exec_command",
        "cmd": "exec_command",
        "terminal": "exec_command",
        "shell": "exec_command",
        "powershell": "exec_command",
        "bash": "exec_command",
        "dir": "list_directory",
        "ls": "list_directory",
        "list_dir": "list_directory",
        "listar_diretorio": "list_directory",
        "listar_pasta": "list_directory",
        "cat": "read_file",
        "view_file": "read_file",
        "read": "read_file",
        "ler_arquivo": "read_file",
        "create_file": "write_file",
        "save_file": "write_file",
        "write": "write_file",
        "escrever_arquivo": "write_file",
        "edit_file": "replace_in_file",
        "patch_file": "replace_in_file",
        "grep": "search_in_files",
        "find_in_files": "search_in_files",
        "telemetry": "get_system_telemetry",
        "sysinfo": "get_system_telemetry",
        "deploy": "vercel_deploy",
        "wait_cmd": "wait_command",
        "wait_process": "wait_command",
        "await_command": "wait_command",
        "aguardar_comando": "wait_command",
        "kill_process": "kill_command",
        "stop_command": "kill_command",
        "abort_command": "kill_command",
        "cancel_command": "kill_command",
        "matar_processo": "kill_command",
        "encerrar_processo": "kill_command",
        "status_command": "check_command_status",
        "check_process": "check_command_status",
    }
    canonical_name = synonyms.get(clean_name, clean_name)

    # Argument normalization
    normalized_args = dict(args) if isinstance(args, dict) else {}

    # Normalize paths
    for k, v in list(normalized_args.items()):
        if isinstance(v, str) and ("\\" in v or "/" in v):
            normalized_args[k] = v.replace("\\", "/")

    # Parameter synonym mapping
    param_synonyms = {
        "exec_command": {"command": "cmd", "script": "cmd", "code": "cmd", "input": "cmd"},
        "read_file": {"path": "file_path", "filename": "file_path", "file": "file_path", "input": "file_path"},
        "write_file": {"path": "file_path", "filename": "file_path", "file": "file_path", "text": "content", "data": "content"},
        "list_directory": {"dir": "path", "directory": "path", "folder": "path", "caminho": "path", "input": "path"},
        "search_in_files": {"search": "query", "pattern": "query", "text": "query", "termo": "query"},
        "free_port": {"p": "port", "porta": "port"},
        "wait_command": {"seconds": "wait_seconds", "time": "wait_seconds", "timeout": "wait_seconds", "duration": "wait_seconds", "process_id": "pid", "id": "pid"},
        "kill_command": {"process_id": "pid", "id": "pid"},
        "check_command_status": {"process_id": "pid", "id": "pid"},
    }
    if canonical_name in param_synonyms:
        for old_k, canon_k in param_synonyms[canonical_name].items():
            if old_k in normalized_args and canon_k not in normalized_args:
                normalized_args[canon_k] = normalized_args.pop(old_k)

    # Normalize PID to int if string
    if canonical_name in ("wait_command", "kill_command", "check_command_status") and "pid" in normalized_args:
        try:
            normalized_args["pid"] = int(str(normalized_args["pid"]).strip())
        except (ValueError, TypeError):
            pass

    return canonical_name, normalized_args

def parse_all_tool_calls(text: str) -> list[tuple[str, dict]]:
    """Extracts and auto-fixes all tool invocations from XML tags, JSON blocks, and function formats."""
    if not text:
        return []

    # Mask didactic/tutorial code blocks (e.g. ```bash, ```python, ```powershell, ```sql, ```html)
    # to prevent code examples or tutorials from being accidentally parsed as executable tools.
    # We preserve ```tool_call and ```toolcall blocks since they are valid invocation formats.
    def _mask_code_blocks(content: str) -> str:
        def _replace_block(match):
            lang = (match.group(1) or '').lower().strip()
            # If the block explicitly designates a tool call, leave it unmasked for extraction
            if lang in ('tool_call', 'toolcall', 'tool'):
                return match.group(0)
            # If it's a json block, only leave unmasked if it contains tool invocation keys
            if lang == 'json':
                body = match.group(2)
                if any(k in body for k in ['"tool"', '"action"', '"function"']):
                    return match.group(0)
            # Otherwise mask it out
            return f"\n<!-- MASKED_CODE_BLOCK_{lang} -->\n"

        return re.sub(r'```([a-zA-Z0-9_-]*)\s*\n([\s\S]*?)```', _replace_block, content)

    sanitized_text = _mask_code_blocks(text)
    raw_calls = []

    # 1. Unified XML / Tag style: <invoke>, <function>, <tool>, <call>
    tag_pattern = r'<(?:invoke|function|tool|call)(?:\s+name=|[=:])[\'"]?([^\s\'">]+)[\'"]?\s*>([\s\S]*?)</(?:invoke|function|tool|call)>'
    for m in re.finditer(tag_pattern, sanitized_text, re.IGNORECASE):
        tool_name = m.group(1).strip()
        body = m.group(2).strip()
        args = {}

        # Extract nested parameters: <parameter name="x">, <parameter=x>, <param:x>, etc.
        param_pattern = r'<(?:parameter|param)(?:\s+name=|[=:])[\'"]?([^\s\'">]+)[\'"]?\s*>([\s\S]*?)</(?:parameter|param)>'
        for pm in re.finditer(param_pattern, body, re.IGNORECASE):
            p_name = pm.group(1).strip()
            p_val = pm.group(2).strip()
            if p_val.isdigit():
                args[p_name] = int(p_val)
            else:
                args[p_name] = p_val

        # If no <parameter> tags found, check if body is a JSON object or string
        if not args:
            if body.startswith("{"):
                args = repair_json(body)
            elif body:
                args = {"input": body}

        if tool_name:
            raw_calls.append((tool_name, args))

    # 2. JSON style ```tool_call ... ``` or ```json ... ``` with auto-fix
    for m in re.finditer(r'```(?:tool_call|toolcall|tool|json)\s*([\s\S]*?)\s*```', sanitized_text, re.IGNORECASE):
        block_text = m.group(1).strip()
        if any(k in block_text for k in ["tool", "action", "function", "cmd", "path"]):
            data = repair_json(block_text)
            if isinstance(data, dict):
                t_name = data.get("tool") or data.get("action") or data.get("function")
                t_args = data.get("args") or data.get("parameters") or data.get("action_input") or {k: v for k, v in data.items() if k not in ["tool", "action", "function"]}
                if t_name:
                    raw_calls.append((t_name, t_args if isinstance(t_args, dict) else {"input": str(t_args)}))

    # 3. JSON tag <tool_call> ... </tool_call> or <action> ... </action> with auto-fix
    for m in re.finditer(r'<(?:tool_call|action)>\s*([\s\S]*?)\s*</(?:tool_call|action)>', sanitized_text, re.IGNORECASE):
        data = repair_json(m.group(1).strip())
        if isinstance(data, dict):
            t_name = data.get("tool") or data.get("action")
            t_args = data.get("args") or data.get("parameters") or data.get("action_input") or {k: v for k, v in data.items() if k not in ["tool", "action"]}
            if t_name:
                raw_calls.append((t_name, t_args if isinstance(t_args, dict) else {"input": str(t_args)}))

    # Apply Auto-Fix & Synonym Normalization on all calls
    final_calls = []
    for tool_name, args in raw_calls:
        c_name, c_args = normalize_tool_call(tool_name, args)
        final_calls.append((c_name, c_args))

    return final_calls



# ---------------------------------------------------------------------------
# Goal check (separate cheap API call)
# ---------------------------------------------------------------------------

_GOAL_CHECK_SYSTEM = (
    "Você é um avaliador de objetivos. Analise se o objetivo do usuário foi alcançado com base nos resultados "
    "das ferramentas fornecidos. Responda de forma MUITO concisa.\n"
    "• Se o objetivo FOI alcançado: comece com <goal_achieved>YES</goal_achieved> e então dê uma resposta "
    "final curta e direta em Português do Brasil (HTML do Telegram).\n"
    "• Se NÃO foi alcançado: explique brevemente o que ainda precisa ser feito (sem tag)."
)

def _check_goal_achieved(goal: str, tool_results_summary: str) -> tuple[bool, str]:
    """
    Makes a cheap API call to check if the goal was achieved.
    Returns (achieved: bool, response_text: str).
    """
    messages = [
        {"role": "system", "content": _GOAL_CHECK_SYSTEM},
        {"role": "user",   "content": (
            f"Objetivo do usuário: {goal}\n\n"
            f"Resultados das ferramentas executadas:\n{tool_results_summary}\n\n"
            "O objetivo foi alcançado? Responda com <goal_achieved>YES</goal_achieved> e a resposta final "
            "OU explique o que ainda falta."
        )}
    ]
    try:
        res = call_openrouter_api(
            messages,
            model=OPENROUTER_FALLBACK_MODEL,
            timeout=40,
            max_tokens=300
        )
        text = (res.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        text = text.strip()
        achieved = bool(re.search(r'<goal_achieved>\s*YES\s*</goal_achieved>', text, re.IGNORECASE))
        return achieved, text
    except Exception as e:
        print(f"[Agent] Erro no goal check: {e}")
        return False, ""

# ---------------------------------------------------------------------------
# Dedicated Two-Stage Synthesizer (Natural Language Summarizer LLM)
# ---------------------------------------------------------------------------

_SYNTHESIZER_SYSTEM = (
    "Você é o Assistente Oficial da AXION Enterprise no Telegram.\n"
    "Sua ÚNICA missão é responder diretamente ao usuário em Português do Brasil com linguagem natural, "
    "humana, profissional e acolhedora.\n\n"
    "REGRAS MANDATÓRIAS (INVIOLÁVEIS):\n"
    "1. É ESTRITAMENTE PROIBIDO escrever comandos de terminal, scripts de PowerShell ou bash (ex: Get-Content, Test-Path, powershell.exe, dir, cat).\n"
    "2. Responda à pergunta do usuário baseando-se nos dados coletados pelas ferramentas no computador.\n"
    "3. Se arquivos foram lidos, resuma as tarefas, códigos e estruturas encontradas de forma clara e organizada com marcadores.\n"
    "4. Se nenhum dado foi encontrado ou o arquivo estava vazio/inexistente, informe isso com naturalidade.\n"
    "5. Formate a resposta usando HTML do Telegram (<b>negrito</b>, <i>itálico</i>, <code>nomes curtos de arquivos/status</code>).\n"
    "6. NUNCA mencione códigos de saída ou termos brutos como 'ARQUIVO_NAO_ENCONTRADO' ou 'SilentlyContinue'.\n"
    "7. NUNCA, SOB NENHUMA HIPÓTESE, peça ao usuário para 'enviar arquivo ZIP', 'subir a pasta', 'fazer upload' ou 'colar arquivos'. "
    "Você opera DENTRO do PC local da AXION e tem acesso direto ao disco rígido. Se você não possui os dados de uma pasta, apenas explique isso cordialmente."
)

def synthesize_in_natural_language(
    user_prompt: str,
    tool_results_accumulator: list[str],
    raw_draft: str,
    model: str = None
) -> str:
    """
    Two-Stage Architecture: Dedicated final synthesis pass.
    Guarantees 100% human natural language response in Telegram HTML.
    Eliminates all raw terminal commands, JSON dumps, and technical noise.
    """
    synth_model = model or OPENROUTER_FALLBACK_MODEL

    # Prepare clean draft without raw execution tags
    clean_draft = re.sub(r'</?(?:invoke|parameter|tool_call|function_call|function)[^>]*>', '', raw_draft, flags=re.IGNORECASE).strip()

    data_summary = "\n\n".join(tool_results_accumulator) if tool_results_accumulator else "(Nenhuma ferramenta foi executada)"

    user_content = (
        f"PERGUNTA DO USUÁRIO:\n{user_prompt}\n\n"
        f"DADOS COLETADOS NO SISTEMA / PC:\n{data_summary[:3500]}\n\n"
        f"RASCUNHO INICIAL DE ANÁLISE:\n{clean_draft[:1000] if clean_draft else '(Sem rascunho textual)'}\n\n"
        "Com base nos dados coletados acima, escreva a resposta final para o usuário em Português limpo e humanizado:"
    )

    messages = [
        {"role": "system", "content": _SYNTHESIZER_SYSTEM},
        {"role": "user", "content": user_content}
    ]

    try:
        res = call_openrouter_api(messages, model=synth_model, timeout=45, max_tokens=1000)
        content = (res.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        content = content.strip()
        if content and len(content) > 15:
            return content
    except Exception as e:
        print(f"[Agent] Erro no sintetizador com {synth_model}: {e}")

    # Fallback to OPENROUTER_MODEL if fallback model failed
    if synth_model != OPENROUTER_MODEL:
        try:
            res = call_openrouter_api(messages, model=OPENROUTER_MODEL, timeout=45, max_tokens=1000)
            content = (res.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
            if content.strip() and len(content.strip()) > 15:
                return content.strip()
        except Exception as e2:
            print(f"[Agent] Erro no sintetizador primário: {e2}")

    return clean_draft

def detect_and_enrich_path_context(user_prompt: str, history: list) -> str:
    """
    Detects directory or file paths mentioned in the user prompt or recent history.
    If a real local path is detected on the PC, injects an explicit mandatory directive
    forcing the agent to call list_directory or read_file autonomously.
    """
    candidate_paths = []

    # 1. Search in current user_prompt
    for m in re.finditer(r'(?:[A-Za-z]:[\\/]|/workspace/|\\workspace\\)[^\s"\'<>`*?]+', user_prompt):
        candidate_paths.append(m.group(0).rstrip('.,;:)'))

    # 2. If user explicitly asks about "pasta", "diretório", "arquivos", "analise", search recent history
    trigger_words = ("pasta", "diretório", "diretorio", "arquivo", "arquivos", "analise", "conteúdo", "conteudo", "explore", "listar")
    if not candidate_paths and any(tw in user_prompt.lower() for tw in trigger_words):
        for msg in reversed(history[-4:]):
            content = msg.get("content", "")
            for m in re.finditer(r'(?:[A-Za-z]:[\\/]|/workspace/|\\workspace\\)[^\s"\'<>`*?]+', content):
                candidate_paths.append(m.group(0).rstrip('.,;:)'))
            if candidate_paths:
                break

    for raw in candidate_paths:
        norm = raw.replace('/', '\\')
        try:
            p = Path(norm)
            if p.exists():
                posix = p.as_posix()
                if p.is_dir():
                    return (
                        f"\n\n[DIRETIVA OBRIGATÓRIA DE ACESSO LOCAL]: O caminho '{posix}' é um DIRETÓRIO LOCAL REAL e existente neste computador. "
                        f"Você DEVE chamar imediatamente a ferramenta 'list_directory' (com path='{posix}') para explorar a estrutura e os arquivos antes de responder. "
                        f"É PROIBIDO pedir ao usuário para enviar arquivos, mandar ZIP ou dizer que não tem dados."
                    )
                elif p.is_file():
                    return (
                        f"\n\n[DIRETIVA OBRIGATÓRIA DE ACESSO LOCAL]: O caminho '{posix}' é um ARQUIVO LOCAL REAL neste computador. "
                        f"Você DEVE chamar imediatamente a ferramenta 'read_file' (com file_path='{posix}') para ler o conteúdo antes de responder. "
                        f"É PROIBIDO pedir ao usuário para enviar arquivos."
                    )
        except Exception:
            continue

    return ""

# ---------------------------------------------------------------------------
# Main autonomous turn
# ---------------------------------------------------------------------------

def run_autonomous_turn(
    user_prompt: str,
    chat_id: int | str,
    on_status_update=None,
    on_step_update=None,
    resume_context: dict = None,
    on_checkpoint=None,
    allow_tools: bool = True,
    max_steps: int = 6,
    is_lead: bool = False,
    on_first_content=None,
    on_stream_update=None,
    intent: str = None,
) -> tuple[str, dict | None, list, dict]:
    """
    Executes an autonomous agent turn with goal-driven ReAct loop on the local PC.

    Args:
        user_prompt:      The user's message / request.
        chat_id:          Telegram chat ID (used for history retrieval).
        on_status_update: Optional callable(str) for legacy status updates.
        on_step_update:   Optional callable(step_num, step_type, description) for live progress.
        resume_context:   Optional dict from task_queue.checkpoint_task() to resume mid-execution.
                          Shape: {step_idx, messages, tools_executed, completed_steps}
        on_checkpoint:    Optional callable(step_idx, messages, tools_executed, completed_steps)
                          called after each tool batch for crash-recovery persistence.
        intent:           Optional semantic intent (CHAT_ONLY, DIAGNOSTIC, ACTION).

    Returns:
        (formatted_html, reply_markup, tools_executed, execution_record)
    """

    # ---- helpers -----------------------------------------------------------
    step_counter = [0]   # mutable container so inner helpers can increment

    def _emit(step_type: str, description: str) -> None:
        step_counter[0] += 1
        if on_step_update:
            try:
                on_step_update(step_counter[0], step_type, description)
            except Exception as ex:
                print(f"[Agent] on_step_update error: {ex}")

    # ---- execution record scaffold -----------------------------------------
    exec_id      = f"exec_{uuid.uuid4().hex[:8]}"
    started_at   = datetime.datetime.now(datetime.timezone.utc)
    exec_record: dict = {
        "execution_id":      exec_id,
        "goal":              user_prompt[:200],
        "chat_id":           chat_id,
        "started_at":        started_at.isoformat(),
        "finished_at":       None,
        "duration_seconds":  None,
        "steps":             [],
        "tools_executed":    [],
        "goal_achieved":     False,
        "goal_check_reason": "",
        "total_steps":       0,
        "model_calls":       0,
        "terminated_by":     "error",
    }

    def _finalize(formatted_html, reply_markup, tools_executed, terminated_by: str) -> tuple:
        finished_at = datetime.datetime.now(datetime.timezone.utc)
        exec_record["finished_at"]      = finished_at.isoformat()
        exec_record["duration_seconds"] = round((finished_at - started_at).total_seconds(), 3)
        exec_record["tools_executed"]   = tools_executed
        exec_record["total_steps"]      = step_counter[0]
        exec_record["terminated_by"]    = terminated_by
        is_success = terminated_by in ("goal_achieved", "completed")
        telemetry.record_request_metric(success=is_success)
        return formatted_html, reply_markup, tools_executed, exec_record


    # ---- guard -------------------------------------------------------------
    if not OPENROUTER_API_KEY:
        err = "⚠️ Chave do OpenRouter não configurada. Defina OPENROUTER_API_KEY no arquivo .env."
        return _finalize(err, None, [], "error")

    # ---- build or restore messages -----------------------------------------
    if resume_context and resume_context.get("messages"):
        # Resume from checkpoint — restore saved conversation
        messages = resume_context["messages"]
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] = build_system_prompt() if allow_tools else build_lead_system_prompt()
        tools_executed = list(resume_context.get("tools_executed", []))
        _resume_step = resume_context.get("step_idx", 0)
        step_counter[0] = _resume_step
        print(f"[Agent] Retomando execução do passo {_resume_step} com {len(messages)} mensagens salvas")
        _emit("think", f"Retomando do passo {_resume_step}... (contexto restaurado)")
    else:
        # Fresh start
        history  = message_store.get_clean_dialogue_history(chat_id, limit=8)
        messages = [{"role": "system", "content": build_system_prompt() if allow_tools else build_lead_system_prompt()}]
        messages.extend(history)

        # Etapa 4: TaskDoneBarrier
        last_turn_was_assistant = bool(history and history[-1].get("role") == "assistant")
        clean_user_input = user_prompt.strip().lower()
        is_short_courtesy = len(clean_user_input) <= 20 and any(
            w in clean_user_input for w in ("ok", "valeu", "obrigado", "show", "blz", "beleza", "top", "perfeito", "agradeço", "vlw")
        )
        if last_turn_was_assistant and is_short_courtesy:
            print(f"[Agent] TaskDoneBarrier ativada para cortesia curta: '{user_prompt}'")
            allow_tools = False
            max_steps = 1
            intent = "CHAT_ONLY"
            messages.append({
                "role": "system",
                "content": (
                    "[BARREIRA DE TAREFA CONCLUÍDA]: A demanda anterior já foi concluída e entregue com sucesso. "
                    "O usuário está apenas agradecendo ou confirmando o recebimento. "
                    "Trate este turno estritamente como cortesia e encerramento cordial. "
                    "É TERMINANTEMENTE PROIBIDO reabrir tarefas antigas, listar diretórios ou executar ferramentas."
                )
            })

        path_directive = detect_and_enrich_path_context(user_prompt, history)
        enriched_user_prompt = user_prompt + path_directive if path_directive else user_prompt
        messages.append({"role": "user", "content": enriched_user_prompt})
        tools_executed: list[str] = []

    # ---- Etapa 3: 100% LLM First Content Streaming & Intent Resolution ----
    resolved_intent = intent
    streamed_full_content = [None]
    stream_done_event = threading.Event()

    if not resume_context and not resolved_intent:
        intent_holder = [None]
        intent_event = threading.Event()

        def _on_intent_cb(det_intent):
            intent_holder[0] = det_intent
            intent_event.set()

        def _stream_worker():
            try:
                from . import first_content_stream
                full_text, _, _ = first_content_stream.generate_first_content_stream(
                    user_prompt,
                    on_first_content_callback=on_first_content,
                    on_stream_update_callback=on_stream_update,
                    on_intent_callback=_on_intent_cb,
                    history=history if 'history' in locals() else None,
                    is_lead=is_lead
                )
                streamed_full_content[0] = full_text
            except Exception as fcs_err:
                print(f"[Agent] First content stream warning: {fcs_err}")
            finally:
                intent_event.set()
                stream_done_event.set()

        threading.Thread(target=_stream_worker, daemon=True, name=f"FirstContent-{chat_id}").start()

        # Wait up to 3.0s for the intent tag (Flash streams it in ~400ms)
        intent_event.wait(timeout=3.0)
        resolved_intent = intent_holder[0] or ("CHAT_ONLY" if is_lead else "ACTION")

    if resolved_intent:
        print(f"[Agent] Turn Intent aplicado: {resolved_intent}")
        if resolved_intent == "CHAT_ONLY":
            allow_tools = False
            max_steps = 1
            # Se o stream já está gerando a resposta completa de CHAT_ONLY, aguarda o término e finaliza direto
            stream_done_event.wait(timeout=10.0)
            full_ans = streamed_full_content[0]
            if full_ans and len(full_ans.strip()) >= 8:
                print(f"[Agent] CHAT_ONLY finalizado via streaming contínuo ({len(full_ans)} chars)")
                clean_ans, reply_markup = dynamic_keyboard.parse_ai_buttons(full_ans) if dynamic_keyboard else (full_ans, None)
                formatted = sanitize_and_convert_to_tg_html(clean_ans)
                return _finalize(formatted, reply_markup, [], "completed")

        elif resolved_intent == "DIAGNOSTIC":
            allow_tools = True
            max_steps = min(max_steps, 3)
        elif resolved_intent == "ACTION":
            allow_tools = True
            max_steps = min(max_steps, 6)

    tool_results_accumulator: list[str] = []   # for goal check summaries
    model_used     = OPENROUTER_MODEL
    final_raw_content = ""
    goal_achieved  = False
    goal_check_text = ""
    terminated_by  = "error"
    completed_steps: list[dict] = []
    circuit_breaker = ToolCircuitBreaker(max_consecutive_failures=2)

    if not allow_tools:
        max_steps = 1


    # ---- ReAct loop --------------------------------------------------------
    for step in range(max_steps):

        if step == 0:
            # First step: describe the goal concisely
            goal_preview = user_prompt[:80].replace('\n', ' ')
            _emit("think", f"Entendendo o pedido: \"{goal_preview}{'...' if len(user_prompt) > 80 else ''}\"")
        else:
            _emit("think", f"Analisando resultados e planejando próxima ação...")
        if on_status_update:
            on_status_update("typing")

        # --- call primary LLM ---
        try:
            res_data = call_openrouter_api(messages, model=OPENROUTER_MODEL, timeout=100)
            exec_record["model_calls"] += 1
        except Exception as e:
            print(f"[!] Erro no modelo primário ({OPENROUTER_MODEL}): {e}. Tentando fallback...")
            try:
                model_used = OPENROUTER_FALLBACK_MODEL
                res_data   = call_openrouter_api(messages, model=OPENROUTER_FALLBACK_MODEL, timeout=60)
                exec_record["model_calls"] += 1
            except Exception as e2:
                err_text = f"❌ <b>Erro na IA Xiaomi Mimo:</b> <code>{html.escape(str(e2))}</code>"
                exec_record["goal_achieved"] = False
                return _finalize(err_text, None, tools_executed, "error")

        # --- parse response ---
        choices = res_data.get("choices") or []
        if not choices:
            print(f"[Agent] Aviso: API retornou choices vazia. Resposta: {str(res_data)[:300]}")
            err_msg = (
                res_data.get("error", {}).get("message", "choices vazia")
                if isinstance(res_data.get("error"), dict)
                else str(res_data.get("error", "resposta inválida da API"))
            )
            if step < max_steps - 2:
                # Nudge retry — don't abort immediately
                print(f"[Agent] Nudge retry após choices vazia (step {step})...")
                messages.append({"role": "user", "content": "Continue sua análise e responda ao pedido do usuário em HTML para Telegram."})
                continue
            final_raw_content = (
                f"❌ <b>Erro temporário da IA:</b> <code>{html.escape(str(err_msg))}</code>\n"
                "Tente novamente em instantes."
            )
            terminated_by = "empty_response"
            break

        choice       = choices[0] or {}
        step_content = ((choice.get("message") or {}).get("content", "") or "").strip()

        # --- check if LLM itself declared goal achieved ---------------------
        if re.search(r'<goal_achieved>\s*YES\s*</goal_achieved>', step_content, re.IGNORECASE):
            final_raw_content = re.sub(
                r'<goal_achieved>\s*YES\s*</goal_achieved>', '', step_content, flags=re.IGNORECASE
            ).strip()
            goal_achieved  = True
            goal_check_text = "Goal confirmed by primary LLM response."
            exec_record["goal_achieved"]     = True
            exec_record["goal_check_reason"] = goal_check_text
            _emit("done", "Objetivo atingido!")
            terminated_by = "goal_achieved"
            break

        # --- check for tool calls ---
        tool_calls = parse_all_tool_calls(step_content) if allow_tools else []

        if tool_calls:
            # Append assistant reasoning to messages
            messages.append({"role": "assistant", "content": step_content})

            tool_feedbacks: list[str] = []
            circuit_tripped = False
            trip_tool_name = ""
            trip_err_detail = ""

            for tool_name, tool_args in tool_calls:
                # Format semantic step description without technical noise or inverted parameter keys
                if tool_name in ("write_file", "replace_in_file", "read_file"):
                    raw_target = tool_args.get("file_path") or tool_args.get("path") or tool_args.get("file") or ""
                    f_name = Path(str(raw_target)).name if raw_target else "arquivo"
                    if tool_name == "read_file":
                        step_desc = f"Consultando configurações em <code>{f_name}</code>..."
                    elif tool_name == "write_file":
                        step_desc = f"Gravando alterações em <code>{f_name}</code>..."
                    else:
                        step_desc = f"Aplicando edição em <code>{f_name}</code>..."
                elif tool_name == "list_directory":
                    raw_dir = tool_args.get("path") or tool_args.get("directory") or tool_args.get("dir") or ""
                    d_name = Path(str(raw_dir)).name or str(raw_dir) or "diretório"
                    step_desc = f"Inspecionando estrutura de <code>{d_name}</code>..."
                elif tool_name == "search_in_files":
                    raw_query = tool_args.get("query") or tool_args.get("text") or tool_args.get("pattern") or ""
                    step_desc = f"Buscando referências no código: <code>{str(raw_query)[:35]}</code>..."
                elif tool_name == "exec_command":
                    cmd_val = str(tool_args.get("cmd") or tool_args.get("command") or "").strip()
                    cmd_low = cmd_val.lower()
                    if "pm2" in cmd_low:
                        step_desc = "Diagnosticando processos e serviços ativos no PM2..."
                    elif "git" in cmd_low:
                        step_desc = "Inspecionando sincronização dos repositórios Git..."
                    elif "netstat" in cmd_low or "port" in cmd_low:
                        step_desc = "Auditando portas de rede e conexões ativas..."
                    elif "tasklist" in cmd_low or "taskkill" in cmd_low:
                        step_desc = "Gerenciando processos do sistema operacional..."
                    else:
                        step_desc = f"Executando diagnóstico no ambiente: <code>{cmd_val[:45]}</code>"
                elif tool_name == "get_system_telemetry":
                    step_desc = "Coletando telemetria do host (CPU, RAM, disco)..."
                elif tool_name == "run_health_check":
                    step_desc = "Executando health check dos serviços essenciais..."
                elif tool_name == "run_ssl_sentinel":
                    step_desc = "Auditando certificados SSL e renovações de domínio..."
                elif tool_name == "run_backup":
                    step_desc = "Disparando rotina de contingência e backup..."
                elif tool_name == "read_backup_log":
                    step_desc = "Auditando integridade dos logs de backup..."
                elif tool_name == "vercel_deploy":
                    step_desc = "Realizando deploy de produção no Vercel..."
                else:
                    step_desc = f"Executando etapa: {tool_name}"

                friendly = step_desc.rstrip(".").rstrip()
                _emit("tool", step_desc)
                if on_status_update:
                    on_status_update(f"tool:{tool_name}")

                print(f"[Agent] Executando autonomamente tool: {tool_name}")
                args_summary = ", ".join(f"{k}={str(v)[:60]}" for k, v in tool_args.items())
                t_start = time.monotonic()

                tool_result = tool_executor.execute_tool(tool_name, tool_args)

                t_elapsed_ms = int((time.monotonic() - t_start) * 1000)
                is_running   = bool(isinstance(tool_result, dict) and tool_result.get("running"))
                success      = not (isinstance(tool_result, dict) and tool_result.get("error"))

                tools_executed.append(tool_name)

                # Record tool metric in telemetry
                err_detail = str(tool_result.get("error")) if (isinstance(tool_result, dict) and tool_result.get("error")) else None
                telemetry.record_tool_metric(tool_name, t_elapsed_ms, success=(success or is_running), error=err_detail)

                # Record step in telemetry
                exec_record["steps"].append({
                    "step":         step + 1,
                    "type":         "tool",
                    "name":         tool_name,
                    "args_summary": args_summary[:200],
                    "success":      success or is_running,
                    "duration_ms":  t_elapsed_ms,
                })

                if is_running:
                    pid = tool_result.get("pid")
                    logs = tool_result.get("partial_output", "")
                    elapsed = tool_result.get("elapsed_seconds", 0)
                    feedback_entry = (
                        f"[PROCESSO EM ANDAMENTO - CHECKPOINT ATINGIDO]:\n"
                        f"A ferramenta '{tool_name}' (PID {pid}) continua executando ativamente ({elapsed}s decorridos).\n"
                        f"NENHUM timeout forçado foi aplicado — o processo NÃO foi finalizado.\n\n"
                        f"LOGS ATUAIS DO PROCESSO:\n"
                        f"----------------------------------------\n"
                        f"{logs}\n"
                        f"----------------------------------------\n\n"
                        f"[DECISÃO OBRIGATÓRIA DA IA]:\n"
                        f"Analise os logs parciais acima para avaliar o andamento da tarefa:\n"
                        f"• Se a tarefa estiver evoluindo normalmente (ex: download, compilação, deploy Vercel), chame 'wait_command':\n"
                        f"  <invoke name=\"wait_command\">\n"
                        f"    <parameter name=\"pid\">{pid}</parameter>\n"
                        f"    <parameter name=\"wait_seconds\">30</parameter>\n"
                        f"  </invoke>\n"
                        f"• Se a tarefa estiver travada, em loop ou esperando confirmação impossível, chame 'kill_command' para encerrar e decida reiniciar:\n"
                        f"  <invoke name=\"kill_command\">\n"
                        f"    <parameter name=\"pid\">{pid}</parameter>\n"
                        f"  </invoke>\n"
                    )
                else:
                    # Strip internal/noisy fields that cause LLM to echo them verbatim
                    _STRIP_FIELDS = {"command", "returncode", "elapsed_seconds"}
                    llm_result = {k: v for k, v in tool_result.items() if k not in _STRIP_FIELDS} if isinstance(tool_result, dict) else tool_result
                    result_str = json.dumps(llm_result, ensure_ascii=False, indent=2)[:3000]
                    feedback_entry = f"[RESULTADO DA TOOL '{tool_name}']:\n{result_str}"

                    if isinstance(tool_result, dict) and tool_result.get("diagnosis"):
                        feedback_entry += (
                            f"\n\n[DICA DE CORREÇÃO AUTOMÁTICA]: {tool_result['diagnosis']}\n"
                            "NÃO repita a mesma chamada falha sem aplicar a correção recomendada acima."
                        )
                    if not success:
                        err_msg = str(tool_result.get("error", "Falha na execução")) if isinstance(tool_result, dict) else "Falha na execução"
                        feedback_entry += (
                            f"\n\n[ERRO NA EXECUÇÃO DA FERRAMENTA]: A chamada para '{tool_name}' falhou: {err_msg}\n"
                            "Analise o erro acima. Se os parâmetros estavam incorretos ou o recurso não existe, "
                            "chame a ferramenta novamente com os parâmetros corrigidos ou use uma alternativa adequada."
                        )

                tool_feedbacks.append(feedback_entry)
                tool_results_accumulator.append(f"Tool '{tool_name}' ({t_elapsed_ms}ms):\n{feedback_entry[:800]}")

                # Build result summary for the step
                status_label = "✅" if success else "❌"
                if is_running:
                    _emit("result", f"⏳ {friendly} em andamento (PID {tool_result.get('pid')}) — analisando logs...")
                elif success:
                    out_preview = ""
                    if isinstance(tool_result, dict):
                        raw_out = (tool_result.get("output") or tool_result.get("content") or
                                   tool_result.get("message") or "")
                        if raw_out and raw_out != "(nenhuma saída padrão gerada)":
                            out_preview = f" — {str(raw_out).strip()[:60]}"
                    _emit("result", f"{friendly} {status_label} ({t_elapsed_ms / 1000:.1f}s){out_preview}")
                else:
                    err_preview = ""
                    if isinstance(tool_result, dict):
                        err_preview = f" — {str(tool_result.get('error', ''))[:60]}"
                    _emit("result", f"{friendly} {status_label} ({t_elapsed_ms / 1000:.1f}s){err_preview}")

                # Track for checkpoint resume_context
                completed_steps.append({
                    "step": step_counter[0],
                    "type": "tool",
                    "name": tool_name,
                    "success": success,
                    "duration_ms": t_elapsed_ms
                })

                # Etapa 5: ToolCircuitBreaker verification
                if circuit_breaker.record_result(tool_name, success or is_running, err_detail or "", tool_args):
                    print(f"[Agent] CIRCUIT BREAKER ATIVADO! Ferramenta '{tool_name}' falhou 2 vezes consecutivas.")
                    _emit("error", f"Circuito de proteção ativado: {friendly} falhou consecutivamente.")
                    circuit_tripped = True
                    trip_tool_name = tool_name
                    trip_err_detail = err_detail
                    break

            if circuit_tripped:
                terminated_by = "circuit_breaker_tripped"
                messages.append({"role": "assistant", "content": step_content})
                messages.append({
                    "role": "user",
                    "content": (
                        f"[CIRCUIT BREAKER DE SEGURANÇA ATIVADO]: A ferramenta '{trip_tool_name}' falhou repetidamente com o erro:\n"
                        f"<code>{html.escape(str(trip_err_detail)[:150])}</code>\n\n"
                        "Interrompa tentativas automáticas. Explique com transparência e clareza ao operador o que "
                        "impediu a execução e pergunte como ele deseja proceder. NÃO tente executar mais ferramentas."
                    )
                })
                try:
                    synth_res = call_openrouter_api(messages, model=model_used, timeout=30)
                    c_text = ((synth_res.get("choices") or [{}])[0].get("message") or {}).get("content", "")
                    final_raw_content = c_text if c_text else f"A ferramenta <code>{trip_tool_name}</code> falhou repetidamente: {trip_err_detail}."
                except Exception:
                    final_raw_content = f"A ferramenta <code>{trip_tool_name}</code> falhou repetidamente: {trip_err_detail}."
                break

            combined_feedback = "\n\n".join(tool_feedbacks)

            # ---- Checkpoint: persist state for crash recovery ---------------
            if on_checkpoint:
                try:
                    on_checkpoint(
                        step_counter[0],
                        list(messages),
                        list(tools_executed),
                        list(completed_steps)
                    )
                except Exception as cp_ex:
                    print(f"[Agent] checkpoint error (non-fatal): {cp_ex}")

            # After last allowed step, force synthesis
            if step == max_steps - 1:
                combined_feedback += (
                    "\n\n[INSTRUÇÃO FINAL]: Todas as ferramentas foram executadas. "
                    "Apresente agora o relatório final e conclusivo para o usuário em HTML claro e objetivo, "
                    "destacando os resultados e sugerindo botões de ação contextuais. "
                    "Emita <goal_achieved>YES</goal_achieved> ao início da sua resposta."
                )

            # Instruct LLM to check goal after tools
            combined_feedback += (
                "\n\n[INSTRUÇÃO]: Com base nos resultados acima, verifique se o objetivo foi atingido. "
                "Se SIM, responda com <goal_achieved>YES</goal_achieved> seguido da resposta final completa. "
                "Se NÃO, continue raciocinando e chame mais ferramentas conforme necessário."
            )

            messages.append({"role": "user", "content": combined_feedback})

            # Anti-Token Blowup: Condense old tool outputs (older than 2 steps)
            if len(messages) > 6:
                for idx in range(1, len(messages) - 3):
                    msg_item = messages[idx]
                    if msg_item.get("role") == "user" and "[RESULTADO DA TOOL" in msg_item.get("content", ""):
                        content_str = msg_item["content"]
                        if len(content_str) > 400:
                            tool_m = re.search(r"\[RESULTADO DA TOOL '([^']+)'\]", content_str)
                            t_name = tool_m.group(1) if tool_m else "ferramenta"
                            messages[idx]["content"] = f"[RESULTADO PRELIMINAR]: {t_name} executado com sucesso (saída condensada para otimizar contexto)."

            # Let the primary LLM continue — it will self-declare <goal_achieved>YES</goal_achieved>
            # if the goal is reached (as instructed in combined_feedback).
            continue

        else:
            # Check if the model attempted an actual tool call that could not be interpreted.
            # Strip suggested button blocks first so {"action": "..."} doesn't trigger false positives.
            content_without_buttons = re.sub(r'```(?:buttons|json)\s*\[[\s\S]*?\]\s*```', '', step_content, flags=re.IGNORECASE)
            malformed_signals = ["<invoke", "<function", "<tool_call", "```tool_call"]
            is_malformed = allow_tools and any(sig in content_without_buttons.lower() for sig in malformed_signals)

            if is_malformed:
                print(f"[Agent] Chamada malformada detectada no step {step + 1}. Injetando erro e continuando loop...")
                telemetry.record_error(
                    "autonomous_agent",
                    "MalformedToolCall",
                    f"Chamada de tool malformada no step {step + 1}: {step_content[:120]}",
                    context={"step": step + 1, "chat_id": chat_id},
                    severity="WARNING"
                )
                _emit("tool", "Chamada de ferramenta não pôde ser interpretada — solicitando correção...")
                messages.append({"role": "assistant", "content": step_content})
                messages.append({
                    "role": "user",
                    "content": (
                        "[ERRO NA CHAMADA DE FERRAMENTA]: Sua tentativa de chamada de ferramenta não pôde ser interpretada no ambiente local.\n"
                        "Por favor, use a sintaxe canônica obrigatória:\n"
                        "<invoke name=\"nome_da_ferramenta\">\n"
                        "  <parameter name=\"nome_do_parametro\">valor</parameter>\n"
                        "</invoke>\n\n"
                        "Exemplo para listar diretório:\n"
                        "<invoke name=\"list_directory\">\n"
                        "  <parameter name=\"path\">C:/workspace/docs</parameter>\n"
                        "</invoke>\n\n"
                        "Corrija os parâmetros e execute novamente agora."
                    )
                })
                continue

            # No tool calls — check if model provided a response
            if step_content:
                final_raw_content = step_content
                if re.search(r'<goal_achieved>\s*YES\s*</goal_achieved>', step_content, re.IGNORECASE):
                    final_raw_content = re.sub(
                        r'<goal_achieved>\s*YES\s*</goal_achieved>', '', step_content, flags=re.IGNORECASE
                    ).strip()
                    goal_achieved = True
                    exec_record["goal_achieved"] = True
                    exec_record["goal_check_reason"] = "Inline goal_achieved tag in final response."
                    terminated_by = "goal_achieved"
                else:
                    goal_achieved = True
                    exec_record["goal_achieved"] = True
                    exec_record["goal_check_reason"] = "Direct conclusive response provided without extra tools."
                    terminated_by = "completed"
                _emit("done", "Resposta pronta!")
            else:
                # step_content is empty but choices was valid — nudge the LLM
                if step < max_steps - 2:
                    print(f"[Agent] step_content vazio no step {step}, tentando nudge...")
                    messages.append({"role": "user", "content": "Sua resposta ficou em branco. Escreva a resposta final para o usuário agora."})
                    continue
                terminated_by = "empty_response"
            break


    else:
        # Exhausted max_steps
        terminated_by = "max_steps"

    # ---- Synthesis pass if final_raw_content is empty ----------------------
    if not final_raw_content.strip() or parse_all_tool_calls(final_raw_content):
        _emit("think", "Sintetizando resposta final...")
        if on_status_update:
            on_status_update("typing")
        messages.append({
            "role": "user",
            "content": (
                "Apresente agora o seu relatório final e estruturado dos testes/ações executados acima "
                "em HTML para o usuário. Emita <goal_achieved>YES</goal_achieved> no início."
            )
        })
        try:
            res_data = call_openrouter_api(messages, model=model_used, timeout=60)
            exec_record["model_calls"] += 1
            raw = (res_data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
            if raw.strip():
                final_raw_content = re.sub(
                    r'<goal_achieved>\s*YES\s*</goal_achieved>', '', raw, flags=re.IGNORECASE
                ).strip()
                exec_record["goal_achieved"] = True
                terminated_by = "completed"
        except Exception as synth_ex:
            print(f"[Agent] Erro no synthesis pass: {synth_ex}")


    # ---- Strip tool call artifacts from final text -------------------------
    final_raw_content = re.sub(
        r'<invoke\s+name=[\'""][^\'"">]+[\'""]>[\s\S]*?</invoke>',
        '', final_raw_content, flags=re.IGNORECASE
    ).strip()
    final_raw_content = re.sub(
        r'<function(?:[=:].*?|\s+name=.*?)>[\s\S]*?</function>',
        '', final_raw_content, flags=re.IGNORECASE
    ).strip()
    final_raw_content = re.sub(
        r'</?(?:invoke|parameter|tool_call|function_call|function)[^>]*>',
        '', final_raw_content, flags=re.IGNORECASE
    ).strip()

    # ---- Two-Stage Natural Language Synthesis Pass -------------------------
    # Route collected data and draft to dedicated summarizer LLM to guarantee 100% natural language.
    # Only run the synthesizer if tools were executed OR if raw technical script artifacts leaked.
    should_synthesize = bool(tools_executed) or any(
        cmd in final_raw_content.lower() for cmd in ["get-content", "powershell", "test-path", "select-object", "<invoke", "<tool_call"]
    )
    if should_synthesize:
        _emit("think", "Sintetizando resposta em linguagem natural...")
        if on_status_update:
            on_status_update("typing")

        synthesized_html = synthesize_in_natural_language(
            user_prompt=user_prompt,
            tool_results_accumulator=tool_results_accumulator,
            raw_draft=final_raw_content,
            model=OPENROUTER_FALLBACK_MODEL
        )
        if synthesized_html and len(synthesized_html.strip()) > 15:
            final_raw_content = synthesized_html

    # ---- Parse AI-suggested buttons ----------------------------------------
    clean_text, reply_markup = dynamic_keyboard.parse_ai_buttons(final_raw_content)

    # ---- Convert to Telegram HTML ------------------------------------------
    formatted_html = sanitize_and_convert_to_tg_html(clean_text)

    if not formatted_html.strip():
        formatted_html = "<b>Execução Concluída</b>\nAs operações solicitadas foram processadas no PC local."

    # ---- Model badge -------------------------------------------------------
    badge_model = "Mimo 2.6 Pro" if "pro" in model_used else "Mimo 2.6 Flash"
    tools_badge = f" | ⚙️ <i>Tools: {', '.join(tools_executed)}</i>" if tools_executed else ""
    goal_badge  = " ✅" if goal_achieved else ""
    formatted_html += f"\n\n<i>🤖 Xiaomi {badge_model}{tools_badge}{goal_badge}</i>"

    return _finalize(formatted_html, reply_markup, tools_executed, terminated_by)


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing autonomous turn with natural language...")
    ans, kb, tools, record = run_autonomous_turn(
        "Qual o uso atual de memória RAM e disco no PC?",
        chat_id=888888
    )
    print("Answer:\n", ans[:300])
    print("Keyboard:\n", kb)
    print("Tools executed:\n", tools)
    print("Execution record:\n", json.dumps(record, indent=2, ensure_ascii=False)[:800])
