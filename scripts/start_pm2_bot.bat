@echo off
setlocal
cd /d C:\workspace
echo [AXION] Starting AXION Telegram Bot and Cognitive Core under PM2...
call pm2 resurrect
call pm2 start C:\workspace\ecosystem.config.js
call pm2 save
exit /b 0
