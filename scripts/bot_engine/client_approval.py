#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client External Resource Approval & OTP Protocol — AXION Enterprise
Standardized human-in-the-loop operational module for requesting external
resources, 2FA/OTP tokens, credentials, and deploy sign-offs from project clients
via WhatsApp, with simultaneous carbon-copy notification to CEO Executive Operator.
"""

import os
import sys
import json
import time
import re
import uuid
import datetime
import threading
import urllib.request
import urllib.error
from pathlib import Path

# Paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

APPROVALS_FILE = WORKSPACE_ROOT / "memory" / "cowork" / "pending_approvals.json"
DAILY_LOGS_DIR = WORKSPACE_ROOT / "memory" / "daily_logs"
TELEGRAM_CHATS_DIR = WORKSPACE_ROOT / "memory" / "telegram" / "chats"

# Endpoints & CEO
WHATSAPP_BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", "http://127.0.0.1:4114")
CEO_WHATSAPP_PHONE = os.environ.get("WHATSAPP_ADMIN_NUMBER", "")
CEO_TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "0"))

_APPROVAL_LOCK = threading.Lock()


def log(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}][ClientApproval] {msg}", flush=True)


def _clean_phone(phone: str) -> str:
    """Normalizes phone string to standard E.164 digits without plus or symbols"""
    digits = re.sub(r"[^0-9]", "", str(phone))
    if len(digits) in [10, 11] and not digits.startswith("55"):
        digits = "55" + digits
    return digits


def load_approvals() -> list:
    """Loads all pending and resolved client approvals"""
    if APPROVALS_FILE.exists():
        try:
            content = APPROVALS_FILE.read_text(encoding="utf-8").strip()
            if content:
                data = json.loads(content)
                return data if isinstance(data, list) else data.get("approvals", [])
        except Exception as e:
            log(f"Aviso ao ler {APPROVALS_FILE}: {e}")
    return []


def save_approvals(approvals: list):
    """Saves approvals list safely"""
    try:
        APPROVALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {"approvals": approvals, "updated_at": datetime.datetime.now().isoformat()}
        APPROVALS_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Erro ao salvar aprovações: {e}")


def _send_whatsapp_internal(to_phone: str, message: str, buttons: list = None) -> dict:
    """Sends message via WhatsApp bridge /send-internal route"""
    clean_target = _clean_phone(to_phone)
    url = f"{WHATSAPP_BRIDGE_URL}/send-internal"
    payload = {
        "to": clean_target,
        "message": message
    }
    if buttons:
        payload["buttons"] = buttons

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log(f"Erro ao disparar WhatsApp para {clean_target}: {e}")
        return {"success": False, "error": str(e)}


def _notify_ceo_of_request(project_name: str, client_name: str, client_phone: str, resource_type: str, reason: str, timeout_minutes: int):
    """Dispatches proactive alert to CEO Executive Operator regarding external client request"""
    wa_ceo = (
        f"📲 *[AXION Sentinel] Solicitação Externa de Recurso / OTP*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Projeto:* {project_name}\n"
        f"• *Cliente:* {client_name} (`{client_phone}`)\n"
        f"• *Recurso Solicitado:* *{resource_type}*\n"
        f"• *Motivo:* {reason}\n"
        f"• *Validade:* `{timeout_minutes} minutos`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Disparado automaticamente pelo agente de IA._"
    )
    _send_whatsapp_internal(CEO_WHATSAPP_PHONE, wa_ceo)


def request_client_resource_approval(
    project_name: str,
    client_phone: str,
    resource_type: str,
    reason: str,
    client_name: str = "Cliente",
    timeout_minutes: int = 15
) -> dict:
    """
    Constructs and sends an urgent, branded WhatsApp approval/OTP request to the client.
    Simultaneously informs CEO Executive Operator and registers in canonical storage.
    """
    clean_to = _clean_phone(client_phone)
    if not clean_to or len(clean_to) < 10:
        return {"success": False, "error": f"Número de WhatsApp inválido: '{client_phone}'. Forneça no formato DDI+DDD+Número (ex: 5511999998888)."}

    approval_id = f"appr_{uuid.uuid4().hex[:8]}"
    now_dt = datetime.datetime.now()
    expires_dt = now_dt + datetime.timedelta(minutes=timeout_minutes)

    # Formatted professional message for the client
    client_msg = (
        f"🔒 *AXION Enterprise — Solicitação de Código de Segurança*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Olá, *{client_name}*!\n\n"
        f"Estamos realizando uma etapa técnica no seu projeto *{project_name}* e precisamos de uma validação de segurança:\n\n"
        f"📌 *Item Necessário:* *{resource_type}* (ex: Código de verificação enviado por SMS/E-mail)\n"
        f"📝 *Finalidade:* {reason}\n"
        f"⏱️ *Validade:* O código expira em *{timeout_minutes} minutos*.\n\n"
        f"👉 *Como responder:* Responda diretamente a esta mensagem com o *código recebido* (ou digite *AUTORIZADO* para aprovar a operação).\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_AXION Enterprise Tecnologia & Automação Segura_"
    )

    buttons = [
        {"text": "✅ Autorizar Operação", "id": f"auth_{approval_id}"}
    ]

    # Dispatch to client via WhatsApp
    res = _send_whatsapp_internal(clean_to, client_msg, buttons=buttons)

    # Record in persistent pending approvals
    with _APPROVAL_LOCK:
        approvals = load_approvals()
        entry = {
            "id": approval_id,
            "project_name": project_name,
            "client_name": client_name,
            "client_phone": clean_to,
            "resource_type": resource_type,
            "reason": reason,
            "status": "pending",
            "created_at": now_dt.isoformat(),
            "expires_at": expires_dt.isoformat(),
            "timeout_minutes": timeout_minutes,
            "received_code": None,
            "approved_at": None,
            "dispatch_success": bool(res.get("success", False))
        }
        approvals.append(entry)
        save_approvals(approvals)

    # Proactive alert to CEO Executive Operator
    _notify_ceo_of_request(project_name, client_name, clean_to, resource_type, reason, timeout_minutes)

    # Log to daily log markdown
    _log_approval_to_journal("SOLICITAÇÃO", approval_id, project_name, clean_to, resource_type, reason)

    return {
        "success": True,
        "approval_id": approval_id,
        "status": "pending",
        "client_phone": clean_to,
        "resource_type": resource_type,
        "expires_at": expires_dt.isoformat(),
        "timeout_minutes": timeout_minutes,
        "message": f"Solicitação de {resource_type} enviada ao cliente com sucesso via WhatsApp.",
        "bridge_response": res
    }


def check_client_approval_status(approval_id: str) -> dict:
    """
    Checks if a client has replied with the OTP or approval keyword.
    Inspects message history in memory/telegram/chats/ and inbox.
    """
    with _APPROVAL_LOCK:
        approvals = load_approvals()
        target = next((a for a in approvals if a.get("id") == approval_id), None)
        if not target:
            return {"success": False, "error": f"Aprovação '{approval_id}' não encontrada."}

        if target.get("status") in ["approved", "rejected", "expired"]:
            return {
                "success": True,
                "approval_id": approval_id,
                "status": target["status"],
                "received_code": target.get("received_code"),
                "approved_at": target.get("approved_at")
            }

        # Check expiration
        now_dt = datetime.datetime.now()
        expires_dt = datetime.datetime.fromisoformat(target["expires_at"])
        if now_dt > expires_dt:
            target["status"] = "expired"
            save_approvals(approvals)
            return {
                "success": True,
                "approval_id": approval_id,
                "status": "expired",
                "message": "Prazo de validade da aprovação expirou."
            }

        # Scan client incoming messages since creation
        client_phone = target["client_phone"]
        created_dt = datetime.datetime.fromisoformat(target["created_at"])
        code_found = _scan_client_reply(client_phone, created_dt)

        if code_found:
            target["status"] = "approved"
            target["received_code"] = code_found
            target["approved_at"] = now_dt.isoformat()
            save_approvals(approvals)

            # Announce receipt to CEO
            ceo_alert = (
                f"✅ *[AXION Sentinel] Código / Aprovação Recebida!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Projeto:* {target['project_name']}\n"
                f"• *Cliente:* {target['client_name']} (`{client_phone}`)\n"
                f"• *Item:* {target['resource_type']}\n"
                f"• *Código/Resposta:* `{code_found}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"_Processamento retomado com sucesso._"
            )
            _send_whatsapp_internal(CEO_WHATSAPP_PHONE, ceo_alert)
            _log_approval_to_journal("APROVADO", approval_id, target["project_name"], client_phone, target["resource_type"], f"Código recebido: {code_found}")

            return {
                "success": True,
                "approval_id": approval_id,
                "status": "approved",
                "received_code": code_found,
                "approved_at": target["approved_at"],
                "message": f"Código {code_found} recebido do cliente com sucesso!"
            }

        return {
            "success": True,
            "approval_id": approval_id,
            "status": "pending",
            "message": "Aguardando resposta do cliente no WhatsApp.",
            "remaining_seconds": max(0, int((expires_dt - now_dt).total_seconds()))
        }


def submit_approval_code(approval_id: str, code: str) -> dict:
    """Allows manual or automated submission of the OTP code"""
    with _APPROVAL_LOCK:
        approvals = load_approvals()
        target = next((a for a in approvals if a.get("id") == approval_id), None)
        if not target:
            return {"success": False, "error": f"Aprovação '{approval_id}' não encontrada."}

        target["status"] = "approved"
        target["received_code"] = str(code).strip()
        target["approved_at"] = datetime.datetime.now().isoformat()
        save_approvals(approvals)

        # Notify CEO
        ceo_alert = (
            f"✅ *[AXION Sentinel] Código / Aprovação Inserida com Sucesso*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Projeto:* {target['project_name']}\n"
            f"• *Código Inserido:* `{code}`\n"
            f"• *Status:* APROVADO\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        _send_whatsapp_internal(CEO_WHATSAPP_PHONE, ceo_alert)

        return {"success": True, "approval_id": approval_id, "status": "approved", "received_code": code}


def _scan_client_reply(client_phone: str, after_dt: datetime.datetime) -> str | None:
    """Inspects chat logs for incoming messages from client after request time"""
    # Look into memory/telegram/chats/<clean_phone>@s.whatsapp.net.jsonl
    chat_file = TELEGRAM_CHATS_DIR / f"{client_phone}@s.whatsapp.net.jsonl"
    if not chat_file.exists():
        # Also check without suffix
        chat_file = TELEGRAM_CHATS_DIR / f"{client_phone}.jsonl"

    if chat_file.exists():
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    if msg.get("direction") == "incoming":
                        msg_time = datetime.datetime.fromisoformat(msg.get("timestamp", ""))
                        if msg_time >= after_dt:
                            text = msg.get("text", "").strip()
                            # Extract 4-8 digit OTP code
                            otp_match = re.search(r"\b\d{4,8}\b", text)
                            if otp_match:
                                return otp_match.group(0)
                            # Affirmative keywords
                            lower = text.lower()
                            if any(k in lower for k in ["autorizado", "aprovado", "sim", "pode", "ok", "confirmo", "liberado"]):
                                return "AUTORIZADO"
                            if len(text) <= 15:
                                return text
        except Exception as e:
            log(f"Erro escaneando chat do cliente {client_phone}: {e}")

    return None


def _log_approval_to_journal(action: str, approval_id: str, project: str, client_phone: str, resource_type: str, details: str):
    """Appends approval lifecycle event to today's daily log markdown"""
    try:
        DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        log_file = DAILY_LOGS_DIR / f"{today}.md"

        entry = (
            f"\n### [{now_time}] [CLIENT_APPROVAL] {action}: {project}\n"
            f"- **ID**: `{approval_id}`\n"
            f"- **Cliente**: `{client_phone}`\n"
            f"- **Recurso**: {resource_type}\n"
            f"- **Detalhes**: {details}\n"
        )

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        log(f"Aviso ao registrar diário: {e}")


def list_pending_approvals() -> list:
    """Returns all currently pending approvals"""
    approvals = load_approvals()
    return [a for a in approvals if a.get("status") == "pending"]


if __name__ == "__main__":
    print("--- Módulo Client Approval & OTP ---")
    pendings = list_pending_approvals()
    print(f"Aprovações pendentes: {len(pendings)}")
