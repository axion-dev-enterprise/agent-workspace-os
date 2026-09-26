# AXION Dev/Prod Manager
# Usage: .\scripts\env.ps1 [start|stop|restart|logs|status] [dev|prod]
param([string]$Action = "status", [string]$Env = "prod")
$EcoFile = if ($Env -eq "dev") { "scripts/pm2/ecosystem.dev.js" } else { "ecosystem.config.js" }
$BrainName = if ($Env -eq "dev") { "axion-brain-dev" } else { "axion-brain-server" }
$Port = if ($Env -eq "dev") { "8766" } else { "8765" }
Write-Host "AXION [$($Env.ToUpper())] $Action" -ForegroundColor Cyan
switch ($Action) {
    "start"   { pm2 start $EcoFile; Start-Sleep 3; try { $h = Invoke-RestMethod "http://127.0.0.1:$Port/v1/health" -TimeoutSec 5; Write-Host "Brain ONLINE (uptime=$([math]::Round($h.uptime_seconds))s)" -ForegroundColor Green } catch { Write-Host "Brain iniciando..." -ForegroundColor Yellow } }
    "stop"    { pm2 stop $BrainName 2>$null; pm2 stop (if ($Env -eq "dev") { "axion-bot-dev" } else { "axion-telegram-bot" }) 2>$null }
    "restart" { pm2 restart $BrainName; Write-Host "Brain reiniciado." -ForegroundColor Green }
    "logs"    { pm2 logs $BrainName --lines 60 }
    "status"  { pm2 status; try { $h = Invoke-RestMethod "http://127.0.0.1:$Port/v1/health" -TimeoutSec 3; Write-Host "Brain API: ONLINE | Uptime:$([math]::Round($h.uptime_seconds))s | Requests:$($h.active_requests)" -ForegroundColor Green } catch { Write-Host "Brain API: OFFLINE" -ForegroundColor Red } }
    default   { Write-Host "Uso: .\scripts\env.ps1 [start|stop|restart|logs|status] [dev|prod]" }
}
