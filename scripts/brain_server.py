import os
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
WORKSPACE_ROOT = Path('C:/workspace')
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

def _wa_send(to: str, message: str, buttons: list = None, is_admin: bool = False, edit_key: dict | str = None):
    """Sends message directly back to WhatsApp bridge with optional interactive buttons and in-place editing"""
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
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"[Brain] Falha ao enviar resposta para WhatsApp ({to}): {e}")
        return {"error": str(e)}

def _wa_bridge_call(endpoint: str, data: dict = None, method: str = 'GET') -> dict:
    """Invokes WhatsApp Bridge HTTP API endpoints"""
    url = f"{WHATSAPP_BRIDGE_URL}{endpoint}"
    payload = json.dumps(data).encode('utf-8') if data is not None else None
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as he:
        try:
            return json.loads(he.read().decode('utf-8'))
        except Exception:
            return {"error": str(he), "status": he.code}
    except Exception as e:
        return {"error": str(e)}

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
        _mark_request_done(request_id, msg_out, [])
        return

    # Direct command: /help
    if cmd_token in ['/help', '/ajuda']:
        msg_out = (
            "<b>📖 GUIA DO CO-PILOTO AUTÔNOMO — AXION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Comandos Rápidos:</b>\n"
            "• <code>/status</code> — Telemetria do host (RAM, Disco, CPU)\n"
            "• <code>/cmd &lt;comando&gt;</code> — Executa comando direto no Windows\n"
            "• <code>/tasks</code> — Lista tarefas pendentes e ativas\n"
            "• <code>/watcher</code> — Painel de observabilidade\n"
            "• <code>/clear</code> — Limpa a memória recente da conversa\n"
            "• <code>/brain</code> — Diagnóstico de saúde do cérebro\n\n"
            "Envie qualquer instrução em linguagem natural para execução autônoma!"
        )
        _dispatch_reply(chat_id, msg_out, source=source, is_admin=is_admin)
        _mark_request_done(request_id, msg_out, [])
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
            elif is_whatsapp and not is_final_dispatched[0]:
                now = time.monotonic()
                if not wa_msg_key[0]:
                    init_text = f"⚙️ *Executando diagnóstico no ambiente...*\n{icon} *Passo {sn}:* {clean_desc}"
                    res = _dispatch_reply(chat_id, init_text, source=source, is_admin=is_admin)
                    if isinstance(res, dict) and res.get("success"):
                        wa_msg_key[0] = res.get("key") or res.get("messageId")
                        wa_last_sent_text[0] = init_text
                        wa_last_edit_time[0] = now
                elif now - wa_last_edit_time[0] >= 1.5:
                    progress_text = f"⚙️ *Executando diagnóstico no ambiente...*\n\n{icon} *Passo {sn}:* {clean_desc}"
                    if progress_text != wa_last_sent_text[0]:
                        wa_last_sent_text[0] = progress_text
                        wa_last_edit_time[0] = now
                        _dispatch_reply(chat_id, progress_text, source=source, is_admin=is_admin, edit_key=wa_msg_key[0])

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
            if is_final_dispatched[0]:
                return
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
                res = _dispatch_reply(chat_id, clean_sentence, source=source, is_admin=is_admin)
                if isinstance(res, dict) and res.get("success"):
                    wa_msg_key[0] = res.get("key") or res.get("messageId")
                    wa_last_sent_text[0] = clean_sentence
                    wa_last_edit_time[0] = time.monotonic()
            elif not is_whatsapp and prog_msg_id:
                print(f"[Brain] >> First Content atualizado no Telegram ({chat_id})")
                step_lines[0] = f'💬 <i>"{html.escape(clean_sentence)}"</i>\n━━━━━━━━━━━━━━━━━━━━━━'
                visible_lines = step_lines[:1] + step_lines[-7:] if len(step_lines) > 8 else step_lines
                _tg_edit(chat_id, prog_msg_id, '\n'.join(visible_lines))

        def _handle_stream_update(accumulated_text):
            if is_final_dispatched[0]:
                return
            if not accumulated_text or not accumulated_text.strip():
                return
            clean_accum = accumulated_text.strip()
            if is_whatsapp and wa_msg_key[0]:
                now = time.monotonic()
                # Throttling de segurança Meta: espaça edições em tempo real em no mínimo 1.2s
                if now - wa_last_edit_time[0] < 1.2:
                    return
                if clean_accum != wa_last_sent_text[0]:
                    wa_last_sent_text[0] = clean_accum
                    wa_last_edit_time[0] = now
                    _dispatch_reply(chat_id, clean_accum, source=source, is_admin=is_admin, edit_key=wa_msg_key[0])
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
                model=target_model
            )
            # Mark final dispatched to prevent late first content race condition
            is_final_dispatched[0] = True
            if len(result) == 4:
                ans_html, reply_markup, tools_used, execution_record = result
            else:
                ans_html, reply_markup, tools_used = result
                execution_record = None

            # Delete progress message on Telegram
            if not is_whatsapp and prog_msg_id:
                _tg_delete(chat_id, prog_msg_id)

            # Send final response directly to Telegram or WhatsApp (in-place edit if streamed)
            if is_whatsapp and wa_msg_key[0]:
                _dispatch_reply(chat_id, ans_html, source=source, reply_markup=reply_markup, is_admin=is_admin, edit_key=wa_msg_key[0])
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
            _dispatch_reply(chat_id, f'❌ <b>Erro interno do agente:</b> <code>{str(e)[:200]}</code>', source=source, is_admin=is_admin)
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


class BrainHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # suppress default logging
        pass
    
    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
    
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
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
                request_id = 'req_' + str(uuid.uuid4())[:8]
                _store_request(request_id, {'status': 'running', 'steps': [], 'chat_id': chat_id, 'started_at': datetime.datetime.now().isoformat(), 'source': source})
                _EXECUTOR.submit(_process_chat_request, request_id, chat_id, message, username, first_name, source=source, is_admin=is_admin, is_lead=is_lead)
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
            else:
                self._send_json({'error': 'Not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def do_GET(self):
        try:
            path = self.path.split('?')[0].rstrip('/')
            if path == '/v1/health':
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
    brain_port = int(os.environ.get('BRAIN_PORT', '8765'))
    axion_env = os.environ.get('AXION_ENV', 'prod')
    server = ThreadingHTTPServer(('127.0.0.1', brain_port), BrainHandler)
    print(f'[Brain] AXION Brain API [{axion_env.upper()}] em http://127.0.0.1:{brain_port}')
    server.serve_forever()

if __name__ == '__main__':
    main()
