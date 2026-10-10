#!/usr/bin/env bash
# ==============================================================================
# Autonomous Agent Workspace OS — Linux/macOS Cold Start Setup
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "   🚀 Autonomous Agent Workspace OS — Setup & Cold Start"
echo "================================================================="

# 1. Prerequisites Check
echo "[*] Verificando pré-requisitos..."
if ! command -v node &> /dev/null; then
    echo "  ❌ Node.js não encontrado! Instale Node.js v18+."
    exit 1
fi
echo "  ✅ Node.js: $(node -v)"

if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 não encontrado! Instale Python 3.10+."
    exit 1
fi
echo "  ✅ Python: $(python3 --version)"

# 2. Setup .env
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "  ✅ Arquivo .env criado a partir de .env.example."
        echo "  ⚠️ Configure suas chaves no .env antes de iniciar!"
    fi
else
    echo "  ✅ Arquivo .env já existe."
fi

# 3. Create required directories
mkdir -p memory/brain/pm2_logs memory/telegram/pm2_logs memory/whatsapp/pm2_logs
mkdir -p memory/desktop_agents memory/cowork memory/daily_logs workspace/inbox/whatsapp/media temp reports
echo "  ✅ Diretórios de memória e logs inicializados."

# 4. WhatsApp Bridge dependencies
if [ -d scripts/whatsapp_bridge ]; then
    echo "[*] Instalando dependências do WhatsApp Bridge (Baileys)..."
    cd scripts/whatsapp_bridge
    npm install --prefer-offline --no-audit --silent || true
    cd "$DIR"
    echo "  ✅ Dependências do WhatsApp Bridge instaladas."
fi

# 5. Python packages
echo "[*] Verificando pacotes Python..."
python3 -c "import requests, psutil" 2>/dev/null || pip3 install requests psutil --quiet || true

# 6. PM2 check
if ! command -v pm2 &> /dev/null; then
    echo "  ℹ️ PM2 não encontrado globalmente. Você pode instalar via: npm install -g pm2"
else
    echo "  ✅ PM2 encontrado: $(pm2 -v)"
fi

echo "================================================================="
echo "  🎉 Setup concluído! Inicie com: ./start.sh"
echo "================================================================="
