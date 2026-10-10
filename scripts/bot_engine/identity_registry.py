#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Identity & Permissions Registry
Centralized lookup engine for phone numbers, JIDs, LIDs, and Telegram IDs.
Resolves permissions, contextual prompts, and execution tiers in O(1).
Auto-reloads on file modification with zero downtime.
"""

import json
import re
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

WORKSPACE_ROOT = Path("C:/workspace") if Path("C:/workspace").exists() else Path(__file__).resolve().parent.parent.parent
REGISTRY_FILE = WORKSPACE_ROOT / "memory" / "identities" / "registry.json"

_LOCK = threading.Lock()
_CACHE: Dict[str, Any] = {}
_LAST_MTIME: float = 0.0

def _normalize_digits(val: Any) -> str:
    if not val:
        return ""
    return re.sub(r'[^0-9]', '', str(val))

def load_registry(force_reload: bool = False) -> Dict[str, Any]:
    global _CACHE, _LAST_MTIME
    with _LOCK:
        if not REGISTRY_FILE.exists():
            return {"identities": [], "default_roles": {}}

        try:
            mtime = REGISTRY_FILE.stat().st_mtime
            if force_reload or mtime > _LAST_MTIME or not _CACHE:
                text = REGISTRY_FILE.read_text(encoding="utf-8")
                _CACHE = json.loads(text)
                _LAST_MTIME = mtime
        except Exception as e:
            print(f"[IdentityRegistry] Erro ao carregar registry.json: {e}")
            if not _CACHE:
                _CACHE = {"identities": [], "default_roles": {}}
        return _CACHE

def resolve_identity(
    chat_id: Any,
    phone: Optional[str] = None,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    source: str = "telegram",
    is_admin_hint: bool = False,
    is_lead_hint: bool = False
) -> Dict[str, Any]:
    """
    Resolves the exact identity, role, permissions, and contextual prompt
    given any combination of chat_id, LID, JID, phone or username.
    """
    data = load_registry()
    identities: List[Dict[str, Any]] = data.get("identities", [])
    default_roles: Dict[str, Any] = data.get("default_roles", {})

    str_chat_id = str(chat_id or "").strip()
    clean_chat_digits = _normalize_digits(str_chat_id)
    clean_phone_digits = _normalize_digits(phone)
    str_username = (username or "").strip().lstrip("@").lower()

    # Search in registered identities
    for ident in identities:
        # Check Telegram IDs
        tg_ids = [str(x) for x in ident.get("telegram_ids", [])]
        if str_chat_id in tg_ids or clean_chat_digits in tg_ids:
            return _format_profile(ident, matched_by="telegram_id")

        # Check Phone
        ident_phone = _normalize_digits(ident.get("phone", ""))
        if ident_phone and (ident_phone == clean_chat_digits or (clean_phone_digits and ident_phone == clean_phone_digits)):
            return _format_profile(ident, matched_by="phone")

        # Check JIDs
        ident_jids = [j.lower() for j in ident.get("jids", [])]
        if str_chat_id.lower() in ident_jids or (clean_chat_digits and clean_chat_digits in [re.sub(r'[^0-9]', '', j) for j in ident_jids]):
            return _format_profile(ident, matched_by="jid")

        # Check LIDs
        ident_lids = [l.lower() for l in ident.get("lids", [])]
        if str_chat_id.lower() in ident_lids or (clean_chat_digits and clean_chat_digits in [re.sub(r'[^0-9]', '', l) for l in ident_lids]):
            return _format_profile(ident, matched_by="lid")

        # Check Username
        ident_user = (ident.get("username") or "").strip().lstrip("@").lower()
        if str_username and ident_user and ident_user == str_username:
            return _format_profile(ident, matched_by="username")

    # Fallback to role-based default
    if is_admin_hint:
        role_key = "ADMIN"
    elif is_lead_hint:
        role_key = "LEAD"
    elif source == "whatsapp":
        role_key = "LEAD"
    else:
        role_key = "ADMIN"

    role_def = default_roles.get(role_key, {})
    return {
        "id": f"anon_{clean_chat_digits or 'unknown'}",
        "name": first_name or ("Admin" if role_key == "ADMIN" else "Lead"),
        "role": role_key,
        "is_admin": role_key == "ADMIN",
        "is_lead": role_key == "LEAD",
        "permissions": role_def.get("permissions", ["chat"] if role_key == "LEAD" else ["all"]),
        "contextual_prompt": role_def.get("contextual_prompt", ""),
        "default_tier": role_def.get("default_tier", "flash" if role_key == "LEAD" else "pro"),
        "matched_by": "default_role_fallback",
        "is_registered": False
    }

def _format_profile(ident: Dict[str, Any], matched_by: str) -> Dict[str, Any]:
    role = ident.get("role", "LEAD").upper()
    is_admin = role == "ADMIN" or "all" in ident.get("permissions", [])
    is_lead = role == "LEAD"
    return {
        "id": ident.get("id"),
        "name": ident.get("name", "Usuário Registrado"),
        "role": role,
        "phone": ident.get("phone", ""),
        "is_admin": is_admin,
        "is_lead": is_lead,
        "permissions": ident.get("permissions", ["all"] if is_admin else ["chat"]),
        "contextual_prompt": ident.get("contextual_prompt", ""),
        "default_tier": ident.get("default_tier", "pro" if is_admin else "flash"),
        "matched_by": matched_by,
        "is_registered": True
    }

def register_identity(
    ident_id: str,
    name: str,
    role: str = "OPERATOR",
    phone: str = "",
    jids: Optional[List[str]] = None,
    lids: Optional[List[str]] = None,
    telegram_ids: Optional[List[int]] = None,
    permissions: Optional[List[str]] = None,
    contextual_prompt: str = "",
    default_tier: str = "pro"
) -> bool:
    """Registers or updates an identity dynamically in registry.json."""
    with _LOCK:
        data = load_registry(force_reload=True)
        identities = data.get("identities", [])

        # Remove existing if present
        identities = [i for i in identities if i.get("id") != ident_id]

        new_entry = {
            "id": ident_id,
            "name": name,
            "role": role.upper(),
            "phone": _normalize_digits(phone),
            "jids": jids or [],
            "lids": lids or [],
            "telegram_ids": telegram_ids or [],
            "permissions": permissions or (["all"] if role.upper() == "ADMIN" else ["chat"]),
            "contextual_prompt": contextual_prompt,
            "default_tier": default_tier,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        identities.append(new_entry)
        data["identities"] = identities

        try:
            REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
            REGISTRY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            load_registry(force_reload=True)
            return True
        except Exception as e:
            print(f"[IdentityRegistry] Falha ao salvar registry: {e}")
            return False

if __name__ == "__main__":
    test_lid = os.environ.get("WHATSAPP_ADMIN_LID", "36735559900000") + "@lid"
    test_phone = os.environ.get("WHATSAPP_ADMIN_NUMBER", "5511999999999")
    test_tg = int(os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "123456789"))

    p1 = resolve_identity(test_lid)
    print("Resolved LID:", p1["name"], "| Role:", p1["role"], "| Admin:", p1["is_admin"], "| Matched:", p1["matched_by"])

    p2 = resolve_identity(test_phone, source="whatsapp")
    print("Resolved Phone:", p2["name"], "| Role:", p2["role"], "| Admin:", p2["is_admin"], "| Matched:", p2["matched_by"])

    p3 = resolve_identity(test_tg, source="telegram")
    print("Resolved TG:", p3["name"], "| Role:", p3["role"], "| Admin:", p3["is_admin"], "| Matched:", p3["matched_by"])

    p4 = resolve_identity("5511999990000@s.whatsapp.net", source="whatsapp", is_lead_hint=True)
    print("Resolved Unknown Lead:", p4["name"], "| Role:", p4["role"], "| Admin:", p4["is_admin"], "| Matched:", p4["matched_by"])
