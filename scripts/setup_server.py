#!/usr/bin/env python3
"""
Agent Workspace OS - Setup & Control Dashboard Server v2
Python ThreadingHTTPServer — zero external deps
"""

import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
import socketserver
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding="utf-8")

PORT = int(os.environ.get("SETUP_PORT", 8765))
WORKSPACE_ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREFLIGHT_SCRIPT  = os.path.join(WORKSPACE_ROOT, "scripts", "preflight_check.py")
DRIVE_SCRIPT      = os.path.join(WORKSPACE_ROOT, "scripts", "google_drive_sync.py")
CONFIG_FILE       = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
TEMPLATE_FILE     = os.path.join(WORKSPACE_ROOT, "workspace.config.template.json")
DASHBOARD_HTML    = os.path.join(os.path.dirname(__file__), "setup_dashboard.html")

_html_cache: bytes | None = None

def get_html() -> bytes:
    global _html_cache
    if _html_cache is None:
        with open(DASHBOARD_HTML, "rb") as f:
            _html_cache = f.read()
    return _html_cache

# ── helpers ──────────────────────────────────────────────────

def load_config() -> dict:
    for fp in (CONFIG_FILE, TEMPLATE_FILE):
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}

def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_preflight_data() -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, PREFLIGHT_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, text=True, timeout=15
        )
        return json.loads(proc.stdout)
    except Exception as e:
        return {"error": str(e), "tools": {}, "auth": {}}

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
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"status": "standby", "connectedNumber": None,
                "mode": "monitor", "lastQrImage": None, "recentMessages": []}

def get_whatsapp_qr() -> dict:
    try:
        req = urllib.request.Request("http://127.0.0.1:4114/api/qr")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"qr": None, "status": "standby"}

# Install command lookup — mirrors preflight_check.py TOOLS list
INSTALL_COMMANDS: dict[str, str] = {
    "python":   "winget install Python.Python.3.11",
    "node":     "winget install OpenJS.NodeJS.LTS",
    "git":      "winget install Git.Git",
    "gh":       "winget install GitHub.cli",
    "vercel":   "npm install -g vercel",
    "wrangler": "npm install -g wrangler",
}

# ── threading server ─────────────────────────────────────────

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── request handler ──────────────────────────────────────────

class SetupHandler(BaseHTTPRequestHandler):

    # ── OPTIONS ──────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET ──────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            body = get_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/preflight":
            self._json(get_preflight_data())

        elif path == "/api/whatsapp/status":
            self._json(get_whatsapp_status())

        elif path == "/api/whatsapp/qr":
            self._json(get_whatsapp_qr())

        elif path == "/api/drive/status":
            self._json(get_drive_status())

        elif path == "/api/config":
            self._json(load_config())

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    # ── POST ─────────────────────────────────────────────────
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
            except Exception as e:
                _sse(json.dumps({"line": str(e), "done": False}))
            _sse(json.dumps({"done": True}))
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
                existing = load_config()
                existing.update(body)
                save_config(existing)
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)})
            return

        self.send_response(404)
        self._cors()
        self.end_headers()

    # ── helpers ──────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # suppress per-request noise; errors still go to stderr
        pass

# ── entry point ──────────────────────────────────────────────

def run_server():
    server = ThreadedHTTPServer(("127.0.0.1", PORT), SetupHandler)
    print("=" * 60)
    print("  Agent Workspace OS - Setup & Control Dashboard v2")
    print(f"  Dashboard: http://127.0.0.1:{PORT}")
    print("=" * 60)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
