#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "  Autonomous Agent Workspace OS - Starting System Services"
echo "================================================================="

if command -v pm2 &> /dev/null; then
    echo "[*] Iniciando servicos via PM2..."
    pm2 start ecosystem.config.js
    pm2 status
    echo "[OK] Servicos iniciados. Brain API: http://127.0.0.1:8765"
else
    echo "[!] PM2 nao encontrado. Iniciando Brain Server via Python..."
    python3 scripts/brain_server.py
fi
