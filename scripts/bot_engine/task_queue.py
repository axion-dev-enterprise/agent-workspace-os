#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace Task Queue Manager — AXION Enterprise
Injects, inspects, executes and updates tasks in canonical workspace memory.
Synchronizes workspace/memory/active_tasks.json and memory/cowork/active_tasks.json.
"""

import os
import sys
import json
import time
import subprocess
import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
WORKSPACE_TASKS_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "active_tasks.json"
COWORK_TASKS_FILE = WORKSPACE_ROOT / "memory" / "cowork" / "active_tasks.json"
BLACKBOARD_FILE = WORKSPACE_ROOT / "memory" / "cowork" / "blackboard.json"
DAILY_LOGS_DIR = WORKSPACE_ROOT / "memory" / "daily_logs"

def _ensure_dirs():
    WORKSPACE_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COWORK_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    BLACKBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks() -> list:
    """Loads tasks prioritizing workspace/memory/active_tasks.json then cowork"""
    _ensure_dirs()
    tasks = []
    
    # Try workspace path first
    for target in [WORKSPACE_TASKS_FILE, COWORK_TASKS_FILE]:
        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        tasks = content
                        break
                    elif isinstance(content, dict) and "tasks" in content:
                        tasks = content["tasks"]
                        break
            except Exception:
                pass
                
    return tasks

def save_tasks(tasks: list):
    """Saves tasks synchronously to both canonical locations"""
    _ensure_dirs()
    payload = tasks
    cowork_payload = {"tasks": tasks}
    
    try:
        with open(WORKSPACE_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[task_queue] Erro ao salvar {WORKSPACE_TASKS_FILE}: {e}")

    try:
        with open(COWORK_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(cowork_payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[task_queue] Erro ao salvar {COWORK_TASKS_FILE}: {e}")

def append_to_daily_log(task_id: str, instruction: str, status: str, output: str):
    """Appends task event to today's daily log markdown"""
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    now_time = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
    log_file = DAILY_LOGS_DIR / f"{today}.md"
    
    entry = (
        f"\n### [{now_time}] [telegram-task-injected] Tarefa `{task_id}`: {status.upper()}\n"
        f"- **Instrução**: {instruction}\n"
        f"- **Status**: `{status}`\n"
        f"- **Resultado**: {output[:300] if output else 'N/A'}\n"
    )
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def update_blackboard(task: dict):
    """Updates blackboard.json with latest task activity"""
    _ensure_dirs()
    data = {}
    if BLACKBOARD_FILE.exists():
        try:
            with open(BLACKBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
    data["last_task_activity"] = {
        "id": task.get("id"),
        "title": task.get("title"),
        "instruction": task.get("instruction"),
        "status": task.get("status"),
        "source": task.get("source"),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    try:
        with open(BLACKBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def inject_task(instruction: str, title: str = None, priority: str = "normal", source: str = "telegram", params: dict = None) -> dict:
    """Injects a new task into the workspace queue"""
    tasks = load_tasks()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    task_num = len(tasks) + 1
    task_id = f"task_{int(time.time())}_{task_num}"
    
    clean_title = title.strip() if title else instruction.strip().split("\n")[0][:45]
    if len(instruction.strip().split("\n")[0]) > 45 and not title:
        clean_title += "..."
        
    new_task = {
        "id": task_id,
        "title": clean_title,
        "instruction": instruction.strip(),
        "status": "pending",
        "priority": priority.lower() if priority in ["low", "normal", "high", "critical"] else "normal",
        "source": source,
        "params": params or {},
        "created_at": now_iso,
        "started_at": None,
        "finished_at": None,
        "output": None,
        "result": None
    }
    
    tasks.insert(0, new_task)
    save_tasks(tasks)
    update_blackboard(new_task)
    append_to_daily_log(task_id, instruction, "pending", "Injetada na fila do workspace via Telegram.")
    
    print(f"[task_queue] Tarefa injetada: [{task_id}] '{clean_title}' (Prioridade: {priority})")
    return new_task

def list_tasks(status: str = None, limit: int = 10) -> list:
    """Lists workspace tasks with optional status filter"""
    tasks = load_tasks()
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return tasks[:limit]

def get_task(task_id: str) -> dict:
    """Finds a task by ID"""
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None

def checkpoint_task(task_id: str, step_idx: int, messages: list, tools_executed: list,
                    completed_steps: list, chat_id: int = None) -> bool:
    """Saves a mid-execution checkpoint so the brain can resume after restart.
    
    Stores the full conversation messages array (trimming tool results to stay compact)
    and the current step index into the task record.
    """
    tasks = load_tasks()
    for idx, t in enumerate(tasks):
        if t.get("id") != task_id:
            continue

        # Trim tool result content to prevent unbounded JSON growth
        # Keep only the last 12 messages and trim long tool results
        trimmed = []
        for msg in messages[-12:]:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 3000:
                content = content[:3000] + "\n...[truncado para checkpoint]"
            trimmed.append({**msg, "content": content})

        t["resume_context"] = {
            "step_idx": step_idx,
            "messages": trimmed,
            "tools_executed": tools_executed,
            "completed_steps": completed_steps,
            "checkpoint_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        if chat_id:
            t["chat_id"] = chat_id
        t["last_step"] = step_idx
        t["last_checkpoint_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        tasks[idx] = t
        save_tasks(tasks)
        print(f"[task_queue] Checkpoint salvo: [{task_id}] passo {step_idx}")
        return True
    return False

def get_resumable_tasks() -> list:
    """Returns tasks that were interrupted mid-execution (status=running with resume_context)."""
    tasks = load_tasks()
    return [t for t in tasks if t.get("status") == "running" and t.get("resume_context")]

def clear_checkpoint(task_id: str):
    """Removes the resume_context from a task after it completes successfully."""
    tasks = load_tasks()
    for idx, t in enumerate(tasks):
        if t.get("id") == task_id:
            t.pop("resume_context", None)
            t.pop("last_step", None)
            tasks[idx] = t
            save_tasks(tasks)
            return


def execute_task(task_id: str) -> dict:
    """Executes a pending task on the local PC"""
    tasks = load_tasks()
    target_task = None
    target_idx = -1
    
    for idx, t in enumerate(tasks):
        if t.get("id") == task_id:
            target_task = t
            target_idx = idx
            break
            
    if not target_task:
        return {"error": f"Tarefa [{task_id}] não encontrada"}

    target_task["status"] = "running"
    target_task["started_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tasks[target_idx] = target_task
    save_tasks(tasks)
    update_blackboard(target_task)

    instruction = target_task.get("instruction", "").strip()
    cmd = ""

    if instruction.startswith("!") or instruction.startswith("cmd:"):
        cmd = instruction.replace("!", "", 1).replace("cmd:", "", 1).strip()
    elif instruction.startswith("ps:"):
        inner = instruction.replace("ps:", "", 1).strip()
        cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{inner}"'
    elif instruction.startswith("python "):
        cmd = instruction
    elif instruction.endswith(".py"):
        cmd = f"python {instruction}"
    else:
        # Default execution via PowerShell
        cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{instruction}"'

    from bot_engine import tool_executor
    res = tool_executor.exec_command(cmd, timeout=90)
    success = res.get("success", False)
    out_val = res.get("output") or ""
    err_val = res.get("error") or ""
    output = out_val if success else (err_val if err_val else out_val)
    result = f"Sucesso (exit 0) em {res.get('elapsed_seconds', 0)}s" if success else f"Falha (exit {res.get('returncode', -1)}) em {res.get('elapsed_seconds', 0)}s"

    target_task["status"] = "completed" if success else "failed"
    target_task["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    target_task["output"] = output
    target_task["result"] = result

    tasks[target_idx] = target_task
    save_tasks(tasks)
    update_blackboard(target_task)
    append_to_daily_log(task_id, instruction, target_task["status"], output)

    print(f"[task_queue] Tarefa [{task_id}] finalizada com status: {target_task['status']}")
    return target_task

def delete_task(task_id: str) -> bool:
    """Removes a task from queue"""
    tasks = load_tasks()
    initial_len = len(tasks)
    tasks = [t for t in tasks if t.get("id") != task_id]
    if len(tasks) < initial_len:
        save_tasks(tasks)
        return True
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        t = inject_task("python -c \"print('Teste do Task Queue OK!')\"", title="Teste Automatizado", priority="high")
        print("Injetada:", t["id"])
        res = execute_task(t["id"])
        print("Executada:", res["status"], "| Output:", res["output"])
