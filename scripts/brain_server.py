import os
import sys
import json
import time
import uuid
import threading
import datetime
import urllib.request
import urllib.parse
import urllib.error
import http.server
from http.server import ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path('C:/workspace')
sys.path.append(str(WORKSPACE_ROOT / 'scripts'))

# Imports from bot_engine
try:
    from bot_engine import (
        autonomous_agent, tool_executor, task_queue,
        message_store, dynamic_keyboard, tentacles, watcher
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

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8994207035:AAHqnAplG1WbGfmCLaqpIlTc9muYEAPLFWs')
TG_API_BASE = f'https://api.telegram.org/bot{BOT_TOKEN}'

STARTUP_TIME = time.time()
_EXECUTOR = ThreadPoolExecutor(max_workers=8)

# Telegram API helpers
def _tg_api(method, data=None, timeout=30):
    url = f'{TG_API_BASE}/{method}'
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
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
    if not message_id:
        return
    _tg_api('editMessageText', {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True})

def _tg_delete(chat_id, message_id):
    if not message_id:
        return
    _tg_api('deleteMessage', {'chat_id': chat_id, 'message_id': message_id})

def _tg_typing(chat_id):
    _tg_api('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})

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
            try: _tg_send_full(int(cid_str), text)
            except: pass

def _tentacle_send(chat_id, text, save_local=True, reply_markup=None, **kwargs):
    _tg_send_full(chat_id, text, reply_markup=reply_markup)
    if save_local and message_store:
        try: message_store.save_message(chat_id, 'outgoing', text)
        except: pass

# Request state management
_ACTIVE_REQUESTS = {}  # request_id -> state dict
_REQUESTS_LOCK = threading.Lock()
REQUESTS_DIR = WORKSPACE_ROOT / 'memory' / 'brain' / 'requests'
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)

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

def _mark_request_error(request_id, error):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id].update({'status': 'error', 'error': error, 'finished_at': datetime.datetime.now().isoformat()})
            (REQUESTS_DIR / f'{request_id}.json').write_text(json.dumps(_ACTIVE_REQUESTS[request_id], ensure_ascii=False, default=str), encoding='utf-8')

def _store_progress_msg_id(request_id, msg_id):
    with _REQUESTS_LOCK:
        if request_id in _ACTIVE_REQUESTS:
            _ACTIVE_REQUESTS[request_id]['progress_msg_id'] = msg_id

def _process_chat_request(request_id, chat_id, message, username, first_name,
                           resume_context=None, task_id=None):
    # 1. Send initial progress message to Telegram (get message_id)
    resume_label = f' (retomando passo {resume_context["step_idx"]})' if resume_context else ''
    prog_msg_id = _tg_send(chat_id, f'⚙️ <b>Agente iniciado</b>{resume_label} — analisando seu pedido...')
    _store_progress_msg_id(request_id, prog_msg_id)
    
    step_lines = [f'⚙️ <b>Agente iniciado</b>{resume_label} — analisando seu pedido...']
    step_num = [0]
    
    def on_step(sn, step_type, description):
        step_num[0] = sn
        icons = {'think': '🧠', 'tool': '⚡', 'result': '📊', 'goal_check': '🎯', 'done': '✅', 'error': '❌'}
        icon = icons.get(step_type, '•')
        step_lines.append(f'{icon} <b>Passo {sn}:</b> {description}')
        _add_request_step(request_id, sn, step_type, description)
        _tg_edit(chat_id, prog_msg_id, '\n'.join(step_lines))
        _tg_typing(chat_id)
    
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
    
    # 2. Save message to message_store
    if message_store:
        message_store.save_message(chat_id, 'incoming', message, user_info={'username': username, 'first_name': first_name})
    
    # 3. Run the agent
    try:
        result = autonomous_agent.run_autonomous_turn(
            message, chat_id,
            on_status_update=lambda _: _tg_typing(chat_id),
            on_step_update=on_step,
            resume_context=resume_context,
            on_checkpoint=on_checkpoint if task_id else None,
        )
        if len(result) == 4:
            ans_html, reply_markup, tools_used, execution_record = result
        else:
            ans_html, reply_markup, tools_used = result
            execution_record = None
        
        # 4. Delete progress message
        _tg_delete(chat_id, prog_msg_id)
        
        # 5. Send final response directly to Telegram
        _tg_send_full(chat_id, ans_html, reply_markup=reply_markup)
        if message_store:
            message_store.save_message(chat_id, 'outgoing', ans_html, metadata={'tools_executed': tools_used})
        
        # 6. Mark request + task done, clear checkpoint
        _mark_request_done(request_id, ans_html, tools_used)
        if task_id and task_queue:
            try:
                task_queue.clear_checkpoint(task_id)
            except Exception:
                pass
        
        # 7. Feed watcher
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
        _tg_delete(chat_id, prog_msg_id)
        _tg_send(chat_id, f'❌ <b>Erro interno do agente:</b> <code>{str(e)[:200]}</code>')
        _mark_request_error(request_id, str(e))


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


def _process_callback(chat_id, query_text=None, action=None, username='', action_payload=None):
    """Handles button callback queries from the thin bot"""
    action_payload = action_payload or {}
    if action == 'task:list':
        # render task list and send directly to telegram
        pass
    elif action == 'telemetry':
        # get telemetry and send to telegram
        pass
    elif action == 'task:execute':
        task_id = action_payload.get('task_id')
        if task_queue:
            res = task_queue.execute_task(task_id)
    elif action == 'task:delete':
        task_id = action_payload.get('task_id')
        if task_queue:
            task_queue.delete_task(task_id)
        _tg_send(chat_id, f'🗑️ <b>Tarefa cancelada.</b>')
    elif action.startswith('tentacle:') if action else False:
        # silence a tentacle
        pass
    elif action and action.startswith('tool:'):
        tool_name = action.split('tool:')[1]
        tool_args = {k: v for k, v in action_payload.items() if k not in ['action', 'title']}
        if tool_executor:
            res = tool_executor.execute_tool(tool_name, tool_args)
            icon = '✅' if res.get('success') else '❌'
            _tg_send_full(chat_id, f'{icon} <b>Ferramenta <code>{tool_name}</code> executada</b>\n<pre>{json.dumps(res, ensure_ascii=False, indent=2)[:3000]}</pre>')
    elif query_text:  # AI query from button
        if message_store:
            message_store.save_message(chat_id, 'incoming', query_text, user_info={'username': username})
        req_id = 'req_' + str(uuid.uuid4())[:8]
        _store_request(req_id, {'status': 'running', 'steps': [], 'chat_id': chat_id, 'started_at': datetime.datetime.now().isoformat()})
        _process_chat_request(req_id, chat_id, query_text, username, '')

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
                request_id = 'req_' + str(uuid.uuid4())[:8]
                _store_request(request_id, {'status': 'running', 'steps': [], 'chat_id': chat_id, 'started_at': datetime.datetime.now().isoformat()})
                _EXECUTOR.submit(_process_chat_request, request_id, chat_id, message, username, first_name)
                self._send_json({'accepted': True, 'request_id': request_id})
            elif path == '/v1/tool':
                tool_name = body.get('tool_name')
                args = body.get('args', {})
                if tool_executor:
                    res = tool_executor.execute_tool(tool_name, args)
                    self._send_json({'result': res})
                else:
                    self._send_json({'error': 'tool_executor not available'}, 500)
            elif path == '/v1/tasks':
                if task_queue:
                    # task inject
                    pass
                self._send_json({'task': {}})
            elif path == '/v1/broadcast':
                message = body.get('message')
                severity = body.get('severity', 'WARNING')
                broadcast_alert(message, severity)
                self._send_json({'sent': 1})
            elif path == '/v1/callback':
                chat_id = body.get('chat_id')
                query_text = body.get('query')
                action = body.get('action')
                username = body.get('username')
                action_payload = body.get('action_payload')
                _EXECUTOR.submit(_process_callback, chat_id, query_text, action, username, action_payload)
                self._send_json({'accepted': True})
            elif '/execute' in path and '/v1/tasks/' in path:
                task_id = path.split('/v1/tasks/')[1].split('/execute')[0]
                if task_queue:
                    res = task_queue.execute_task(task_id)
                    self._send_json({'result': res})
                else:
                    self._send_json({'error': 'task_queue not available'}, 500)
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
                    "watcher": bool(watcher)
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
            elif path == '/v1/watcher/stats':
                if watcher:
                    self._send_json({"stats": watcher.get_stats()})
                else:
                    self._send_json({"stats": {}})

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
