import os
import subprocess
import re
import sys
import json
import time
import uuid
import threading
import datetime
import html
import urllib.request
import urllib.parse
import urllib.error
import http.server
from http.server import ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Setup paths
WORKSPACE_ROOT = Path(os.environ.get('WORKSPACE_ROOT', Path(__file__).resolve().parent.parent))
sys.path.append(str(WORKSPACE_ROOT / 'scripts'))

# Load environment secrets (.env / vault)
try:
    if str(WORKSPACE_ROOT) not in sys.path:
        sys.path.insert(0, str(WORKSPACE_ROOT))
    from scripts.vault_loader import load_vault
    load_vault()
except Exception:
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

# Imports from bot_engine
try:
    from bot_engine import (
        autonomous_agent, tool_executor, task_queue,
        message_store, dynamic_keyboard, tentacles, watcher,
        telemetry, error_handlers, intent_router, hit_cache,
        first_content_stream, identity_registry
    )
except ImportError as e:
    print(f"Warning: Failed to import bot_engine modules: {e}")
    # Provide stubs or let it fail if needed
    autonomous_agent = None
    tool_executor = None
    task_queue = None
    message_store = None
    dynamic_keyboard = None
    tentacles = None
    watcher = None
    telemetry = None
    error_handlers = None
    intent_router = None
    hit_cache = None
    first_content_stream = None
    identity_registry = None

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TG_API_BASE = f'https://api.telegram.org/bot{BOT_TOKEN}'

STARTUP_TIME = time.time()
_EXECUTOR = ThreadPoolExecutor(max_workers=8)

# Telegram API helpers
def _tg_api(method, data=None, timeout=30, max_retries=2):
    url = f'{TG_API_BASE}/{method}'
    body = json.dumps(data).encode('utf-8') if data else None

    def _call():
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))

    try:
        if error_handlers and max_retries > 0:
            return error_handlers.retry_with_backoff(
                _call,
                max_retries=max_retries,
                initial_delay=0.8,
                service_name="telegram_api",
                circuit=error_handlers.TELEGRAM_CIRCUIT
            )
        return _call()
    except Exception as e:
        if telemetry:
            telemetry.record_error("telegram_api", type(e).__name__, str(e), severity="WARNING")
        return {'ok': False, 'error': str(e)}

def _tg_send(chat_id, text, parse_mode='HTML'):
    """Sends a message, returns message_id or None"""
    res = _tg_api('sendMessage', {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode, 'disable_web_page_preview': True})
    if res.get('ok'):
        return res.get('result', {}).get('message_id')
    # Try without parse_mode on failure
    import re as _re
    plain = _re.sub(r'<[^>]+>', '', text)
    res2 = _tg_api('sendMessage', {'chat_id': chat_id, 'text': plain[:4000]})
    return res2.get('result', {}).get('message_id') if res2.get('ok') else None

def _tg_send_full(chat_id, text, reply_markup=None):
    """Sends with chunking and optional reply_markup"""
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)] if len(text) > 4000 else [text]
    for i, chunk in enumerate(chunks):
        payload = {'chat_id': chat_id, 'text': chunk, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        if reply_markup and i == len(chunks)-1:
            payload['reply_markup'] = reply_markup
        res = _tg_api('sendMessage', payload)
        if not res.get('ok'):
            import re as _re
            plain = _re.sub(r'<[^>]+>', '', chunk)
            _tg_api('sendMessage', {'chat_id': chat_id, 'text': plain[:4000]})

def _tg_edit(chat_id, message_id, text):
    """Non-blocking in-place progress edit with short timeout"""
    if not message_id:
        return
    def _run():
        try:
            _tg_api('editMessageText', {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}, timeout=4, max_retries=0)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

def _tg_delete(chat_id, message_id):
    """Non-blocking message deletion with short timeout"""
    if not message_id:
        return
    def _run():
        try:
            _tg_api('deleteMessage', {'chat_id': chat_id, 'message_id': message_id}, timeout=4, max_retries=0)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

def _tg_typing(chat_id):
    """Non-blocking typing indicator"""
    def _run():
        try:
            _tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'}, timeout=3, max_retries=0)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

# broadcast_alert
SUBSCRIBERS_PATH = WORKSPACE_ROOT / 'workspace' / 'telegram_subscribers.json'

def broadcast_alert(message, severity='WARNING'):
    if not SUBSCRIBERS_PATH.exists(): return
    try:
        subs = json.loads(SUBSCRIBERS_PATH.read_text(encoding='utf-8'))
    except: return
    icon = '🚨' if severity == 'CRITICAL' else '⚠️'
    text = f'{icon} <b>ALERTA [{severity}]</b>\n━━━━━━━━━━━━━━━━━━━━━━\n{message}\n━━━━━━━━━━━━━━━━━━━━━━'
    for cid_str, sub in subs.items():
        if sub.get('notifications_enabled', True):
            try:
                cid_int = int(cid_str)
                _tg_send_full(cid_int, text)
                if message_store:
                    message_store.save_message(
                        cid_int, 'outgoing', text,
                        metadata={'is_system_broadcast': True, 'broadcast_type': 'alert', 'severity': severity}
                    )
            except: pass

def _tentacle_send(chat_id, text, save_local=True, reply_markup=None, **kwargs):
    _tg_send_full(chat_id, text, reply_markup=reply_markup)
    if save_local and message_store:
        try:
            message_store.save_message(
                chat_id, 'outgoing', text,
                metadata={'is_system_broadcast': True, 'broadcast_type': 'tentacle'}
            )
        except: pass

# Request state management & Per-Chat Concurrency
_ACTIVE_REQUESTS = {}  # request_id -> state dict
_REQUESTS_LOCK = threading.Lock()
REQUESTS_DIR = WORKSPACE_ROOT / 'memory' / 'brain' / 'requests'
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)

class PerChatLockManager:
    """
    Serializes concurrent requests for the same chat_id (FIFO queue).
    Different chat_ids execute concurrently in full parallel performance.
    """
    def __init__(self):
        self._locks = {}
        self._global_lock = threading.Lock()

    def get_lock(self, chat_id: str | int) -> threading.Lock:
        cid = str(chat_id)
        with self._global_lock:
            if cid not in self._locks:
                self._locks[cid] = threading.Lock()
            return self._locks[cid]

_CHAT_LOCKS = PerChatLockManager()

def _cleanup_old_requests():
    """
    Evicts requests older than 60 minutes from in-memory _ACTIVE_REQUESTS,
    and removes request files on disk older than 7 days.
    """
    now = datetime.datetime.now()
    cutoff_mem = now - datetime.timedelta(minutes=60)
    cutoff_disk = now - datetime.timedelta(days=7)

    with _REQUESTS_LOCK:
        expired_keys = []
        for rid, req in list(_ACTIVE_REQUESTS.items()):
            fin = req.get("finished_at")
            if fin:
                try:
                    dt = datetime.datetime.fromisoformat(fin)
                    if dt < cutoff_mem:
                        expired_keys.append(rid)
                except Exception:
                    pass
        for k in expired_keys:
            del _ACTIVE_REQUESTS[k]

    try:
        if REQUESTS_DIR.exists():
            for f in REQUESTS_DIR.glob("*.json"):
                try:
                    mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < cutoff_disk:
                        f.unlink()
                except Exception:
                    pass
    except Exception:
        pass

def _store_request(request_id, state):
    with _REQUESTS_LOCK:
        _ACTIVE_REQUESTS[request_id] = state
        (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(state, ensure_ascii=False, default=str), encoding='utf-8')

def _get_request(request_id):
    with _REQUESTS_LOCK:
        return _ACTIVE_REQUESTS.get(request_id)

def _add_request_step(request_id, step_num, step_type, description):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id].setdefault('steps', []).append({'step': step_num, 'type': step_type, 'description': description, 'ts': datetime.datetime.now().isoformat()})
            (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(_ACTIVE_REQUESTS[request_id], ensure_ascii=False, default=str), encoding='utf-8')

def _mark_request_done(request_id, result_html, tools_used):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id].update({'status': 'done', 'result_html': result_html, 'tools_used': tools_used, 'finished_at': datetime.datetime.now().isoformat()})
            (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(_ACTIVE_REQUESTS[request_id], ensure_ascii=False, default=str), encoding='utf-8')
    try:
        _cleanup_old_requests()
    except Exception:
        pass

def _mark_request_error(request_id, error):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id].update({'status': 'error', 'error': error, 'finished_at': datetime.datetime.now().isoformat()})
            (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(_ACTIVE_REQUESTS[request_id], ensure_ascii=False, default=str), encoding='utf-8')

def _store_progress_msg_id(request_id, msg_id):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id]['progress_msg_id'] = msg_id

WHATSAPP_BRIDGE_URL = os.environ.get('WHATSAPP_BRIDGE_URL', 'http://127.0.0.1:4114')

def tg_html_to_whatsapp(text: str) -> str:
    """Converts Telegram HTML formatting to WhatsApp markdown format"""
    if not text:
        return ""
    import re
    # Bold: <b>, <strong> -> *text*
    text = re.sub(r'</?(?:b|strong)>', '*', text)
    # Italic: <i>, <em> -> _text_
    text = re.sub(r'</?(?:i|em)>', '_', text)
    # Inline code: <code> -> `code`
    text = re.sub(r'</?code>', '`', text)
    # Code block: <pre> -> ```
    text = re.sub(r'</?pre>', '```', text)
    # Convert <br> or <br/> to newline
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Strip any other tags
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()

def _format_help_html(is_admin=True) -> str:
    """Renders the executive guide for the AXION autonomous co-pilot."""
    return (
        "<b>📖 CO-PILOTO AUTÔNOMO AXION — GUIA EXECUTIVO & OPERACIONAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Motor Principal:</b> Xiaomi Mimo 2.6 Pro (Single-Pass & Streaming)\n"
        "🖥️ <b>Orquestração Desktop:</b> Codex ⚡ | Antigravity 🧠 | OpenCode 🚀\n"
        "🌐 <b>Canais Conectados:</b> WhatsApp Business + Telegram Bot + Brain API\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🖥️ 1. ORQUESTRAÇÃO DE AGENTES DESKTOP</b>\n"
        "• <code>/desktop</code> ou <code>/agentes</code> — Painel de telemetria dos agentes desktop.\n"
        "• <code>/quotas</code> — Saldo de cotas, rate-limits (429) e status de cooldowns.\n"
        "• <code>/varrer</code> — Força varredura imediata de tarefas finalizadas em background.\n"
        "<i>💬 Despacho em Linguagem Natural:</i>\n"
        "  ↳ <i>\"Peça ao Codex para corrigir o bug de responsividade no checkout\"</i>\n"
        "  ↳ <i>\"Peça ao Antigravity para validar as regras do AGENTS.md\"</i>\n"
        "  ↳ <i>\"Peça ao OpenCode para rodar um teste de carga no endpoint\"</i>\n\n"
        "<b>⚡ 2. INFRAESTRUTURA & HOST WINDOWS</b>\n"
        "• <code>/status</code> — Telemetria ao vivo do PC (CPU, RAM, SSD, Tailnet Mesh, Uptime).\n"
        "• <code>/cmd &lt;comando&gt;</code> — Executa comandos nativos no PowerShell / CMD com retorno imediato.\n"
        "• <code>/services</code> ou <code>/pm2</code> — Status de saúde dos daemons de produção.\n"
        "• <code>/brain</code> — Latência, requests ativos e integridade do Brain Server.\n"
        "• <code>/clear</code> — Reinicia o contexto imediato da conversa mantendo o histórico salvo.\n\n"
        "<b>📋 3. FILA DE TAREFAS EM BACKGROUND</b>\n"
        "• <code>/tasks</code> — Lista as tarefas da esteira (pendentes, ativas e concluídas).\n"
        "• <code>/task add &lt;instrução&gt;</code> — Enfileira nova tarefa com checkpointing e resiliência a falhas.\n\n"
        "<b>🔒 4. GOVERNANÇA, SENTINEL & SEGURANÇA</b>\n"
        "• <code>/aprovacoes</code> ou <code>/otp</code> — Central de códigos SMS/2FA e autorizações de clientes aguardando validação.\n"
        "  ↳ <i>Hook Instantâneo:</i> Quando o cliente responde com código no WhatsApp, o Sentinel captura e notifica o CEO na hora!\n"
        "• <code>/equipe</code> — Lista membros da equipe corporativa e permissões.\n"
        "• <code>/leads</code> — Painel de captação, CRM e qualificação de novos leads do WhatsApp.\n"
        "• <code>/cadastrar &lt;num&gt; &lt;cargo&gt; &lt;nome&gt;</code> — Autoriza operador corporativo.\n"
        "• <code>/remover &lt;num&gt;</code> — Revoga acesso corporativo.\n\n"
        "<b>📊 5. OBSERVABILIDADE & QUALIDADE (WATCHER)</b>\n"
        "• <code>/watcher</code> — Painel executivo com métricas de completude, eficiência e scoring (A/B/C/D/F).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💡 COMANDOS LIVRES EM LINGUAGEM NATURAL</b>\n"
        "Você não precisa se limitar a comandos! Pode me enviar qualquer instrução em texto ou áudio:\n"
        "• <i>\"Crie uma landing page de alta conversão para o projeto X e publique na Vercel\"</i>\n"
        "• <i>\"Audite os containers Docker e veja se há algum processo travado\"</i>\n"
        "• <i>\"Gere um resumo executivo das entregas de hoje\"</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def _wa_send(to: str, message: str, buttons: list = None, is_admin: bool = False, edit_key: dict | str = None, max_retries: int = 3):
    """Sends message directly back to WhatsApp bridge with automatic retry on transient failure and edit fallback."""
    url = f"{WHATSAPP_BRIDGE_URL}/send-internal"
    payload_dict = {
        "to": to,
        "message": message,
        "buttons": buttons or [],
        "is_admin": is_admin
    }
    if edit_key:
        payload_dict["edit_key"] = edit_key
    payload = json.dumps(payload_dict).encode('utf-8')

    last_res = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                if res_data.get("success"):
                    return res_data
                last_res = res_data
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode('utf-8')
                last_res = json.loads(err_body)
            except Exception:
                last_res = {"error": f"HTTP {he.code}: {he.reason}"}
        except Exception as e:
            last_res = {"error": str(e)}

        if attempt < max_retries:
            time.sleep(1.5 * attempt)

    # If edit attempt failed across all retries, fall back to sending as fresh new message
    if edit_key:
        print(f"[Brain] Edit WhatsApp falhou para {to} após {max_retries} tentativas. Enviando como nova mensagem...")
        return _wa_send(to, message, buttons=buttons, is_admin=is_admin, edit_key=None, max_retries=2)

    print(f"[Brain] Falha crítica ao enviar resposta para WhatsApp ({to}) após {max_retries} tentativas: {last_res}")
    return last_res or {"error": "Falha no envio para WhatsApp", "success": False}

def _wa_bridge_call(endpoint: str, data: dict = None, method: str = 'GET', max_retries: int = 3) -> dict:
    """Invokes WhatsApp Bridge HTTP API endpoints with automatic retries on transient connection issues."""
    url = f"{WHATSAPP_BRIDGE_URL}{endpoint}"
    payload = json.dumps(data).encode('utf-8') if data is not None else None

    last_res = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method=method)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as he:
            try:
                return json.loads(he.read().decode('utf-8'))
            except Exception:
                last_res = {"error": str(he), "status": he.code}
        except Exception as e:
            last_res = {"error": str(e)}

        if attempt < max_retries:
            time.sleep(1.0 * attempt)

    return last_res or {"error": "Falha na chamada ao bridge", "success": False}

def _dispatch_reply(chat_id, text_html, source='telegram', reply_markup=None, is_admin=False, edit_key=None):
    """Dispatches reply to the appropriate platform (Telegram or WhatsApp), supporting in-place editing"""
    if source == 'test' or str(chat_id).startswith('test'):
        return {"ok": True, "test": True}
    is_wa = (source == 'whatsapp' or (isinstance(chat_id, str) and ('@s.whatsapp.net' in str(chat_id) or '@lid' in str(chat_id))))
    if is_wa:
        buttons = []
        if reply_markup and isinstance(reply_markup, dict):
            buttons = reply_markup.get('button_items', [])
        
        wa_text = tg_html_to_whatsapp(text_html)
        
        # If buttons exist, also format fallback numbered options in the text for desktop/web clients
        if buttons and dynamic_keyboard and hasattr(dynamic_keyboard, 'format_whatsapp_buttons_fallback'):
            wa_text = dynamic_keyboard.format_whatsapp_buttons_fallback(wa_text, buttons)

        return _wa_send(str(chat_id), wa_text, buttons=buttons, is_admin=is_admin, edit_key=edit_key)
    else:
        return _tg_send_full(chat_id, text_html, reply_markup=reply_markup)


def _process_chat_request(request_id, chat_id, message, username, first_name,
                           resume_context=None, task_id=None,
                           source='telegram', is_admin=False, is_lead=False):
    is_whatsapp = (source == 'whatsapp' or (isinstance(chat_id, str) and ('@s.whatsapp.net' in str(chat_id) or '@lid' in str(chat_id))))
    clean_msg = message.strip()

    # 0. Centralized Identity & Permissions Lookup (O(1))
    user_profile = None
    if identity_registry:
        user_profile = identity_registry.resolve_identity(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            source=source,
            is_admin_hint=is_admin,
            is_lead_hint=is_lead
        )
        is_admin = user_profile.get("is_admin", is_admin)
        is_lead = user_profile.get("is_lead", is_lead)
        if user_profile.get("is_registered") and user_profile.get("name"):
            first_name = user_profile.get("name")

    words = clean_msg.split()
    cmd_token = words[0].lower() if words else ""
    if '@' in cmd_token:
        cmd_token = cmd_token.split('@')[0]
    cmd_args = clean_msg[len(words[0]):].strip() if len(words) > 1 else ""

    # 1. Deterministic Fast-Intent Catcher (Instant < 1ms, zero LLM, immune to hallucinations)
    fast_match = intent_router.match_fast_intent(clean_msg) if intent_router else None
    if fast_match:
        intent_name, fast_text, fast_buttons = fast_match
        print(f"[Brain Fast-Intent] Intenção '{intent_name}' capturada para {chat_id} (0.5ms)")
        _dispatch_reply(chat_id, fast_text, source=source, reply_markup={"button_items": fast_buttons}, is_admin=is_admin)
        _mark_request_done(request_id, fast_text, [])
        return

    # 2. Hit Cache Lookup (< 2ms)
    cache_key = hit_cache.hit_cache.normalize_key(clean_msg, context_scope="lead" if is_lead else "chat") if hit_cache else ""
    if cache_key and not clean_msg.startswith('/') and not clean_msg.startswith('!'):
        cached_entry = hit_cache.hit_cache.get(cache_key)
        if cached_entry:
            ans_cached = cached_entry.get("ans_html")
            btns_cached = cached_entry.get("buttons")
            print(f"[Brain Hit-Cache] Cache hit para chave '{cache_key}' (1.0ms)")
            _dispatch_reply(chat_id, ans_cached, source=source, reply_markup={"button_items": btns_cached} if btns_cached else None, is_admin=is_admin)
            _mark_request_done(request_id, ans_cached, [])
            return

    # Direct action token resolution (e.g. from WhatsApp button click or numeric shortcut)
    if dynamic_keyboard and (clean_msg.startswith('act:') or clean_msg.startswith('cb_') or clean_msg.startswith('task:exec:') or clean_msg.startswith('task:del:') or clean_msg.startswith('tool:')):
        resolved_action = dynamic_keyboard.resolve_callback_action(clean_msg)
        if resolved_action:
            print(f"[Brain] Ação de botão resolvida ({source}): '{clean_msg}' -> {resolved_action}")
            act = resolved_action.get('action', '')
            query = resolved_action.get('query', '')
            _EXECUTOR.submit(_process_callback, chat_id, query, act, username, resolved_action, source, is_admin)
            _mark_request_done(request_id, f"Ação executada: {act}", [])
            return

    # Direct command: /watcher dashboard
    if cmd_token in ['/watcher', '/watch', '/score']:
        dash = watcher.get_dashboard_html(limit=10) if watcher else "⚠️ Watcher não disponível."
        _dispatch_reply(chat_id, dash, source=source, is_admin=is_admin)
        _mark_request_done(request_id, dash, [])
        return

    # Direct command: /clear
    if cmd_token in ['/clear', '/limpar', '/reset']:
        if message_store:
            message_store.clear_chat_history(chat_id)
        msg_out = "🧹 <b>Histórico limpo!</b>\nA memória recente da conversa foi reiniciada. O agente começará sem contexto prévio."
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /status
    if cmd_token in ['/status', '/telemetria', '/telemetry']:
        if tool_executor:
            tele = tool_executor.get_system_telemetry()
            msg_out = _format_telemetry_html(tele)
        else:
            msg_out = "⚠️ tool_executor não disponível."
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /cmd or !
    if cmd_token == '/cmd' or clean_msg.startswith('!'):
        cmd_to_run = ""
        if is_lead:
            msg_out = "⚠️ Comandos de terminal são restritos ao Administrador."
        else:
            cmd_to_run = clean_msg[1:].strip() if clean_msg.startswith('!') else cmd_args
            if not cmd_to_run:
                msg_out = (
                    "⚡ <b>Execução Direta de Comandos</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Uso: <code>/cmd &lt;comando&gt;</code> ou <code>!&lt;comando&gt;</code>\n\n"
                    "Exemplo:\n• <code>/cmd pm2 status</code>\n• <code>!dir</code>\n• <code>!git status</code>"
                )
            else:
                if tool_executor:
                    res = tool_executor.execute_tool('exec_command', {'cmd': cmd_to_run})
                    msg_out = _format_tool_result_html('exec_command', res)
                else:
                    msg_out = "⚠️ tool_executor não disponível."
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        _mark_request_done(request_id, msg_out, ['exec_command'] if cmd_to_run else [])
        return

    # Direct command: /tasks
    if cmd_token in ['/tasks', '/task']:
        if is_lead:
            msg_out = "⚠️ O gerenciamento de tarefas internas é restrito à equipe."
        elif cmd_args.lower().startswith('add ') or cmd_args.lower().startswith('criar '):
            inst = cmd_args.split(maxsplit=1)[1] if len(cmd_args.split()) > 1 else ""
            if task_queue and inst:
                t = task_queue.inject_task(instruction=inst, source=source)
                msg_out = f"✅ <b>Tarefa injetada na fila:</b>\nID: <code>{t.get('id')}</code>\nInstrução: <code>{html.escape(inst)}</code>"
            else:
                msg_out = "⚠️ Forneça uma instrução: <code>/task add &lt;instrução&gt;</code>"
        else:
            tasks = task_queue.list_tasks(limit=10) if task_queue else []
            if not tasks:
                msg_out = "📋 <b>Fila de tarefas vazia.</b>\nUse <code>/task add &lt;instrução&gt;</code> para adicionar."
            else:
                lines = ['📋 <b>Tarefas do Workspace</b>\n━━━━━━━━━━━━━━━━━━━━━━']
                icons = {'pending': '⏳', 'running': '⚙️', 'completed': '✅', 'failed': '❌'}
                for t in tasks:
                    st = t.get('status', 'pending')
                    lines.append(f"{icons.get(st, '•')} <b>{t.get('title', 'Sem título')}</b>\n   ID: <code>{t.get('id')}</code> | Status: <code>{st}</code>")
                lines.append('━━━━━━━━━━━━━━━━━━━━━━\n<i>Dica: /task add &lt;instrução&gt; para criar nova</i>')
                msg_out = '\n'.join(lines)
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /brain
    if cmd_token in ['/brain', '/brain_status', '/ping']:
        uptime_seconds = time.time() - STARTUP_TIME
        active_requests = sum(1 for req in _ACTIVE_REQUESTS.values() if req.get('status') == 'running')
        msg_out = (
            f"🟢 <b>Brain Server ONLINE</b>\n"
            f"Uptime: <code>{uptime_seconds:.0f}s</code> | Requests ativos: <code>{active_requests}</code>"
        )
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /help, /ajuda, /menu
    if cmd_token in ['/help', '/ajuda', '/menu']:
        help_buttons = [
            {"text": "📊 Telemetria", "query": "/status"},
            {"text": "🖥️ Agentes Desktop", "query": "/desktop"},
            {"text": "📋 Fila de Tarefas", "query": "/tasks"},
            {"text": "🎯 Watcher Score", "query": "/watcher"},
            {"text": "🔒 Aprovações OTP", "query": "/aprovacoes"},
            {"text": "📈 Cotas e Limites", "query": "/quotas"}
        ]
        reply_markup = {
            "inline_keyboard": [
                [{"text": "📊 Telemetria", "callback_data": "act:telemetry"}, {"text": "🖥️ Agentes", "callback_data": "desktop:refresh"}],
                [{"text": "📋 Tarefas", "callback_data": "act:task:list"}, {"text": "🎯 Watcher", "callback_data": "act:watcher"}],
                [{"text": "🔒 Aprovações", "callback_data": "act:aprovacoes"}, {"text": "📈 Cotas", "callback_data": "act:quotas"}]
            ],
            "button_items": help_buttons
        }
        msg_out = _format_help_html(is_admin=is_admin)
        _dispatch_reply(chat_id, msg_out, source=source, reply_markup=reply_markup, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /desktop or /agentes
    if cmd_token in ['/desktop', '/agentes', '/orchestrator']:
        lines = [
            "<b>🖥️ PAINEL DE AGENTES DESKTOP — AXION ORCHESTRATOR</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        try:
            from bot_engine import desktop_orchestrator
            dash = desktop_orchestrator.get_orchestrator_dashboard()
            for ag in dash.get("agents", []):
                st_icon = "🟢" if ag.get("status") == "ready" and ag.get("ready") else ("🟡" if ag.get("status") in ["degraded", "rate_limited"] else "🔴")
                cd_txt = f" | ⏳ Cooldown: {ag['cooldown_remaining']}s" if ag.get("cooldown_remaining", 0) > 0 else ""
                lines.append(
                    f"{st_icon} <b>{ag['name']}</b> ({ag['agent'].upper()})\n"
                    f"   • Modelo: <code>{ag['model']}</code> | Tier: <code>{ag['tier'].upper()}</code>\n"
                    f"   • Status: <code>{ag['status'].upper()}</code>{cd_txt}\n"
                    f"   • Hoje: {ag['successful_today']} ok / {ag['failed_today']} falhas (Total: {ag['invocations_today']})\n"
                )
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("<i>💡 Dica: Peça em texto livre: 'Peça ao Codex para...' ou envie /quotas</i>")
        except Exception as de:
            lines.append(f"⚠️ Erro ao consultar agentes desktop: <code>{de}</code>")
        msg_out = "\n".join(lines)
        desktop_buttons = [
            {"text": "🔍 Varrer Tarefas", "query": "/varrer"},
            {"text": "📈 Ver Cotas", "query": "/quotas"},
            {"text": "📖 Guia Completo", "query": "/help"}
        ]
        _dispatch_reply(chat_id, msg_out, source=source, reply_markup={"button_items": desktop_buttons}, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /quotas
    if cmd_token in ['/quotas', '/cota', '/cotas']:
        lines = [
            "<b>📈 LEDGER DE COTAS E LIMITES DOS AGENTES DESKTOP</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        try:
            from bot_engine import desktop_orchestrator
            dash = desktop_orchestrator.get_orchestrator_dashboard()
            lines.append(f"• <b>Data do Ledger:</b> <code>{dash.get('date')}</code>")
            lines.append(f"• <b>Total de Invocações Hoje:</b> <code>{dash.get('total_invocations_today', 0)}</code>\n")
            for ag in dash.get("agents", []):
                st = ag.get("status", "unknown").upper()
                lines.append(
                    f"• <b>{ag['name']}:</b> <code>{st}</code>\n"
                    f"  Modelo: <code>{ag['model']}</code> | Processos ativos: <code>{ag.get('running_processes', 0)}</code>\n"
                    f"  Execuções: <b>{ag.get('successful_today', 0)}</b> sucesso | <b>{ag.get('failed_today', 0)}</b> falhas\n"
                )
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("<i>Fallback inteligente ativado automaticamente em caso de 429 ou esgotamento.</i>")
        except Exception as qe:
            lines.append(f"⚠️ Erro ao carregar cotas: <code>{qe}</code>")
        msg_out = "\n".join(lines)
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /aprovacoes or /otp
    if cmd_token in ['/aprovacoes', '/aprovacao', '/otp']:
        lines = [
            "<b>🔒 CENTRAL DE APROVAÇÕES EXTERNAS & OTPs</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        try:
            approvals_file = WORKSPACE_ROOT / "memory" / "cowork" / "pending_approvals.json"
            approvals = []
            if approvals_file.exists():
                try:
                    data = json.loads(approvals_file.read_text(encoding="utf-8"))
                    approvals = data if isinstance(data, list) else data.get("approvals", [])
                except Exception: pass

            pendings = [a for a in approvals if a.get("status") == "pending"]
            recent_resolved = [a for a in approvals if a.get("status") == "approved"][-3:]

            lines.append(f"• <b>Pendentes:</b> <code>{len(pendings)}</code> | <b>Total no Histórico:</b> <code>{len(approvals)}</code>\n")
            if not pendings:
                lines.append("✅ <i>Nenhuma aprovação externa pendente no momento.</i>\n")
            else:
                lines.append("<b>Aprovações Aguardando Cliente:</b>")
                for p in pendings:
                    rem_txt = ""
                    if p.get("expires_at"):
                        try:
                            exp_dt = datetime.datetime.fromisoformat(p["expires_at"].replace("Z", "+00:00"))
                            rem_min = max(0, int((exp_dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 60))
                            rem_txt = f" | Expira em: <b>{rem_min} min</b>"
                        except Exception: pass
                    lines.append(
                        f"• <b>{p.get('project_name', 'Projeto')}</b> ({p.get('client_name', 'Cliente')} - <code>{p.get('client_phone')}</code>)\n"
                        f"  Item: <i>{p.get('resource_type', 'Autenticação')}</i>{rem_txt}"
                    )
            if recent_resolved:
                lines.append("\n<b>Últimas Validações Concluídas:</b>")
                for r in recent_resolved:
                    lines.append(f"• ✅ <b>{r.get('project_name')}:</b> Código <code>{r.get('received_code')}</code>")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("<i>Quando o cliente responder no WhatsApp, o Sentinel processa instantaneamente.</i>")
        except Exception as ape:
            lines.append(f"⚠️ Erro ao consultar aprovações: <code>{ape}</code>")
        msg_out = "\n".join(lines)
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /services or /pm2
    if cmd_token in ['/services', '/pm2', '/processos']:
        if tool_executor:
            res = tool_executor.execute_tool('exec_command', {'cmd': 'pm2 status'})
            msg_out = _format_tool_result_html('exec_command', res)
        else:
            msg_out = "⚠️ tool_executor não disponível."
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, ['exec_command'])
        return

    # Direct command: /start
    if cmd_token == '/start':
        msg_out = (
            f"Olá, <b>{first_name}</b>! 👋\n\n"
            "Sou o <b>Co-piloto Autônomo AXION</b>, motorizado pelo <b>Xiaomi Mimo</b>.\n\n"
            "⚡ <b>Modo:</b> Arquitetura Brain/Multi-Channel (Telegram & WhatsApp)\n"
            "🧠 <b>Brain API:</b> <code>http://127.0.0.1:8765</code>\n\n"
            "Basta me enviar qualquer pedido em texto livre!"
        )
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', msg_out, metadata={'command': cmd_token, 'task_completed': True})
        _mark_request_done(request_id, msg_out, [])
        return

    # Acquire per-chat lock to serialize concurrent messages from the same user (FIFO)
    canonical_lock_id = message_store.normalize_chat_id(chat_id) if message_store else chat_id
    chat_lock = _CHAT_LOCKS.get_lock(canonical_lock_id)
    acquired = chat_lock.acquire(timeout=120.0)
    if not acquired:
        print(f"[Brain] Timeout aguardando chat_lock para {chat_id} (req {request_id})")
        _dispatch_reply(chat_id, "⏳ Seu pedido anterior ainda está sendo processado. Por favor, aguarde alguns instantes.", source=source, is_admin=is_admin)
        _mark_request_error(request_id, "Timeout aguardando lock do chat")
        return

    try:
        # Progress tracking message (Telegram only)
        prog_msg_id = None
        step_lines = []
        if not is_whatsapp and source != 'test' and not str(chat_id).startswith('test'):
            resume_label = f' (retomando passo {resume_context["step_idx"]})' if resume_context else ''
            prog_msg_id = _tg_send(chat_id, f'⚙️ <b>Agente iniciado</b>{resume_label} — analisando seu pedido...')
            _store_progress_msg_id(request_id, prog_msg_id)
            step_lines = [f'⚙️ <b>Agente iniciado</b>{resume_label} — analisando seu pedido...']

        is_final_dispatched = [False]
        wa_msg_key = [None]
        wa_last_sent_text = [""]
        wa_last_edit_time = [0.0]
        step_num = [0]
        prog_lines_wa = []
        wa_state_lock = threading.Lock()

        def on_step(sn, step_type, description):
            step_num[0] = sn
            _add_request_step(request_id, sn, step_type, description)
            icons = {'think': '🧠', 'tool': '⚡', 'result': '📊', 'goal_check': '🎯', 'done': '✅', 'error': '❌'}
            icon = icons.get(step_type, '•')
            import re as _re
            clean_desc = _re.sub(r'<[^>]+>', '', description)

            if not is_whatsapp and prog_msg_id:
                step_lines.append(f'{icon} <b>Passo {sn}:</b> {html.escape(clean_desc)}')
                visible_lines = step_lines[:1] + step_lines[-7:] if len(step_lines) > 8 else step_lines
                _tg_edit(chat_id, prog_msg_id, '\n'.join(visible_lines))
                _tg_typing(chat_id)
            elif is_whatsapp:
                with wa_state_lock:
                    if is_final_dispatched[0]:
                        return
                    current_key = wa_msg_key[0]
                    last_edit = wa_last_edit_time[0]
                    last_text = wa_last_sent_text[0]

                now = time.monotonic()
                prog_lines_wa.append(f"{icon} *Passo {sn}:* {clean_desc}")
                visible_wa = prog_lines_wa[:1] + prog_lines_wa[-5:] if len(prog_lines_wa) > 6 else prog_lines_wa
                progress_text = "⚙️ *Executando tarefa no ambiente...*\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(visible_wa)
                if not current_key:
                    res = _dispatch_reply(chat_id, progress_text, source=source, is_admin=is_admin)
                    if isinstance(res, dict) and res.get("success"):
                        with wa_state_lock:
                            wa_msg_key[0] = res.get("key") or res.get("messageId")
                            wa_last_sent_text[0] = progress_text
                            wa_last_edit_time[0] = now
                elif now - last_edit >= 1.5:
                    if progress_text != last_text:
                        with wa_state_lock:
                            wa_last_sent_text[0] = progress_text
                            wa_last_edit_time[0] = now
                        _dispatch_reply(chat_id, progress_text, source=source, is_admin=is_admin, edit_key=current_key)

        def on_checkpoint(step_idx, messages, tools_executed, completed_steps):
            """Persists mid-execution state to disk for crash recovery."""
            if task_id and task_queue:
                try:
                    task_queue.checkpoint_task(
                        task_id, step_idx, messages,
                        tools_executed, completed_steps, chat_id
                    )
                except Exception as cp_err:
                    print(f'[Brain] checkpoint error for task {task_id}: {cp_err}')

        # Save message to message_store
        if message_store:
            message_store.save_message(chat_id, 'incoming', message, user_info={'username': username, 'first_name': first_name})

        # Prepare prompt for LLM (Contextual Persona via Identity Registry)
        effective_message = message
        contextual_prompt = user_profile.get("contextual_prompt") if user_profile else None
        if contextual_prompt:
            effective_message = f"{contextual_prompt}\n\nMensagem do Usuário: {message}"
        elif is_lead:
            effective_message = (
                "[CANAL WHATSAPP - MODO ATENDIMENTO E QUALIFICAÇÃO DE LEAD]:\n"
                "O usuário é um potencial cliente ou contato comercial em atendimento via WhatsApp corporativo da AXION Enterprise. "
                "Você atua como Consultor de Soluções e Inteligência Artificial da AXION. "
                "Atenda em Português do Brasil de forma simpática, profissional, concisa e acolhedora. "
                "Tire dúvidas sobre nossos serviços de tecnologia, software, IA e automação. "
                "É TERMINANTEMENTE PROIBIDO executar comandos de terminal, taskkill ou expor códigos e dados de servidores internos. "
                "Foque em qualificar a demanda do lead e convidá-lo a agendar uma conversa ou reunião comercial.\n\n"
                f"Mensagem do Lead: {message}"
            )

        def _handle_first_content(sentence):
            with wa_state_lock:
                if is_final_dispatched[0]:
                    return
                current_key = wa_msg_key[0]
            if not sentence or not sentence.strip():
                return
            clean_sentence = sentence.strip()
            with _REQUESTS_LOCK:
                if request_id in _ACTIVE_REQUESTS:
                    _ACTIVE_REQUESTS[request_id]['first_content'] = clean_sentence
                    try:
                        (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(_ACTIVE_REQUESTS[request_id], ensure_ascii=False, default=str), encoding='utf-8')
                    except: pass
            if source == 'test' or str(chat_id).startswith('test'):
                print(f"[Brain Test] >> First Content capturado: \"{clean_sentence[:80]}...\"")
                return
            if is_whatsapp:
                print(f"[Brain] >> First Content despachado para WhatsApp ({chat_id}): \"{clean_sentence[:60]}...\"")
                if current_key:
                    res = _dispatch_reply(chat_id, clean_sentence, source=source, is_admin=is_admin, edit_key=current_key)
                    if not (isinstance(res, dict) and res.get("success")):
                        res = _dispatch_reply(chat_id, clean_sentence, source=source, is_admin=is_admin)
                else:
                    res = _dispatch_reply(chat_id, clean_sentence, source=source, is_admin=is_admin)

                if isinstance(res, dict) and res.get("success"):
                    with wa_state_lock:
                        wa_msg_key[0] = res.get("key") or res.get("messageId") or current_key
                        wa_last_sent_text[0] = clean_sentence
                        wa_last_edit_time[0] = time.monotonic()
            elif not is_whatsapp and prog_msg_id:
                print(f"[Brain] >> First Content atualizado no Telegram ({chat_id})")
                step_lines[0] = f'💬 <i>"{html.escape(clean_sentence)}"</i>\n━━━━━━━━━━━━━━━━━━━━━━'
                visible_lines = step_lines[:1] + step_lines[-7:] if len(step_lines) > 8 else step_lines
                _tg_edit(chat_id, prog_msg_id, '\n'.join(visible_lines))

        def _handle_stream_update(accumulated_text):
            with wa_state_lock:
                if is_final_dispatched[0]:
                    return
                current_key = wa_msg_key[0]
                last_edit = wa_last_edit_time[0]
                last_text = wa_last_sent_text[0]
            if not accumulated_text or not accumulated_text.strip():
                return
            clean_accum = accumulated_text.strip()
            if source == 'test' or str(chat_id).startswith('test'):
                with _REQUESTS_LOCK:
                    if request_id in _ACTIVE_REQUESTS:
                        _ACTIVE_REQUESTS[request_id]['result_html'] = clean_accum
            if is_whatsapp and current_key:
                now = time.monotonic()
                # Throttling de segurança Meta: espaça edições em tempo real em no mínimo 1.2s
                if now - last_edit < 1.2:
                    return
                if clean_accum != last_text:
                    with wa_state_lock:
                        wa_last_sent_text[0] = clean_accum
                        wa_last_edit_time[0] = now
                    _dispatch_reply(chat_id, clean_accum, source=source, is_admin=is_admin, edit_key=current_key)
            elif not is_whatsapp and prog_msg_id:
                step_lines[0] = f'💬 <i>"{html.escape(clean_accum[:180])}..."</i>\n━━━━━━━━━━━━━━━━━━━━━━'
                visible_lines = step_lines[:1] + step_lines[-7:] if len(step_lines) > 8 else step_lines
                _tg_edit(chat_id, prog_msg_id, '\n'.join(visible_lines))

        # Run the agent with hardened constraints and dynamic model routing
        try:
            allow_tools = not is_lead
            max_steps = 1 if is_lead else 6
            chosen_tier = user_profile.get("default_tier", "pro") if user_profile else ("flash" if is_lead else "pro")
            target_model = getattr(autonomous_agent, 'OPENROUTER_FALLBACK_MODEL', 'xiaomi/mimo-v2.6-flash') if chosen_tier == "flash" else getattr(autonomous_agent, 'OPENROUTER_MODEL', 'xiaomi/mimo-v2.6-pro')

            result = autonomous_agent.run_autonomous_turn(
                effective_message, chat_id,
                on_status_update=(lambda _: _tg_typing(chat_id)) if (not is_whatsapp and source != 'test' and not str(chat_id).startswith('test')) else None,
                on_step_update=on_step,
                resume_context=resume_context,
                on_checkpoint=on_checkpoint if task_id else None,
                allow_tools=allow_tools,
                max_steps=max_steps,
                is_lead=is_lead,
                on_first_content=_handle_first_content,
                on_stream_update=_handle_stream_update,
                intent="CHAT_ONLY" if is_lead else None,
                model=target_model
            )
            # Mark final dispatched to prevent late first content race condition
            with wa_state_lock:
                is_final_dispatched[0] = True
                final_wa_key = wa_msg_key[0]

            if len(result) == 4:
                ans_html, reply_markup, tools_used, execution_record = result
            else:
                ans_html, reply_markup, tools_used = result
                execution_record = None

            # Delete progress message on Telegram
            if not is_whatsapp and prog_msg_id:
                _tg_delete(chat_id, prog_msg_id)

            # Send final response directly to Telegram or WhatsApp (in-place edit if streamed)
            if is_whatsapp and final_wa_key:
                edit_res = _dispatch_reply(chat_id, ans_html, source=source, reply_markup=reply_markup, is_admin=is_admin, edit_key=final_wa_key)
                if not (isinstance(edit_res, dict) and edit_res.get("success")):
                    print(f"[Brain WhatsApp] Edit falhou ({edit_res}), enviando resposta como nova mensagem...")
                    _dispatch_reply(chat_id, ans_html, source=source, reply_markup=reply_markup, is_admin=is_admin)
            else:
                _dispatch_reply(chat_id, ans_html, source=source, reply_markup=reply_markup, is_admin=is_admin)
            if message_store:
                message_store.save_message(chat_id, 'outgoing', ans_html, metadata={'tools_executed': tools_used, 'task_completed': True})

            # Store in Hit Cache if suitable (no dynamic system tools used, valid text)
            if cache_key and hit_cache and not tools_used and ans_html and len(ans_html) > 40:
                btns_to_cache = reply_markup.get("button_items", []) if isinstance(reply_markup, dict) else []
                hit_cache.hit_cache.set(cache_key, {"ans_html": ans_html, "buttons": btns_to_cache}, ttl_seconds=1800)

            # Mark request + task done
            _mark_request_done(request_id, ans_html, tools_used)
            if task_id and task_queue:
                try:
                    task_queue.clear_checkpoint(task_id)
                except Exception:
                    pass

            # Feed watcher
            if execution_record and watcher:
                try:
                    scored = watcher.record_execution(execution_record, final_answer=ans_html)
                    print(f'[Watcher] {execution_record.get("execution_id","?")} → Score: {scored.get("total_score",0):.1f}/10 [{scored.get("grade","?")}]')
                except Exception as we:
                    print(f'[Watcher] Erro: {we}')

        except Exception as e:
            with wa_state_lock:
                is_final_dispatched[0] = True
                final_wa_key = wa_msg_key[0]

            import traceback
            err = traceback.format_exc()
            print(f'[Brain] Erro no request {request_id}: {err}')
            if telemetry:
                telemetry.record_error(
                    "brain_server",
                    type(e).__name__,
                    str(e),
                    exc_info=e,
                    context={"request_id": request_id, "chat_id": chat_id, "message": message[:80], "source": source},
                    severity="ERROR"
                )
            if not is_whatsapp and prog_msg_id:
                _tg_delete(chat_id, prog_msg_id)

            err_text = f'❌ <b>Erro interno do agente:</b> <code>{html.escape(str(e)[:200])}</code>' if not is_whatsapp else f'❌ *Erro interno do agente:* {str(e)[:200]}'
            if is_whatsapp and final_wa_key:
                edit_res = _dispatch_reply(chat_id, err_text, source=source, is_admin=is_admin, edit_key=final_wa_key)
                if not (isinstance(edit_res, dict) and edit_res.get("success")):
                    _dispatch_reply(chat_id, err_text, source=source, is_admin=is_admin)
            else:
                _dispatch_reply(chat_id, err_text, source=source, is_admin=is_admin)
            _mark_request_error(request_id, str(e))
    finally:
        chat_lock.release()


def _recover_interrupted_tasks():
    """On brain startup, find tasks that were running when the brain last died and resume them."""
    if not task_queue:
        return
    try:
        resumable = task_queue.get_resumable_tasks()
        if not resumable:
            print('[Brain] Nenhuma tarefa interrompida para retomar.')
            return
        print(f'[Brain] {len(resumable)} tarefa(s) interrompida(s) encontrada(s) — retomando...')
        for task in resumable:
            task_id = task.get('id')
            chat_id = task.get('chat_id')
            instruction = task.get('instruction', '')
            resume_ctx = task.get('resume_context', {})
            step_idx = resume_ctx.get('step_idx', 0)
            if not chat_id:
                print(f'[Brain] Tarefa {task_id} sem chat_id — ignorando retomada.')
                continue
            print(f'[Brain] Retomando tarefa {task_id} do passo {step_idx} para chat {chat_id}')
            # Notify user that we're resuming
            _tg_send(chat_id, (
                f'🔄 <b>Retomando tarefa interrompida</b>\n'
                f'O brain foi reiniciado e está retomando sua tarefa do passo <code>{step_idx}</code>:\n'
                f'<i>{instruction[:100]}</i>'
            ))
            req_id = f'req_{uuid.uuid4().hex[:8]}'
            _store_request(req_id, {
                'status': 'running', 'steps': [], 'chat_id': chat_id,
                'started_at': datetime.datetime.now().isoformat(),
                'task_id': task_id, 'resumed': True
            })
            _EXECUTOR.submit(
                _process_chat_request,
                req_id, chat_id, instruction, '', '',
                resume_ctx, task_id
            )
    except Exception as e:
        print(f'[Brain] Erro ao recuperar tarefas: {e}')


def _format_telemetry_html(res: dict) -> str:
    """Formats system telemetry into clean Telegram HTML."""
    if not isinstance(res, dict):
        return f"<code>{html.escape(str(res))}</code>"

    ram = res.get('ram', {})
    disk_c = res.get('c_drive') or res.get('disk_c', {})
    disk_e = res.get('e_backup_drive') or res.get('disk_e', {})
    tail_summary = res.get('tailscale_summary') or 'Disponível'

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
    return '\n'.join(lines)


def _format_tool_result_html(tool_name: str, res: dict) -> str:
    """Formats raw tool execution dictionary into clean, human-readable Telegram HTML."""
    if not isinstance(res, dict):
        return f"<code>{html.escape(str(res))}</code>"

    if tool_name == 'get_system_telemetry':
        return _format_telemetry_html(res)

    success = res.get('success', True)
    icon = '✅' if success else '❌'
    elapsed = res.get('elapsed_seconds')
    elapsed_str = f" ({elapsed}s)" if elapsed is not None else ""

    titles = {
        'run_health_check': 'Varredura de Saúde & Auto-Fix',
        'run_ssl_sentinel': 'Auditoria de Certificados SSL',
        'run_backup': 'Backup Inteligente do Sistema',
        'read_backup_log': 'Log de Execução do Backup',
        'exec_command': 'Execução de Comando no Host',
        'read_file': 'Leitura de Arquivo',
        'write_file': 'Escrita de Arquivo',
        'replace_in_file': 'Edição Cirúrgica de Arquivo',
        'search_in_files': 'Busca no Código-Fonte',
        'free_port': 'Liberação de Porta Local',
        'list_directory': 'Listagem de Diretório',
        'get_system_telemetry': 'Telemetria do Sistema',
        'vercel_deploy': 'Deploy no Vercel'
    }
    title = titles.get(tool_name, f"Ferramenta <code>{tool_name}</code>")

    msg = res.get('message')
    out_text = res.get('output') or res.get('tail') or res.get('content')
    err_text = res.get('error')
    diagnosis = res.get('diagnosis')

    lines = [f"{icon} <b>{title} concluída!</b>{elapsed_str}\n━━━━━━━━━━━━━━━━━━━━━━"]

    if msg:
        lines.append(f"{msg}\n")

    if out_text and str(out_text).strip() and str(out_text).strip() != "(nenhuma saída padrão gerada)":
        clean_out = str(out_text).strip()
        escaped_out = html.escape(clean_out[:3500])
        lines.append(f"<pre>{escaped_out}</pre>")

    if err_text:
        lines.append(f"\n⚠️ <b>Erro:</b> <code>{html.escape(str(err_text)[:500])}</code>")

    if diagnosis:
        lines.append(f"\n💡 <b>Dica de Diagnóstico:</b> <i>{html.escape(str(diagnosis))}</i>")

    if not out_text and not msg and not err_text:
        if tool_name == 'search_in_files':
            matches = res.get('matches', [])
            lines.append(f"🔍 <b>Resultados para:</b> <code>{res.get('query')}</code> ({res.get('total_matches', 0)} encontrados)")
            for m in matches[:10]:
                lines.append(f"• <code>{m.get('file')}:{m.get('line')}</code>: {html.escape(str(m.get('text', '')))}")
        elif tool_name == 'list_directory':
            items = res.get('items', [])
            lines.append(f"📁 <b>Itens em:</b> <code>{res.get('path')}</code> ({len(items)} itens)")
            for it in items[:15]:
                f_icon = "📁" if it.get('is_dir') else "📄"
                lines.append(f"{f_icon} <code>{it.get('name')}</code>")
        elif tool_name == 'vercel_deploy':
            lines.append(f"🌐 <b>URL Pública:</b> <a href=\"{res.get('url')}\">{res.get('url')}</a>")
        else:
            lines.append(f"<pre>{html.escape(json.dumps(res, ensure_ascii=False, indent=2)[:3000])}</pre>")

    return '\n'.join(lines)


def _process_callback(chat_id, query_text=None, action=None, username='', action_payload=None, source='telegram', is_admin=False):
    """Handles resolved button callback actions in the brain."""
    action_payload = action_payload or {}
    print(f'[Brain] Callback ({source}): action={action}, query={query_text}, chat={chat_id}')

    if action == 'task:list':
        if task_queue:
            tasks = task_queue.list_tasks(limit=10)
            if not tasks:
                _dispatch_reply(chat_id, '📋 <b>Fila de tarefas vazia.</b>\nUse /task add para injetar uma nova tarefa.', source=source, is_admin=is_admin)
                return
            lines = ['📋 <b>Tarefas do Workspace</b>\n━━━━━━━━━━━━━━━━━━━━━━']
            icons = {'pending': '⏳', 'running': '⚙️', 'completed': '✅', 'failed': '❌'}
            for t in tasks:
                st = t.get('status', 'pending')
                lines.append(f"{icons.get(st, '•')} <b>{t.get('title', 'Sem título')}</b>\n   ID: <code>{t.get('id')}</code> | {st}")
            _dispatch_reply(chat_id, '\n'.join(lines), source=source, is_admin=is_admin)
        else:
            _dispatch_reply(chat_id, '⚠️ task_queue não disponível.', source=source, is_admin=is_admin)

    elif action == 'telemetry':
        if tool_executor:
            res = tool_executor.get_system_telemetry()
            _dispatch_reply(chat_id, _format_telemetry_html(res), source=source, is_admin=is_admin)
        else:
            _dispatch_reply(chat_id, '⚠️ tool_executor não disponível.', source=source, is_admin=is_admin)

    elif action == 'task:execute':
        task_id = action_payload.get('task_id')
        if task_queue and task_id:
            _dispatch_reply(chat_id, f'⚙️ <i>Executando tarefa <code>{task_id}</code>...</i>', source=source, is_admin=is_admin)
            res = task_queue.execute_task(task_id)
            st = res.get('status', '?')
            icon = '✅' if st == 'completed' else '❌'
            out = res.get('output', '')
            _dispatch_reply(chat_id, (
                f'{icon} <b>Tarefa <code>{task_id}</code> finalizada!</b>\n'
                f'Status: <code>{st}</code>\n'
                f'<pre>{out[:2500]}</pre>' if out else f'{icon} <b>Tarefa <code>{task_id}</code></b>: {st}'
            ), source=source, is_admin=is_admin)

    elif action == 'task:delete':
        task_id = action_payload.get('task_id')
        if task_queue and task_id:
            task_queue.delete_task(task_id)
        _dispatch_reply(chat_id, '🗑️ <b>Tarefa cancelada.</b>', source=source, is_admin=is_admin)

    elif action and action.startswith('tentacle:'):
        parts = action.split(':')
        subact = parts[1] if len(parts) > 1 else ''
        if subact == 'silence':
            key = parts[2] if len(parts) > 2 else 'alert'
            hours = float(parts[3]) if len(parts) > 3 else 2.0
            if tentacles:
                tentacles.silence_key(key, hours)
            _dispatch_reply(chat_id, f'🔕 <b>Alerta <code>{key}</code> silenciado por {hours}h.</b>', source=source, is_admin=is_admin)

    elif action and action.startswith('tool:'):
        raw_tool = action.split('tool:')[1]
        parts = raw_tool.split(':')
        tool_name = parts[0]
        tool_args = {k: v for k, v in action_payload.items() if k not in ['action', 'title']}
        if len(parts) > 1 and tool_name == 'run_backup' and 'backup_type' not in tool_args:
            tool_args['backup_type'] = parts[1]
        if tool_executor:
            _dispatch_reply(chat_id, f'⚙️ <i>Executando: <code>{tool_name}</code>...</i>', source=source, is_admin=is_admin)
            res = tool_executor.execute_tool(tool_name, tool_args)
            formatted_res = _format_tool_result_html(tool_name, res)
            _dispatch_reply(chat_id, formatted_res, source=source, is_admin=is_admin)

    elif action == 'desktop:refresh':
        try:
            from bot_engine import desktop_watcher
            status_data = desktop_watcher.get_desktop_watcher_status()
            notified = status_data.get("recent_alerts", [])
            lines = [
                '🖥️ <b>Painel de Agentes Desktop — AXION Enterprise</b>',
                '━━━━━━━━━━━━━━━━━━━━━━',
                '• <b>Antigravity:</b> 🟢 Ativo (Sessões & Background Tasks)',
                '• <b>Codex:</b> 🟢 Ativo (Workspaces & Active Tasks)',
                '• <b>OpenCode:</b> 🟢 Ativo (Active Tasks)',
                f'• <b>Tarefas Notificadas:</b> <code>{status_data.get("total_monitored_finished", 0)}</code>',
                '━━━━━━━━━━━━━━━━━━━━━━',
                '<b>Últimas Tarefas Finalizadas:</b>'
            ]
            if not notified:
                lines.append('• <i>Nenhuma tarefa finalizada recentemente.</i>')
            else:
                for t in notified[:5]:
                    icon = '✅' if t.get('status') == 'completed' else '❌'
                    time_str = (t.get('notified_at') or '')[11:16]
                    lines.append(f"• {icon} <b>[{t.get('agent', 'Agente')}]</b> <code>{t.get('title', t.get('id', ''))}</code> ({time_str})")
            lines.append('━━━━━━━━━━━━━━━━━━━━━━\n<i>Notificações proativas enviadas ao CEO Executive Operator.</i>')
            buttons = [
                [
                    {"text": "🔄 Atualizar", "callback_data": "desktop:refresh"},
                    {"text": "🔍 Varrer Agora", "callback_data": "desktop:scan"}
                ]
            ]
            _dispatch_reply(chat_id, '\n'.join(lines), reply_markup={"inline_keyboard": buttons}, source=source, is_admin=is_admin)
        except Exception as e:
            _dispatch_reply(chat_id, f'⚠️ Erro ao atualizar painel desktop: <code>{e}</code>', source=source, is_admin=is_admin)

    elif action == 'desktop:scan':
        try:
            from bot_engine import desktop_watcher
            _dispatch_reply(chat_id, '🔍 <i>Executando varredura imediata de tarefas desktop...</i>', source=source, is_admin=is_admin)
            res = desktop_watcher.scan_and_notify_finished_tasks(send_fn=_tentacle_send)
            new_count = res.get('newly_notified_count', 0)
            _dispatch_reply(chat_id, f'✅ <b>Varredura concluída!</b>\nNovas tarefas finalizadas encontradas: <code>{new_count}</code>', source=source, is_admin=is_admin)
        except Exception as e:
            _dispatch_reply(chat_id, f'⚠️ Erro na varredura desktop: <code>{e}</code>', source=source, is_admin=is_admin)

    elif query_text:
        # AI follow-up query from button
        if message_store:
            message_store.save_message(chat_id, 'incoming', query_text, user_info={'username': username})
        req_id = f'req_{uuid.uuid4().hex[:8]}'
        _store_request(req_id, {'status': 'running', 'steps': [], 'chat_id': chat_id,
                                'started_at': datetime.datetime.now().isoformat()})
        _process_chat_request(req_id, chat_id, query_text, username, '', source=source, is_admin=is_admin)

    else:
        _dispatch_reply(chat_id, f'⚠️ Ação não reconhecida: <code>{action}</code>', source=source, is_admin=is_admin)


_PREFLIGHT_CACHE = None
_PREFLIGHT_CACHE_TIME = 0.0

def _get_preflight_data(force_refresh=False):
    global _PREFLIGHT_CACHE, _PREFLIGHT_CACHE_TIME
    now = time.time()
    if not force_refresh and _PREFLIGHT_CACHE is not None and (now - _PREFLIGHT_CACHE_TIME < 60.0):
        return _PREFLIGHT_CACHE
    try:
        import preflight_check
        data = preflight_check.run_preflight()
        import shutil
        data.setdefault('desktop_clis', {
            'codex': bool(shutil.which('codex')),
            'agy': bool(shutil.which('agy')),
            'opencode': bool(shutil.which('opencode'))
        })
        _PREFLIGHT_CACHE = data
        _PREFLIGHT_CACHE_TIME = now
        return data
    except Exception as e:
        if _PREFLIGHT_CACHE is not None:
            return _PREFLIGHT_CACHE
        return {"error": str(e), "tools": {}, "auth": {}, "all_required_met": False}

def _get_drive_status():
    sa_file = WORKSPACE_ROOT / "credentials" / "google_service_account.json"
    if sa_file.exists():
        try:
            data = json.loads(sa_file.read_text(encoding='utf-8'))
            email = data.get('client_email', '')
            proj = data.get('project_id', '')
            return {
                "authenticated": True,
                "type": "service_account",
                "client_email": email,
                "project_id": proj,
                "details": f"Conta de Serviço ativa: {email}"
            }
        except Exception as e:
            return {"authenticated": False, "type": "corrupted", "details": f"Arquivo JSON inválido: {e}"}
    return {"authenticated": False, "type": "none", "details": "Nenhum arquivo em credentials/google_service_account.json"}

def _save_drive_credentials(payload):
    cred_dir = WORKSPACE_ROOT / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    dest = cred_dir / "google_service_account.json"
    
    data = None
    if isinstance(payload, dict):
        if 'credentials_json' in payload:
            try:
                data = json.loads(payload['credentials_json'])
            except Exception:
                pass
        elif 'client_email' in payload:
            data = payload
        elif 'service_account' in payload and isinstance(payload['service_account'], dict):
            data = payload['service_account']
    elif isinstance(payload, str):
        try:
            data = json.loads(payload)
        except Exception:
            pass
    
    if not data or not isinstance(data, dict):
        return {"ok": False, "error": "Conteúdo JSON inválido."}
    
    if not data.get("client_email"):
        return {"ok": False, "error": "JSON não contém 'client_email' de uma Conta de Serviço válida."}
    
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    return {
        "ok": True,
        "message": f"Credenciais salvas com sucesso! ({data.get('client_email')})",
        "client_email": data.get("client_email"),
        "project_id": data.get("project_id", "")
    }

def _update_env_var(key, val):
    val = str(val).strip()
    os.environ[key] = val
    env_file = WORKSPACE_ROOT / '.env'
    lines = []
    found = False
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8', errors='ignore').splitlines():
            line_s = line.strip()
            if line_s and not line_s.startswith('#') and '=' in line_s:
                k, _ = line_s.split('=', 1)
                if k.strip() == key:
                    lines.append(f"{key}={val}")
                    found = True
                    continue
            lines.append(line)
    if not found:
        lines.append(f"{key}={val}")
    env_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


class BrainHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # suppress default logging
        pass
    
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
    
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)
    
    def do_POST(self):
        try:
            body = self._read_body()
            path = self.path.rstrip('/')
            if path == '/v1/chat':
                chat_id = body.get('chat_id')
                message = body.get('message', '')
                username = body.get('username', '')
                first_name = body.get('first_name', '')
                source = body.get('source', 'telegram')
                is_admin = bool(body.get('is_admin', False))
                is_lead = bool(body.get('is_lead', False))
                is_test = bool(body.get('test_mode', False))
                dispatch_source = 'test' if is_test else source
                request_id = 'req_' + str(uuid.uuid4())[:8]
                _store_request(request_id, {'status': 'running', 'steps': [], 'chat_id': chat_id, 'started_at': datetime.datetime.now().isoformat(), 'source': dispatch_source})
                _EXECUTOR.submit(_process_chat_request, request_id, chat_id, message, username, first_name, source=dispatch_source, is_admin=is_admin, is_lead=is_lead)
                self._send_json({'accepted': True, 'request_id': request_id})
            elif path == '/v1/tool':
                tool_name = body.get('tool_name')
                args = body.get('args', {})
                if tool_executor:
                    res = tool_executor.execute_tool(tool_name, args)
                    self._send_json({'result': res})
                else:
                    self._send_json({'error': 'tool_executor not available'}, 500)
            elif path == '/v1/chat/clear':
                chat_id = body.get('chat_id')
                if message_store and chat_id:
                    message_store.clear_chat_history(chat_id)
                self._send_json({'success': True, 'chat_id': chat_id})
            elif path == '/v1/tasks':
                if task_queue and body.get('instruction'):
                    task = task_queue.inject_task(
                        instruction=body.get('instruction'),
                        title=body.get('title'),
                        priority=body.get('priority', 'normal'),
                        source=body.get('source', 'telegram')
                    )
                    self._send_json({'task': task, 'success': True})
                else:
                    self._send_json({'task': {}, 'success': False})
            elif path == '/v1/broadcast':
                message = body.get('message')
                severity = body.get('severity', 'WARNING')
                broadcast_alert(message, severity)
                self._send_json({'sent': 1})
            elif path == '/v1/callback':
                chat_id = body.get('chat_id')
                token = body.get('token', '')
                username = body.get('username', '')
                msg_obj = body.get('message', {})

                print(f"[Brain] POST /v1/callback: chat_id={chat_id}, token={token}, user=@{username}")

                # Resolve button token → action_payload via dynamic_keyboard
                action_payload = None
                if dynamic_keyboard and token:
                    try:
                        action_payload = dynamic_keyboard.resolve_token(token)
                    except Exception as e:
                        print(f"[Brain] Erro em dynamic_keyboard.resolve_token: {e}")

                if not action_payload and dynamic_keyboard:
                    # Self-heal by button label
                    btn_text = ''
                    for row in msg_obj.get('reply_markup', {}).get('inline_keyboard', []):
                        for btn in row:
                            if btn.get('callback_data') == token:
                                btn_text = btn.get('text', '')
                                break
                    if btn_text:
                        print(f"[Brain] Tentando self-heal por label do botão: '{btn_text}'")
                        try:
                            action_payload = dynamic_keyboard.resolve_by_label(btn_text)
                        except Exception as e:
                            print(f"[Brain] Erro em dynamic_keyboard.resolve_by_label: {e}")

                if not action_payload and body.get('action'):
                    action_payload = {'action': body.get('action')}
                if not action_payload and body.get('action_payload'):
                    action_payload = body.get('action_payload')

                # Direct pattern resolution fallback
                if not action_payload and token:
                    if token.startswith('tool:'):
                        action_payload = {'action': token}
                    elif token.startswith('tentacle:'):
                        action_payload = {'action': token}
                    elif token.startswith('act:tool:'):
                        sub = token.split('act:tool:')[1]
                        action_payload = {'action': f'tool:{sub}'}
                    elif token.startswith('task:'):
                        action_payload = {'action': token}
                    elif token.startswith('act:task:'):
                        action_payload = {'action': token[4:]}

                if not action_payload:
                    print(f"[Brain] Botão não reconhecido: token='{token}'")
                    _tg_send(chat_id, f'⚠️ <b>Botão expirado ou não reconhecido.</b>\nToken: <code>{token[:20]}</code>\nUse <code>/start</code> para recarregar o menu.')
                    self._send_json({'accepted': True, 'warning': 'token_not_found'})
                    return

                action = action_payload.get('action', '')
                query_text = action_payload.get('query', '')

                print(f"[Brain] Token '{token}' resolvido -> action='{action}', query='{query_text[:60] if query_text else ''}'")

                source = body.get('source', 'whatsapp' if ('@' in str(chat_id)) else 'telegram')
                is_admin = bool(body.get('is_admin', False))
                _EXECUTOR.submit(_process_callback, chat_id, query_text, action, username, action_payload, source, is_admin)
                self._send_json({'accepted': True})


            elif '/execute' in path and '/v1/tasks/' in path:
                task_id = path.split('/v1/tasks/')[1].split('/execute')[0]
                if task_queue:
                    res = task_queue.execute_task(task_id)
                    self._send_json({'result': res})
                else:
                    self._send_json({'error': 'task_queue not available'}, 500)
            elif path == '/v1/whatsapp/send':
                res = _wa_bridge_call('/whatsapp/send', data=body, method='POST')
                status_code = 200 if res.get('success') else (403 if res.get('blocked_by_anti_ban') else 400)
                self._send_json(res, status=status_code)
            elif path == '/v1/desktop/scan':
                try:
                    from bot_engine import desktop_watcher
                    res = desktop_watcher.scan_and_notify_finished_tasks(send_fn=_tentacle_send)
                    self._send_json({"success": True, "result": res})
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/desktop/cli':
                agent = body.get('agent', '').lower()
                prompt = body.get('prompt', '')
                subcmd = body.get('subcommand', '')
                extra_args = body.get('extra_args', '')
                timeout = int(body.get('timeout', 120))
                try:
                    from bot_engine import tool_executor
                    if 'codex' in agent:
                        res = tool_executor.run_codex_cli(prompt=prompt, subcommand=subcmd or 'exec', extra_args=extra_args, timeout=timeout)
                    elif 'antigravity' in agent or 'agy' in agent:
                        res = tool_executor.run_antigravity_cli(prompt=prompt, subcommand=subcmd or 'print', extra_args=extra_args, timeout=timeout)
                    elif 'opencode' in agent:
                        res = tool_executor.run_opencode_cli(prompt=prompt, subcommand=subcmd or 'run', extra_args=extra_args, timeout=timeout)
                    else:
                        res = {"success": False, "error": f"Agente desconhecido: '{agent}'. Suportados: codex, antigravity, opencode."}
                    self._send_json(res)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/desktop/dispatch':
                task_desc = body.get('task_description') or body.get('prompt', '')
                pref_agent = body.get('preferred_agent')
                timeout = int(body.get('timeout', 180))
                try:
                    from bot_engine import desktop_orchestrator
                    res = desktop_orchestrator.dispatch_task_to_desktop_agent(
                        task_description=task_desc,
                        preferred_agent=pref_agent,
                        timeout=timeout
                    )
                    self._send_json(res)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/approval/resolved':
                appr_id = body.get('approval_id')
                proj = body.get('project_name')
                client_phone = body.get('client_phone')
                code = body.get('code')
                print(f"[Brain] POST /v1/approval/resolved: id={appr_id}, projeto={proj}, code={code}")
                try:
                    from bot_engine import client_approval
                    if appr_id and code:
                        client_approval.submit_approval_code(appr_id, code)
                    client_approval._log_approval_to_journal("RESOLVIDO_VIA_HOOK", appr_id or "", proj or "", client_phone or "", "OTP/Aprovação", f"Código: {code}")
                except Exception as je:
                    print(f"[Brain] Erro ao registrar aprovação no diário: {je}")
                self._send_json({"success": True})
            elif path == '/api/whatsapp/pair':
                phone = body.get('number', '')
                res = _wa_bridge_call('/pair', data={'number': phone}, method='POST')
                self._send_json(res)
            elif path in ('/api/whatsapp/start', '/api/whatsapp/restart'):
                try:
                    subprocess.run(['pm2', 'restart', 'axion-whatsapp-bridge'], capture_output=True, timeout=5)
                    self._send_json({'ok': True, 'message': 'WhatsApp Bridge reiniciado via PM2.'})
                except Exception as e:
                    self._send_json({'ok': False, 'error': str(e)})
            elif path == '/api/whatsapp/mode':
                mode = body.get('mode', 'monitor')
                _update_env_var('WHATSAPP_OPERATIONAL_MODE', mode)
                _wa_bridge_call('/mode', data={'mode': mode}, method='POST')
                self._send_json({'ok': True, 'mode': mode, 'message': f'Modo WhatsApp alterado para {mode.upper()}'})
            elif path == '/api/oauth/github':
                token = body.get('token', '').strip()
                if token:
                    _update_env_var('GITHUB_TOKEN', token)
                    global _PREFLIGHT_CACHE
                    _PREFLIGHT_CACHE = None
                    self._send_json({'ok': True, 'authenticated': True, 'message': 'Token GitHub salvo com sucesso!'})
                else:
                    import shutil
                    gh_bin = shutil.which('gh')
                    if gh_bin:
                        try:
                            import queue
                            p = subprocess.Popen([gh_bin, 'auth', 'login', '--web'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
                            q = queue.Queue()
                            threading.Thread(target=lambda: [q.put(l) for l in iter(p.stderr.readline, '')], daemon=True).start()
                            code = None
                            t0 = time.time()
                            while time.time() - t0 < 3.5:
                                try:
                                    line = q.get(timeout=0.3)
                                    m = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4})', line)
                                    if m:
                                        code = m.group(1)
                                        break
                                except Exception:
                                    pass
                            self._send_json({'ok': True, 'url': 'https://github.com/login/device', 'code': code})
                        except Exception as ge:
                            self._send_json({'ok': False, 'error': str(ge), 'url': 'https://github.com/settings/tokens/new?scopes=repo,read:org&description=AgentWorkspaceOS'})
                    else:
                        self._send_json({
                            'ok': False,
                            'error': 'gh CLI não instalado no servidor. Utilize a opção de Token Pessoal (PAT) abaixo.',
                            'url': 'https://github.com/settings/tokens/new?scopes=repo,read:org&description=AgentWorkspaceOS',
                            'action': 'use_token'
                        })
            elif path == '/api/oauth/vercel':
                token = body.get('token', '').strip()
                if token:
                    _update_env_var('VERCEL_TOKEN', token)
                    _PREFLIGHT_CACHE = None
                    self._send_json({'ok': True, 'authenticated': True, 'message': 'Token Vercel salvo com sucesso!'})
                else:
                    import shutil
                    vercel_bin = shutil.which('vercel')
                    if vercel_bin:
                        self._send_json({'ok': True, 'url': 'https://vercel.com/login'})
                    else:
                        self._send_json({
                            'ok': False,
                            'error': 'Vercel CLI não instalada no servidor. Insira seu VERCEL_TOKEN diretamente abaixo.',
                            'url': 'https://vercel.com/account/tokens',
                            'action': 'use_token'
                        })
            elif path == '/api/drive/credentials':
                res = _save_drive_credentials(body)
                status_code = 200 if res.get('ok') else 400
                self._send_json(res, status=status_code)
            elif path == '/api/drive/sync':
                drive_script = WORKSPACE_ROOT / 'scripts' / 'google_drive_sync.py'
                try:
                    proc = subprocess.run([sys.executable, str(drive_script), '--sync'], capture_output=True, text=True, timeout=60)
                    try:
                        res = json.loads(proc.stdout)
                    except Exception:
                        res = {'ok': True, 'output': proc.stdout.strip() or proc.stderr.strip()}
                    self._send_json(res)
                except Exception as e:
                    self._send_json({'ok': False, 'error': str(e)})
            elif path in ('/api/config', '/api/config/env'):
                KEY_NORM = {
                    'github_token': 'GITHUB_TOKEN',
                    'vercel_token': 'VERCEL_TOKEN',
                    'cloudflare_token': 'CLOUDFLARE_API_TOKEN',
                    'cloudflare_api_token': 'CLOUDFLARE_API_TOKEN',
                    'groq_api_key': 'GROQ_API_KEY',
                    'whatsapp_pairing_number': 'WHATSAPP_PAIRING_NUMBER',
                    'whatsapp_admin_number': 'WHATSAPP_ADMIN_NUMBER',
                }
                updates = body.get('env', body)
                cfg_updates = {}
                for k, v in updates.items():
                    val = str(v).strip()
                    if val and not val.startswith('***') and '...' not in val:
                        norm_k = KEY_NORM.get(k.lower(), k)
                        _update_env_var(norm_k, val)
                        if k in ('organization', 'git', 'deployment', 'google_drive'):
                            cfg_updates[k] = v
                if cfg_updates:
                    cfg_file = WORKSPACE_ROOT / 'workspace.config.json'
                    try:
                        existing_cfg = json.loads(cfg_file.read_text(encoding='utf-8')) if cfg_file.exists() else {}
                        existing_cfg.update(cfg_updates)
                        cfg_file.write_text(json.dumps(existing_cfg, indent=2, ensure_ascii=False), encoding='utf-8')
                    except Exception as ce:
                        print(f"[Brain] Erro ao salvar workspace.config.json: {ce}")
                _PREFLIGHT_CACHE = None
                self._send_json({'ok': True, 'message': 'Configurações salvas com sucesso!'})
            elif path == '/api/services/restart':
                svc = body.get('service', 'all')
                try:
                    target = 'all' if svc == 'all' else svc
                    subprocess.run(['pm2', 'restart', target], capture_output=True, timeout=5)
                    self._send_json({'ok': True, 'message': f'Serviço ({svc}) reiniciado com sucesso!'})
                except Exception as e:
                    self._send_json({'ok': False, 'error': str(e)})
            else:
                self._send_json({'error': 'Not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def do_GET(self):
        try:
            path = self.path.split('?')[0].rstrip('/')
            if path in ('', '/', '/dashboard', '/setup', '/index.html', '/dashboard.html', '/setup.html'):
                dash_file = WORKSPACE_ROOT / 'scripts' / 'setup_dashboard.html'
                if dash_file.exists():
                    body = dash_file.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self._cors()
                    self.end_headers()
                    self.wfile.write(body)
                    return
                else:
                    self._send_json({'error': 'setup_dashboard.html not found'}, 404)
                    return
            elif path == '/api/whatsapp/status':
                res = _wa_bridge_call('/status', method='GET')
                self._send_json(res)
                return
            elif path in ('/api/whatsapp/qr', '/api/whatsapp/pairing-code'):
                res = _wa_bridge_call('/status', method='GET')
                self._send_json({
                    'qr_image': res.get('lastQrImage'),
                    'qr_raw': res.get('lastQrRaw'),
                    'pairing_code': res.get('pairingCode'),
                    'pairing_number': res.get('pairingNumber'),
                    'connected_number': res.get('connectedNumber'),
                    'status': res.get('status', 'offline'),
                    'message': res.get('message', '')
                })
                return
            elif path == '/api/drive/status':
                self._send_json(_get_drive_status())
                return
            elif path == '/api/config':
                cfg = {}
                cfg_file = WORKSPACE_ROOT / 'workspace.config.json'
                if cfg_file.exists():
                    try:
                        cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
                    except Exception:
                        pass
                env_file = WORKSPACE_ROOT / '.env'
                env_data = {}
                if env_file.exists():
                    for line in env_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            val = v.strip().strip("'\"")
                            if any(s in k.lower() for s in ('key', 'secret', 'password', 'token')):
                                masked = val[:6] + '...' + val[-4:] if len(val) > 12 else ('******' if val else '')
                                env_data[k.strip()] = masked
                            else:
                                env_data[k.strip()] = val
                cfg['env'] = env_data
                self._send_json(cfg)
                return
            elif path == '/api/preflight':
                force = 'refresh=1' in self.path
                self._send_json(_get_preflight_data(force_refresh=force))
                return
            elif path == '/api/status/summary':
                uptime_seconds = time.time() - STARTUP_TIME
                wa_st = _wa_bridge_call('/status', method='GET')
                dt_count = 0
                try:
                    from bot_engine import desktop_watcher
                    dt_st = desktop_watcher.get_desktop_watcher_status()
                    dt_count = dt_st.get("total_monitored_finished", 0)
                except Exception:
                    pass
                self._send_json({
                    'brain': {'status': 'online', 'uptime': round(uptime_seconds), 'port': int(os.environ.get('BRAIN_PORT', 8765))},
                    'whatsapp': wa_st,
                    'telegram': {'configured': bool(BOT_TOKEN), 'status': 'online' if bool(BOT_TOKEN) else 'not_configured'},
                    'desktop': {'status': 'active', 'monitored_tasks': dt_count},
                    'watcher': bool(watcher),
                    'tentacles': bool(tentacles)
                })
                return
            elif path == '/v1/health':
                uptime_seconds = time.time() - STARTUP_TIME
                active_requests = sum(1 for req in _ACTIVE_REQUESTS.values() if req.get('status') == 'running')
                self._send_json({
                    "status": "ok", 
                    "uptime_seconds": uptime_seconds, 
                    "active_requests": active_requests, 
                    "tentacles": bool(tentacles), 
                    "watcher": bool(watcher),
                    "agents_md_loaded": bool((WORKSPACE_ROOT / "AGENTS.md").exists())
                })
            elif path.startswith('/v1/chat/'):
                request_id = path.split('/v1/chat/')[1]
                req = _get_request(request_id)
                if req:
                    self._send_json(req)
                else:
                    self._send_json({'error': 'Request not found'}, 404)
            elif path == '/v1/tasks':
                if task_queue:
                    self._send_json({"tasks": task_queue.list_tasks()})
                else:
                    self._send_json({"tasks": []})
            elif path == '/v1/watcher/dashboard':
                if watcher:
                    self._send_json({"html": watcher.get_dashboard_html(limit=10)})
                else:
                    self._send_json({"html": "⚠️ Watcher não disponível."})
            elif path == '/v1/cache/stats':
                if hit_cache:
                    self._send_json(hit_cache.hit_cache.get_stats())
                else:
                    self._send_json({"error": "hit_cache not loaded"}, 500)
            elif path == '/v1/watcher/stats':
                if watcher:
                    self._send_json({"stats": watcher.get_stats()})
                else:
                    self._send_json({"stats": {}})
            elif path == '/v1/telemetry':
                system_telem = tool_executor.get_system_telemetry() if tool_executor else {}
                ops_summary = telemetry.get_telemetry_summary() if telemetry else {}
                self._send_json({
                    "system": system_telem,
                    "operational": ops_summary
                })
            elif path == '/v1/telemetry/errors':
                err_list = telemetry.get_recent_errors(limit=20) if telemetry else []
                self._send_json({"errors": err_list})
            elif path == '/v1/telemetry/dashboard':
                dash_html = telemetry.format_telemetry_html() if telemetry else "⚠️ Telemetria indisponível."
                self._send_json({"html": dash_html})
            elif path == '/v1/whatsapp/status':
                res = _wa_bridge_call('/status', method='GET')
                self._send_json(res)
            elif path == '/v1/whatsapp/pairing-code':
                res = _wa_bridge_call('/pairing-code', method='GET')
                self._send_json(res)
            elif path == '/v1/whatsapp/leads':
                res = _wa_bridge_call('/leads', method='GET')
                self._send_json(res)
            elif path == '/v1/whatsapp/team':
                res = _wa_bridge_call('/team', method='GET')
                self._send_json(res)
            elif path == '/v1/desktop/status':
                try:
                    from bot_engine import desktop_watcher
                    self._send_json({"status": "ok", "telemetry": desktop_watcher.get_desktop_watcher_status()})
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/desktop/clis':
                try:
                    from bot_engine import tool_executor
                    self._send_json(tool_executor.get_desktop_clis_status())
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path in ['/v1/desktop/quotas', '/v1/desktop/orchestrator']:
                try:
                    from bot_engine import desktop_orchestrator
                    self._send_json(desktop_orchestrator.get_orchestrator_dashboard())
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/approvals':
                try:
                    from bot_engine import client_approval
                    self._send_json({"status": "ok", "approvals": client_approval.load_approvals()})
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/email/latest-otp':
                try:
                    import importlib.util
                    from pathlib import Path
                    otp_file = WORKSPACE_ROOT / "services" / "agent-email" / "otp_client.py"
                    spec = importlib.util.spec_from_file_location("axion_otp_client", otp_file)
                    otp_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(otp_mod)
                    query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                    to_filter = query.get('to', ['dev@example.com'])[0]
                    timeout = int(query.get('timeout', ['3'])[0])
                    res = otp_mod.get_latest_email_otp(recipient=to_filter, timeout_seconds=timeout)
                    self._send_json(res)
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)
            elif path == '/v1/email/inbox':
                try:
                    import importlib.util
                    from pathlib import Path
                    otp_file = WORKSPACE_ROOT / "services" / "agent-email" / "otp_client.py"
                    spec = importlib.util.spec_from_file_location("axion_otp_client", otp_file)
                    otp_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(otp_mod)
                    self._send_json(otp_mod.get_recent_emails())
                except Exception as e:
                    self._send_json({"error": str(e)}, 500)


            else:
                self._send_json({'error': 'Not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def do_DELETE(self):
        try:
            path = self.path.rstrip('/')
            if path.startswith('/v1/tasks/'):
                task_id = path.split('/v1/tasks/')[1]
                if task_queue:
                    result = task_queue.delete_task(task_id)
                    self._send_json({'success': result})
                else:
                    self._send_json({'error': 'task_queue not available'}, 500)
            else:
                self._send_json({'error': 'Not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

def main():
    _start = time.time()

    # Install global process and thread exception catchers
    if error_handlers:
        error_handlers.install_global_catchers("brain_server", broadcast_alert)

    # Start tentacles daemon
    if tentacles:
        tentacles.start_tentacles_daemon(_tentacle_send)
    
    # Start watcher daemon
    if watcher:
        try:
            watcher.start_watcher_daemon(broadcast_fn=broadcast_alert)
            print('[Brain] Watcher daemon iniciado.')
        except Exception as e:
            print(f'[Brain] Watcher não disponível: {e}')
    
    # Startup pulse
    if tentacles:
        threading.Thread(
            target=tentacles.on_startup, 
            args=(lambda cid, txt, **kw: _tg_send_full(cid, txt, reply_markup=kw.get('reply_markup')),), 
            daemon=True
        ).start()
    
    # Recover interrupted tasks (from before last brain restart)
    threading.Thread(target=_recover_interrupted_tasks, daemon=True).start()

    # Start HTTP server
    brain_host = os.environ.get('BRAIN_HOST', '0.0.0.0')
    brain_port = int(os.environ.get('BRAIN_PORT', '8765'))
    axion_env = os.environ.get('AXION_ENV', 'prod')
    server = ThreadingHTTPServer((brain_host, brain_port), BrainHandler)
    print(f'[Brain] AXION Brain API & Web Setup [{axion_env.upper()}] em http://{brain_host}:{brain_port}')
    server.serve_forever()

if __name__ == '__main__':
    main()
