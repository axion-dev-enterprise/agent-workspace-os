#!/usr/bin/env python3
"""
Preflight Environment Diagnostic Tool (High-Performance Concurrent)
Agent Workspace OS - Diagnostic and CLI Verification Engine
"""

import sys
import os
import shutil
import subprocess
import json
import platform
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

TOOLS = [
    {
        "id": "python",
        "name": "Python 3",
        "cmd": "python --version",
        "required": True,
        "install_win": "winget install --id Python.Python.3.11 --exact --accept-source-agreements --accept-package-agreements",
        "url": "https://www.python.org/downloads/"
    },
    {
        "id": "node",
        "name": "Node.js (LTS)",
        "cmd": "node -v",
        "required": True,
        "install_win": "winget install --id OpenJS.NodeJS.LTS --exact --accept-source-agreements --accept-package-agreements",
        "url": "https://nodejs.org/"
    },
    {
        "id": "git",
        "name": "Git",
        "cmd": "git --version",
        "required": True,
        "install_win": "winget install --id Git.Git --exact --accept-source-agreements --accept-package-agreements",
        "url": "https://git-scm.com/"
    },
    {
        "id": "gh",
        "name": "GitHub CLI (gh)",
        "cmd": "gh --version",
        "required": False,
        "install_win": "winget install --id GitHub.cli --exact --accept-source-agreements --accept-package-agreements",
        "url": "https://cli.github.com/"
    },
    {
        "id": "vercel",
        "name": "Vercel CLI",
        "cmd": "vercel --version",
        "required": False,
        "install_win": "npm install -g vercel",
        "url": "https://vercel.com/cli"
    },
    {
        "id": "wrangler",
        "name": "Cloudflare Wrangler CLI",
        "cmd": "wrangler --version",
        "required": False,
        "install_win": "npm install -g wrangler",
        "url": "https://developers.cloudflare.com/workers/wrangler/install-and-update/"
    }
]

def check_tool(tool):
    binary_name = tool["id"]
    path = shutil.which(binary_name) or shutil.which(f"{binary_name}.cmd") or shutil.which(f"{binary_name}.exe")
    if not path:
        return tool["id"], False, None
    try:
        proc = subprocess.run(
            tool["cmd"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=2
        )
        out = (proc.stdout.strip() or proc.stderr.strip()).split('\n')[0].strip()
        return tool["id"], True, out if out else "Instalado"
    except Exception:
        return tool["id"], True, "Instalado"

def check_auth_statuses():
    statuses = {}
    
    # 1. GitHub Auth (fast local config check)
    gh_paths = [
        os.path.expandvars(r'%APPDATA%\GitHub CLI\hosts.yml'),
        os.path.expanduser("~/.config/gh/hosts.yml"),
    ]
    gh_logged = False
    gh_detail = "Não autenticado"
    for gp in gh_paths:
        if os.path.exists(gp):
            try:
                with open(gp, "r", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.strip().startswith("user:"):
                            active_user = line.strip().split(":", 1)[1].strip()
                            if active_user:
                                gh_logged = True
                                gh_detail = f"Conectado ({active_user})"
                                break
                    if gh_logged:
                        break
            except Exception:
                pass
    
    if not gh_logged and shutil.which("gh"):
        gh_detail = "Não autenticado (execute 'gh auth login --web')"
    elif not shutil.which("gh"):
        gh_detail = "gh CLI não instalado"

    statuses["github"] = {"authenticated": gh_logged, "details": gh_detail}

    # 2. Vercel Auth (fast local config check)
    v_paths = [
        os.path.expandvars(r'%APPDATA%\com.vercel.cli\auth.json'),
        os.path.expanduser("~/AppData/Roaming/com.vercel.cli/auth.json"),
        os.path.expanduser("~/.vercel/auth.json"),
    ]
    v_token = os.environ.get("VERCEL_TOKEN", "")
    has_v_auth = False
    v_detail = "Não autenticado (execute 'vercel login')"
    
    if v_token:
        has_v_auth = True
        v_detail = "Token configurado via VERCEL_TOKEN"
    else:
        for vp in v_paths:
            if os.path.exists(vp):
                try:
                    with open(vp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("token"):
                            has_v_auth = True
                            v_detail = "Autenticado (Sessão local com token ativo)"
                            break
                except Exception:
                    pass
    statuses["vercel"] = {"authenticated": has_v_auth, "details": v_detail}

    # 3. Cloudflare Token
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    cf_config = os.path.expanduser("~/.wrangler/config/default.toml")
    cf_logged = bool(cf_token) or os.path.exists(cf_config)
    cf_detail = "Token ativo" if cf_token else ("Config local presente" if os.path.exists(cf_config) else "Token ausente (CLOUDFLARE_API_TOKEN)")
    statuses["cloudflare"] = {"authenticated": cf_logged, "details": cf_detail}

    return statuses

def run_preflight():
    results = {
        "platform": platform.platform(),
        "os_name": platform.system(),
        "tools": {},
        "auth": check_auth_statuses(),
        "all_required_met": True
    }

    with ThreadPoolExecutor(max_workers=6) as executor:
        tool_results = list(executor.map(check_tool, TOOLS))

    tool_dict = {tid: (inst, ver) for tid, inst, ver in tool_results}

    for tool in TOOLS:
        tid = tool["id"]
        installed, version_str = tool_dict.get(tid, (False, None))
        results["tools"][tid] = {
            "name": tool["name"],
            "installed": installed,
            "version": version_str,
            "required": tool["required"],
            "install_win": tool["install_win"],
            "url": tool["url"]
        }
        if tool["required"] and not installed:
            results["all_required_met"] = False

    return results

if __name__ == "__main__":
    report = run_preflight()
    print(json.dumps(report, indent=2, ensure_ascii=False))
