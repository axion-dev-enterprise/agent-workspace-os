#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Keyboard Generator and Callback Registry — AXION Enterprise
Parses AI-suggested buttons from LLM responses, ensures Telegram 64-byte callback_data safety,
provides zero-expiration direct tokens, persistent disk storage across restarts, and instant visual feedback.
"""

import os
import sys
import json
import re
import uuid
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")
REGISTRY_FILE = WORKSPACE_ROOT / "memory" / "telegram" / "callbacks_registry.json"
LEGACY_REGISTRY_FILE = WORKSPACE_ROOT / "workspace" / "memory" / "callbacks_registry.json"

# In-memory cache backed by persistent JSON
_CALLBACK_ACTIONS = {}

def _load_registry():
    global _CALLBACK_ACTIONS
    data = {}
    for p in [LEGACY_REGISTRY_FILE, REGISTRY_FILE]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data.update(loaded)
            except Exception:
                pass
    _CALLBACK_ACTIONS.update(data)

def _save_registry():
    global _CALLBACK_ACTIONS
    try:
        # Cap to 1000 entries
        if len(_CALLBACK_ACTIONS) > 1000:
            keys = list(_CALLBACK_ACTIONS.keys())[-800:]
            _CALLBACK_ACTIONS = {k: _CALLBACK_ACTIONS[k] for k in keys}
        for target in [REGISTRY_FILE, LEGACY_REGISTRY_FILE]:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(_CALLBACK_ACTIONS, f, ensure_ascii=False)
    except Exception:
        pass

# Initialize registry on import
_load_registry()

def register_callback_action(action_data: dict) -> str:
    """
    Registers an action payload and returns a callback_data token.
    Uses self-contained deterministic prefix tokens (< 64 bytes) for standard actions
    so they NEVER expire even across process restarts.
    """
    if not isinstance(action_data, dict):
        return "act:unknown"

    act = action_data.get("action", "")
    query = action_data.get("query", "")

    # 1. Deterministic direct tokens (Immune to restarts/expiration, <= 64 bytes)
    if act == "task:list":
        return "act:task:list"
    elif act == "tool:run_health_check":
        return "act:tool:health"
    elif act == "tool:run_backup":
        b_type = action_data.get("backup_type", "smart")
        return f"act:tool:backup:{b_type}"
    elif act == "tool:run_ssl_sentinel":
        return "act:tool:ssl"
    elif act == "tool:get_system_telemetry":
        return "act:telemetry"
    elif act == "task:execute" and "task_id" in action_data:
        return f"task:exec:{action_data['task_id']}"
    elif act == "task:delete" and "task_id" in action_data:
        return f"task:del:{action_data['task_id']}"
    elif act.startswith("tentacle:"):
        return act[:64]
    elif query and "telemetria" in query.lower():
        return "act:telemetry"

    # 2. Dynamic UUID token for custom LLM queries
    token = f"cb_{uuid.uuid4().hex[:12]}"
    _CALLBACK_ACTIONS[token] = action_data
    _save_registry()
    return token

def resolve_callback_action(token: str) -> dict | None:
    """
    Retrieves action payload by callback_data token.
    Resolves both direct deterministic tokens and UUID registry tokens.
    """
    if not token:
        return None

    # 1. Direct deterministic tokens
    if token == "act:task:list":
        return {"action": "task:list", "title": "Ver Tarefas"}
    elif token == "act:telemetry":
        return {"action": "telemetry", "query": "Mostre a telemetria completa em tempo real do PC", "title": "Telemetria"}
    elif token == "act:tool:health":
        return {"action": "tool:run_health_check", "title": "Health Check"}
    elif token.startswith("act:tool:backup:"):
        b_type = token.split("act:tool:backup:")[1]
        return {"action": "tool:run_backup", "backup_type": b_type, "title": "Backup Inteligente"}
    elif token == "act:tool:backup":
        return {"action": "tool:run_backup", "backup_type": "smart", "title": "Backup Inteligente"}
    elif token == "act:tool:ssl":
        return {"action": "tool:run_ssl_sentinel", "title": "Auditoria SSL"}
    elif token.startswith("task:exec:"):
        tid = token.split("task:exec:")[1]
        return {"action": "task:execute", "task_id": tid, "title": f"Executar {tid}"}
    elif token.startswith("task:del:"):
        tid = token.split("task:del:")[1]
        return {"action": "task:delete", "task_id": tid, "title": f"Excluir {tid}"}
    elif token.startswith("tentacle:"):
        return {"action": token, "title": "Sentinela"}
    elif token.startswith("tool:"):
        raw_tool = token.split("tool:")[1]
        parts = raw_tool.split(":")
        t_name = parts[0]
        res = {"action": f"tool:{t_name}", "title": t_name}
        if len(parts) > 1 and t_name == "run_backup":
            res["backup_type"] = parts[1]
        return res
    elif token.startswith("act:tool:"):
        subtool = token.split("act:tool:")[1]
        parts = subtool.split(":")
        t_name = parts[0]
        res = {"action": f"tool:{t_name}", "title": t_name}
        if len(parts) > 1 and t_name == "backup":
            res["action"] = "tool:run_backup"
            res["backup_type"] = parts[1]
        return res
    elif token.startswith("action:"):
        return {"action": token[7:], "title": "Ação"}
    elif token.startswith("query:"):
        return {"query": token[6:], "title": "Consulta"}

    # 2. Check in-memory cache
    if token in _CALLBACK_ACTIONS:
        return _CALLBACK_ACTIONS[token]

    # 3. Reload from disk to handle multi-process or recent persistence
    _load_registry()
    return _CALLBACK_ACTIONS.get(token)

def resolve_token(token: str) -> dict | None:
    """Alias for resolve_callback_action"""
    return resolve_callback_action(token)

def resolve_by_label(label: str) -> dict | None:
    """Finds matching action payload by button text label if token was lost across process restarts"""
    if not label:
        return None
    _load_registry()
    clean = label.strip().lower()
    for item in _CALLBACK_ACTIONS.values():
        if isinstance(item, dict) and item.get("text", "").strip().lower() == clean:
            return item
    for item in _CALLBACK_ACTIONS.values():
        if isinstance(item, dict) and clean in item.get("text", "").strip().lower():
            return item
    # Contextual domain heuristics
    if "alice" in clean:
        return {
            "action": "",
            "query": "Crie o site da Alice com animações 3D, coelhos e flores e faça o deploy na Vercel imediatamente, retornando o link público.",
            "title": "Site Alice"
        }
    if "telemetria" in clean:
        return {"action": "telemetry", "title": "Telemetria"}
    if "backup" in clean or "disparar backup" in clean:
        return {"action": "tool:run_backup", "backup_type": "smart", "title": "Backup"}
    if "lembrar" in clean or "silenciar" in clean or "adiar" in clean:
        hours = 4.0
        if "2h" in clean:
            hours = 2.0
        elif "8h" in clean:
            hours = 8.0
        elif "24h" in clean:
            hours = 24.0
        return {"action": f"tentacle:silence:backup_stale:{hours}", "title": "Lembrar mais tarde"}
    if "tarefa" in clean or "tasks" in clean:
        return {"action": "task:list", "title": "Tarefas"}
    if "health" in clean or "saúde" in clean or "diagnóstico" in clean:
        return {"action": "tool:run_health_check", "title": "Health Check"}
    if "ssl" in clean or "certificado" in clean:
        return {"action": "tool:run_ssl_sentinel", "title": "Auditoria SSL"}
    if "deploy" in clean:
        return {"query": "Faça o deploy do projeto no Vercel", "title": "Deploy Vercel"}
    return None

def parse_ai_buttons(text: str) -> tuple[str, dict | None]:
    """
    Finds ```buttons ... ``` or <buttons>...</buttons> in LLM text,
    removes it from the clean message, and builds Telegram inline keyboard.
    Returns: (clean_text, reply_markup_dict or None)
    """
    if not text:
        return "", None

    buttons_json_raw = None
    clean_text = text

    # 1. Match ```buttons ... ``` block
    pattern_code = r'```(?:buttons|json:buttons)?\s*([\s\S]*?)\s*```'
    m = re.search(pattern_code, text, re.IGNORECASE)
    if m:
        buttons_json_raw = m.group(1).strip()
        clean_text = (text[:m.start()] + text[m.end():]).strip()
    else:
        # 2. Match <buttons>...</buttons> tag
        pattern_tag = r'<buttons>\s*([\s\S]*?)\s*</buttons>'
        m2 = re.search(pattern_tag, text, re.IGNORECASE)
        if m2:
            buttons_json_raw = m2.group(1).strip()
            clean_text = (text[:m2.start()] + text[m2.end():]).strip()
        else:
            # 3. Match raw 'buttons\n[...]' block
            pattern_raw = r'(?:^|\n)\s*buttons\s*\n\s*(\[\s*\{[\s\S]*?\}\s*\])'
            m3 = re.search(pattern_raw, text, re.IGNORECASE)
            if m3:
                buttons_json_raw = m3.group(1).strip()
                clean_text = (text[:m3.start()] + "\n\n" + text[m3.end():]).strip()
            else:
                # 4. Match any loose JSON array of buttons at the end
                pattern_loose = r'(?:^|\n)\s*(\[\s*\{\s*["\']text["\'][\s\S]*?\}\s*\])\s*(?=\n\s*(?:🤖|<i|<b|$))'
                m4 = re.search(pattern_loose, text, re.IGNORECASE)
                if m4:
                    buttons_json_raw = m4.group(1).strip()
                    clean_text = (text[:m4.start()] + "\n\n" + text[m4.end():]).strip()

    if not buttons_json_raw:
        # Emergency strip of any orphan 'buttons\n[' to avoid raw JSON leaking
        clean_text = re.sub(r'(?:^|\n)\s*buttons\s*\n\s*\[[\s\S]*?\]', '', clean_text, flags=re.IGNORECASE).strip()
        return clean_text, None

    # Try to parse JSON array
    try:
        button_items = json.loads(buttons_json_raw)
        if not isinstance(button_items, list):
            return clean_text, None
    except Exception:
        clean_text = re.sub(r'(?:^|\n)\s*buttons\s*\n\s*\[[\s\S]*?\]', '', clean_text, flags=re.IGNORECASE).strip()
        return clean_text, None

    # Build keyboard structure: max 2 buttons per row, up to 6 buttons total
    keyboard = []
    current_row = []

    for item in button_items[:6]:
        if not isinstance(item, dict):
            continue
        btn_text = item.get("text", "").strip()
        if not btn_text:
            continue

        # Check if button is URL
        if "url" in item:
            btn_dict = {"text": btn_text, "url": item["url"]}
        else:
            token = register_callback_action(item)
            btn_dict = {"text": btn_text, "callback_data": token}

        current_row.append(btn_dict)
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    if not keyboard:
        return clean_text, None

    return clean_text, {
        "inline_keyboard": keyboard,
        "button_items": button_items
    }

def format_whatsapp_buttons_fallback(text: str, button_items: list) -> str:
    """Appends an elegant numbered list to text for platforms without native buttons support"""
    if not button_items or not isinstance(button_items, list):
        return text
    number_icons = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
    lines = [text.strip(), "", "👉 *Escolha uma opção:*"]
    for idx, item in enumerate(button_items[:8]):
        icon = number_icons[idx] if idx < len(number_icons) else f"[{idx+1}]"
        label = item.get("text", f"Opção {idx+1}")
        lines.append(f"{icon} {label}")
    lines.append("_(Clique no botão acima ou responda com o número)_")
    return "\n".join(lines)

def build_task_action_keyboard(task_id: str, status: str = "pending") -> dict | None:
    """Generates dynamic action buttons for a workspace task"""
    if status == "pending":
        token_exec = register_callback_action({"action": "task:execute", "task_id": task_id})
        token_del = register_callback_action({"action": "task:delete", "task_id": task_id})
        return {
            "inline_keyboard": [
                [
                    {"text": "⚡ Executar no PC", "callback_data": token_exec},
                    {"text": "🗑️ Cancelar", "callback_data": token_del}
                ]
            ]
        }
    return None

if __name__ == "__main__":
    t1 = register_callback_action({"action": "task:list"})
    t2 = register_callback_action({"action": "task:execute", "task_id": "task_123"})
    print("Token 1:", t1, "Resolved:", resolve_callback_action(t1))
    print("Token 2:", t2, "Resolved:", resolve_callback_action(t2))
