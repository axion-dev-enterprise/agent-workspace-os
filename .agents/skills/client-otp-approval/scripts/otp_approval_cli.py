#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
otp_approval_cli.py — CLI Operacional de Aprovação de Recursos & OTP de Clientes
Part of client-otp-approval skill — AXION Enterprise
Permite listar aprovações pendentes, consultar status e simular requisições.
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import json
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPTS_DIR = Path(r"C:\workspace\scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def list_approvals(status_filter: str = None) -> list:
    """Carrega todas as aprovações registradas."""
    try:
        from bot_engine import client_approval
        approvals = client_approval.load_approvals()
        if status_filter:
            return [a for a in approvals if a.get("status") == status_filter]
        return approvals
    except Exception as e:
        return [{"error": str(e)}]


def check_single_approval(request_id: str) -> dict:
    """Verifica o status de uma aprovação específica."""
    try:
        from bot_engine import client_approval
        return client_approval.check_approval_status(request_id)
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="CLI de Aprovação e Gestão de OTP/Recursos de Clientes (AXION)")
    parser.add_argument("--list", action="store_true", help="Lista todas as aprovações registradas")
    parser.add_argument("--status", choices=["pending", "approved", "rejected", "expired"], help="Filtra por status")
    parser.add_argument("--check-id", help="Consulta status de um request_id específico")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON estruturado")
    args = parser.parse_args()

    if args.check_id:
        result = check_single_approval(args.check_id)
    else:
        result = list_approvals(args.status)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n═════════════════════════════════════════════════════════════════════")
        print("       AXION CLIENT OTP & RESOURCE APPROVAL — AUDITORIA              ")
        print("═════════════════════════════════════════════════════════════════════")
        if isinstance(result, list):
            print(f"Total de Registros: {len(result)}")
            for item in result:
                req_id = item.get("request_id", "N/A")
                st = item.get("status", "unknown").upper()
                client = item.get("client_name", "Desconhecido")
                res_type = item.get("resource_type", "Recurso")
                print(f"  • [{st}] {req_id} | {client} ({res_type})")
        elif isinstance(result, dict):
            for k, v in result.items():
                print(f"  • {k.ljust(18)}: {v}")
        print("═════════════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
