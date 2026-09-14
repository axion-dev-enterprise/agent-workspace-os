#!/usr/bin/env bash
echo "============================================================"
echo "  Agent Workspace OS v1.1.0 - Setup & Control Center"
echo "============================================================"
echo ""
echo "Abrindo painel visual no seu navegador..."
if command -v xdg-open > /dev/null; then
  xdg-open "http://127.0.0.1:8765" &
elif command -v open > /dev/null; then
  open "http://127.0.0.1:8765" &
fi
echo ""
echo "Servidor ativo em: http://127.0.0.1:8765"
echo "Pressione Ctrl+C para encerrar o servidor."
echo ""
python3 scripts/setup_server.py || python scripts/setup_server.py
