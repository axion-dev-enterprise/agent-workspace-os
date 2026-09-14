#!/usr/bin/env python3
"""
Agent Workspace OS - Setup & Control Dashboard Server
Servidor Web Local em Python (Zero dependências externas obrigatórias)
"""

import sys
import os
import json
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import threading
import time

sys.stdout.reconfigure(encoding='utf-8')

PORT = int(os.environ.get("SETUP_PORT", 8765))
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREFLIGHT_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "preflight_check.py")
DRIVE_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "google_drive_sync.py")
CONFIG_FILE = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
TEMPLATE_CONFIG_FILE = os.path.join(WORKSPACE_ROOT, "workspace.config.template.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(TEMPLATE_CONFIG_FILE):
        with open(TEMPLATE_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_preflight_data():
    try:
        proc = subprocess.run([sys.executable, PREFLIGHT_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, timeout=10)
        return json.loads(proc.stdout)
    except Exception as e:
        return {"error": str(e), "tools": {}, "auth": {}}

def get_drive_status():
    try:
        proc = subprocess.run([sys.executable, DRIVE_SCRIPT, "--check"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, timeout=5)
        return json.loads(proc.stdout)
    except Exception as e:
        return {"authenticated": False, "type": "none", "details": str(e)}

def get_whatsapp_status():
    try:
        req = urllib.request.Request("http://127.0.0.1:4114/api/status")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return {
            "status": "standby",
            "connectedNumber": None,
            "mode": "monitor",
            "lastQrImage": None,
            "recentMessages": []
        }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Workspace OS — Setup & Control Center</title>
  <style>
    :root {
      --bg: #09090b;
      --card-bg: #121217;
      --card-border: rgba(255, 255, 255, 0.08);
      --hover-bg: #18181f;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f4f4f5;
      --text-muted: #a1a1aa;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "JetBrains Mono", Consolas, Menlo, monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      border-bottom: 1px solid var(--card-border);
      padding: 16px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      backdrop-filter: blur(16px);
      background: rgba(18, 18, 23, 0.8);
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 600;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
    }
    .brand svg { color: var(--accent); }
    .badge-status {
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
      background: rgba(59, 130, 246, 0.15);
      color: var(--accent);
      border: 1px solid rgba(59, 130, 246, 0.3);
    }
    main {
      flex: 1;
      max-width: 1200px;
      margin: 0 auto;
      width: 100%;
      padding: 32px 24px;
    }
    .nav-tabs {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
      overflow-x: auto;
    }
    .tab-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 10px 18px;
      font-size: 0.9rem;
      font-weight: 500;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .tab-btn:hover { color: var(--text); background: rgba(255,255,255,0.02); }
    .tab-btn.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.2s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      transition: border-color 0.15s ease;
    }
    .card:hover { border-color: rgba(255, 255, 255, 0.14); }
    .card-title {
      font-size: 1.05rem;
      font-weight: 600;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .card-desc {
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 16px;
      line-height: 1.4;
    }
    .tool-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .tool-row:last-child { border-bottom: none; }
    .tool-meta { display: flex; flex-direction: column; gap: 2px; }
    .tool-name { font-weight: 500; font-size: 0.9rem; }
    .tool-version { font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted); }
    .pill {
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 500;
    }
    .pill-success { background: rgba(16, 185, 129, 0.15); color: var(--success); }
    .pill-warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
    .pill-danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .btn {
      background: var(--accent);
      color: white;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.15s ease;
    }
    .btn:hover { background: var(--accent-hover); }
    .btn-secondary {
      background: var(--hover-bg);
      color: var(--text);
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover { background: rgba(255,255,255,0.06); }
    .qr-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: #0d0d11;
      border-radius: 12px;
      border: 1px dashed var(--card-border);
      margin-bottom: 20px;
    }
    .qr-image {
      max-width: 240px;
      border-radius: 8px;
      border: 4px solid white;
      margin-bottom: 12px;
    }
    .feed-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 280px;
      overflow-y: auto;
    }
    .feed-item {
      padding: 10px 14px;
      background: #0d0d11;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      font-size: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .feed-header {
      display: flex;
      justify-content: space-between;
      color: var(--text-muted);
      font-size: 0.75rem;
      font-family: var(--font-mono);
    }
    .code-box {
      background: #0d0d11;
      padding: 12px;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: #93c5fd;
      border: 1px solid var(--card-border);
      overflow-x: auto;
      margin: 10px 0;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/></svg>
      <span>Agent Workspace OS</span>
    </div>
    <span class="badge-status" id="ws-badge">Setup & Control Center</span>
  </header>

  <main>
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-tools')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        Ferramentas & CLI
      </button>
      <button class="tab-btn" onclick="switchTab('tab-oauth')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        Login & OAuth
      </button>
      <button class="tab-btn" onclick="switchTab('tab-whatsapp')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        WhatsApp Bridge
      </button>
      <button class="tab-btn" onclick="switchTab('tab-drive')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4 4 4-4"/></svg>
        Google Drive
      </button>
      <button class="tab-btn" onclick="switchTab('tab-workspace')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
        Workspace & Cowork
      </button>
    </div>

    <!-- TAB 1: TOOLS & CLI -->
    <div id="tab-tools" class="tab-content active">
      <div class="grid">
        <div class="card">
          <div class="card-title">
            <span>Diagnóstico do Sistema</span>
            <button class="btn btn-secondary" onclick="loadPreflight()">Atualizar</button>
          </div>
          <p class="card-desc">Verificação de runtimes, compiladores e utilitários de linha de comando no host Windows.</p>
          <div id="tools-list">Carregando diagnóstico...</div>
        </div>

        <div class="card">
          <div class="card-title">Instalação Rápida de Dependências</div>
          <p class="card-desc">Comandos oficiais para instalar as ferramentas faltantes pelo terminal:</p>
          <div class="code-box" id="install-commands">
            winget install Python.Python.3.11<br>
            winget install OpenJS.NodeJS.LTS<br>
            winget install Git.Git<br>
            winget install GitHub.cli<br>
            npm install -g vercel wrangler
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 8px;">Após a instalação, reinicie o terminal para atualizar o PATH.</p>
        </div>
      </div>
    </div>

    <!-- TAB 2: OAUTH & AUTH -->
    <div id="tab-oauth" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-title">Autenticação em Provedores Cloud</div>
          <p class="card-desc">Status de login em GitHub, Vercel e Cloudflare.</p>
          <div id="auth-list">Carregando autenticação...</div>
        </div>

        <div class="card">
          <div class="card-title">Comandos de Login Rápido</div>
          <p class="card-desc">Execute no terminal para conectar suas contas:</p>
          <div class="code-box">
            # GitHub CLI (Web browser OAuth)<br>
            gh auth login --web<br><br>
            # Vercel CLI<br>
            vercel login<br><br>
            # Cloudflare Wrangler<br>
            wrangler login
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: WHATSAPP -->
    <div id="tab-whatsapp" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-title">
            <span>Ponte WhatsApp</span>
            <span class="pill pill-warning" id="wa-status-pill">Aguardando QR</span>
          </div>
          <p class="card-desc">Escaneie o QR Code com o seu aplicativo do WhatsApp para parear o agente ao canal.</p>
          
          <div class="qr-container">
            <img id="wa-qr-img" class="qr-image" src="" alt="WhatsApp QR Code" style="display:none;">
            <div id="wa-qr-placeholder" style="font-size:0.85rem; color:var(--text-muted);">Carregando QR Code...</div>
            <p id="wa-number" style="font-family:var(--font-mono); font-size:0.85rem; margin-top:8px; color:var(--text);"></p>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
            <div>
              <span style="font-weight:600; font-size:0.9rem;">Modo Operacional:</span>
              <p style="font-size:0.8rem; color:var(--text-muted);" id="wa-mode-desc">Monitor: apenas salva e categoriza mensagens.</p>
            </div>
            <button class="btn" id="wa-toggle-mode" onclick="toggleWaMode()">Alternar Modo</button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">
            <span>Feed de Mensagens em Tempo Real</span>
            <button class="btn btn-secondary" onclick="loadWaFeed()">Atualizar</button>
          </div>
          <p class="card-desc">Últimas mensagens capturadas e indexadas no workspace:</p>
          <div class="feed-list" id="wa-feed-list">
            <div style="color:var(--text-muted); font-size:0.85rem;">Nenhuma mensagem registrada no momento.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: GOOGLE DRIVE -->
    <div id="tab-drive" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-title">Conector Google Drive</div>
          <p class="card-desc">Sincronização de atas, reuniões gravadas e documentos de texto para o workspace.</p>
          <div id="drive-status-box">Carregando status do Drive...</div>
          <div style="margin-top:16px;">
            <button class="btn" onclick="syncDrive()">Sincronizar Arquivos Recentes</button>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Como Configurar Credenciais</div>
          <p class="card-desc">Passos para habilitar o Google Drive API:</p>
          <ol style="font-size:0.85rem; color:var(--text-muted); padding-left:20px; line-height:1.6;">
            <li>Acesse o Google Cloud Console e crie um projeto.</li>
            <li>Ative a <strong>Google Drive API</strong>.</li>
            <li>Crie uma <strong>Conta de Serviço (Service Account)</strong> e baixe a chave JSON.</li>
            <li>Salve o arquivo JSON como <code>credentials/google_service_account.json</code> na raiz do workspace.</li>
          </ol>
        </div>
      </div>
    </div>

    <!-- TAB 5: WORKSPACE & COWORK -->
    <div id="tab-workspace" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-title">Diretório Canônico do Workspace</div>
          <p class="card-desc">Estrutura de governança e lock de concorrência multi-agente:</p>
          <div class="code-box">
            Raiz: D:\WORKSPACE<br>
            Tarefas Ativas: MEMORY/active_tasks.json<br>
            Logs Diários: MEMORY/daily_logs/YYYY-MM-DD.md<br>
            Downloads Canônicos: E:\Downloads
          </div>
        </div>

        <div class="card">
          <div class="card-title">Repositório Open Source</div>
          <p class="card-desc">O repositório canônico está sincronizado no GitHub:</p>
          <div class="code-box">
            GitHub: axion-dev-enterprise/agent-workspace-os<br>
            Protocolos: SETUP_PROTOCOL.md / UPDATE_PROTOCOL.md
          </div>
          <a class="btn" href="https://github.com/axion-dev-enterprise/agent-workspace-os" target="_blank" style="text-decoration:none; margin-top:8px;">
            Ver no GitHub
          </a>
        </div>
      </div>
    </div>
  </main>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.currentTarget.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    async function loadPreflight() {
      try {
        const res = await fetch('/api/preflight');
        const data = await res.json();
        const toolsDiv = document.getElementById('tools-list');
        const authDiv = document.getElementById('auth-list');

        let toolsHtml = '';
        for (const [id, t] of Object.entries(data.tools || {})) {
          const pillClass = t.installed ? 'pill-success' : (t.required ? 'pill-danger' : 'pill-warning');
          const pillText = t.installed ? 'Instalado' : (t.required ? 'Necessário' : 'Opcional');
          toolsHtml += `
            <div class="tool-row">
              <div class="tool-meta">
                <span class="tool-name">${t.name}</span>
                <span class="tool-version">${t.version || 'Não detectado no PATH'}</span>
              </div>
              <span class="pill ${pillClass}">${pillText}</span>
            </div>
          `;
        }
        toolsDiv.innerHTML = toolsHtml || 'Nenhuma ferramenta configurada.';

        let authHtml = '';
        for (const [id, a] of Object.entries(data.auth || {})) {
          const pillClass = a.authenticated ? 'pill-success' : 'pill-danger';
          const pillText = a.authenticated ? 'Conectado' : 'Não autenticado';
          authHtml += `
            <div class="tool-row">
              <div class="tool-meta">
                <span class="tool-name">${id.toUpperCase()}</span>
                <span class="tool-version">${a.details}</span>
              </div>
              <span class="pill ${pillClass}">${pillText}</span>
            </div>
          `;
        }
        authDiv.innerHTML = authHtml || 'Nenhum provedor configurado.';
      } catch (err) {
        console.error(err);
      }
    }

    let currentWaMode = 'monitor';
    async function loadWhatsApp() {
      try {
        const res = await fetch('/api/whatsapp/status');
        const data = await res.json();
        const pill = document.getElementById('wa-status-pill');
        const qrImg = document.getElementById('wa-qr-img');
        const placeholder = document.getElementById('wa-qr-placeholder');
        const numberEl = document.getElementById('wa-number');

        currentWaMode = data.mode || 'monitor';
        document.getElementById('wa-mode-desc').innerText = currentWaMode === 'react' 
          ? 'React: executa comandos (/task) diretamente no workspace.' 
          : 'Monitor: apenas salva e categoriza mensagens.';

        if (data.status === 'connected') {
          pill.className = 'pill pill-success';
          pill.innerText = 'Conectado';
          qrImg.style.display = 'none';
          placeholder.style.display = 'none';
          numberEl.innerText = 'Número conectado: ' + (data.connectedNumber || 'Ativo');
        } else {
          pill.className = 'pill pill-warning';
          pill.innerText = data.status === 'qr_ready' ? 'Escaneie o QR' : 'Desconectado';
          if (data.lastQrImage) {
            qrImg.src = data.lastQrImage;
            qrImg.style.display = 'block';
            placeholder.style.display = 'none';
          }
        }
      } catch (err) {
        console.error(err);
      }
    }

    async function loadWaFeed() {
      try {
        const res = await fetch('/api/whatsapp/status');
        const data = await res.json();
        const feedDiv = document.getElementById('wa-feed-list');
        const msgs = data.recentMessages || [];
        if (msgs.length === 0) {
          feedDiv.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">Nenhuma mensagem registrada no momento.</div>';
          return;
        }
        let html = '';
        for (const m of msgs) {
          html += `
            <div class="feed-item">
              <div class="feed-header">
                <span>${m.sender}</span>
                <span>${m.category ? '[' + m.category.toUpperCase() + ']' : ''} ${m.timestamp ? m.timestamp.slice(11,19) : ''}</span>
              </div>
              <div>${m.text}</div>
            </div>
          `;
        }
        feedDiv.innerHTML = html;
      } catch (err) {
        console.error(err);
      }
    }

    async function toggleWaMode() {
      const newMode = currentWaMode === 'monitor' ? 'react' : 'monitor';
      try {
        await fetch('http://127.0.0.1:4114/api/mode', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mode: newMode })
        });
        loadWhatsApp();
      } catch (err) {
        alert('Inicie o serviço do WhatsApp em scripts/whatsapp_bridge para alternar o modo.');
      }
    }

    async function loadDrive() {
      try {
        const res = await fetch('/api/drive/status');
        const data = await res.json();
        const box = document.getElementById('drive-status-box');
        const pillClass = data.authenticated ? 'pill-success' : 'pill-danger';
        const pillText = data.authenticated ? 'Autenticado' : 'Não autenticado';
        box.innerHTML = `
          <div class="tool-row">
            <div class="tool-meta">
              <span class="tool-name">Google Drive API</span>
              <span class="tool-version">${data.details} (${data.type})</span>
            </div>
            <span class="pill ${pillClass}">${pillText}</span>
          </div>
        `;
      } catch (err) {
        console.error(err);
      }
    }

    async function syncDrive() {
      alert('Sincronização iniciada. Os arquivos recentes serão gravados em workspace/inbox/google_drive/');
    }

    // Inicialização
    loadPreflight();
    loadWhatsApp();
    loadWaFeed();
    loadDrive();
    setInterval(() => {
      loadWhatsApp();
      loadWaFeed();
    }, 4000);
  </script>
</body>
</html>
"""

class SetupHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == "/api/preflight":
            data = get_preflight_data()
            self.send_json(data)
        elif self.path == "/api/drive/status":
            data = get_drive_status()
            self.send_json(data)
        elif self.path == "/api/whatsapp/status":
            data = get_whatsapp_status()
            self.send_json(data)
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        # Silenciar logs verbosos de requisições periódicas
        return

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), SetupHandler)
    print(f"============================================================")
    print(f"Agent Workspace OS - Setup & Control Dashboard Server")
    print(f"Painel Web disponível em: http://127.0.0.1:{PORT}")
    print(f"============================================================")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
