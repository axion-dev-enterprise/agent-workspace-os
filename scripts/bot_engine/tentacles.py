#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tentacles Autonomous Engine — AXION Enterprise
Extends the cognitive agent into a proactive, sentient background daemon:
1. Auto-Start Pulse: Proactive executive greeting on system boot/recovery.
2. Mesh Network Sentinel: Periodic WireGuard/Tailnet node health and latency audit.
3. Storage & Vault Sentinel: Disk space threshold surveillance (C: SSD and E: Backup Vault).
4. SSL & Domain Sentinel: Continuous TLS certificate expiration tracking (< 30 days).
5. Backup Staleness Sentinel: Proactive prompt when backups exceed SLA (> 24 hours).
6. Autonomous Task Dispatcher: Background execution of pending critical workspace tasks.
7. Daily Executive Briefing: Unsolicited morning infrastructure & operational brief.
8. Anti-Fatigue Ledger: Deduplication and cooldown state persistence to eliminate spam.
"""

import os
import sys
import json
import time
import socket
import ssl
import shutil
import datetime
import threading
import re
import html
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import tool_executor
from bot_engine import dynamic_keyboard
from bot_engine import task_queue

STATE_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "tentacles_state.json"
SUBSCRIBERS_PATH = WORKSPACE_ROOT / "workspace" / "telegram_subscribers.json"
BACKUP_ROOT = Path(r"E:\backups\axion_enterprise")

# Thresholds & SLAs (Hysteresis & Anti-Fatigue Governance)
DISK_C_WARN_PCT = 15.0
DISK_C_CRIT_PCT = 8.0
RAM_WARN_PCT = 92.0
RAM_CRIT_PCT = 96.0
RAM_NORM_PCT = 80.0                # Strict hysteresis deadband (must drop below 80% to normalize)
RAM_ALERT_COOLDOWN_SECS = 14400    # 4 hours between repeat alerts of the same level
SSL_WARN_DAYS = 30
BACKUP_STALE_HOURS = 24
STARTUP_COOLDOWN_SECS = 600       # 10 minutes between startup greetings
BRIEFING_START_HOUR = 8           # 08:00 local time
BRIEFING_END_HOUR = 10            # 10:00 local time

def log(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}][Tentacles] {msg}", flush=True)

# ==========================================
# STATE & ANTI-FATIGUE LEDGER
# ==========================================
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            content = STATE_FILE.read_text(encoding="utf-8").strip()
            if content:
                return json.loads(content)
        except Exception as e:
            log(f"Erro ao ler estado dos tentáculos: {e}")
    return {
        "last_startup_pulse": 0,
        "last_briefing_date": "",
        "last_backup_prompt": 0,
        "mesh_nodes": {},
        "disk_state": {"c_level": "NOMINAL", "e_level": "NOMINAL"},
        "ssl_warned_domains": {},
        "silenced_until": {}
    }

def save_state(state: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Erro ao salvar estado dos tentáculos: {e}")

def is_silenced(key: str, state: dict) -> bool:
    silenced = state.get("silenced_until", {})
    exp = silenced.get(key, 0)
    return time.time() < exp

def silence_key(key: str, hours: float = 2.0):
    state = load_state()
    if "silenced_until" not in state:
        state["silenced_until"] = {}
    state["silenced_until"][key] = time.time() + (hours * 3600)
    save_state(state)
    log(f"Alerta '{key}' silenciado por {hours} horas.")

# ==========================================
# TENTACLE 1: AUTO-START & BOOT ANNOUNCER
# ==========================================
def on_startup(send_fn):
    """Fires immediately when the bot daemon comes online"""
    state = load_state()
    now_ts = time.time()
    
    # Cooldown prevents spamming if the bot is rapidly restarted during development
    if (now_ts - state.get("last_startup_pulse", 0)) < STARTUP_COOLDOWN_SECS:
        log("Pulso de inicialização ignorado (cooldown de reinicialização ativo).")
        return

    log("Disparando anúncio autônomo de inicialização dos Tentáculos...")
    telemetry = tool_executor.get_system_telemetry()
    ram = telemetry.get("ram", {})
    c_disk = telemetry.get("c_drive", {})
    e_disk = telemetry.get("e_backup_drive", {})
    tasks = task_queue.list_tasks(status="pending")
    
    e_status = f"{e_disk.get('free_gb')} GB livres" if e_disk.get("exists") else "Não montado"
    
    startup_msg = (
        "🚀 <b>AXION Co-Pilot Online & Autônomo</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "O agente cognitivo da AXION Enterprise foi inicializado e está operando sob gestão permanente <b>PM2</b>.\n\n"
        "📊 <b>Diagnóstico de Partida:</b>\n"
        f"• 💻 <b>RAM:</b> <code>{ram.get('free_gb', 0)} GB livres ({ram.get('percent_used', 0)}% em uso)</code>\n"
        f"• 💾 <b>Disco C:</b> <code>{c_disk.get('free_gb', 0)} GB ({c_disk.get('percent_free', 0)}% livre)</code>\n"
        f"• 🗄️ <b>Cofre E:</b> <code>{e_status}</code>\n"
        f"• 🌐 <b>Tailscale:</b> <code>{telemetry.get('tailscale_summary', 'OK')}</code>\n"
        f"• 📋 <b>Fila Workspace:</b> <code>{len(tasks)} tarefas pendentes</code>\n\n"
        "⚡ <i>Tentáculos de varredura proativa armados e ativos no PC local.</i>"
    )

    buttons = [
        [
            {"text": "📊 Telemetria Completa", "callback_data": dynamic_keyboard.register_callback_action({"query": "Mostre a telemetria completa em tempo real do PC"})},
            {"text": "🩺 Varredura Imediata", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_health_check"})}
        ],
        [
            {"text": "📋 Ver Tarefas", "callback_data": dynamic_keyboard.register_callback_action({"action": "task:list"})},
            {"text": "💾 Disparar Backup", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_backup"})}
        ]
    ]

    broadcast_to_subscribers(send_fn, startup_msg, reply_markup={"inline_keyboard": buttons})
    state["last_startup_pulse"] = now_ts
    save_state(state)

# ==========================================
# TENTACLE 2: TAILNET MESH & NODE LATENCY
# ==========================================
TAILNET_TARGET_NODES = [
    {"name": "Traefik Gateway & API", "ip": "100.64.0.1", "port": 22},
    {"name": "PostgreSQL & Flow Engine", "ip": "100.64.0.2", "port": 22}
]

def check_node_connectivity(ip: str, port: int = 22, timeout: float = 3.0) -> tuple[bool, float]:
    start = time.time()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            latency_ms = round((time.time() - start) * 1000, 1)
            return True, latency_ms
    except Exception:
        return False, -1.0

def sweep_tailnet_mesh(send_fn):
    """Audits WireGuard/Tailnet mesh nodes and alerts on state changes"""
    log("Varredura de nós Tailnet Mesh em andamento...")
    state = load_state()
    mesh_state = state.get("mesh_nodes", {})
    
    for node in TAILNET_TARGET_NODES:
        ip = node["ip"]
        name = node["name"]
        key = f"mesh_node_{ip}"
        
        ok, latency = check_node_connectivity(ip, node.get("port", 22))
        prev_ok = mesh_state.get(ip, {}).get("ok", True)
        
        # Node degraded/down transition
        if not ok and prev_ok:
            if not is_silenced(key, state):
                alert_text = (
                    f"⚠️ <b>Tentáculo Mesh: Nó Inacessível Detectado!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Nó:</b> <code>{name}</code>\n"
                    f"• <b>IP Tailnet:</b> <code>{ip}</code>\n"
                    f"• <b>Diagnóstico:</b> Falha na conexão TCP porta {node.get('port', 22)}.\n"
                    f"• <b>Ação Recomendada:</b> Executar watchdog de auto-correção."
                )
                buttons = [
                    [
                        {"text": "🔧 Executar Auto-Fix", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_health_check"})},
                        {"text": "🔕 Silenciar 2h", "callback_data": dynamic_keyboard.register_callback_action({"action": f"tentacle:silence:{key}:2"})}
                    ]
                ]
                broadcast_to_subscribers(send_fn, alert_text, reply_markup={"inline_keyboard": buttons})
                
        # Node recovery transition
        elif ok and not prev_ok:
            recov_text = (
                f"✅ <b>Tentáculo Mesh: Nó Restabelecido!</b>\n"
                f"• <b>Nó:</b> <code>{name}</code> ({ip})\n"
                f"• <b>Latência:</b> <code>{latency} ms</code> (Nominal)"
            )
            broadcast_to_subscribers(send_fn, recov_text)

        mesh_state[ip] = {"ok": ok, "latency_ms": latency, "checked_at": time.time()}

    state["mesh_nodes"] = mesh_state
    save_state(state)

# ==========================================
# TENTACLE 3: STORAGE & DISK CAPACITY
# ==========================================
def sweep_storage_disks(send_fn):
    """Surveils C: SSD and E: Backup Vault space, preventing alert fatigue"""
    log("Varredura de capacidade de armazenamento...")
    state = load_state()
    disk_state = state.get("disk_state", {"c_level": "NOMINAL", "e_level": "NOMINAL"})
    
    # Check C: drive
    c_usage = shutil.disk_usage("C:\\")
    c_free_pct = (c_usage.free / c_usage.total) * 100
    c_free_gb = round(c_usage.free / (1024**3), 2)
    
    current_c_level = "CRITICAL" if c_free_pct < DISK_C_CRIT_PCT else ("WARNING" if c_free_pct < DISK_C_WARN_PCT else "NOMINAL")
    
    if current_c_level != disk_state.get("c_level", "NOMINAL"):
        if current_c_level in ["WARNING", "CRITICAL"]:
            alert_text = (
                f"💾 <b>Tentáculo de Armazenamento: Capacidade do Disco C: em {current_c_level}!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Espaço Livre:</b> <code>{c_free_gb} GB ({round(c_free_pct, 1)}%)</code>\n"
                f"• <b>Limite de Alerta:</b> <code>&lt; {DISK_C_WARN_PCT}%</code>\n"
                f"• <b>Ação:</b> Recomenda-se rotação de logs e limpeza temporária."
            )
            buttons = [
                [
                    {"text": "🧹 Limpar Logs / Temp", "callback_data": dynamic_keyboard.register_callback_action({"query": "Limpe os arquivos temporários e logs antigos para liberar espaço no disco C:"})},
                    {"text": "📊 Telemetria", "callback_data": dynamic_keyboard.register_callback_action({"query": "Mostre a telemetria completa em tempo real do PC"})}
                ]
            ]
            broadcast_to_subscribers(send_fn, alert_text, reply_markup={"inline_keyboard": buttons})
        elif current_c_level == "NOMINAL" and disk_state.get("c_level") in ["WARNING", "CRITICAL"]:
            broadcast_to_subscribers(send_fn, f"✅ <b>Disco C: Normalizado!</b> Espaço livre atual: <code>{c_free_gb} GB ({round(c_free_pct, 1)}%)</code>.")
        
        disk_state["c_level"] = current_c_level

    # Check E: drive (Backup Vault)
    if os.path.exists("E:\\"):
        e_usage = shutil.disk_usage("E:\\")
        e_free_pct = (e_usage.free / e_usage.total) * 100
        e_free_gb = round(e_usage.free / (1024**3), 2)
        current_e_level = "WARNING" if e_free_pct < 10.0 else "NOMINAL"
        
        if current_e_level != disk_state.get("e_level", "NOMINAL"):
            if current_e_level == "WARNING":
                alert_text = (
                    f"⚠️ <b>Tentáculo de Backup: Cofre Offline (Disco E:) Quase Cheio!</b>\n"
                    f"Espaço livre: <code>{e_free_gb} GB ({round(e_free_pct, 1)}%)</code>. Recomenda-se podar snapshots antigos."
                )
                buttons = [
                    [{"text": "✂️ Podar Backups Antigos", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_backup", "backup_type": "prune"})}]
                ]
                broadcast_to_subscribers(send_fn, alert_text, reply_markup={"inline_keyboard": buttons})
            disk_state["e_level"] = current_e_level
    else:
        if disk_state.get("e_level") != "DISCONNECTED":
            broadcast_to_subscribers(send_fn, "⚠️ <b>Tentáculo de Armazenamento: Disco E: (Cofre Offline) Desconectado!</b>")
            disk_state["e_level"] = "DISCONNECTED"

    state["disk_state"] = disk_state
    save_state(state)

# ==========================================
# TENTACLE 4: SSL & DOMAIN SENTINEL
# ==========================================
KEY_DOMAINS_TO_PROBE = [
    "example.com",
    "api.example.com",
    "axionflow.my",
    "yannascimentoads.com",
    "axion-flow-gamma.vercel.app"
]

def check_domain_ssl_days(domain: str) -> tuple[int, str]:
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((domain, 443), timeout=4) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                not_after_str = cert.get("notAfter")
                # Format: 'Sep 25 12:00:00 2026 GMT'
                exp_date = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                days_left = (exp_date - datetime.datetime.now(datetime.timezone.utc)).days
                return days_left, exp_date.strftime("%Y-%m-%d")
    except Exception as e:
        return -999, str(e)

def sweep_ssl_certificates(send_fn):
    """Proactively flags TLS certificates expiring in less than 30 days"""
    log("Varredura de certificados SSL em andamento...")
    state = load_state()
    warned = state.get("ssl_warned_domains", {})
    now_ts = time.time()
    
    expiring_soon = []
    
    for dom in KEY_DOMAINS_TO_PROBE:
        days, exp_str = check_domain_ssl_days(dom)
        if 0 <= days <= SSL_WARN_DAYS:
            # Check 24-hour cooldown per domain
            last_warned = warned.get(dom, 0)
            if (now_ts - last_warned) > 86400:
                expiring_soon.append((dom, days, exp_str))
                warned[dom] = now_ts

    if expiring_soon:
        items_str = "\n".join([f"• <code>{d}</code>: <b>{days} dias restantes</b> (expira {exp})" for d, days, exp in expiring_soon])
        msg = (
            f"🔒 <b>Tentáculo de Segurança: Certificados SSL com Renovação Próxima!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{items_str}\n\n"
            f"<i>Recomenda-se checar a auto-renovação no Cloudflare ou Let's Encrypt.</i>"
        )
        buttons = [
            [
                {"text": "🔍 Auditar Todos os 16 SSL", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_ssl_sentinel"})},
                {"text": "📋 Ver Domínios", "callback_data": dynamic_keyboard.register_callback_action({"query": "Qual o status de expiração de todos os nossos 16 domínios e certificados?"})}
            ]
        ]
        broadcast_to_subscribers(send_fn, msg, reply_markup={"inline_keyboard": buttons})
        state["ssl_warned_domains"] = warned
        save_state(state)

# ==========================================
# TENTACLE 5: BACKUP STALENESS SENTINEL
# ==========================================
def sweep_backup_vault(send_fn):
    """Proactively alerts and initiates conversation if backups exceed 24 hours"""
    log("Varredura de integridade do cofre de backups...")
    state = load_state()
    now_ts = time.time()
    
    # 12-hour prompt cooldown
    if (now_ts - state.get("last_backup_prompt", 0)) < (12 * 3600):
        return

    latest_backup_time = None
    if BACKUP_ROOT.exists():
        try:
            dirs = [d for d in BACKUP_ROOT.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            if dirs:
                latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)
                latest_backup_time = latest_dir.stat().st_mtime
        except Exception:
            pass

    hours_since_backup = ((now_ts - latest_backup_time) / 3600) if latest_backup_time else 999.0
    
    if hours_since_backup > BACKUP_STALE_HOURS:
        hours_str = f"{round(hours_since_backup, 1)} horas" if latest_backup_time else "Nenhum backup encontrado"
        msg = (
            f"💾 <b>Tentáculo de Backup: Sincronização Corporativa Pendente</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Detectei que o último backup inteligente para o disco E: ocorreu há <b>{hours_str}</b> (limite SLA: {BACKUP_STALE_HOURS}h).\n\n"
            f"Deseja disparar o backup inteligente de código, configs e schemas agora?"
        )
        buttons = [
            [
                {"text": "⚡ Disparar Backup Agora", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_backup"})},
                {"text": "⏰ Lembrar em 4h", "callback_data": dynamic_keyboard.register_callback_action({"action": "tentacle:silence:backup_stale:4"})}
            ]
        ]
        broadcast_to_subscribers(send_fn, msg, reply_markup={"inline_keyboard": buttons})
        state["last_backup_prompt"] = now_ts
        save_state(state)

# ==========================================
# TENTACLE 6: AUTONOMOUS TASK DISPATCHER
# ==========================================
def sweep_workspace_tasks(send_fn):
    """Executes critical/auto_run tasks in background and announces completion with executive clarity"""
    tasks = task_queue.list_tasks(status="pending")
    for t in tasks:
        task_id = t["id"]
        is_critical = t.get("priority") == "critical"
        auto_run = t.get("params", {}).get("auto_run", False)
        
        if is_critical or auto_run:
            log(f"Iniciando execução autônoma da tarefa {task_id}: {t.get('title')}")
            res = task_queue.execute_task(task_id)
            is_success = res.get("status") == "completed"
            status_icon = "✅" if is_success else "❌"
            status_label = "Concluída com Sucesso" if is_success else "Falha na Execução"
            action_needed = "Nenhuma ação requerida — entrega operando normalmente." if is_success else "Atenção requerida — falha na execução precisa de intervenção."

            output = res.get("output") or ""
            clean_summary = res.get("result") or output[:250] or "Tarefa executada com êxito."
            
            url_m = re.search(r'https?://[^\s<>"]+', output)
            link_line = f"\n• <b>Link / Evidência:</b> <code>{url_m.group(0)}</code>" if url_m else ""
            
            completion_msg = (
                f"🚀 <b>[AXION ENTREGA EXECUTIVA]</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Projeto/Tarefa:</b> <b>{html.escape(t.get('title', 'Tarefa Autônoma'))}</b>\n"
                f"• <b>ID:</b> <code>{task_id}</code>\n"
                f"• <b>Status:</b> {status_icon} <b>{status_label}</b>\n"
                f"• <b>Entregável / Resumo:</b> {clean_summary}{link_line}\n"
                f"• <b>Ação para o CEO:</b> <i>{action_needed}</i>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Execução autônoma governada no workspace.</i>"
            )
            buttons = [
                [
                    {"text": "📋 Ver Tarefas", "callback_data": dynamic_keyboard.register_callback_action({"action": "task:list"})},
                    {"text": "📊 Telemetria", "callback_data": dynamic_keyboard.register_callback_action({"query": "Mostre a telemetria do sistema"})}
                ]
            ]
            broadcast_to_subscribers(send_fn, completion_msg, reply_markup={"inline_keyboard": buttons})

# ==========================================
# TENTACLE 7: DAILY EXECUTIVE BRIEFING
# ==========================================
def check_daily_briefing(send_fn):
    """Proactively initiates morning operational briefing between 08:00 and 10:00"""
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    if BRIEFING_START_HOUR <= now.hour < BRIEFING_END_HOUR:
        state = load_state()
        if state.get("last_briefing_date") == today_str:
            return  # Already briefed today
            
        log("Gerando Briefing Executivo Matinal Proativo...")
        telemetry = tool_executor.get_system_telemetry()
        ram = telemetry.get("ram", {})
        c_disk = telemetry.get("c_drive", {})
        e_disk = telemetry.get("e_backup_drive", {})
        pending_tasks = task_queue.list_tasks(status="pending")
        completed_tasks = task_queue.list_tasks(status="completed")
        
        briefing_msg = (
            f"☀️ <b>Briefing Operacional Matinal — AXION Enterprise</b>\n"
            f"<i>{now.strftime('%d/%m/%Y %H:%M')} | Co-piloto Autônomo</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Bom dia, Operador! Aqui está o resumo proativo da nossa infraestrutura:\n\n"
            f"• 🖥️ <b>Workstation:</b> Nominal (RAM {ram.get('percent_used', 0)}% | C: {c_disk.get('free_gb', 0)} GB livres)\n"
            f"• 🌐 <b>Rede Mesh:</b> <code>{telemetry.get('tailscale_summary', 'Ativa')}</code>\n"
            f"• 🗄️ <b>Cofre E:</b> {e_disk.get('free_gb', 0)} GB disponíveis para snapshots\n"
            f"• 📋 <b>Esteira de Tarefas:</b> <code>{len(pending_tasks)} pendentes</code> | <code>{len(completed_tasks)} concluídas</code>\n\n"
            f"Qual é o objetivo principal das operações de hoje?"
        )
        
        buttons = [
            [
                {"text": "📋 Ver Tarefas do Workspace", "callback_data": dynamic_keyboard.register_callback_action({"action": "task:list"})},
                {"text": "🩺 Health Check Completo", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_health_check"})}
            ],
            [
                {"text": "💾 Fazer Backup Matinal", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_backup"})},
                {"text": "🔒 Checar Domínios SSL", "callback_data": dynamic_keyboard.register_callback_action({"action": "tool:run_ssl_sentinel"})}
            ]
        ]
        
        broadcast_to_subscribers(send_fn, briefing_msg, reply_markup={"inline_keyboard": buttons})
        state["last_briefing_date"] = today_str
        save_state(state)

# ==========================================
# BROADCAST HELPER
# ==========================================
def broadcast_to_subscribers(send_fn, message: str, reply_markup: dict = None):
    """Dispatches a message to all registered and active subscribers"""
    if not SUBSCRIBERS_PATH.exists():
        return
    try:
        with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
            subscribers = json.load(f)
    except Exception as e:
        log(f"Erro ao ler assinantes para broadcast: {e}")
        return

    for cid_str, sub in subscribers.items():
        if sub.get("notifications_enabled", True):
            try:
                cid = int(cid_str)
                send_fn(cid, message, reply_markup=reply_markup, save_local=True)
            except Exception as e:
                log(f"Falha ao enviar broadcast para {cid_str}: {e}")

# ==========================================
# ==========================================
# TENTACLE 8: DESKTOP AGENTS SENTINEL
# ==========================================
def sweep_desktop_agents(send_fn):
    """Monitors desktop agents (Antigravity, Codex, OpenCode) and alerts CEO Executive Operator upon task completion"""
    try:
        from bot_engine import desktop_watcher
        desktop_watcher.scan_and_notify_finished_tasks(send_fn=send_fn)
    except Exception as e:
        log(f"Erro no tentáculo de observabilidade desktop: {e}")

# ==========================================
# TENTACLE 9: RAM MEMORY PRESSURE SENTINEL
# ==========================================
def sweep_ram_pressure(send_fn):
    """Surveils workstation RAM usage with strict hysteresis, cooldown and informative process tracking"""
    try:
        state = load_state()
        ram_state = state.get("ram_state", {"level": "NOMINAL", "last_alert_ts": 0.0, "last_norm_ts": 0.0})
        
        telemetry = tool_executor.get_system_telemetry()
        ram = telemetry.get("ram", {})
        pct = ram.get("percent_used", 0)
        used_gb = ram.get("used_gb", 0)
        total_gb = ram.get("total_gb", 0)
        top_procs = ram.get("top_processes", [])
        now_ts = time.time()
        
        previous_level = ram_state.get("level", "NOMINAL")
        last_alert_ts = ram_state.get("last_alert_ts", 0.0)
        
        # Determina nível atual com histerese estrita
        if pct >= RAM_CRIT_PCT:
            current_level = "CRITICAL"
        elif pct >= RAM_WARN_PCT:
            current_level = "WARNING"
        elif pct <= RAM_NORM_PCT:
            current_level = "NOMINAL"
        else:
            # Zona de histerese (entre 80.0% e 92.0%): mantém o estado anterior
            current_level = previous_level

        # Cooldown check: alertas do mesmo nível só podem disparar após 4h
        is_cooldown_expired = (now_ts - last_alert_ts) >= RAM_ALERT_COOLDOWN_SECS
        is_escalation = (previous_level == "WARNING" and current_level == "CRITICAL")
        
        should_alert = False
        if current_level in ["WARNING", "CRITICAL"]:
            if previous_level != current_level or is_cooldown_expired or is_escalation:
                should_alert = True

        if should_alert:
            # Lista de processos reais
            procs_lines = []
            for idx, p in enumerate(top_procs[:3], 1):
                p_name = p.get("name", "unknown")
                p_mb = p.get("memory_mb", 0)
                procs_lines.append(f"  {idx}. <code>{p_name}</code>: <b>{p_mb} MB</b>")
            procs_str = "\n".join(procs_lines) if procs_lines else "  • <i>Identificando via tasklist...</i>"

            alert_text = (
                f"🧠 <b>[TELEMETRIA DO HOST] Pressão Sustentada de RAM ({pct}%)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Consumo Real:</b> <code>{used_gb} GB de {total_gb} GB ({pct}%)</code>\n"
                f"• <b>Severidade:</b> <code>{current_level}</code> (limite: &gt; {RAM_WARN_PCT}%)\n"
                f"• <b>Maiores Consumidores de Memória:</b>\n{procs_str}\n\n"
                f"• <b>Ação Recomendada:</b> Encerre abas inativas ou recicle workers pesados.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Anti-fadiga: Próximo alerta para este nível retido por 4 horas.</i>"
            )
            buttons = [
                [
                    {"text": "📊 Processos Detalhados", "callback_data": dynamic_keyboard.register_callback_action({"query": "Liste os 10 processos com maior consumo de RAM no Windows"})},
                    {"text": "🔕 Silenciar 4h", "callback_data": dynamic_keyboard.register_callback_action({"action": "tentacle:silence:ram_pressure:4"})}
                ]
            ]
            broadcast_to_subscribers(send_fn, alert_text, reply_markup={"inline_keyboard": buttons})
            ram_state["level"] = current_level
            ram_state["last_alert_ts"] = now_ts
            state["ram_state"] = ram_state
            save_state(state)

        elif current_level == "NOMINAL" and previous_level in ["WARNING", "CRITICAL"]:
            # Só notifica normalização se houve alerta prévio E caiu abaixo de 80%
            broadcast_to_subscribers(
                send_fn,
                f"✅ <b>[TELEMETRIA DO HOST] Pressão de RAM Normalizada!</b>\n"
                f"Consumo atual estabilizado em <code>{pct}% ({used_gb} GB / {total_gb} GB)</code>."
            )
            ram_state["level"] = "NOMINAL"
            ram_state["last_norm_ts"] = now_ts
            state["ram_state"] = ram_state
            save_state(state)
            
    except Exception as e:
        log(f"Erro no tentáculo de pressão de RAM: {e}")

# ==========================================
# MASTER TENTACLES BACKGROUND THREAD
# ==========================================
def _tentacles_worker(send_fn):
    """Infinite loop executing scheduled proactive sweeps at calibrated intervals"""
    log("Tentáculos ativados. Ciclo autônomo iniciado.")
    
    last_mesh = 0
    last_disks = 0
    last_ram = 0
    last_ssl = 0
    last_backup = 0
    
    while True:
        try:
            now = time.time()
            
            # 1. Sweep workspace tasks (every 25 seconds)
            sweep_workspace_tasks(send_fn)

            # 1B. Sweep desktop agents tasks (Antigravity, Codex, OpenCode) (every 25 seconds)
            sweep_desktop_agents(send_fn)
            
            # 2. Check storage disks (every 10 minutes = 600s)
            if now - last_disks > 600:
                last_disks = now
                sweep_storage_disks(send_fn)
                
            # 2B. Check RAM pressure (every 5 minutes = 300s)
            if now - last_ram > 300:
                last_ram = now
                sweep_ram_pressure(send_fn)
                
            # 3. Check Tailnet Mesh nodes (every 15 minutes = 900s)
            if now - last_mesh > 900:
                last_mesh = now
                sweep_tailnet_mesh(send_fn)
                
            # 4. Check Backup freshness (every 2 hours = 7200s)
            if now - last_backup > 7200:
                last_backup = now
                sweep_backup_vault(send_fn)
                
            # 5. Check SSL Certificates (every 6 hours = 21600s)
            if now - last_ssl > 21600:
                last_ssl = now
                sweep_ssl_certificates(send_fn)
                
            # 6. Check Daily Executive Briefing (every check iteration)
            check_daily_briefing(send_fn)

        except Exception as e:
            log(f"Erro não tratado no worker de tentáculos: {e}")

        time.sleep(25)

def start_tentacles_daemon(send_fn):
    """Spawns the background tentacles orchestrator thread"""
    t = threading.Thread(target=_tentacles_worker, args=(send_fn,), daemon=True, name="AXION-Tentacles-Worker")
    t.start()
    log("[✓] Thread do Tentacles Orchestrator iniciada com sucesso.")
