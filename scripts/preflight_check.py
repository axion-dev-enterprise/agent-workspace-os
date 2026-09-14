#!/usr/bin/env python3
"""
Preflight Environment Diagnostic Tool (Ultra-Fast & Safe)
Agent Workspace OS - Diagnostic and CLI Verification Engine
"""

import sys
import os
import shutil
import subprocess
import json
import platform

sys.stdout.reconfigure(encoding='utf-8')

TOOLS = [
    {
        "id": "python",
        "name": "Python 3",
        "cmd": "python --version",
        "required": True,
        "install_win": "winget install Python.Python.3.11",
        "url": "https://www.python.org/downloads/"
    },
    {
        "id": "node",
        "name": "Node.js (LTS)",
        "cmd": "node -v",
        "required": True,
        "install_win": "winget install OpenJS.NodeJS.LTS",
        "url": "https://nodejs.org/"
    },
    {
        "id": "git",
        "name": "Git",
        "cmd": "git --version",
        "required": True,
        "install_win": "winget install Git.Git",
        "url": "https://git-scm.com/"
    },
    {
        "id": "gh",
        "name": "GitHub CLI (gh)",
        "cmd": "gh --version",
        "required": False,
        "install_win": "winget install GitHub.cli",
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
        return False, None
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
        return True, out if out else "Instalado"
    except Exception:
        return True, "Instalado"

def check_auth_statuses():
    statuses = {}
    
    # 1. GitHub Auth (via gh auth status)
    gh_bin = shutil.which("gh") or shutil.which("gh.exe")
    if gh_bin:
        try:
            proc = subprocess.run(
                "gh auth status",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=3
            )
            out = proc.stdout.strip() or proc.stderr.strip()
            is_logged = ("Logged in to" in out) or (proc.returncode == 0)
            details = "Não autenticado"
            if is_logged:
                for line in out.split('\n'):
                    if "Logged in to" in line:
                        details = line.strip()
                        break
                if details == "Não autenticado":
                    details = "Autenticado (Conta ativa)"
            statuses["github"] = {"authenticated": is_logged, "details": details}
        except Exception as e:
            statuses["github"] = {"authenticated": False, "details": "Timeout ou erro ao verificar"}
    else:
        statuses["github"] = {"authenticated": False, "details": "gh CLI não instalado"}

    # 2. Vercel Auth (via auth.json file or env)
    v_paths = [
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

    for tool in TOOLS:
        installed, version_str = check_tool(tool)
        results["tools"][tool["id"]] = {
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
