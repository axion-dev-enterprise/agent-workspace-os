@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Autonomous Agent Workspace OS
echo =================================================================
echo   Autonomous Agent Workspace OS - Starting System Services
echo =================================================================
echo.

where pm2 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Iniciando servicos via PM2 Process Manager...
    call pm2 start ecosystem.config.js
    call pm2 status
    echo.
    echo [OK] Servicos iniciados no background.
    echo Brain API: http://127.0.0.1:8765
    echo.
) else (
    echo [!] PM2 nao detectado. Iniciando Brain API diretamente via Python...
    echo Para gerenciar em background, instale: npm install -g pm2
    echo.
    python scripts/brain_server.py
)

pause
