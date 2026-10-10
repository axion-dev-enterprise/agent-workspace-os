#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Telegram Bot — Thin Client Bridge
Role: Receive Telegram updates and forward them to Brain Server at BRAIN_URL.
The Brain handles ALL AI, tools, tasks, watcher, and sends responses directly to Telegram.
"""

import os
import sys
import json
import time
import html
import threading
import urllib.request
import urllib.parse
import urllib.error
import datetime
import socket
from pathlib import Path

# Prevent unhandled indefinite TCP socket hangs
socket.setdefaulttimeout(40)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPTS_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent

# ==========================================
# LOAD VAULT SECRETS
# ==========================================
try:
    if str(WORKSPACE_ROOT) not in sys.path:
        sys.path.insert(0, str(WORKSPACE_ROOT))
    from scripts.vault_loader import load_vault
    load_vault()
except Exception as _ve:
    pass

_dotenv = WORKSPACE_ROOT / '.env'
if _dotenv.exists():
    try:
        with open(_dotenv, 'r', encoding='utf-8') as _df:
            for _line in _df:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    if _k.strip() and _k.strip() not in os.environ:
                        os.environ[_k.strip()] = _v.strip()
    except Exception:
        pass

# ==========================================
# CONSTANTS
# ==========================================
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
API_BASE = f'https://api.telegram.org/bot{BOT_TOKEN}'
BRAIN_URL = os.environ.get('BRAIN_URL', 'http://127.0.0.1:8765')
SUBSCRIBERS_PATH = WORKSPACE_ROOT / 'workspace' / 'telegram_subscribers.json'


# ==========================================
# LOGGING
# ==========================================
def log(msg: str):
    """Timestamped stdout print with immediate flush"""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{now}] {msg}', flush=True)


# ==========================================
# TELEGRAM API
# ==========================================
def tg_api(method: str, data: dict = None, timeout: int = 35) -> dict:
    url = f'{API_BASE}/{method}'
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8', errors='ignore')
        return {'ok': False, 'error_code': e.code, 'description': err_msg}
    except Exception as e:
        err_str = str(e)
        is_timeout = 'timed out' in err_str.lower() or 'timeout' in err_str.lower()
        return {'ok': False, 'error': err_str, 'timeout': is_timeout}


def send_message(chat_id: int, text: str, parse_mode: str = 'HTML', reply_markup: dict = None) -> dict:
    """Sends message to Telegram with chunking and HTML fallback"""
    import re
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] if len(text) > 4000 else [text]
    last_res = None
    for idx, chunk in enumerate(chunks):
        payload = {
            'chat_id': chat_id,
            'text': chunk,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        if reply_markup and idx == len(chunks) - 1:
            payload['reply_markup'] = reply_markup
        res = tg_api('sendMessage', payload)
        if not res.get('ok') and parse_mode:
            payload.pop('parse_mode')
            payload['text'] = re.sub(r'<[^>]+>', '', chunk)
            res = tg_api('sendMessage', payload)
        last_res = res
    return last_res


# ==========================================
# SUBSCRIBER REGISTRY
# ==========================================
def save_subscriber(chat_id: int, username: str = None, first_name: str = None):
    """Registers subscriber for automated alert notifications (writes directly to JSON)"""
    subscribers = {}
    if SUBSCRIBERS_PATH.exists():
        try:
            with open(SUBSCRIBERS_PATH, 'r', encoding='utf-8') as f:
                subscribers = json.load(f)
        except Exception:
            subscribers = {}

    cid_str = str(chat_id)
    if cid_str not in subscribers:
        subscribers[cid_str] = {
            'chat_id': chat_id,
            'username': username,
            'first_name': first_name,
            'registered_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'notifications_enabled': True
        }
        SUBSCRIBERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SUBSCRIBERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, indent=2, ensure_ascii=False)
        log(f'[+] Novo assinante registrado: {first_name} (@{username}) [ID: {chat_id}]')


# ==========================================
# BRAIN API HELPERS
# ==========================================
def call_brain(endpoint: str, data: dict = None, method: str = 'POST') -> dict:
    """Makes HTTP call to Brain API server"""
    url = f'{BRAIN_URL}{endpoint}'
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': 'application/json'},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.URLError as e:
        return {'error': f'Brain server unavailable: {e}', 'brain_offline': True}
    except Exception as e:
        return {'error': str(e)}


def _brain_get(endpoint: str) -> dict:
    """Makes a GET request to Brain API server"""
    url = f'{BRAIN_URL}{endpoint}'
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e), 'brain_offline': True}


# ==========================================
# SOCIAL & INTELLIGENCE FORMATTERS
# ==========================================
def _format_twitter_digest(query: str = "") -> str:
    log_path = Path("c:/workspace/memory/intelligence/twitter_hits.jsonl")
    if not log_path.exists():
        return "🐦 <b>Twitter/X Monitor:</b> Nenhum dado coletado ainda."
    lines = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    try:
                        lines.append(json.loads(l))
                    except Exception:
                        pass
    except Exception as e:
        return f"⚠️ Erro ao ler tweets: {e}"

    if not lines:
        return "🐦 <b>Twitter/X:</b> Sem tweets registrados."

    if query:
        q = query.lower()
        filtered = [t for t in lines if q in t.get("text", "").lower() or q in t.get("username", "").lower()]
    else:
        filtered = lines[-5:]

    if not filtered:
        return f"🐦 Nenhum tweet encontrado com o termo: <code>{html.escape(query)}</code>"

    res = [f"🐦 <b>Twitter/X Hits ({len(filtered)} exibidos):</b>\n━━━━━━━━━━━━━━━━━━━━━━"]
    for t in filtered[-5:]:
        u = t.get("username", "tech")
        txt = html.escape(t.get("text", "")[:180].replace("\n", " "))
        kws = ", ".join(t.get("keywords_matched", [])[:3])
        url = t.get("url", f"https://x.com/{u}")
        res.append(f"• <b>@{u}</b>: {txt}...\n  🏷️ <i>{kws}</i> | <a href='{url}'>Ver no X</a>\n")
    return "\n".join(res)


def _format_instagram_digest() -> str:
    log_path = Path("c:/workspace/memory/intelligence/instagram_hits.jsonl")
    if not log_path.exists():
        return "📸 <b>Instagram Monitor:</b> Sem dados registrados ainda."
    lines = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    try:
                        lines.append(json.loads(l))
                    except Exception:
                        pass
    except Exception as e:
        return f"⚠️ Erro ao ler instagram hits: {e}"

    if not lines:
        return "📸 <b>Instagram:</b> Sem posts registrados."

    res = ["📸 <b>Instagram — Novidades Monitoradas:</b>\n━━━━━━━━━━━━━━━━━━━━━━"]
    for p in lines[-5:]:
        prof = p.get("profile", "tech")
        cap = html.escape(p.get("caption", "")[:180].replace("\n", " "))
        kws = ", ".join(p.get("keywords_matched", [])[:3])
        url = p.get("url", f"https://www.instagram.com/{prof}/")
        res.append(f"• <b>@{prof}</b>: {cap}...\n  🏷️ <i>{kws}</i> | <a href='{url}'>Abrir post</a>\n")
    return "\n".join(res)


def _format_intel_digest() -> str:
    digest_path = Path("c:/workspace/memory/intelligence/daily_digest.jsonl")
    if not digest_path.exists():
        return "📡 <b>Content Intelligence:</b> Nenhum digest registrado ainda."
    last = None
    try:
        with open(digest_path, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    try:
                        last = json.loads(l)
                    except Exception:
                        pass
    except Exception as e:
        return f"⚠️ Erro ao ler digest: {e}"

    if not last:
        return "📡 <b>Content Intelligence:</b> Digest vazio."

    total = last.get("total_fetched", 0)
    new_items = last.get("new_items", 0)
    hits = last.get("keyword_hits", 0)
    dt = last.get("run_at", "")[:19].replace("T", " ")

    res = [
        f"📡 <b>AXION Content Intelligence Monitor</b>",
        f"<i>Último ciclo: {dt} UTC</i>\n━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 Total analisado: <code>{total} items</code>",
        f"🆕 Novos detectados: <code>{new_items}</code>",
        f"🎯 Hits técnicos AXION: <code>{hits}</code>\n",
        f"<b>Top Descobertas:</b>"
    ]
    for h in last.get("top_hits", [])[:5]:
        src = h.get("source", "feed")
        title = html.escape((h.get("title") or h.get("repo", "Item"))[:80])
        url = h.get("url", "")
        kws = ", ".join(h.get("keywords_matched", [])[:2])
        res.append(f"• [{src}] <a href='{url}'>{title}</a> ({kws})")

    res.append("\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Comandos rápidos: /twitter, /instagram, /social</i>")
    return "\n".join(res)


def _format_vault_status() -> str:
    try:
        from scripts.vault_loader import VAULT_ROOT, mask_secret
        modules = sorted(VAULT_ROOT.glob("*/*/index.json"))
        res = ["🔐 <b>AXION Secrets Vault — Auditoria</b>\n━━━━━━━━━━━━━━━━━━━━━━"]
        for mod in modules:
            data = json.loads(mod.read_text(encoding="utf-8"))
            cat = data.get("category", "")
            plat = data.get("platform", "")
            vars_spec = data.get("variables", {})
            res.append(f"📁 <b>[{cat.upper()}] {plat.upper()}</b>")
            for var_name, var_info in vars_spec.items():
                val = os.environ.get(var_name, "")
                st = "✅" if val else "⚠️"
                res.append(f"  {st} <code>{var_name}</code> ({mask_secret(val)})")
        res.append("━━━━━━━━━━━━━━━━━━━━━━\n<i>Nenhuma credencial completa é exposta no chat.</i>")
        return "\n".join(res)
    except Exception as e:
        return f"⚠️ Erro ao auditar Vault: {e}"


def _format_social_status() -> str:
    presence_file = Path("c:/workspace/memory/infrastructure/AGENT_DIGITAL_PRESENCE.json")
    if not presence_file.exists():
        return "🌐 Presença digital não inicializada."
    try:
        data = json.loads(presence_file.read_text(encoding="utf-8"))
        sp = data.get("social_presence", {})
        res = [
            "🌐 <b>Presença Digital do Agente AXION</b>\n━━━━━━━━━━━━━━━━━━━━━━",
            f"🐦 <b>Twitter/X:</b> {sp.get('twitter_x', {}).get('status', 'ACTIVE')} (Syndication Bypass)",
            f"📸 <b>Instagram:</b> {sp.get('instagram', {}).get('status', 'ACTIVE')} ({sp.get('instagram', {}).get('account', '@devbarreto')})",
            f"💬 <b>WhatsApp:</b> {sp.get('whatsapp', {}).get('status', 'ACTIVE')} (Baileys Bridge)",
            f"✈️ <b>Telegram:</b> @axion_assistant_bot (Online)",
            f"🐙 <b>GitHub:</b> 25 repositórios rastreados",
            "━━━━━━━━━━━━━━━━━━━━━━\n<i>Dica: /twitter, /instagram, /intel</i>"
        ]
        return "\n".join(res)
    except Exception as e:
        return f"⚠️ Erro ao ler presença digital: {e}"


def _format_pipeline_run() -> str:
    try:
        from services.ai_intelligence_pipeline.pipeline_orchestrator import run_full_pipeline
        summary = run_full_pipeline(max_insights_to_validate=2, auto_build_skills=True)
        res = [
            "🚀 <b>AI Intelligence Pipeline: Ciclo Concluído</b>",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"🔍 <b>Motor 1 (Descoberta):</b> {summary.get('motor_1_profiles_evaluated')} perfis avaliados",
            f"⭐ <b>Perfis Recomendados:</b> {', '.join(['@' + h for h in summary.get('motor_1_recommended', [])]) or 'Nenhum novo no limiar'}",
            f"🧠 <b>Motor 2 (Validação):</b> {summary.get('motor_2_insights_validated')} insights factuais extraídos",
            f"🛠️ <b>Motor 3 (Skills Criadas):</b> {', '.join(summary.get('motor_3_skills_created', [])) or 'Nenhuma skill nova'}",
            f"✅ <b>Motor 4 (Testes Aprovados):</b> {summary.get('motor_4_tests_passed')} verificações empíricas",
            f"💰 <b>Eficiência de Custos:</b> {summary.get('cost_efficiency')}",
            "━━━━━━━━━━━━━━━━━━━━━━\n<i>Execute /skills ou /vault para mais detalhes.</i>"
        ]
        return "\n".join(res)
    except Exception as e:
        return f"⚠️ Erro ao executar pipeline: {e}"


def _format_discover_run(args: str = "") -> str:
    try:
        from services.ai_intelligence_pipeline.profile_discovery_engine import discover_and_evaluate_profiles
        handles = [h.strip().lstrip("@") for h in args.split() if h.strip()] if args else None
        profiles = discover_and_evaluate_profiles(candidate_handles=handles)
        res = [
            f"🔍 <b>Motor 1: Descoberta & Scoring ({len(profiles)} perfis)</b>",
            "━━━━━━━━━━━━━━━━━━━━━━"
        ]
        for p in profiles[:6]:
            h = p.get("handle")
            score = p.get("final_score")
            rec = "⭐ RECOMENDADO" if p.get("recommended") else "Monitorando"
            verd = html.escape(p.get("verdict", "")[:100])
            topics = ", ".join(p.get("primary_topics", [])[:2])
            res.append(f"• <b>@{h}</b> (Score: <b>{score}/100</b> | {rec})\n  🏷️ <i>{topics}</i>\n  💬 {verd}\n")
        res.append("━━━━━━━━━━━━━━━━━━━━━━\n<i>Dica: /discover [handle] para avaliar um perfil específico.</i>")
        return "\n".join(res)
    except Exception as e:
        return f"⚠️ Erro no Motor de Descoberta: {e}"


def _format_validate_run() -> str:
    try:
        from services.ai_intelligence_pipeline.insight_validator_engine import run_insight_validation
        insights = run_insight_validation(max_items=3)
        if not insights:
            return "🧠 <b>Motor 2 (Validação):</b> Nenhum post novo pendente de validação."
        res = [
            f"🧠 <b>Motor 2: Insights Analisados & Validados ({len(insights)})</b>",
            "━━━━━━━━━━━━━━━━━━━━━━"
        ]
        for ins in insights:
            cat = ins.get("category", "AI")
            head = html.escape(ins.get("headline", ""))
            conf = int(ins.get("confidence_score", 0) * 100)
            skill = ins.get("suggested_skill_name") or "N/A"
            res.append(f"• <b>[{cat}]</b> (Confiança: {conf}%)\n  📌 {head}\n  🛠️ <i>Candidato a Skill: {skill}</i>\n")
        res.append("━━━━━━━━━━━━━━━━━━━━━━\n<i>Use /autobuild para gerar skills a partir destes insights.</i>")
        return "\n".join(res)
    except Exception as e:
        return f"⚠️ Erro no Motor de Validação: {e}"


# ==========================================
# MESSAGE HANDLER (THIN BRIDGE)
# ==========================================
def handle_message(msg: dict):
    chat = msg.get('chat', {})
    chat_id = chat.get('id')
    user = msg.get('from', {})
    username = user.get('username', '')
    first_name = user.get('first_name', 'Operador')
    text = msg.get('text', '').strip()

    if not chat_id or not text:
        return

    log(f'📥 [{username or chat_id}]: {text[:60]}')
    save_subscriber(chat_id, username, first_name)

    raw_text = text.strip()
    words = raw_text.split()
    first_token = words[0].lower() if words else ""
    if '@' in first_token:
        first_token = first_token.split('@')[0]
    cmd_args = raw_text[len(words[0]):].strip() if len(words) > 1 else ""

    # /start — handled locally (instant, no brain needed)
    if first_token == '/start':
        send_message(chat_id, (
            f'Olá, <b>{first_name}</b>! 👋\n\n'
            'Sou o <b>Co-piloto Autônomo AXION</b>, motorizado pelo <b>Xiaomi Mimo</b>.\n\n'
            '⚡ <b>Modo:</b> Arquitetura Brain/Bot separados\n'
            '🧠 <b>Brain API:</b> <code>http://127.0.0.1:8765</code>\n\n'
            'Envie qualquer instrução em texto livre ou digite <code>/help</code> para comandos rápidos!'
        ))
        return

    # /clear — clear conversation history
    if first_token in ['/clear', '/limpar', '/reset']:
        res = call_brain('/v1/chat/clear', {'chat_id': chat_id})
        if res.get('error') and not res.get('success'):
            send_message(chat_id, f"⚠️ Erro ao limpar histórico: <code>{res.get('error')}</code>")
        else:
            send_message(
                chat_id,
                "🧹 <b>Histórico limpo com sucesso!</b>\n"
                "A memória recente da conversa foi reiniciada. O agente começará sem contexto prévio."
            )
        return

    # /status — system telemetry
    if first_token in ['/status', '/telemetria', '/telemetry']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        res = call_brain('/v1/tool', {'tool_name': 'get_system_telemetry', 'args': {}})
        tele = res.get('result', {})
        if res.get('error') or not tele:
            send_message(chat_id, f"⚠️ Falha ao obter telemetria: <code>{res.get('error', 'Sem resposta')}</code>")
        else:
            ram = tele.get('ram', {})
            disk_c = tele.get('c_drive') or tele.get('disk_c', {})
            disk_e = tele.get('e_backup_drive') or tele.get('disk_e', {})
            tail_summary = tele.get('tailscale_summary') or 'Disponível'

            ram_free = ram.get('free_gb', 0)
            ram_total = ram.get('total_gb', 0)
            ram_pct = ram.get('percent_used', ram.get('used_pct', 0))

            c_free = disk_c.get('free_gb', 0)
            c_total = disk_c.get('total_gb', 0)
            c_pct = disk_c.get('percent_free', disk_c.get('free_pct', 0))

            e_exists = disk_e.get('exists', False)
            e_free = disk_e.get('free_gb', 0)
            e_total = disk_e.get('total_gb', 0)
            e_str = f"<code>{e_free} GB livres</code> (de {e_total} GB)" if e_exists else "Não montado"

            lines = [
                '📊 <b>Telemetria do Sistema — AXION Enterprise</b>\n━━━━━━━━━━━━━━━━━━━━━━',
                f'🧠 <b>RAM:</b> <code>{ram_free} GB livres</code> de {ram_total} GB (<b>{ram_pct}%</b> em uso)',
                f'💾 <b>Disco C:</b> <code>{c_free} GB livres</code> de {c_total} GB (<b>{c_pct}%</b> livre)',
                f'🗄️ <b>Cofre E:</b> {e_str}',
                f'🌐 <b>Tailscale:</b> <code>{tail_summary}</code>',
                '━━━━━━━━━━━━━━━━━━━━━━',
                f'<i>Atualizado em: {datetime.datetime.now().strftime("%H:%M:%S")}</i>'
            ]
            send_message(chat_id, '\n'.join(lines))
        return

    # /cmd or ! — direct host command execution without AI
    if first_token == '/cmd' or raw_text.startswith('!'):
        cmd_to_run = raw_text[1:].strip() if raw_text.startswith('!') else cmd_args
        if not cmd_to_run:
            send_message(chat_id, (
                "⚡ <b>Execução Direta de Comandos</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "Execute comandos de terminal no Windows host de forma instantânea sem acionar o agente de IA.\n\n"
                "<b>Uso:</b>\n"
                "• <code>/cmd &lt;comando&gt;</code>\n"
                "• <code>!&lt;comando&gt;</code>\n\n"
                "<b>Exemplos:</b>\n"
                "• <code>/cmd pm2 status</code>\n"
                "• <code>!dir C:\\workspace</code>\n"
                "• <code>!git status</code>\n"
                "• <code>!ipconfig</code>"
            ))
            return

        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        res = call_brain('/v1/tool', {'tool_name': 'exec_command', 'args': {'cmd': cmd_to_run}})
        if res.get('error') or res.get('brain_offline'):
            send_message(chat_id, f"🔴 <b>Erro na execução:</b> <code>{res.get('error', 'Brain offline')}</code>")
            return

        out = res.get('result', {})
        success = out.get('success', True)
        icon = '✅' if success else '❌'
        out_text = out.get('output') or out.get('error') or out.get('message') or '(nenhuma saída padrão gerada)'
        escaped = html.escape(str(out_text)[:3500])
        send_message(
            chat_id,
            f"{icon} <b>Execução direta:</b> <code>{html.escape(cmd_to_run)}</code>\n"
            f"<pre>{escaped}</pre>"
        )
        return

    # /tasks — show or add workspace tasks directly
    if first_token in ['/tasks', '/task']:
        if cmd_args.lower().startswith('add ') or cmd_args.lower().startswith('criar '):
            instruction = cmd_args.split(maxsplit=1)[1] if len(cmd_args.split()) > 1 else ""
            if instruction:
                res = call_brain('/v1/tasks', {'instruction': instruction, 'source': 'telegram'})
                tid = res.get('task', {}).get('id', '?')
                send_message(chat_id, f"✅ <b>Tarefa injetada na fila:</b>\nID: <code>{tid}</code>\nInstrução: <code>{html.escape(instruction)}</code>")
            else:
                send_message(chat_id, "⚠️ Informe a instrução: <code>/task add &lt;instrução&gt;</code>")
            return
        else:
            res = _brain_get('/v1/tasks')
            tasks = res.get('tasks', [])
            if not tasks:
                send_message(chat_id, '📋 <b>Fila de tarefas vazia.</b>\nUse <code>/task add &lt;instrução&gt;</code> para adicionar.')
            else:
                lines = ['📋 <b>Tarefas do Workspace</b>\n━━━━━━━━━━━━━━━━━━━━━━']
                icons = {'pending': '⏳', 'running': '⚙️', 'completed': '✅', 'failed': '❌'}
                for t in tasks[:10]:
                    st = t.get('status', 'pending')
                    lines.append(f"{icons.get(st, '•')} <b>{t.get('title', 'Sem título')}</b>\n   ID: <code>{t.get('id')}</code> | Status: <code>{st}</code>")
                lines.append('━━━━━━━━━━━━━━━━━━━━━━\n<i>Dica: /task add &lt;instrução&gt; para criar nova</i>')
                send_message(chat_id, '\n'.join(lines))
            return

    # /watcher — show watcher dashboard directly
    if first_token in ['/watcher', '/watch', '/score']:
        res = _brain_get('/v1/watcher/dashboard')
        html_dash = res.get('html')
        if html_dash:
            send_message(chat_id, html_dash)
        else:
            send_message(chat_id, '⚠️ <b>Watcher não disponível no momento.</b>')
        return

    # /telemetry or /metrics — show operational telemetry dashboard
    if first_token in ['/telemetry', '/metrics', '/metricas']:
        res = _brain_get('/v1/telemetry/dashboard')
        html_dash = res.get('html')
        if html_dash:
            send_message(chat_id, html_dash)
        else:
            send_message(chat_id, '⚠️ <b>Telemetria não disponível no momento.</b>')
        return

    # /errors or /falhas — show recent recorded errors
    if first_token in ['/errors', '/erros', '/falhas']:
        res = _brain_get('/v1/telemetry/errors')
        err_list = res.get('errors', [])
        if not err_list:
            send_message(chat_id, '✅ <b>Nenhum erro registrado</b> no ledger operacional.')
        else:
            lines = ['🚨 <b>Últimos Erros Registrados no Sistema</b>\n━━━━━━━━━━━━━━━━━━━━━━']
            for e in err_list[:5]:
                t = e.get("timestamp", "")[11:19]
                svc = e.get("service", "core")
                typ = e.get("error_type", "Error")
                msg = html.escape(e.get("message", "")[:120])
                lines.append(f"• [<code>{t}</code>] <b>[{svc}]</b> <code>{typ}</code>:\n  <i>{msg}</i>")
            lines.append('━━━━━━━━━━━━━━━━━━━━━━\n<i>Use /brain ou /status para verificar a saúde dos nós.</i>')
            send_message(chat_id, '\n'.join(lines))
        return

    # /brain — check if brain is online
    if first_token in ['/brain', '/brain_status', '/ping']:
        res = _brain_get('/v1/health')
        if res.get('error'):
            send_message(chat_id, '🔴 <b>Brain Server OFFLINE!</b>\nVerifique PM2: <code>pm2 status</code>')
        else:
            uptime = res.get('uptime_seconds', 0)
            active = res.get('active_requests', 0)
            agents_md = '✅' if res.get('agents_md_loaded') else '❌'
            send_message(
                chat_id,
                f'🟢 <b>Brain Server ONLINE</b>\n'
                f'Uptime: <code>{uptime:.0f}s</code> | '
                f'Requests ativos: <code>{active}</code>\n'
                f'AGENTS.md carregado: {agents_md}'
            )
        return

    # /social — presence and status of digital channels
    if first_token in ['/social', '/redes', '/presenca']:
        send_message(chat_id, _format_social_status())
        return

    # /twitter or /x — view latest tweets and search
    if first_token in ['/twitter', '/x', '/tweets']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, _format_twitter_digest(cmd_args))
        return

    # /instagram or /ig — view instagram intelligence
    if first_token in ['/instagram', '/ig']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, _format_instagram_digest())
        return

    # /intel or /digest — content intelligence summary
    if first_token in ['/intel', '/digest', '/noticias']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, _format_intel_digest())
        return

    # /vault — secrets vault security audit
    if first_token in ['/vault', '/segredos', '/keys']:
        send_message(chat_id, _format_vault_status())
        return

    # /pipeline — run full AI intelligence pipeline
    if first_token in ['/pipeline', '/ia_pipeline']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, "⚙️ <b>Executando AI Intelligence Pipeline completo...</b>\n<i>(Descoberta -> Validação -> Fábrica -> Teste)</i>")
        send_message(chat_id, _format_pipeline_run())
        return

    # /discover — profile discovery and scoring
    if first_token in ['/discover', '/descoberta', '/perfis']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, _format_discover_run(cmd_args))
        return

    # /validate — insight validation
    if first_token in ['/validate', '/validar', '/insights']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, _format_validate_run())
        return

    # /desktop or /agentes — desktop agents monitoring panel
    if first_token in ['/desktop', '/agentes', '/desktop_status']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        res = _brain_get('/v1/desktop/status')
        telem = res.get('telemetry', {})
        if res.get('error') or not telem:
            send_message(chat_id, f"⚠️ Erro ao obter status desktop: <code>{res.get('error', 'Sem resposta')}</code>")
        else:
            notified = telem.get('recent_alerts', [])
            total = telem.get('total_monitored_finished', 0)
            lines = [
                '🖥️ <b>Painel de Agentes Desktop — AXION Enterprise</b>\n━━━━━━━━━━━━━━━━━━━━━━',
                '• <b>Antigravity:</b> 🟢 Ativo (Sessões & Background Tasks)',
                '• <b>Codex:</b> 🟢 Ativo (Workspaces & Active Tasks)',
                '• <b>OpenCode:</b> 🟢 Ativo (Active Tasks)',
                f'• <b>Tarefas Notificadas:</b> <code>{total}</code>',
                '━━━━━━━━━━━━━━━━━━━━━━',
                '<b>Últimas Tarefas Finalizadas:</b>'
            ]
            if not notified:
                lines.append('• <i>Nenhuma tarefa finalizada recentemente.</i>')
            else:
                for t in notified[:5]:
                    icon = '✅' if t.get('status') == 'completed' else '❌'
                    time_str = (t.get('notified_at') or '')[11:16]
                    lines.append(f"• {icon} <b>[{t.get('agent', 'Agente')}]</b> <code>{html.escape(t.get('title', t.get('id', '')))}</code> ({time_str})")
            lines.append('━━━━━━━━━━━━━━━━━━━━━━\n<i>Notificações proativas enviadas ao CEO Executive Operator.</i>')
            buttons = [
                [
                    {"text": "🔄 Atualizar", "callback_data": "desktop:refresh"},
                    {"text": "🔍 Varrer Agora", "callback_data": "desktop:scan"}
                ]
            ]
            send_message(chat_id, '\n'.join(lines), reply_markup={"inline_keyboard": buttons})
        return

    # /varrer — manual desktop scan trigger
    if first_token in ['/varrer', '/scan_desktop']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        send_message(chat_id, "🔍 <i>Executando varredura imediata de tarefas desktop...</i>")
        res = call_brain('/v1/desktop/scan', {})
        if res.get('error'):
            send_message(chat_id, f"⚠️ Falha na varredura: <code>{res.get('error')}</code>")
        else:
            new_count = res.get('result', {}).get('newly_notified_count', 0)
            send_message(chat_id, f"✅ <b>Varredura Desktop Concluída!</b>\nNovas tarefas finalizadas encontradas: <code>{new_count}</code>\nStatus: <b>Operacional</b>")
        return

    # /aprovacoes or /otp — client external approvals tracker
    if first_token in ['/aprovacoes', '/aprovacao', '/otp']:
        tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})
        res = _brain_get('/v1/approvals')
        approvals = res.get('approvals', [])
        pendings = [a for a in approvals if a.get('status') == 'pending']
        recent_resolved = [a for a in approvals if a.get('status') == 'approved'][-3:]

        lines = [
            '🔒 <b>Central de Aprovações & OTPs — AXION</b>\n━━━━━━━━━━━━━━━━━━━━━━',
            f'• <b>Aprovações Pendentes:</b> <code>{len(pendings)}</code>',
            f'• <b>Total Registrado:</b> <code>{len(approvals)}</code>',
            '━━━━━━━━━━━━━━━━━━━━━━'
        ]

        if not pendings:
            lines.append('✅ <b>Nenhuma aprovação externa pendente no momento.</b>\nTodas as esteiras de projetos operam nominalmente.')
        else:
            lines.append('<b>Aprovações Aguardando Cliente:</b>')
            now_dt = datetime.datetime.now()
            for p in pendings:
                try:
                    exp_dt = datetime.datetime.fromisoformat(p.get('expires_at', ''))
                    rem_min = max(0, int((exp_dt - now_dt).total_seconds() // 60))
                except Exception:
                    rem_min = '?'
                lines.append(
                    f"• <b>{html.escape(p.get('project_name', 'Projeto'))}</b> ({html.escape(p.get('client_name', 'Cliente'))} - <code>{p.get('client_phone')}</code>)\n"
                    f"  Item: <i>{html.escape(p.get('resource_type', ''))}</i>\n"
                    f"  Expira em: <b>{rem_min} min</b>"
                )

        if recent_resolved:
            lines.append('\n<b>Últimas Resolvidas:</b>')
            for r in recent_resolved:
                lines.append(f"• ✅ <b>{html.escape(r.get('project_name', 'Projeto'))}:</b> Código <code>{html.escape(str(r.get('received_code', '')))}</code>")

        lines.append('━━━━━━━━━━━━━━━━━━━━━━')
        send_message(chat_id, '\n'.join(lines))
        return

    # /help — help guide
    if first_token in ['/help', '/ajuda']:
        help_text = (
            "<b>📖 GUIA DO CO-PILOTO AUTÔNOMO — AXION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Pipeline de IA & Automação:</b>\n"
            "• <code>/pipeline</code> — Executa o ciclo autônomo completo de IA\n"
            "• <code>/discover [handle]</code> — Descobre e pontua novos perfis de IA\n"
            "• <code>/validate</code> — Valida tecnicamente os insights mais recentes\n"
            "• <code>/vault</code> — Auditoria segura de credenciais do Vault\n\n"
            "<b>Agentes Desktop & Aprovações:</b>\n"
            "• <code>/desktop</code> ou <code>/agentes</code> — Monitor de tarefas desktop (Antigravity, Codex, OpenCode)\n"
            "• <code>/varrer</code> — Varredura manual imediata de tarefas finalizadas\n"
            "• <code>/aprovacoes</code> ou <code>/otp</code> — Monitor de aprovações externas & OTPs de clientes\n\n"
            "<b>Redes Sociais & Inteligência:</b>\n"
            "• <code>/social</code> — Presença digital do agente nas redes\n"
            "• <code>/twitter &lt;termo&gt;</code> ou <code>/x</code> — Tweets recentes (Syndication)\n"
            "• <code>/instagram</code> — Atualizações monitoradas do Instagram\n"
            "• <code>/intel</code> — Resumo diário de inteligência de conteúdo\n\n"
            "<b>Comandos de Sistema:</b>\n"
            "• <code>/status</code> — Telemetria do host (RAM, Disco, CPU)\n"
            "• <code>/cmd &lt;comando&gt;</code> ou <code>!&lt;cmd&gt;</code> — Executa comando no Windows sem IA\n"
            "• <code>/tasks</code> — Lista tarefas pendentes e ativas\n"
            "• <code>/clear</code> — Limpa a memória recente da conversa\n"
            "• <code>/brain</code> — Diagnóstico de saúde do Brain Server\n\n"
            "<b>Execução Autônoma no PC:</b>\n"
            "Envie qualquer instrução em linguagem natural:\n"
            "• <i>'Descubra perfis de agentes e LLM hoje'</i>\n"
            "• <i>'Valide as novidades da Anthropic e crie a skill correspondente'</i>\n"
            "• <i>'Qual o resumo das novidades da Cloudflare hoje?'</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_message(chat_id, help_text)
        return

    # Unknown slash command
    if first_token.startswith('/') and '/' not in first_token[1:]:
        send_message(
            chat_id,
            f"⚠️ Comando <code>{html.escape(first_token)}</code> não reconhecido.\n"
            "Use <code>/help</code> para ver os comandos disponíveis, ou envie sua instrução em texto normal."
        )
        return

    # All other messages → forward to brain
    res = call_brain('/v1/chat', {
        'chat_id': chat_id,
        'message': text,
        'username': username,
        'first_name': first_name
    })

    if res.get('brain_offline') or res.get('error'):
        send_message(chat_id, (
            '🔴 <b>Brain Server temporariamente offline.</b>\n'
            'Aguarde alguns segundos e tente novamente.\n'
            f'<code>{res.get("error", "")[:100]}</code>'
        ))
        log(f'[!] Brain offline para {chat_id}: {res.get("error")}')
    else:
        log(f'[Brain] Request {res.get("request_id", "?")} aceito para {chat_id}')
        # Brain sends the response directly to Telegram — bot does nothing else


# ==========================================
# CALLBACK QUERY HANDLER (THIN BRIDGE)
# ==========================================
def handle_callback_query(cb: dict):
    cb_id = cb.get('id')
    token = cb.get('data', '')
    msg = cb.get('message', {})
    chat = msg.get('chat', {}) if isinstance(msg, dict) else {}
    chat_id = chat.get('id') or cb.get('from', {}).get('id')
    user = cb.get('from', {})
    username = user.get('username', '')

    if not chat_id:
        try:
            tg_api('answerCallbackQuery', {'callback_query_id': cb_id})
        except Exception:
            pass
        return

    log(f'🔘 [Callback @{username or chat_id}]: token={token}')
    # Instant visual toast
    try:
        tg_api('answerCallbackQuery', {'callback_query_id': cb_id, 'text': '⚡ Processando...'})
    except Exception as e:
        log(f'[!] Erro ao responder callback query {cb_id}: {e}')

    # Forward callback to brain asynchronously with response logging
    def _forward_cb():
        payload = {
            'chat_id': chat_id,
            'token': token,
            'username': username,
            'message': msg
        }
        res = call_brain('/v1/callback', payload)
        if res.get('error'):
            log(f'[!] Erro ao encaminhar callback {token} para Brain: {res.get("error")}')
            send_message(chat_id, f"⚠️ Erro ao comunicar com Brain Server: <code>{res.get('error')[:100]}</code>")
        else:
            log(f'[Callback] Token {token} processado com sucesso pelo Brain: {res}')

    threading.Thread(target=_forward_cb, daemon=True).start()



def sync_bot_commands():
    """Synchronizes the slash command menu in the Telegram client UI."""
    commands = [
        {"command": "start", "description": "Iniciar co-piloto e ver status"},
        {"command": "pipeline", "description": "Ciclo completo de IA (Descoberta->Teste)"},
        {"command": "discover", "description": "Descobrir e pontuar perfis de IA/LLM"},
        {"command": "validate", "description": "Validar e interpretar insights técnicos"},
        {"command": "help", "description": "Guia de comandos e recursos"},
        {"command": "intel", "description": "Digest diário de inteligência técnica"},
        {"command": "social", "description": "Status da presença digital nas redes"},
        {"command": "twitter", "description": "Últimos tweets e buscas (Syndication)"},
        {"command": "instagram", "description": "Novidades monitoradas do Instagram"},
        {"command": "vault", "description": "Auditoria de credenciais e segurança"},
        {"command": "status", "description": "Telemetria do host (RAM, Disco, CPU)"},
        {"command": "cmd", "description": "Executar comando direto no Windows"},
        {"command": "clear", "description": "Limpar histórico da conversa ativa"},
        {"command": "brain", "description": "Diagnóstico do cérebro operacional"},
        {"command": "telemetry", "description": "Painel de telemetria, erros e métricas"},
        {"command": "errors", "description": "Diagnóstico dos últimos erros do sistema"}
    ]
    res = tg_api("setMyCommands", {"commands": commands})
    if res.get("ok"):
        log("[*] Menu de comandos do Telegram sincronizado com sucesso.")
    else:
        log(f"[!] Falha ao sincronizar comandos do Telegram: {res.get('description')}")


# ==========================================
# LONG POLLING LOOP
# ==========================================
def run_bot_polling():
    log('=' * 50)
    log('   AXION TELEGRAM BOT — THIN CLIENT ATIVO')
    log(f'   Brain API: {BRAIN_URL}')
    log('   Modo: Apenas roteamento Telegram → Brain')
    log('=' * 50)

    # Install global exception catchers for bot process
    try:
        from bot_engine import error_handlers
        error_handlers.install_global_catchers("telegram_bot", None)
    except Exception as _e:
        log(f"[!] Aviso: Não foi possível instalar error_handlers: {_e}")

    # Ensure no webhook conflicts with getUpdates polling
    tg_api("deleteWebhook", {"drop_pending_updates": False})

    # Sync slash commands with Telegram UI
    sync_bot_commands()

    log('[*] Iniciando long polling do Telegram...')
    offset = None
    _ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query', 'inline_query', 'channel_post', 'edited_channel_post']

    while True:
        try:
            params = {
                'timeout': 20,
                'allowed_updates': _ALLOWED_UPDATES
            }
            if offset is not None:
                params['offset'] = offset
            res = tg_api('getUpdates', params, timeout=30)
            if res.get('ok'):
                for u in res.get('result', []):
                    offset = u['update_id'] + 1
                    if 'message' in u:
                        threading.Thread(target=handle_message, args=(u['message'],), daemon=True).start()
                    elif 'callback_query' in u:
                        threading.Thread(target=handle_callback_query, args=(u['callback_query'],), daemon=True).start()
            elif res.get('timeout'):
                # Normal long polling timeout without updates - cycle immediately
                continue
            else:
                err_desc = res.get("description") or res.get("error") or "desconhecido"
                log(f'[!] Telegram API error: {err_desc}')
                time.sleep(2)
        except KeyboardInterrupt:
            log('Bot encerrado.')
            break
        except Exception as e:
            log(f'[!] Polling error: {e}')
            time.sleep(3)


if __name__ == '__main__':
    run_bot_polling()
