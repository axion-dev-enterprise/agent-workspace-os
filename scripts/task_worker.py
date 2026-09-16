#!/usr/bin/env python3
"""
Task Queue Worker — Agent Workspace OS
Monitors and executes tasks from workspace/memory/active_tasks.json.
Lifecycle: pending -> running -> completed | failed.
Records execution output, updates daily timeline log and notifies via WhatsApp bridge.
"""

import sys
import os
import json
import time
import subprocess
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TASKS_FILE = os.path.join(WORKSPACE_ROOT, "workspace", "memory", "active_tasks.json")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "memory", "daily_logs")
BLACKBOARD_FILE = os.path.join(WORKSPACE_ROOT, "memory", "cowork", "blackboard.json")

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "tasks" in data:
                return data["tasks"]
            return []
    except Exception:
        return []

def save_tasks(tasks):
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def append_to_daily_log(task_id, instruction, status, output):
    today = time.strftime("%Y-%m-%d")
    now_time = time.strftime("%H:%M:%S")
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"{today}.md")

    entry = f"\n### [{now_time}] [task-worker] Tarefa {task_id}: {status.upper()}\n- **Instrução**: {instruction}\n- **Status**: {status}\n- **Evidência**: {output[:300]}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def notify_whatsapp_completion(task):
    remote_jid = task.get("from_jid") or task.get("from")
    if not remote_jid:
        return
    instruction = task.get("instruction", "")
    task_id = task.get("id", "")
    status = task.get("status", "")
    icon = "✅" if status == "completed" else "❌"
    msg_text = f"{icon} *Tarefa [{task_id}] Concluída!*\n\n*Pedido*: {instruction}\n*Status*: {status.upper()}\n*Resultado*: {task.get('result', 'Executado com sucesso.')}"
    
    try:
        payload = json.dumps({"to": remote_jid, "text": msg_text}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:4114/api/send-message",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

def execute_task(task):
    instruction = task.get("instruction", "").strip()
    task_id = task.get("id", f"task_{int(time.time())}")
    print(f"[WORKER] Iniciando tarefa [{task_id}]: {instruction}")

    task["status"] = "running"
    task["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Save running state immediately
    current_tasks = load_tasks()
    for idx, t in enumerate(current_tasks):
        if t.get("id") == task_id:
            current_tasks[idx] = task
            break
    save_tasks(current_tasks)

    output = ""
    result_text = ""
    success = True

    try:
        # Check if instruction is a direct shell command prefixed by ! or cmd:
        if instruction.startswith("!") or instruction.startswith("cmd:"):
            cmd = instruction.replace("!", "", 1).replace("cmd:", "", 1).strip()
            proc = subprocess.run(
                cmd, shell=True, cwd=WORKSPACE_ROOT,
                capture_output=True, text=True, timeout=30
            )
            output = proc.stdout if proc.returncode == 0 else proc.stderr
            success = proc.returncode == 0
            result_text = f"Comando executado (exit {proc.returncode})."
        else:
            # High-level Agentic Task Dispatch
            # Update cowork blackboard
            os.makedirs(os.path.dirname(BLACKBOARD_FILE), exist_ok=True)
            blackboard_data = {}
            if os.path.exists(BLACKBOARD_FILE):
                try:
                    with open(BLACKBOARD_FILE, "r", encoding="utf-8") as bf:
                        blackboard_data = json.load(bf)
                except Exception:
                    blackboard_data = {}
            
            blackboard_data["last_executed_task"] = {
                "id": task_id,
                "instruction": instruction,
                "source": task.get("source", "whatsapp"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            with open(BLACKBOARD_FILE, "w", encoding="utf-8") as bf:
                json.dump(blackboard_data, bf, indent=2, ensure_ascii=False)

            output = f"Tarefa processada e registrada na esteira do Agent Workspace OS. Instrução: '{instruction}'"
            result_text = "Tarefa processada e despachada para o ecossistema com sucesso."
            success = True

    except Exception as e:
        output = f"Erro na execução da tarefa: {str(e)}"
        result_text = f"Falha na execução: {str(e)}"
        success = False

    task["status"] = "completed" if success else "failed"
    task["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    task["output"] = output.strip()
    task["result"] = result_text

    # Update in persisted list
    current_tasks = load_tasks()
    for idx, t in enumerate(current_tasks):
        if t.get("id") == task_id:
            current_tasks[idx] = task
            break
    save_tasks(current_tasks)

    append_to_daily_log(task_id, instruction, task["status"], output)
    notify_whatsapp_completion(task)
    print(f"[WORKER] Tarefa [{task_id}] finalizada com status: {task['status']}")
    return task

def run_worker_once():
    tasks = load_tasks()
    pending = [t for t in tasks if t.get("status") == "pending"]
    processed = []
    for task in pending:
        res = execute_task(task)
        processed.append(res)
    return processed

def run_worker_loop():
    print("[TASK WORKER] Iniciando loop de monitoramento da fila de tarefas...")
    while True:
        try:
            run_worker_once()
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
        time.sleep(2)

def main():
    if "--once" in sys.argv:
        processed = run_worker_once()
        print(json.dumps({"processed_count": len(processed)}, ensure_ascii=False))
    else:
        run_worker_loop()

if __name__ == "__main__":
    main()
