"""
AXION Agent Email Client
========================
Sistema de e-mail para agentes AXION via IMAP/SMTP.
Suporta:
  - Proton Mail Bridge (IMAP/SMTP local em 127.0.0.1)
  - Gmail IMAP (OAuth2 ou App Password)
  - Qualquer provedor IMAP/SMTP padrão

Arquitetura:
  - Cada agente tem um "mailbox" lógico (pasta IMAP ou label Gmail)
  - Mensagens de entrada são parseadas e despachadas como eventos
  - Mensagens de saída são enfileiradas e enviadas em batch
  - Histórico de e-mails é persistido em memory/email/

Config via environment (nunca hardcoded):
  AGENT_EMAIL_USER     = endereço do agente (ex: agent@example.com)
  AGENT_EMAIL_PASSWORD = App Password / Bridge password
  AGENT_EMAIL_IMAP     = host IMAP (ex: 127.0.0.1 para Bridge, imap.gmail.com)
  AGENT_EMAIL_SMTP     = host SMTP
  AGENT_EMAIL_IMAP_PORT = porta IMAP (993 SSL / 1143 Bridge)
  AGENT_EMAIL_SMTP_PORT = porta SMTP (587 STARTTLS / 1025 Bridge)
"""

import os
import json
import imaplib
import smtplib
import email
import email.utils
import logging
import hashlib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Carregar segredos centralizados do AXION Vault
try:
    from scripts.vault_loader import load_vault
    load_vault()
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────
IMAP_HOST  = os.environ.get("AGENT_EMAIL_IMAP",      "127.0.0.1")
IMAP_PORT  = int(os.environ.get("AGENT_EMAIL_IMAP_PORT", "993"))
SMTP_HOST  = os.environ.get("AGENT_EMAIL_SMTP",      "127.0.0.1")
SMTP_PORT  = int(os.environ.get("AGENT_EMAIL_SMTP_PORT", "587"))
EMAIL_USER = os.environ.get("AGENT_EMAIL_USER",      "")
EMAIL_PASS = os.environ.get("AGENT_EMAIL_PASSWORD",  "")

MEMORY_DIR = Path("c:/workspace/memory/email")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
INBOX_LOG  = MEMORY_DIR / "inbox.jsonl"
SENT_LOG   = MEMORY_DIR / "sent.jsonl"
AGENTS_DIR = MEMORY_DIR / "agents"
AGENTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AGENT-EMAIL] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("agent_email")

# ── Known agent mailboxes ─────────────────────────────────────────────────────
AGENT_MAILBOXES: dict[str, dict] = {
    "axion-core": {
        "display": "AXION Core Agent",
        "folder":  "INBOX/axion-core",
        "tags":    ["ops", "infra", "alerts"],
    },
    "axion-monitor": {
        "display": "AXION Content Monitor",
        "folder":  "INBOX/axion-monitor",
        "tags":    ["content", "feeds", "intelligence"],
    },
    "axion-security": {
        "display": "AXION Security Agent",
        "folder":  "INBOX/axion-security",
        "tags":    ["pentest", "osint", "alerts"],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# IMAP Reader
# ══════════════════════════════════════════════════════════════════════════════

class AgentIMAPReader:
    """Lê e-mails de uma caixa de entrada IMAP."""

    def __init__(self):
        self.conn: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None

    def connect(self) -> bool:
        if not EMAIL_USER or not EMAIL_PASS:
            log.error("AGENT_EMAIL_USER / AGENT_EMAIL_PASSWORD não definidos.")
            return False
        try:
            if IMAP_PORT == 993:
                self.conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            else:
                self.conn = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
                self.conn.starttls()
            self.conn.login(EMAIL_USER, EMAIL_PASS)
            log.info(f"IMAP conectado: {IMAP_HOST}:{IMAP_PORT} como {EMAIL_USER}")
            return True
        except Exception as e:
            log.error(f"Falha IMAP connect: {e}")
            return False

    def fetch_unseen(self, folder: str = "INBOX") -> list[dict]:
        """Retorna lista de mensagens não lidas do folder especificado."""
        if not self.conn:
            return []
        messages = []
        try:
            self.conn.select(folder, readonly=False)
            _, nums = self.conn.search(None, "UNSEEN")
            for num in nums[0].split():
                _, data = self.conn.fetch(num, "(RFC822)")
                raw = data[0][1]
                msg = email.message_from_bytes(raw)
                parsed = self._parse(msg, num)
                messages.append(parsed)
                # Marcar como lido
                self.conn.store(num, "+FLAGS", "\\Seen")
        except Exception as e:
            log.warning(f"Erro ao buscar mensagens de {folder}: {e}")
        return messages

    def _parse(self, msg: email.message.Message, uid: bytes) -> dict:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        return {
            "uid":       uid.decode(),
            "message_id": msg.get("Message-ID", ""),
            "from":      msg.get("From", ""),
            "to":        msg.get("To", ""),
            "subject":   msg.get("Subject", ""),
            "date":      msg.get("Date", ""),
            "body":      body.strip(),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }

    def disconnect(self):
        if self.conn:
            try:
                self.conn.logout()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# SMTP Sender
# ══════════════════════════════════════════════════════════════════════════════

class AgentSMTPSender:
    """Envia e-mails via SMTP."""

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_name: str = "AXION Agent",
        reply_to: str | None = None,
        html_body: str | None = None,
    ) -> bool:
        if not EMAIL_USER or not EMAIL_PASS:
            log.error("Credenciais de e-mail não configuradas.")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = email.utils.formataddr((from_name, EMAIL_USER))
            msg["To"]      = to
            msg["Subject"] = subject
            msg["Date"]    = email.utils.formatdate(localtime=True)
            if reply_to:
                msg["Reply-To"] = reply_to

            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                if SMTP_PORT != 25:
                    server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, [to], msg.as_bytes())

            record = {
                "to": to, "subject": subject, "body_preview": body[:200],
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent",
            }
            with open(SENT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.info(f"E-mail enviado para {to}: {subject}")
            return True

        except Exception as e:
            log.error(f"Falha ao enviar e-mail: {e}")
            return False


# ══════════════════════════════════════════════════════════════════════════════
# Agent Email Manager
# ══════════════════════════════════════════════════════════════════════════════

class AgentEmailManager:
    """
    Gerenciador central de e-mails para agentes AXION.
    
    Uso:
        mgr = AgentEmailManager()
        
        # Enviar alerta de infra
        mgr.send_agent_email(
            agent="axion-core",
            to="iago@example.com",
            subject="[ALERTA] SSL expirando em 7 dias",
            body="Domínio api.example.com expira em 2026-10-03",
        )
        
        # Processar inbox
        messages = mgr.poll_inbox()
        for msg in messages:
            print(msg["subject"], msg["from"])
    """

    def __init__(self):
        self.reader = AgentIMAPReader()
        self.sender = AgentSMTPSender()

    def send_agent_email(
        self,
        agent: str,
        to: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> bool:
        agent_info = AGENT_MAILBOXES.get(agent, {"display": "AXION Agent"})
        return self.sender.send(
            to=to,
            subject=subject,
            body=body,
            from_name=agent_info["display"],
            html_body=html_body,
        )

    def poll_inbox(self, folder: str = "INBOX") -> list[dict]:
        if not self.reader.connect():
            log.warning("IMAP indisponível — modo offline")
            return []
        messages = self.reader.fetch_unseen(folder)
        for msg in messages:
            with open(INBOX_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.reader.disconnect()
        log.info(f"Inbox polled: {len(messages)} novas mensagens")
        return messages

    def get_inbox_history(self, limit: int = 50) -> list[dict]:
        if not INBOX_LOG.exists():
            return []
        lines = INBOX_LOG.read_text("utf-8").strip().splitlines()
        return [json.loads(l) for l in lines[-limit:]]

    def get_sent_history(self, limit: int = 50) -> list[dict]:
        if not SENT_LOG.exists():
            return []
        lines = SENT_LOG.read_text("utf-8").strip().splitlines()
        return [json.loads(l) for l in lines[-limit:]]


# ══════════════════════════════════════════════════════════════════════════════
# CLI / Demo
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    mgr = AgentEmailManager()

    if len(sys.argv) > 1 and sys.argv[1] == "poll":
        msgs = mgr.poll_inbox()
        print(f"[poll] {len(msgs)} mensagens novas")
        for m in msgs:
            print(f"  FROM: {m['from']} | SUBJECT: {m['subject']}")

    elif len(sys.argv) > 1 and sys.argv[1] == "send":
        # python agent_email_client.py send "dest@email.com" "Assunto" "Corpo"
        _, _, to, subject, body = sys.argv[:5]
        ok = mgr.send_agent_email("axion-core", to, subject, body)
        print("[send] OK" if ok else "[send] FALHOU")

    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        print("=== INBOX HISTORY ===")
        for m in mgr.get_inbox_history(10):
            print(f"  {m.get('received_at','')} | {m.get('from','')} | {m.get('subject','')}")
        print("=== SENT HISTORY ===")
        for m in mgr.get_sent_history(10):
            print(f"  {m.get('sent_at','')} | {m.get('to','')} | {m.get('subject','')}")

    else:
        print("AXION Agent Email Client")
        print("  python agent_email_client.py poll       — buscar e-mails não lidos")
        print("  python agent_email_client.py send <to> <subject> <body>")
        print("  python agent_email_client.py history    — histórico inbox/sent")
        print()
        print("Variáveis de ambiente necessárias:")
        print("  AGENT_EMAIL_USER, AGENT_EMAIL_PASSWORD")
        print("  AGENT_EMAIL_IMAP, AGENT_EMAIL_IMAP_PORT")
        print("  AGENT_EMAIL_SMTP, AGENT_EMAIL_SMTP_PORT")
