#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Message Persistence Store — AXION Enterprise
Persists all incoming and outgoing Telegram messages locally in JSONL format,
and synchronizes conversation events with daily markdown logs.
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")
TELEGRAM_MEMORY_DIR = WORKSPACE_ROOT / "memory" / "telegram"
GLOBAL_MESSAGES_LOG = TELEGRAM_MEMORY_DIR / "messages.jsonl"
CHATS_DIR = TELEGRAM_MEMORY_DIR / "chats"
DAILY_LOGS_DIR = WORKSPACE_ROOT / "memory" / "daily_logs"

def _ensure_dirs():
    TELEGRAM_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def normalize_chat_id(chat_id: int | str) -> str:
    """
    Normaliza identificadores de chat para unificar histórico entre LIDs e números de telefone reais.
    Ex: '<admin_lid>@lid' -> '<admin_phone>@s.whatsapp.net'
    """
    cid_str = str(chat_id).strip()
    clean_digits = "".join(c for c in cid_str if c.isdigit())
    
    # 1. Mapeamento do Administrador / Equipe AXION (whatsapp_team.json)
    team_file = WORKSPACE_ROOT / "workspace" / "whatsapp_team.json"
    if team_file.exists():
        try:
            team_data = json.loads(team_file.read_text(encoding="utf-8"))
            member = team_data.get(clean_digits)
            if member and member.get("linked_phone"):
                return f"{member['linked_phone']}@s.whatsapp.net"
        except Exception:
            pass

    # 2. Resolução do LID do Administrador Principal via variáveis de ambiente
    admin_phone = os.environ.get("WHATSAPP_ADMIN_NUMBER", "").strip()
    admin_lid = os.environ.get("WHATSAPP_ADMIN_LID", "").strip()
    if admin_phone and (clean_digits == admin_lid or clean_digits == admin_phone):
        return f"{admin_phone}@s.whatsapp.net"

    if "@" in cid_str:
        return cid_str
    if clean_digits.startswith("55") and len(clean_digits) >= 12:
        return f"{clean_digits}@s.whatsapp.net"

    return cid_str

def save_message(chat_id: int | str, direction: str, text: str, user_info: dict = None, metadata: dict = None) -> dict:
    """
    Persists an incoming or outgoing Telegram/WhatsApp message locally.
    direction: 'incoming' (user -> bot) or 'outgoing' (bot -> user)
    """
    _ensure_dirs()
    canon_id = normalize_chat_id(chat_id)
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_dt.isoformat()
    now_time = now_dt.strftime("%H:%M:%S UTC")
    today_str = now_dt.strftime("%Y-%m-%d")

    entry = {
        "id": f"msg_{int(time.time()*1000)}",
        "timestamp": now_iso,
        "chat_id": canon_id,
        "direction": direction,
        "text": text,
        "user_info": user_info or {},
        "metadata": metadata or {}
    }

    entry_line = json.dumps(entry, ensure_ascii=False) + "\n"

    # 1. Global log
    try:
        with open(GLOBAL_MESSAGES_LOG, "a", encoding="utf-8") as f:
            f.write(entry_line)
    except Exception as e:
        print(f"[message_store] Erro ao salvar global log: {e}")

    # 2. Chat specific log
    chat_file = CHATS_DIR / f"{canon_id}.jsonl"
    try:
        with open(chat_file, "a", encoding="utf-8") as f:
            f.write(entry_line)
    except Exception as e:
        print(f"[message_store] Erro ao salvar chat log: {e}")

    # 3. Daily human-readable markdown log
    daily_file = DAILY_LOGS_DIR / f"{today_str}.md"
    sender = user_info.get("first_name", "Operador") if user_info else "Operador"
    username = f"@{user_info.get('username')}" if user_info and user_info.get("username") else f"ID:{chat_id}"
    
    platform = "WhatsApp" if ("@s.whatsapp.net" in str(chat_id) or "@lid" in str(chat_id)) else "Telegram"
    if direction == "incoming":
        md_entry = (
            f"\n#### [{now_time}] 📥 {platform} [User: {sender} ({username})]\n"
            f"- **Mensagem**: {text.strip()}\n"
        )
    else:
        model = metadata.get("model", "Xiaomi Mimo") if metadata else "Xiaomi Mimo"
        tools = metadata.get("tools_executed", []) if metadata else []
        tools_str = f" | Tools: `{'`, `'.join(tools)}`" if tools else ""
        full_text = text.strip()
        quoted_lines = ["> " + ln if ln.strip() else ">" for ln in full_text.split("\n")]
        quoted_block = "\n".join(quoted_lines)
        md_entry = (
            f"##### [{now_time}] 📤 {platform} [Bot: {model}{tools_str}]\n"
            f"{quoted_block}\n"
        )

    try:
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(md_entry)
    except Exception:
        pass

    return entry

_BROADCAST_KEYWORDS = (
    "<b>ALERTA", "ALERTA [", "Tentáculo de", "Tentáculos de",
    "Briefing Operacional", "Relatório de Backup", "Notificação do Sistema",
    "Pulso de Inicialização", "[Tentacles]", "Tentáculo:"
)

def get_clean_dialogue_history(chat_id: int | str, limit: int = 10) -> list:
    """
    Retrieves recent chat history filtered strictly to human dialogue (user <-> assistant).
    Excludes unsolicited proactive system broadcasts, morning briefings, and tentacle alerts
    so they do not contaminate the LLM conversational context.
    """
    canon_id = normalize_chat_id(chat_id)
    chat_file = CHATS_DIR / f"{canon_id}.jsonl"
    if not chat_file.exists():
        return []

    lines = []
    try:
        with open(chat_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    clean_items = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            meta = item.get("metadata") or {}
            if meta.get("is_system_broadcast") or meta.get("is_broadcast"):
                continue

            text = (item.get("text") or "").strip()
            direction = item.get("direction")

            # Check known broadcast keywords for backwards-compatibility with historical logs
            if direction == "outgoing" and any(kw in text for kw in _BROADCAST_KEYWORDS):
                continue

            role = "user" if direction == "incoming" else "assistant"
            content = text
            if role == "assistant":
                content = content.split("<i>🤖 Xiaomi")[0].strip()

            clean_items.append({"role": role, "content": content})
            if len(clean_items) >= limit:
                break
        except Exception:
            continue

    clean_items.reverse()
    return clean_items

def get_chat_history(chat_id: int | str, limit: int = 10, clean: bool = True) -> list:
    """
    Retrieves recent chat history converted to LLM roles (user/assistant).
    If clean=True (default), filters out unsolicited system alerts and broadcasts.
    """
    if clean:
        return get_clean_dialogue_history(chat_id, limit=limit)

    canon_id = normalize_chat_id(chat_id)
    chat_file = CHATS_DIR / f"{canon_id}.jsonl"
    if not chat_file.exists():
        return []

    lines = []
    try:
        with open(chat_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    recent = lines[-limit:]
    history = []
    for line in recent:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            role = "user" if item.get("direction") == "incoming" else "assistant"
            content = item.get("text", "")
            if role == "assistant":
                content = content.split("<i>🤖 Xiaomi")[0].strip()
            history.append({"role": role, "content": content})
        except Exception:
            continue

    return history

def clear_chat_history(chat_id: int | str):
    """Archives or clears local chat history for a given chat_id"""
    canon_id = normalize_chat_id(chat_id)
    chat_file = CHATS_DIR / f"{canon_id}.jsonl"
    if chat_file.exists():
        archive_name = CHATS_DIR / f"{canon_id}_archived_{int(time.time())}.jsonl"
        try:
            chat_file.rename(archive_name)
        except Exception:
            pass

def search_messages(query: str, chat_id: int | str = None, limit: int = 15) -> list:
    """
    Searches message history across a specific chat or all chats.
    Performs case-insensitive substring search and returns matching messages.
    """
    _ensure_dirs()
    target_files = []
    if chat_id:
        canon_id = normalize_chat_id(chat_id)
        chat_file = CHATS_DIR / f"{canon_id}.jsonl"
        if chat_file.exists():
            target_files.append(chat_file)
    else:
        if GLOBAL_MESSAGES_LOG.exists():
            target_files.append(GLOBAL_MESSAGES_LOG)
        else:
            target_files = list(CHATS_DIR.glob("*.jsonl"))

    matches = []
    q_lower = query.lower().strip()

    for fpath in target_files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        text = entry.get("text", "")
                        if q_lower in text.lower():
                            matches.append(entry)
                    except Exception:
                        continue
        except Exception:
            continue

    return matches[-limit:]

def read_daily_log_content(date_str: str = None, lines: int = 60, query: str = None) -> dict:
    """
    Reads the daily markdown activity log for a specific date (YYYY-MM-DD) or today.
    Optionally filters lines containing a query string.
    """
    _ensure_dirs()
    if not date_str:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        date_str = now_dt.strftime("%Y-%m-%d")

    target_file = DAILY_LOGS_DIR / f"{date_str}.md"
    if not target_file.exists():
        available = [p.stem for p in DAILY_LOGS_DIR.glob("*.md")]
        return {
            "success": False,
            "error": f"Log diário para {date_str} não encontrado.",
            "available_dates": available[-7:]
        }

    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()

        if query:
            q_lower = query.lower()
            matching_lines = [l for l in all_lines if q_lower in l.lower()]
            result_text = "\n".join(matching_lines[-lines:])
            return {
                "success": True,
                "date": date_str,
                "query": query,
                "matches_count": len(matching_lines),
                "content": result_text
            }
        else:
            result_text = "\n".join(all_lines[-lines:])
            return {
                "success": True,
                "date": date_str,
                "total_lines": len(all_lines),
                "content": result_text
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    test_id = 999999
    save_message(test_id, "incoming", "Olá, teste local!", {"first_name": "Dev", "username": "dev_test"})
    save_message(test_id, "outgoing", "Olá! Resposta salva.", metadata={"model": "xiaomi/mimo-v2.6-pro"})
    hist = get_chat_history(test_id)
    print("History test:", hist)

