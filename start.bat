@echo off
chcp 65001 >nul
title Agent Workspace OS - Setup & Control Center
echo ============================================================
echo   Agent Workspace OS v1.1.0 - Setup & Control Center
echo ============================================================
echo.
echo Abrindo painel visual no seu navegador...
start "" "http://127.0.0.1:8765"
echo.
echo Servidor ativo em: http://127.0.0.1:8765
echo Pressione Ctrl+C para encerrar o servidor.
echo.
python scripts/setup_server.py
pause
