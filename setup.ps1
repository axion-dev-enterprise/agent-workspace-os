# ==============================================================================
# Autonomous Agent Workspace OS — One-Click Setup & Cold-Start Script
# ==============================================================================
param (
    [switch]$SkipNpm,
    [switch]$SkipPython
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   🚀 Autonomous Agent Workspace OS — Setup & Cold Start" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Check Prerequisites
Write-Host "`n[*] Verificando pré-requisitos do sistema..." -ForegroundColor Yellow

# Node.js
try {
    $nodeVer = (node -v).Trim()
    Write-Host "  ✅ Node.js encontrado: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Node.js não encontrado! Por favor, instale o Node.js v18+ (https://nodejs.org)." -ForegroundColor Red
    exit 1
}

# Python
try {
    $pyVer = (python --version).Trim()
    Write-Host "  ✅ Python encontrado: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python não encontrado! Por favor, instale o Python 3.10+ (https://python.org)." -ForegroundColor Red
    exit 1
}

# Git
try {
    $gitVer = (git --version).Trim()
    Write-Host "  ✅ Git encontrado: $gitVer" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Git não encontrado no PATH. Algumas ferramentas de versionamento podem falhar." -ForegroundColor Yellow
}

# PM2
$pm2Installed = $false
try {
    $pm2Ver = (pm2 -v 2>$null).Trim()
    if ($pm2Ver) {
        Write-Host "  ✅ PM2 Process Manager encontrado: v$pm2Ver" -ForegroundColor Green
        $pm2Installed = $true
    }
} catch {
    $pm2Installed = $false
}

if (-not $pm2Installed) {
    Write-Host "  ⚠️ PM2 não detectado globalmente. Instalando via npm install -g pm2..." -ForegroundColor Yellow
    try {
        npm install -g pm2 --silent
        Write-Host "  ✅ PM2 instalado com sucesso globalmente!" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Não foi possível instalar PM2 globalmente. Você pode executar 'npm install -g pm2' manualmente." -ForegroundColor Yellow
    }
}

# 2. Setup Environment Configuration (.env)
Write-Host "`n[*] Verificando arquivo de ambiente .env..." -ForegroundColor Yellow
$envPath = Join-Path $ScriptDir ".env"
$envExamplePath = Join-Path $ScriptDir ".env.example"

if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item -Path $envExamplePath -Destination $envPath
        Write-Host "  ✅ Arquivo .env criado a partir de .env.example!" -ForegroundColor Green
        Write-Host "  ⚠️ LEMBRE-SE: Abra o arquivo .env e configure suas chaves (OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN, etc.)." -ForegroundColor Magenta
    } else {
        Write-Host "  ⚠️ .env.example não encontrado para cópia." -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ Arquivo .env já existe." -ForegroundColor Green
}

# 3. Create Required Directory Hierarchy
Write-Host "`n[*] Criando estrutura de diretórios e memória persistente..." -ForegroundColor Yellow
$requiredDirs = @(
    "memory/brain/pm2_logs",
    "memory/telegram/pm2_logs",
    "memory/whatsapp/pm2_logs",
    "memory/desktop_agents",
    "memory/cowork",
    "memory/daily_logs",
    "workspace/inbox/whatsapp/media",
    "temp",
    "reports"
)

foreach ($dir in $requiredDirs) {
    $target = Join-Path $ScriptDir $dir
    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Force -Path $target | Out-Null
    }
}
Write-Host "  ✅ Estrutura de memória e logs inicializada." -ForegroundColor Green

# 4. Install WhatsApp Bridge Dependencies (Node.js)
if (-not $SkipNpm) {
    Write-Host "`n[*] Instalando dependências do WhatsApp Bridge (Baileys)..." -ForegroundColor Yellow
    $waBridgeDir = Join-Path $ScriptDir "scripts\whatsapp_bridge"
    if (Test-Path $waBridgeDir) {
        Push-Location $waBridgeDir
        try {
            npm install --prefer-offline --no-audit --silent
            Write-Host "  ✅ Módulos npm do WhatsApp Bridge instalados!" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️ Falha ao rodar npm install no WhatsApp bridge: $_" -ForegroundColor Yellow
        } finally {
            Pop-Location
        }
    }
}

# 5. Install Python Core Dependencies
if (-not $SkipPython) {
    Write-Host "`n[*] Verificando e instalando pacotes essenciais do Python..." -ForegroundColor Yellow
    $pyPkgs = @("requests", "psutil")
    foreach ($pkg in $pyPkgs) {
        try {
            python -c "import $pkg" 2>$null
            Write-Host "  ✅ Python: $pkg disponível" -ForegroundColor Green
        } catch {
            Write-Host "  Instalando $pkg via pip..." -ForegroundColor Gray
            pip install $pkg --quiet
        }
    }
}

# 6. Verify Desktop CLIs Availability
Write-Host "`n[*] Inspecionando agentes desktop instalados no host..." -ForegroundColor Yellow
$clis = @(
    @{ Name = "OpenAI Codex"; Cmd = "codex" },
    @{ Name = "Google Antigravity"; Cmd = "agy" },
    @{ Name = "OpenCode"; Cmd = "opencode" }
)

foreach ($cli in $clis) {
    try {
        $c = Get-Command $cli.Cmd -ErrorAction SilentlyContinue
        if ($c) {
            Write-Host "  ✅ $($cli.Name) encontrado no PATH: $($c.Source)" -ForegroundColor Green
        } else {
            Write-Host "  ℹ️ $($cli.Name) ('$($cli.Cmd)') não encontrado no PATH (opcional - orquestrador usará fallback se necessário)." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "  ℹ️ $($cli.Name) não detectado." -ForegroundColor DarkGray
    }
}

# 7. Final Instructions
Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  🎉 Setup concluído com sucesso!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Para iniciar o sistema:" -ForegroundColor White
Write-Host "  1. Edite o arquivo .env com suas chaves de API." -ForegroundColor Yellow
Write-Host "  2. Execute: .\start.bat  (ou 'pm2 start ecosystem.config.js')" -ForegroundColor Yellow
Write-Host "  3. Painel Brain API escutando em: http://127.0.0.1:8765" -ForegroundColor White
Write-Host "=================================================================`n" -ForegroundColor Cyan
