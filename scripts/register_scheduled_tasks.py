"""
AXION Task Scheduler Registration
==================================
Registra tarefas agendadas no Windows Task Scheduler
para o AXION Content Intelligence Monitor.

Execute como Administrador:
  python scripts/register_scheduled_tasks.py

Ou via:
  Start-Process powershell -Verb RunAs -ArgumentList "-Command python c:/workspace/scripts/register_scheduled_tasks.py"
"""

import subprocess
import sys
from pathlib import Path

WORKSPACE = "C:\\workspace"
PYTHON    = sys.executable

TASKS = [
    {
        "name":        "AXION-Content-Intelligence",
        "description": "Monitor diário de conteúdo: GitHub Trending, HN, RSS feeds — AXION Ecosystem",
        "script":      f"{WORKSPACE}\\scripts\\content_intelligence_monitor.py",
        "schedule":    "DAILY",
        "time":        "08:00",
        "extra_args":  [],
    },
    {
        "name":        "AXION-Agent-Email-Poll",
        "description": "Polling de inbox de e-mail do agente AXION (verifica mensagens novas)",
        "script":      f"{WORKSPACE}\\services\\agent-email\\agent_email_client.py",
        "schedule":    "HOURLY",
        "time":        None,
        "extra_args":  ["poll"],
    },
]


def register_task(task: dict) -> bool:
    name   = task["name"]
    script = task["script"]
    sched  = task["schedule"]
    desc   = task["description"]
    time   = task.get("time", "08:00")
    args   = " ".join(task.get("extra_args", []))

    action = f'"{PYTHON}" "{script}" {args}'.strip()

    cmd = [
        "schtasks", "/create", "/tn", name,
        "/tr", action,
        "/sc", sched,
        "/ru", "SYSTEM",
        "/f",
        "/rl", "HIGHEST",
    ]
    if sched == "DAILY" and time:
        cmd += ["/st", time]
    elif sched == "HOURLY":
        cmd += ["/mo", "1"]

    print(f"\n[+] Registrando: {name}")
    print(f"    Ação: {action}")
    print(f"    Schedule: {sched}" + (f" às {time}" if time else ""))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"    ✓ SUCESSO")
        return True
    else:
        print(f"    ✗ ERRO: {result.stderr.strip() or result.stdout.strip()}")
        return False


if __name__ == "__main__":
    print("=== AXION Task Scheduler Registration ===\n")
    ok = 0
    for t in TASKS:
        if register_task(t):
            ok += 1
    print(f"\n[resultado] {ok}/{len(TASKS)} tarefas registradas com sucesso")
    if ok < len(TASKS):
        print("[!] Execute como Administrador se houver erros de permissão")
