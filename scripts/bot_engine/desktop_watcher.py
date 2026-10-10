#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Agents Watcher & Executive Notification Sentinel — Autonomous Agent Workspace OS
Continuously monitors background and foreground tasks executed by desktop agents
(Antigravity, Codex, OpenCode) across workspace registries, background task logs,
and process lifecycles. Emits proactive executive alerts
via WhatsApp and Telegram upon task completion.
"""

import os
import sys
import json
import time
import datetime
import threading
import urllib.request
import urllib.error
import re
import html
from pathlib import Path

# Paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

STATE_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "desktop_watcher_state.json"
COWORK_TASKS_FILE = WORKSPACE_ROOT / "memory" / "cowork" / "active_tasks.json"
WORKSPACE_TASKS_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "active_tasks.json"
DAILY_LOGS_DIR = WORKSPACE_ROOT / "memory" / "daily_logs"
ANTIGRAVITY_BRAIN_DIR = Path(os.path.expanduser(r"~\.gemini\antigravity\brain"))
SUBSCRIBERS_PATH = WORKSPACE_ROOT / "workspace" / "telegram_subscribers.json"

# CEO Credentials & Endpoints
CEO_WHATSAPP_PHONE = os.environ.get("WHATSAPP_ADMIN_NUMBER", "")
CEO_WHATSAPP_LID = os.environ.get("WHATSAPP_ADMIN_LID", "")
CEO_TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "0"))
WHATSAPP_BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", "http://127.0.0.1:4114")

_WATCHER_LOCK = threading.Lock()


def log(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}][DesktopWatcher] {msg}", flush=True)


def load_state() -> dict:
    """Loads notified tasks ledger to eliminate duplicates (anti-fatigue)"""
    if STATE_FILE.exists():
        try:
            content = STATE_FILE.read_text(encoding="utf-8").strip()
            if content:
                return json.loads(content)
        except Exception as e:
            log(f"Aviso ao ler estado do desktop watcher: {e}")
    return {
        "notified_task_ids": {},
        "antigravity_monitored_tasks": {},
        "last_sweep_ts": 0.0
    }


def save_state(state: dict):
    """Saves notified tasks ledger safely"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Erro ao salvar estado do desktop watcher: {e}")


def _send_whatsapp_ceo(message: str) -> bool:
    """Sends proactive alert to CEO Executive Operator via WhatsApp Bridge internal route"""
    try:
        url = f"{WHATSAPP_BRIDGE_URL}/send-internal"
        payload = json.dumps({
            "to": CEO_WHATSAPP_PHONE,
            "message": message
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode("utf-8"))
            return bool(res.get("success", False))
    except Exception as e:
        log(f"Falha ao enviar WhatsApp para o CEO: {e}")
        return False


def _send_telegram_ceo(message: str, send_fn=None) -> bool:
    """Sends proactive alert to CEO Executive Operator via Telegram"""
    if send_fn:
        try:
            send_fn(CEO_TELEGRAM_CHAT_ID, message)
            return True
        except Exception as e:
            log(f"Falha no send_fn Telegram para CEO: {e}")

    # Fallback: check bot_token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if token:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({
                "chat_id": CEO_TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return True
        except Exception as e:
            log(f"Falha na API direta do Telegram para CEO: {e}")

    return False


def is_executive_task_eligible(task_info: dict) -> bool:
    """
    Filtro de Relevância Executiva:
    Garante que apenas entregas de valor real, marcos de projeto e tarefas
    gerenciadas com escopo de negócio sejam enviadas ao CEO.
    Elimina 100% de comandos internos de scratch, sub-logs temporários e ruído.
    """
    title = str(task_info.get("title", "")).strip()
    result = str(task_info.get("result", "")).strip()
    source = str(task_info.get("source", "")).strip()

    # 1. Bloqueia explicitamente subprocessos de scratch do Antigravity
    if source == "antigravity_tasks_dir":
        is_delivery = any(k in title.lower() or k in result.lower() for k in [
            "deploy", "produção", "release", "milestone", "entrega", "publicad", "liberad"
        ])
        if not is_delivery:
            return False

    # 2. Bloqueia títulos genéricos de background
    if re.search(r"^Processo(\s+em\s+Background)?\s*\(task-", title, re.IGNORECASE):
        return False
    if "Processo finalizado (log:" in result:
        return False
    if title.lower() in ["tarefa sem título", "sem título", "teste", "comando", "cmd"]:
        return False

    return True


def _extract_deliverable_evidence(text: str) -> str:
    """Extrai evidência concreta (URL, domínio, porta ou commit) do resultado"""
    if not text:
        return ""
    url_m = re.search(r'https?://[^\s<>"]+', text)
    if url_m:
        return url_m.group(0).rstrip(".,;)")
    dom_m = re.search(r'\b[a-zA-Z0-9-]+\.(?:cloud|com|app|io|net|org)\b', text)
    if dom_m:
        return dom_m.group(0)
    port_m = re.search(r'porta\s+(\d+)\s+ativa', text, re.IGNORECASE)
    if port_m:
        return f"Porta {port_m.group(1)} ativa"
    sha_m = re.search(r'\bcommit\s+([a-f0-9]{7,40})\b', text, re.IGNORECASE)
    if sha_m:
        return f"Commit {sha_m.group(1)}"
    return ""


def notify_ceo(task_info: dict, send_fn=None):
    """
    Formats and dispatches high-priority completion alert to CEO Executive Operator
    across both WhatsApp and Telegram with executive relevance filter.
    """
    task_id = task_info.get("id", "task_unknown")
    agent_name = task_info.get("agent", "Desktop Agent").title()
    task_title = task_info.get("title", "Tarefa sem título")

    # Filtro de Relevância Executiva: descarta comandos internos de scratch
    if not is_executive_task_eligible(task_info):
        log(f"Tarefa {task_id} ignorada para notificação do CEO (classificada como subprocesso/scratch sem valor executivo).")
        return

    status = task_info.get("status", "completed")
    result_summary = task_info.get("result") or task_info.get("output") or "Executada com êxito."
    duration = task_info.get("duration", "")
    finished_at = task_info.get("finished_at") or datetime.datetime.now().strftime("%H:%M:%S")

    is_success = status in ["completed", "done", "success"]
    icon = "✅" if is_success else "❌"
    status_label = "Concluída com Sucesso" if is_success else f"Falha ({status})"
    action_needed = "Nenhuma ação requerida — entrega operando normalmente." if is_success else "Atenção requerida — falha na execução precisa de intervenção técnica."

    clean_summary = str(result_summary).strip()
    deliverable = _extract_deliverable_evidence(clean_summary + " " + str(task_info.get("output", "")))

    if len(clean_summary) > 350:
        clean_summary = clean_summary[:347] + "..."

    # 1. WhatsApp Format (Markdown) - Formato Executivo de Alto Valor
    wa_msg = (
        f"🚀 *[AXION ENTREGA EXECUTIVA]*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Projeto/Tarefa:* *{task_title}*\n"
        f"• *Agente Responsável:* {agent_name} (`{task_id}`)\n"
        f"• *Status:* {icon} *{status_label}*\n"
        f"• *Entregável / Resumo:* {clean_summary}\n"
    )
    if deliverable:
        wa_msg += f"• *Evidência / Link:* `{deliverable}`\n"
    if duration:
        wa_msg += f"• *Duração:* `{duration}`\n"
    wa_msg += (
        f"• *Horário:* `{finished_at}`\n"
        f"• *Ação para o CEO:* _{action_needed}_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Notificação proativa executiva enviada ao CEO Executive Operator._"
    )

    # 2. Telegram Format (HTML) - Formato Executivo de Alto Valor
    tg_msg = (
        f"🚀 <b>[AXION ENTREGA EXECUTIVA]</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Projeto/Tarefa:</b> <b>{html.escape(task_title)}</b>\n"
        f"• <b>Agente Responsável:</b> {agent_name} (<code>{task_id}</code>)\n"
        f"• <b>Status:</b> {icon} <b>{status_label}</b>\n"
        f"• <b>Entregável / Resumo:</b> {clean_summary}\n"
    )
    if deliverable:
        tg_msg += f"• <b>Evidência / Link:</b> <code>{deliverable}</code>\n"
    if duration:
        tg_msg += f"• <b>Duração:</b> <code>{duration}</code>\n"
    tg_msg += (
        f"• <b>Horário:</b> <code>{finished_at}</code>\n"
        f"• <b>Ação para o CEO:</b> <i>{action_needed}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Notificação proativa executiva enviada ao CEO Executive Operator.</i>"
    )

    # Dispatch to both channels (bypass in test mode to protect CEO against test spam)
    if os.environ.get("AXION_TEST_MODE") == "1" or os.environ.get("CI") == "1":
        wa_ok = True
        tg_ok = True
    else:
        wa_ok = _send_whatsapp_ceo(wa_msg)
        tg_ok = _send_telegram_ceo(tg_msg, send_fn=send_fn)
    log(f"Alerta emitido ao CEO para tarefa {task_id} ({agent_name}) -> WA: {wa_ok} | TG: {tg_ok}")

    # Log to daily markdown
    _log_to_daily_journal(agent_name, task_id, task_title, status_label, clean_summary)


def _log_to_daily_journal(agent_name: str, task_id: str, title: str, status: str, summary: str):
    """Records completion event in today's daily log markdown"""
    try:
        DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        log_file = DAILY_LOGS_DIR / f"{today}.md"

        entry = (
            f"\n### [{now_time}] [DESKTOP_WATCHER] Tarefa Concluída: {agent_name}\n"
            f"- **ID**: `{task_id}`\n"
            f"- **Título**: {title}\n"
            f"- **Status**: {status}\n"
            f"- **Resultado**: {summary}\n"
        )

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        log(f"Aviso ao registrar log diário: {e}")


MAX_TASK_ALERT_AGE_SECONDS = 300   # Somente tarefas finalizadas nos últimos 5 min geram alerta
MAX_CONV_DIR_AGE_SECONDS = 7200    # Somente inspeciona sessões Antigravity das últimas 2 horas


def _scan_workspace_tasks(state: dict, send_fn=None, is_cold_start: bool = False) -> list:
    """Scans memory/cowork/active_tasks.json and workspace/memory/active_tasks.json"""
    finished_found = []
    notified = state.setdefault("notified_task_ids", {})

    all_tasks = []
    for file_path in [COWORK_TASKS_FILE, WORKSPACE_TASKS_FILE]:
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                tasks = data if isinstance(data, list) else data.get("tasks", [])
                all_tasks.extend(tasks)
            except Exception as e:
                log(f"Erro lendo {file_path}: {e}")

    # Deduplicate by task ID
    seen_ids = set()
    for t in all_tasks:
        tid = t.get("id")
        if not tid or tid in seen_ids:
            continue
        seen_ids.add(tid)

        status = t.get("status", "").lower()
        if status in ["completed", "done", "success", "failed", "error"]:
            if tid not in notified:
                raw_agent = str(t.get("agent") or t.get("source") or "").lower()
                agent_type = "Desktop Agent"
                if any(k in raw_agent for k in ["antigravity", "gemini", "agy"]):
                    agent_type = "Antigravity"
                elif "codex" in raw_agent:
                    agent_type = "Codex"
                elif "opencode" in raw_agent or "open-code" in raw_agent:
                    agent_type = "OpenCode"
                else:
                    agent_type = raw_agent.title() or "Desktop Agent"

                task_info = {
                    "id": tid,
                    "agent": agent_type,
                    "title": t.get("title", tid),
                    "status": status,
                    "output": t.get("output", ""),
                    "result": t.get("result", ""),
                    "finished_at": t.get("finished_at", ""),
                    "source": "workspace_active_tasks"
                }

                # Se for cold start (inicialização), semeia silenciosamente sem alertar histórico passado
                if is_cold_start:
                    notified[tid] = {
                        "agent": agent_type,
                        "title": task_info["title"],
                        "status": status,
                        "notified_at": datetime.datetime.now().isoformat(),
                        "silent_baseline": True
                    }
                    continue

                # Checagem de frescor temporal (tarefas antigas são registradas sem alerta)
                finished_at_str = t.get("finished_at", "")
                is_fresh = True
                if finished_at_str:
                    try:
                        fin_dt = datetime.datetime.fromisoformat(finished_at_str.replace("Z", "+00:00"))
                        now_utc = datetime.datetime.now(datetime.timezone.utc)
                        if (now_utc - fin_dt).total_seconds() > MAX_TASK_ALERT_AGE_SECONDS:
                            is_fresh = False
                    except Exception:
                        pass

                if not is_fresh:
                    notified[tid] = {
                        "agent": agent_type,
                        "title": task_info["title"],
                        "status": status,
                        "notified_at": datetime.datetime.now().isoformat(),
                        "silent_stale": True
                    }
                    continue

                notify_ceo(task_info, send_fn=send_fn)
                notified[tid] = {
                    "agent": agent_type,
                    "title": task_info["title"],
                    "status": status,
                    "notified_at": datetime.datetime.now().isoformat()
                }
                finished_found.append(task_info)

    return finished_found


def _scan_antigravity_background_tasks(state: dict, send_fn=None, is_cold_start: bool = False) -> list:
    """
    Scans Antigravity brain sessions in ~/.gemini/antigravity/brain/*/
    Detects finished background task logs (.system_generated/tasks/task-*.log)
    """
    finished_found = []
    if not ANTIGRAVITY_BRAIN_DIR.exists():
        return finished_found

    notified = state.setdefault("notified_task_ids", {})
    monitored = state.setdefault("antigravity_monitored_tasks", {})
    now_ts = time.time()

    try:
        for conv_dir in ANTIGRAVITY_BRAIN_DIR.iterdir():
            if not conv_dir.is_dir():
                continue

            # Pula conversas antigas de dias anteriores
            try:
                conv_age = now_ts - conv_dir.stat().st_mtime
                if conv_age > MAX_CONV_DIR_AGE_SECONDS:
                    continue
            except Exception:
                continue

            tasks_dir = conv_dir / ".system_generated" / "tasks"
            if not tasks_dir.exists():
                continue

            for task_log in tasks_dir.glob("task-*.log"):
                task_key = f"antigravity_{conv_dir.name[:8]}_{task_log.stem}"
                if task_key in notified:
                    continue

                try:
                    stat = task_log.stat()
                    age_seconds = now_ts - stat.st_mtime

                    # Se for cold start (inicialização), semeia silenciosamente sem alertar histórico
                    if is_cold_start:
                        notified[task_key] = {
                            "agent": "Antigravity",
                            "title": f"Processo ({task_log.stem})",
                            "status": "completed",
                            "notified_at": datetime.datetime.now().isoformat(),
                            "silent_baseline": True
                        }
                        continue

                    # Se a tarefa finalizou há mais de 5 minutos, marca silenciosamente como antiga
                    if age_seconds > MAX_TASK_ALERT_AGE_SECONDS:
                        notified[task_key] = {
                            "agent": "Antigravity",
                            "title": f"Processo ({task_log.stem})",
                            "status": "completed",
                            "notified_at": datetime.datetime.now().isoformat(),
                            "silent_stale": True
                        }
                        continue

                    # Se ainda foi modificado há menos de 10s, ainda pode estar em execução
                    if age_seconds < 10:
                        monitored[task_key] = {"size": stat.st_size, "last_active": stat.st_mtime}
                        continue

                    # Tarefa recente finalizada!
                    content = task_log.read_text(encoding="utf-8", errors="replace")

                    # Filtro de Subprocesso Interno: Comandos de terminal/scratch comuns sem
                    # declaração explícita de entrega de negócio são registrados silenciosamente no ledger
                    # sem notificar o CEO, eliminando 100% do spam de 'task-XXXX'.
                    is_delivery = any(k in content.lower() for k in [
                        "[executive_delivery]", "deploy_success", "deploy_completed",
                        "liberado_ok", "produção", "release_completed", "milestone"
                    ])

                    if not is_delivery:
                        notified[task_key] = {
                            "agent": "Antigravity",
                            "title": f"Processo ({task_log.stem})",
                            "status": "completed",
                            "notified_at": datetime.datetime.now().isoformat(),
                            "silent_scratch": True
                        }
                        continue

                    tail = "\n".join(content.strip().splitlines()[-4:]) if content else "Execução finalizada."
                    clean_first_line = content.strip().splitlines()[0][:80] if content.strip() else task_log.stem
                    task_info = {
                        "id": task_key,
                        "agent": "Antigravity",
                        "title": f"Entrega: {clean_first_line}",
                        "status": "completed",
                        "output": tail,
                        "result": tail,
                        "finished_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S"),
                        "source": "antigravity_tasks_dir"
                    }

                    notify_ceo(task_info, send_fn=send_fn)
                    notified[task_key] = {
                        "agent": "Antigravity",
                        "title": task_info["title"],
                        "status": "completed",
                        "notified_at": datetime.datetime.now().isoformat()
                    }
                    finished_found.append(task_info)
                except Exception as task_err:
                    log(f"Aviso ao ler log de task {task_log}: {task_err}")

    except Exception as e:
        log(f"Erro escaneando Antigravity brain: {e}")

    return finished_found


def scan_and_notify_finished_tasks(send_fn=None, force_notify=False) -> dict:
    """
    Master sweep function:
    1. Detects cold start and establishes silent baseline without spamming CEO
    2. Scans workspace tasks (Codex, OpenCode, Antigravity) with freshness window
    3. Scans Antigravity background task logs
    4. Emits alerts to CEO only for newly completed, fresh tasks
    5. Persists deduplication state
    """
    with _WATCHER_LOCK:
        state = load_state()
        is_cold_start = (state.get("last_sweep_ts", 0.0) == 0.0)

        if is_cold_start:
            log("Inicializando baseline de observabilidade desktop (varredura silenciosa do histórico)...")

        ws_finished = _scan_workspace_tasks(state, send_fn=send_fn, is_cold_start=is_cold_start)
        ag_finished = _scan_antigravity_background_tasks(state, send_fn=send_fn, is_cold_start=is_cold_start)

        state["last_sweep_ts"] = time.time()
        save_state(state)

        total_new = len(ws_finished) + len(ag_finished)
        return {
            "success": True,
            "cold_start": is_cold_start,
            "newly_notified_count": total_new,
            "workspace_tasks_found": ws_finished,
            "antigravity_tasks_found": ag_finished,
            "total_notified_history": len(state.get("notified_task_ids", {}))
        }


def record_desktop_task_completion(agent: str, task_id: str, title: str, status: str = "completed", result: str = "", output: str = "", send_fn=None) -> dict:
    """
    Explicitly registers and announces completion of a desktop task.
    Can be called directly by agents (Antigravity, Codex, OpenCode) upon finishing a job.
    """
    with _WATCHER_LOCK:
        state = load_state()
        notified = state.setdefault("notified_task_ids", {})

        task_info = {
            "id": task_id,
            "agent": agent.title(),
            "title": title,
            "status": status,
            "result": result or output or "Tarefa finalizada com sucesso.",
            "finished_at": datetime.datetime.now().strftime("%H:%M:%S")
        }

        notify_ceo(task_info, send_fn=send_fn)
        notified[task_id] = {
            "agent": agent.title(),
            "title": title,
            "status": status,
            "notified_at": datetime.datetime.now().isoformat()
        }
        save_state(state)

        return {"success": True, "notified": True, "task": task_info}


def get_desktop_watcher_status() -> dict:
    """Returns telemetry and recent completed tasks for reporting"""
    state = load_state()
    notified = state.get("notified_task_ids", {})
    recent = sorted(
        [{"id": k, **v} for k, v in notified.items()],
        key=lambda x: x.get("notified_at", ""),
        reverse=True
    )[:10]

    return {
        "status": "active",
        "last_sweep_ts": state.get("last_sweep_ts", 0),
        "total_monitored_finished": len(notified),
        "recent_alerts": recent,
        "ceo_destinations": {
            "whatsapp": CEO_WHATSAPP_PHONE,
            "telegram": CEO_TELEGRAM_CHAT_ID
        }
    }


if __name__ == "__main__":
    print("--- Executando Varredura do Desktop Watcher ---")
    res = scan_and_notify_finished_tasks()
    print(json.dumps(res, indent=2, ensure_ascii=False))
