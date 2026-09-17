#!/usr/bin/env python3
"""
Agent Workspace OS - Setup & Control Dashboard Server v2.1
Python ThreadingHTTPServer — zero external deps
High-performance in-memory caching & 1-click WhatsApp Bridge lifecycle
"""

import sys
import os
import json
import subprocess
import shutil
import urllib.request
import urllib.error
import socketserver
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

from openai_proxy import get_models_list, handle_chat_completions
from telemetry_service import get_telemetry_summary, generate_trace_id, record_metric

sys.stdout.reconfigure(encoding="utf-8")

PORT = int(os.environ.get("SETUP_PORT", 8765))
BIND_ADDRESS = os.environ.get("SETUP_BIND_ADDRESS", "127.0.0.1")
WORKSPACE_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREFLIGHT_SCRIPT  = os.path.join(WORKSPACE_ROOT, "scripts", "preflight_check.py")
DRIVE_SCRIPT      = os.path.join(WORKSPACE_ROOT, "scripts", "google_drive_sync.py")
CONFIG_FILE       = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
TEMPLATE_FILE     = os.path.join(WORKSPACE_ROOT, "workspace.config.template.json")
DASHBOARD_HTML    = os.path.join(os.path.dirname(__file__), "setup_dashboard.html")
LANDING_HTML      = os.path.join(WORKSPACE_ROOT, "landing.html")

_dashboard_cache: bytes | None = None
_landing_cache: bytes | None = None
_preflight_cache: dict | None = None
_preflight_cache_time: float = 0.0
_whatsapp_process = None

def get_dashboard_html() -> bytes:
    global _dashboard_cache
    if _dashboard_cache is None:
        with open(DASHBOARD_HTML, "rb") as f:
            _dashboard_cache = f.read()
    return _dashboard_cache

def get_landing_html() -> bytes:
    global _landing_cache
    if _landing_cache is None:
        if os.path.exists(LANDING_HTML):
            with open(LANDING_HTML, "rb") as f:
                _landing_cache = f.read()
        else:
            return get_dashboard_html()
    return _landing_cache

def invalidate_html_cache() -> None:
    global _dashboard_cache, _landing_cache
    _dashboard_cache = None
    _landing_cache = None

# ── helpers ──────────────────────────────────────────────────

def sanitize_value(v: any) -> any:
    if isinstance(v, str):
        if v.startswith("{{") and v.endswith("}}"):
            return ""
        return v
    if isinstance(v, dict):
        return {k: sanitize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [sanitize_value(x) for x in v]
    return v

def redact_sensitive_values(v: any) -> any:
    sensitive = ("secret", "token", "password", "api_key", "authorization", "cookie")
    if isinstance(v, dict):
        return {k: ("[redacted]" if any(part in k.lower() for part in sensitive) else redact_sensitive_values(value)) for k, value in v.items()}
    if isinstance(v, list):
        return [redact_sensitive_values(item) for item in v]
    return sanitize_value(v)

def load_config(raw: bool = False) -> dict:
    cfg = {}
    for fp in (CONFIG_FILE, TEMPLATE_FILE):
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    break
            except Exception:
                pass
    if raw:
        return cfg
    # Return sanitized version so template placeholders {{...}} are stripped
    sanitized = redact_sensitive_values(cfg)
    # Ensure current workspace root is provided if empty
    if not sanitized.get("paths", {}).get("canonical_root"):
        if "paths" not in sanitized:
            sanitized["paths"] = {}
        sanitized["paths"]["canonical_root"] = WORKSPACE_ROOT
    return sanitized

def apply_setup_initialization(cfg: dict) -> None:
    """Create local runtime state without rewriting distribution documentation."""
    dirs = [
        "apps", "services", "packages", "docs", "memory/daily_logs",
        "memory/cowork/handoffs", "workspace/config", "workspace/inbox/messages", "workspace/memory"
    ]
    for d in dirs:
        os.makedirs(os.path.join(WORKSPACE_ROOT, d), exist_ok=True)

    tasks_file = os.path.join(WORKSPACE_ROOT, "memory", "cowork", "active_tasks.json")
    if not os.path.exists(tasks_file):
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f, indent=2)

    blackboard_file = os.path.join(WORKSPACE_ROOT, "memory", "cowork", "blackboard.json")
    if not os.path.exists(blackboard_file):
        with open(blackboard_file, "w", encoding="utf-8") as f:
            json.dump({
                "setup_completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "workspace": cfg.get("workspace", {}).get("name"),
                "status": "READY"
            }, f, indent=2)

    today_str = time.strftime("%Y-%m-%d")
    now_time = time.strftime("%H:%M:%S")
    log_file = os.path.join(WORKSPACE_ROOT, "memory", "daily_logs", f"{today_str}.md")
    workspace_name = cfg.get("workspace", {}).get("name", "Project")
    git_user = cfg.get("git", {}).get("user_name", "Developer")
    git_email = cfg.get("git", {}).get("user_email", "")
    target = cfg.get("deployment", {}).get("primary_target", "unconfigured")
    log_entry = f"\n## [{now_time}] [setup] Workspace initialized via local dashboard\n- **Workspace**: {workspace_name}\n- **Git identity configured**: {bool(git_user and git_email)}\n- **Target**: {target}\n- **Status**: setup complete.\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_preflight_data(force_refresh: bool = False) -> dict:
    global _preflight_cache, _preflight_cache_time
    now = time.time()
    if not force_refresh and _preflight_cache is not None and (now - _preflight_cache_time < 60.0):
        return _preflight_cache
    try:
        proc = subprocess.run(
            [sys.executable, PREFLIGHT_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, text=True, timeout=8
        )
        data = json.loads(proc.stdout)
        _preflight_cache = data
        _preflight_cache_time = now
        return data
    except Exception as e:
        if _preflight_cache is not None:
            return _preflight_cache
        return {"error": str(e), "tools": {}, "auth": {}, "all_required_met": False}

def get_drive_status() -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, DRIVE_SCRIPT, "--check"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, text=True, timeout=8
        )
        return json.loads(proc.stdout)
    except Exception as e:
        return {"authenticated": False, "type": "none", "details": str(e)}

def get_whatsapp_status() -> dict:
    try:
        req = urllib.request.Request("http://127.0.0.1:4114/api/status")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {
            "status": "offline",
            "connectedNumber": None,
            "mode": "monitor",
            "lastQrImage": None,
            "recentMessages": []
        }

def get_whatsapp_qr() -> dict:
    try:
        req = urllib.request.Request("http://127.0.0.1:4114/api/qr")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"qr_image": None, "qr_raw": None, "status": "offline"}

def start_whatsapp_bridge() -> dict:
    global _whatsapp_process
    # Check if already running
    try:
        req = urllib.request.Request("http://127.0.0.1:4114/api/status")
        with urllib.request.urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "status": data.get("status", "running"), "message": "Bridge já está em execução na porta 4114."}
    except Exception:
        pass

    bridge_dir = os.path.join(WORKSPACE_ROOT, "scripts", "whatsapp_bridge")
    bridge_script = os.path.join(bridge_dir, "server.js")
    node_bin = shutil.which("node") or shutil.which("node.exe")
    if not node_bin:
        return {"ok": False, "error": "Node.js não foi encontrado no PATH do sistema. Instale o Node.js primeiro."}

    # 1. Garantir que as dependências do Baileys e QRCode estão instaladas
    baileys_path = os.path.join(bridge_dir, "node_modules", "@whiskeysockets", "baileys")
    qrcode_path = os.path.join(bridge_dir, "node_modules", "qrcode")
    if not os.path.exists(baileys_path) or not os.path.exists(qrcode_path):
        npm_bin = shutil.which("npm") or shutil.which("npm.cmd")
        if not npm_bin:
            return {"ok": False, "error": "npm não foi encontrado no PATH para instalar as dependências do WhatsApp."}
        try:
            print("[SETUP] Instalando dependências do WhatsApp Bridge (npm install)...")
            proc_install = subprocess.run(
                [npm_bin, "install", "--no-audit", "--no-fund"],
                cwd=bridge_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            if proc_install.returncode != 0:
                print(f"[SETUP] Aviso ao instalar dependências: {proc_install.stderr}")
        except Exception as inst_err:
            return {"ok": False, "error": f"Falha ao instalar dependências do WhatsApp: {str(inst_err)}"}

    # Secrets are supplied only by the caller environment or a local secret manager.
    child_env = os.environ.copy()
    child_env["WHATSAPP_PORT"] = "4114"
    
    try:
        _whatsapp_process = subprocess.Popen(
            [node_bin, bridge_script],
            cwd=bridge_dir,
            env=child_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        # Poll up to 6 seconds for port 4114 to respond
        for _ in range(30):
            time.sleep(0.2)
            try:
                req = urllib.request.Request("http://127.0.0.1:4114/api/status")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    st = data.get("status", "qr_ready")
                    return {"ok": True, "status": st, "message": "Bridge WhatsApp iniciada e pronta para pareamento!"}
            except Exception:
                pass
        return {"ok": True, "status": "starting", "message": "Bridge inicializada em segundo plano."}
    except Exception as e:
        return {"ok": False, "error": f"Erro ao iniciar bridge: {str(e)}"}

def stop_whatsapp_bridge() -> dict:
    global _whatsapp_process
    if _whatsapp_process:
        try:
            _whatsapp_process.terminate()
            _whatsapp_process = None
            return {"ok": True, "message": "Bridge WhatsApp encerrada com sucesso."}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": True, "message": "Bridge não estava em execução."}

INSTALL_COMMANDS: dict[str, str] = {
    "python":   "winget install --id Python.Python.3.11 --exact --accept-source-agreements --accept-package-agreements",
    "node":     "winget install --id OpenJS.NodeJS.LTS --exact --accept-source-agreements --accept-package-agreements",
    "git":      "winget install --id Git.Git --exact --accept-source-agreements --accept-package-agreements",
    "gh":       "winget install --id GitHub.cli --exact --accept-source-agreements --accept-package-agreements",
    "vercel":   "npm install -g vercel",
    "wrangler": "npm install -g wrangler",
}

# ── threading server ─────────────────────────────────────────

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── request handler ──────────────────────────────────────────

class SetupHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        query = self.path.split("?")[1] if "?" in self.path else ""

        if path in ("/", "/index.html"):
            body = get_landing_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        elif path in ("/setup", "/dashboard", "/setup.html", "/dashboard.html"):
            body = get_dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/preflight":
            force = "refresh=1" in query
            self._json(get_preflight_data(force_refresh=force))

        elif path == "/api/whatsapp/status":
            self._json(get_whatsapp_status())

        elif path == "/api/whatsapp/qr":
            self._json(get_whatsapp_qr())

        elif path == "/api/drive/status":
            self._json(get_drive_status())

        elif path == "/api/config":
            self._json(load_config())

        elif path in ("/v1/models", "/models"):
            self._json(get_models_list())

        elif path == "/api/telemetry":
            self._json(get_telemetry_summary())

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw)
        except Exception:
            body = {}

        # ── SSE install stream ────────────────────────────────
        if path == "/api/install":
            tool_id = body.get("tool_id", "")
            cmd = INSTALL_COMMANDS.get(tool_id)
            if not cmd:
                self._json({"error": f"Unknown tool_id: {tool_id}"}, status=400)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self._cors()
            self.end_headers()

            def _sse(payload: str):
                line = f"data: {payload}\n\n"
                try:
                    self.wfile.write(line.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            try:
                proc = subprocess.Popen(
                    cmd, shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, text=True,
                    encoding="utf-8", errors="replace"
                )
                for line in proc.stdout:
                    _sse(json.dumps({"line": line.rstrip(), "done": False}))
                proc.wait()
                rc = proc.returncode
                _sse(json.dumps({"line": f"[exit code {rc}]", "done": False}))
                # Invalidate preflight cache after tool install
                get_preflight_data(force_refresh=True)
            except Exception as e:
                _sse(json.dumps({"line": str(e), "done": False}))
            _sse(json.dumps({"done": True}))
            return

        # ── OpenAI-Compatible Chat Completions ─────────────────
        if path in ("/v1/chat/completions", "/chat/completions"):
            is_stream = bool(body.get("stream", False))
            client_ip = self.client_address[0] if hasattr(self, "client_address") else "127.0.0.1"
            headers_dict = dict(self.headers)

            if is_stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Accel-Buffering", "no")
                self._cors()
                self.end_headers()

                def _stream_writer(chunk):
                    try:
                        if isinstance(chunk, str):
                            chunk = chunk.encode("utf-8")
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except Exception:
                        pass

                handle_chat_completions(body, headers_dict, client_ip=client_ip, sse_writer=_stream_writer)
                return
            else:
                res = handle_chat_completions(body, headers_dict, client_ip=client_ip)
                status_code = res.get("status", 200)
                self.send_response(status_code)
                for h_k, h_v in res.get("headers", {}).items():
                    self.send_header(h_k, h_v)
                self._cors()
                self.end_headers()
                self.wfile.write(res.get("body", b"{}"))
                return

        # ── Telemetry OpenRouter Key Save ───────────────────────
        if path == "/api/telemetry/key":
            key_val = body.get("openrouter_api_key", "").strip()
            try:
                cfg = load_config(raw=True)
                if "ai" not in cfg:
                    cfg["ai"] = {}
                cfg["ai"]["openrouter_api_key"] = key_val
                save_config(cfg)
                self._json({"ok": True, "message": "Chave OpenRouter salva com sucesso!"})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        # ── WhatsApp Start / Stop ─────────────────────────────
        if path == "/api/whatsapp/start":
            res = start_whatsapp_bridge()
            self._json(res)
            return

        if path == "/api/whatsapp/stop":
            res = stop_whatsapp_bridge()
            self._json(res)
            return

        # ── WhatsApp mode toggle ──────────────────────────────
        if path == "/api/whatsapp/mode":
            try:
                payload = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(
                    "http://127.0.0.1:4114/api/mode",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                self._json(result)
            except Exception as e:
                self._json({"ok": False, "error": str(e)})
            return

        # ── WhatsApp Install Dependencies ─────────────────────
        if path == "/api/whatsapp/install":
            bridge_dir = os.path.join(WORKSPACE_ROOT, "scripts", "whatsapp_bridge")
            npm_bin = shutil.which("npm") or shutil.which("npm.cmd")
            if not npm_bin:
                self._json({"ok": False, "error": "npm não encontrado no sistema."}, status=400)
                return
            try:
                proc = subprocess.run([npm_bin, "install", "--no-audit", "--no-fund"], cwd=bridge_dir, capture_output=True, text=True, timeout=120)
                self._json({"ok": proc.returncode == 0, "output": proc.stdout or proc.stderr})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        # ── WhatsApp Set Transcription Key ────────────────────
        if path == "/api/whatsapp/transcription-key":
            groq_key = body.get("groq_api_key", "").strip()
            try:
                cfg = load_config(raw=True)
                if "ai" not in cfg:
                    cfg["ai"] = {}
                cfg["ai"]["groq_api_key"] = groq_key
                save_config(cfg)
                stop_whatsapp_bridge()
                time.sleep(0.5)
                start_res = start_whatsapp_bridge()
                self._json({"ok": True, "message": "Chave de transcrição salva com sucesso!", "bridge": start_res})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        # ── GitHub OAuth ──────────────────────────────────────
        if path == "/api/oauth/github":
            subprocess.Popen(
                "gh auth login --web", shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._json({"started": True})
            return

        # ── Vercel OAuth ──────────────────────────────────────
        if path == "/api/oauth/vercel":
            subprocess.Popen(
                "vercel login", shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._json({"started": True})
            return

        # ── Drive sync ───────────────────────────────────────
        if path == "/api/drive/sync":
            try:
                proc = subprocess.run(
                    [sys.executable, DRIVE_SCRIPT, "--sync"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL, text=True, timeout=60
                )
                try:
                    result = json.loads(proc.stdout)
                except Exception:
                    result = {"ok": True, "output": proc.stdout.strip() or proc.stderr.strip()}
            except Exception as e:
                result = {"ok": False, "error": str(e)}
            self._json(result)
            return

        # ── Config save ──────────────────────────────────────
        if path == "/api/config":
            try:
                existing = load_config(raw=True)
                existing.update(body)
                save_config(existing)
                apply_setup_initialization(existing)
                self._json({"ok": True, "initialized": True, "message": "Workspace configurado e inicializado com sucesso!"})
            except Exception as e:
                self._json({"ok": False, "error": str(e)})
            return

        self.send_response(404)
        self._cors()
        self.end_headers()

    def _cors(self):
        origin = self.headers.get("Origin")
        if origin in {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Trace-ID, x-trace-id, X-Title, HTTP-Referer")

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass

# ── entry point ──────────────────────────────────────────────

def run_server():
    # Warm up cache in background immediately
    threading.Thread(target=get_preflight_data, daemon=True).start()
    server = ThreadedHTTPServer((BIND_ADDRESS, PORT), SetupHandler)
    print("=" * 60)
    print("  Agent Workspace OS - Setup & Control Dashboard v2.1")
    print(f"  Dashboard: http://localhost:{PORT} ou http://127.0.0.1:{PORT}")
    print("  WhatsApp Tab: http://localhost:{PORT}/#tab-whatsapp")
    print("=" * 60)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
