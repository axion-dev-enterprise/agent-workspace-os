@echo off
chcp 65001 >nul
title Autonomous Agent Workspace OS - Cold Start Setup
echo =================================================================
echo   Autonomous Agent Workspace OS - One-Click Cold Start Setup
echo =================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
echo.
pause
