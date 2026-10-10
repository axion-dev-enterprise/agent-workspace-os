#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Monitor & Self-Healing Watchdog 2.0 — AXION Enterprise
Continuously inspects:
1. Tailnet Mesh nodes connectivity and latency (Spaceship VPS Core, VPS Clients, Poseidon)
2. Production Web & API endpoints (Central API Gateway, Flow Backend, Flow App)
3. Local workstation resources (RAM, Disk C:, Disk E: Backups) and local services
4. Triggers automatic self-healing routines (Auto-Fix) for identified issues
5. Dispatches anti-fatigue state-change alerts via Telegram Bot to Executive Leadership
Outputs: docs/HEALTH_STATUS.md, workspace/health_telemetry.json, workspace/memory/health_monitor_state.json
"""

import sys
import os
import json
import ssl
import shutil
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import datetime
import argparse
from pathlib import Path

# Fix terminal encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
TAILSCALE_BIN = r"C:\Program Files\Tailscale\tailscale.exe"
if not os.path.exists(TAILSCALE_BIN):
    TAILSCALE_BIN = "tailscale"

STATE_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "health_monitor_state.json"
TELEMETRY_FILE = WORKSPACE_ROOT / "workspace" / "health_telemetry.json"
HEALTH_MD_FILE = WORKSPACE_ROOT / "docs" / "HEALTH_STATUS.md"

# Carregamento seguro do Vault
try:
    sys.path.insert(0, str(WORKSPACE_ROOT))
    import scripts.vault_loader as vault_loader
    vault_loader.load_vault()
except Exception:
    pass

# SSL Context defensivo para endpoints internos/testes
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Topologia Canônica Oficial da Infraestrutura AXION
NODES = [
    {
        "name": "vps-node-01-core",
        "ip": "100.83.25.74",
        "public_ip": "209.74.71.36",
        "role": "Spaceship Core (Gateway Nginx, Postgres, Redis, Flow Backend :3020, Fail2ban)"
    },
    {
        "name": "vps-node-01-clients",
        "ip": "100.93.18.70",
        "public_ip": "209.74.86.49",
        "role": "Spaceship Clients (Ambientes isolados de clientes, Fail2ban)"
    },
    {
        "name": "poseidon",
        "ip": "100.64.188.73",
        "public_ip": "Local",
        "role": "Workstation Windows 10 (Operador & IDE Antigravity)"
    }
]

# 2. Endpoints Web, Edge e APIs Produtivas
WEB_ENDPOINTS = [
    {
        "name": "AXION Central API Gateway Health",
        "url": "https://api.example.com/healthz",
        "expected_code": 200,
        "critical": True
    },
    {
        "name": "AXION Flow Backend Health",
        "url": "https://api.example.com/flow/health",
        "expected_code": 200,
        "critical": True
    },
    {
        "name": "AXION Flow Production App (Vercel)",
        "url": "https://flow.example.com",
        "expected_code": 200,
        "critical": True
    },
    {
        "name": "Yan Nascimento Ads (Vite/CF)",
        "url": "https://yannascimentoads.com",
        "expected_code": 200,
        "critical": False
    }
]

def _silent_run(cmd, **kwargs):
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = 0x08000000 | 0x00000200
    return subprocess.run(cmd, **kwargs)

def send_telegram_alert(html_message: str) -> bool:
    """Envia alerta formatado via Telegram Bot para o canal executivo configurado no Vault."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
    if not token or not chat_id:
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Watchdog] Falha ao despachar alerta Telegram: {e}", file=sys.stderr)
        return False

def check_tailscale_node(node):
    if node["ip"] == "100.64.188.73":
        # Poseidon é o nó local atual
        return {"status": "HEALTHY", "latency": "0.0ms (Local Node)"}
    
    cmd = [TAILSCALE_BIN, "ping", "--c=1", node["ip"]]
    try:
        res = _silent_run(cmd, capture_output=True, text=True, timeout=6)
        if res.returncode == 0 and "pong from" in res.stdout:
            parts = res.stdout.strip().split()
            latency = parts[-1] if parts else "OK"
            return {"status": "HEALTHY", "latency": latency}
        else:
            return {"status": "DEGRADED", "latency": "Timeout / No Pong"}
    except Exception as e:
        return {"status": "UNREACHABLE", "latency": str(e)}

def check_web_endpoint(endpoint):
    url = endpoint["url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AXION-Health-Watchdog/2.0"})
        with urllib.request.urlopen(req, timeout=7, context=ctx) as resp:
            return {"status": "HEALTHY", "code": resp.status}
    except urllib.error.HTTPError as e:
        if e.code in [401, 403]:
            return {"status": "HEALTHY (Auth Protected)", "code": e.code}
        return {"status": f"ERROR (HTTP {e.code})", "code": e.code}
    except Exception as e:
        return {"status": "DOWN", "code": str(e)}

def check_workstation_resources():
    # Disco C:
    total_c, used_c, free_c = shutil.disk_usage("C:\\")
    free_c_gb = round(free_c / (1024**3), 2)
    total_c_gb = round(total_c / (1024**3), 2)
    percent_c_free = round((free_c / total_c) * 100, 1)

    # Disco E: (Backups)
    res_e = {"exists": False}
    if os.path.exists("E:\\"):
        try:
            total_e, used_e, free_e = shutil.disk_usage("E:\\")
            res_e = {
                "exists": True,
                "free_gb": round(free_e / (1024**3), 2),
                "total_gb": round(total_e / (1024**3), 2),
                "percent_free": round((free_e / total_e) * 100, 1)
            }
        except Exception:
            pass

    # Status do backup mais recente
    backup_root = Path(r"E:\backups\axion_enterprise")
    backup_status = "N/A"
    last_backup_date = "Nenhum backup encontrado"
    if backup_root.exists():
        manifests = list(backup_root.glob("backup_*/manifest.json"))
        if manifests:
            manifests.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            latest_manifest = manifests[0]
            try:
                with open(latest_manifest, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    backup_status = mdata.get("status", "UNKNOWN")
                    last_backup_date = mdata.get("backup_date", "UNKNOWN")
            except Exception:
                backup_status = "READ_ERROR"

    # Status do Serviço Tailscale no Windows
    tailscale_svc = "UNKNOWN"
    try:
        svc_out = _silent_run(["powershell", "-NoProfile", "-Command", "(Get-Service Tailscale -ErrorAction SilentlyContinue).Status"], capture_output=True, text=True)
        tailscale_svc = svc_out.stdout.strip() or "NOT_FOUND"
    except Exception:
        pass

    status = "HEALTHY" if percent_c_free > 15 else "WARNING (Low Disk Space)"
    return {
        "status": status,
        "tailscale_service": tailscale_svc,
        "c_drive": {
            "free_gb": free_c_gb,
            "total_gb": total_c_gb,
            "percent_free": percent_c_free
        },
        "e_backup_drive": res_e,
        "backup_verification": {
            "status": backup_status,
            "last_backup": last_backup_date
        }
    }

def auto_fix_routines(tailnet_results, web_results, res_local):
    actions_taken = []

    # Auto-Fix 1: Se o serviço Tailscale local estiver parado, reiniciar
    if res_local.get("tailscale_service") in ["Stopped", "Paused"]:
        print("[Auto-Fix] Serviço Tailscale inativo! Reiniciando via PowerShell...")
        try:
            _silent_run(["powershell", "-NoProfile", "-Command", "Start-Service Tailscale"], capture_output=True)
            actions_taken.append("Reiniciado serviço local do Tailscale via PowerShell")
        except Exception as e:
            actions_taken.append(f"Falha ao reiniciar Tailscale: {e}")

    # Auto-Fix 2: Sincronização do Registro de Skills se estiver ausente
    registry_file = WORKSPACE_ROOT / "docs" / "SKILLS_REGISTRY.md"
    if not registry_file.exists():
        print("[Auto-Fix] docs/SKILLS_REGISTRY.md ausente. Executando auto-sincronização...")
        try:
            _silent_run(["python", str(WORKSPACE_ROOT / "scripts" / "sync_skills_registry.py")], capture_output=True)
            actions_taken.append("Regenerado docs/SKILLS_REGISTRY.md automaticamente")
        except Exception as e:
            actions_taken.append(f"Falha ao sincronizar skills: {e}")

    return actions_taken

def load_previous_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"nodes": {}, "endpoints": {}, "last_alert": None}

def save_current_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def process_alerts_and_notify(tailnet_results, web_results, res_local, force_summary=False):
    previous_state = load_previous_state()
    prev_nodes = previous_state.get("nodes", {})
    prev_endpoints = previous_state.get("endpoints", {})
    now_str = datetime.datetime.now().strftime("%H:%M:%S")

    changes = []
    current_nodes_state = {}
    current_endpoints_state = {}

    # Avalia transições em Nós Tailnet
    for node in tailnet_results:
        key = node["name"]
        curr_status = node["status"]
        current_nodes_state[key] = curr_status
        old_status = prev_nodes.get(key, "UNKNOWN")

        if old_status != "UNKNOWN" and old_status != curr_status:
            if curr_status == "HEALTHY":
                changes.append({
                    "type": "RECOVERY",
                    "item": f"Nó Tailnet: <b>{node['name']}</b> ({node['ip']})",
                    "detail": f"Status normalizado para HEALTHY ({node['latency']})"
                })
            else:
                changes.append({
                    "type": "INCIDENT",
                    "item": f"Nó Tailnet: <b>{node['name']}</b> ({node['ip']})",
                    "detail": f"Status degradado de {old_status} para <b>{curr_status}</b> ({node['latency']})"
                })

    # Avalia transições em Endpoints Web
    for ep in web_results:
        key = ep["name"]
        curr_status = "HEALTHY" if "HEALTHY" in ep["status"] else "DOWN"
        current_endpoints_state[key] = curr_status
        old_status = prev_endpoints.get(key, "UNKNOWN")

        if old_status != "UNKNOWN" and old_status != curr_status:
            if curr_status == "HEALTHY":
                changes.append({
                    "type": "RECOVERY",
                    "item": f"Serviço Web: <b>{ep['name']}</b>",
                    "detail": f"Normalizado para HTTP {ep['code']}"
                })
            else:
                changes.append({
                    "type": "INCIDENT",
                    "item": f"Serviço Web: <b>{ep['name']}</b>",
                    "detail": f"Falha detectada! Status: <b>{ep['status']}</b> (Código: {ep['code']})"
                })

    # Atualiza o estado para a próxima rodada
    new_state = {
        "nodes": current_nodes_state,
        "endpoints": current_endpoints_state,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    save_current_state(new_state)

    # Dispara alertas pontuais de transição (Anti-Fatigue)
    if changes:
        for c in changes:
            if c["type"] == "INCIDENT":
                msg = (
                    f"🚨 <b>[AXION SRE Incident] Alerta de Infraestrutura</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Alvo:</b> {c['item']}\n"
                    f"• <b>Problema:</b> {c['detail']}\n"
                    f"• <b>Horário:</b> <code>{now_str}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"<i>Watchdog automatizado em execução via Windows Task Scheduler.</i>"
                )
            else:
                msg = (
                    f"✅ <b>[AXION SRE Recovery] Serviço Normalizado</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Alvo:</b> {c['item']}\n"
                    f"• <b>Resultado:</b> {c['detail']}\n"
                    f"• <b>Horário:</b> <code>{now_str}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"<i>Restabelecimento confirmado com sucesso.</i>"
                )
            send_telegram_alert(msg)
            print(f"[Telegram Alert] Disparado: {c['type']} - {c['item']}")

    # Se solicitado sumário forçado (ex: teste ou rotina periódica)
    if force_summary:
        all_nodes_ok = all(n["status"] == "HEALTHY" for n in tailnet_results)
        all_web_ok = all("HEALTHY" in w["status"] for w in web_results)
        c_drive = res_local["c_drive"]
        e_drive = res_local["e_backup_drive"]
        
        status_global = "🟢 <b>OPERACIONAL & SAUDÁVEL</b>" if (all_nodes_ok and all_web_ok) else "⚠️ <b>ATENÇÃO REQUERIDA</b>"
        e_info_str = f"{e_drive['free_gb']}GB ({e_drive['percent_free']}%)" if e_drive.get("exists") else "Não detectado"

        summary_msg = (
            f"🛡️ <b>[AXION SRE Watchdog] Relatório de Integridade</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Status Global:</b> {status_global}\n"
            f"• <b>Tailnet Mesh:</b> {'🟢 3/3 nós online' if all_nodes_ok else '🔴 Degradação em nós'}\n"
            f"• <b>APIs & Web:</b> {'🟢 4/4 endpoints OK' if all_web_ok else '🔴 Falha em endpoints'}\n"
            f"• <b>Disco C:</b> {c_drive['free_gb']}GB livres ({c_drive['percent_free']}%)\n"
            f"• <b>Disco E (Backups):</b> {e_info_str}\n"
            f"• <b>Horário:</b> <code>{now_str}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Relatório executivo enviado ao CEO Executive Operator.</i>"
        )
        sent = send_telegram_alert(summary_msg)
        print(f"[Telegram Summary] Enviado com sucesso: {sent}")

def main():
    parser = argparse.ArgumentParser(description="AXION Enterprise Health Watchdog 2.0")
    parser.add_argument("--test-notify", action="store_true", help="Dispara um relatório sumário de teste para o Telegram")
    parser.add_argument("--notify-all", action="store_true", help="Força envio de notificação no Telegram independente de mudança de estado")
    parser.add_argument("--quiet", action="store_true", help="Execução silenciosa (sem saída de console desnecessária)")
    args = parser.parse_args()

    if not args.quiet:
        print("==================================================")
        print("    AXION ENTERPRISE HEALTH WATCHDOG & AUTO-FIX   ")
        print("==================================================")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Nós da Tailnet
    if not args.quiet:
        print("[1/3] Inspecionando nós da Tailnet Mesh...")
    tailnet_results = []
    for node in NODES:
        res = check_tailscale_node(node)
        if not args.quiet:
            print(f"  -> {node['name']} ({node['ip']}): {res['status']} ({res['latency']})")
        tailnet_results.append({**node, **res})

    # 2. Endpoints Web & APIs
    if not args.quiet:
        print("[2/3] Inspecionando endpoints Web & Edge...")
    web_results = []
    for ep in WEB_ENDPOINTS:
        res = check_web_endpoint(ep)
        if not args.quiet:
            print(f"  -> {ep['name']}: {res['status']} (Código: {res['code']})")
        web_results.append({**ep, **res})

    # 3. Recursos Locais & Backups
    if not args.quiet:
        print("[3/3] Checando recursos da estação de trabalho e backups...")
    res_local = check_workstation_resources()
    c_info = res_local["c_drive"]
    e_info = res_local["e_backup_drive"]
    b_info = res_local["backup_verification"]
    if not args.quiet:
        print(f"  -> Disco C: {c_info['free_gb']} GB livres ({c_info['percent_free']}%) - Status: {res_local['status']}")
        if e_info.get("exists"):
            print(f"  -> Disco E (Backups): {e_info['free_gb']} GB livres ({e_info['percent_free']}%)")
        print(f"  -> Tailscale Service: {res_local['tailscale_service']}")

    # 4. Auto-Fix
    actions = auto_fix_routines(tailnet_results, web_results, res_local)
    if actions and not args.quiet:
        print(f"[Auto-Fix Realizado] {', '.join(actions)}")

    # 5. Processamento de Alertas e Notificações no Telegram
    force_summary = args.test_notify or args.notify_all
    process_alerts_and_notify(tailnet_results, web_results, res_local, force_summary=force_summary)

    # 6. Salva Telemetria JSON
    telemetry = {
        "timestamp": now_iso,
        "tailnet_nodes": tailnet_results,
        "web_endpoints": web_results,
        "workstation_resources": res_local,
        "auto_fix_actions": actions
    }
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2, ensure_ascii=False)

    # 7. Gera Relatório Markdown Canônico docs/HEALTH_STATUS.md
    all_ok = all(n["status"] == "HEALTHY" for n in tailnet_results) and all("HEALTHY" in w["status"] for w in web_results)
    global_status_icon = "🟢" if all_ok else "⚠️"
    global_status_text = "OPERACIONAL E SAUDÁVEL" if all_ok else "ATENÇÃO REQUERIDA"

    md_lines = [
        "# Painel de Saúde & Auto-Fix da Infraestrutura",
        "",
        f"> **Última Varredura**: {now_str} (UTC: {now_iso})  ",
        f"> **Status Global do Sistema**: {global_status_icon} **{global_status_text}**  ",
        "",
        "---",
        "",
        "## 1. Nós da Rede Privada (Tailnet)",
        "",
        "| Nó / Servidor | IP Tailscale | Função | Status | Latência |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for n in tailnet_results:
        icon = "🟢" if n["status"] == "HEALTHY" else "🔴"
        md_lines.append(f"| `{n['name']}` | `{n['ip']}` | {n['role']} | {icon} {n['status']} | {n['latency']} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Endpoints Web, Vercel & Edge",
        "",
        "| Aplicação | URL | Status | Resposta HTTP |",
        "| :--- | :--- | :--- | :--- |"
    ])
    for w in web_results:
        icon = "🟢" if "HEALTHY" in w["status"] else "🔴"
        md_lines.append(f"| **{w['name']}** | [{w['url']}]({w['url']}) | {icon} {w['status']} | `{w['code']}` |")

    e_md = f"- **Unidade de Backups (`E:`)**: {e_info['free_gb']} GB livres de {e_info['total_gb']} GB ({e_info['percent_free']}%) — Status: **HEALTHY**" if e_info.get("exists") else "- **Unidade de Backups (`E:`)**: Não detectada"
    b_md = f"- **Último Backup Offline Verificado**: `{b_info['last_backup']}` (Integridade: **{b_info['status']}**)"

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Estação de Trabalho Local & Armazenamento",
        "",
        f"- **Espaço em Disco (`C:`)**: {c_info['free_gb']} GB livres de {c_info['total_gb']} GB ({c_info['percent_free']}%) — Status: **{res_local['status']}**",
        f"- **Serviço Local Tailscale**: `{res_local['tailscale_service']}`",
        e_md,
        b_md,
        f"- **Ações de Auto-Fix Executadas**: {', '.join(actions) if actions else 'Nenhuma intervenção necessária (sistema íntegro)'}",
        "",
        "---",
        "",
        "## Sincronização & Execução Contínua",
        "O monitor é orquestrado automaticamente pelo Windows Task Scheduler (`AXION-Health-Watchdog`).",
        "Para executar manualmente ou disparar teste de alerta:",
        "```powershell",
        "# Execução padrão",
        "python scripts/health_monitor_autofix.py",
        "",
        "# Execução com envio forçado de relatório no Telegram",
        "python scripts/health_monitor_autofix.py --test-notify",
        "```"
    ])

    HEALTH_MD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    if not args.quiet:
        print(f"\n[OK] Telemetria salva em: {TELEMETRY_FILE}")
        print(f"[OK] Relatório de saúde salvo em: {HEALTH_MD_FILE}")

if __name__ == "__main__":
    main()
