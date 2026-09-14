/**
 * WhatsApp Client Bridge — Agent Workspace OS
 * 
 * Expõe endpoints HTTP locais para:
 * - GET  /status : Retorna o status de conexão (disconnected, qr_ready, connected) e número
 * - GET  /qr     : Retorna a imagem do QR code em Data URL (PNG)
 * - POST /mode   : Alterna entre 'monitor' e 'react'
 * - GET  /feed   : Retorna as últimas mensagens capturadas
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const QRCode = require('qrcode');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.WHATSAPP_PORT || 4114;
const WORKSPACE_ROOT = path.resolve(__dirname, '../../');
const INBOX_DIR = path.join(WORKSPACE_ROOT, 'workspace', 'inbox', 'whatsapp');
const TASKS_FILE = path.join(WORKSPACE_ROOT, 'workspace', 'memory', 'active_tasks.json');

fs.mkdirSync(INBOX_DIR, { recursive: true });
fs.mkdirSync(path.dirname(TASKS_FILE), { recursive: true });

let state = {
  status: 'qr_ready', // 'disconnected' | 'qr_ready' | 'connected'
  connectedNumber: null,
  mode: 'monitor', // 'monitor' | 'react'
  lastQrRaw: 'https://github.com/axion-dev-enterprise/agent-workspace-os#whatsapp-pairing-demo',
  lastQrImage: null,
  recentMessages: []
};

// Generate initial QR code image
QRCode.toDataURL(state.lastQrRaw, { width: 300, margin: 2 }, (err, url) => {
  if (!err) state.lastQrImage = url;
});

// Registrar mensagem no feed e no workspace
function recordMessage(msg) {
  state.recentMessages.unshift(msg);
  if (state.recentMessages.length > 50) state.recentMessages.pop();

  const today = new Date().toISOString().slice(0, 10);
  const logFile = path.join(INBOX_DIR, `${today}.jsonl`);
  fs.appendFileSync(logFile, JSON.stringify(msg) + '\n', 'utf8');

  // Modo REACT: se contiver /task ou menção, enfileirar no active_tasks.json
  if (state.mode === 'react' && msg.text && (msg.text.startsWith('/task') || msg.text.toLowerCase().includes('@agente'))) {
    enqueTask(msg);
  }
}

function enqueTask(msg) {
  try {
    let tasks = [];
    if (fs.existsSync(TASKS_FILE)) {
      tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8'));
    }
    const newTask = {
      id: `task_${Date.now()}`,
      source: 'whatsapp',
      from: msg.sender,
      instruction: msg.text.replace(/^\/task\s*/i, '').trim(),
      status: 'pending',
      created_at: new Date().toISOString()
    };
    tasks.push(newTask);
    fs.writeFileSync(TASKS_FILE, JSON.stringify(tasks, null, 2), 'utf8');
    console.log(`[REACT] Nova tarefa enfileirada: ${newTask.instruction}`);
  } catch (err) {
    console.error('[REACT ERROR]', err);
  }
}

// Iniciação do Baileys real se instalado
let sock = null;
async function initBaileys() {
  try {
    const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
    const authDir = path.join(__dirname, 'auth_info_baileys');
    fs.mkdirSync(authDir, { recursive: true });
    const { state: authState, saveCreds } = await useMultiFileAuthState(authDir);

    sock = makeWASocket({
      auth: authState,
      printQRInTerminal: false,
      browser: ['Agent Workspace OS', 'Chrome', '1.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;
      if (qr) {
        state.status = 'qr_ready';
        state.lastQrRaw = qr;
        state.lastQrImage = await QRCode.toDataURL(qr, { width: 300, margin: 2 });
      }
      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
        state.status = 'disconnected';
        state.connectedNumber = null;
        if (shouldReconnect) initBaileys();
      } else if (connection === 'open') {
        state.status = 'connected';
        state.connectedNumber = sock.user?.id?.split(':')[0] || 'Conectado';
      }
    });

    sock.ev.on('messages.upsert', async (m) => {
      const msg = m.messages[0];
      if (!msg.key.fromMe && m.type === 'notify') {
        const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || '[Mídia / Áudio / Documento]';
        const sender = msg.key.remoteJid;
        const entry = {
          id: msg.key.id,
          sender: sender,
          text: text,
          timestamp: new Date().toISOString(),
          category: categorizeMessage(text)
        };
        recordMessage(entry);
      }
    });
  } catch (err) {
    console.log('[INFO] Baileys real em modo standby ou pacotes não instalados. Operando com simulador e API pronta.');
  }
}

function categorizeMessage(text) {
  const t = text.toLowerCase();
  if (t.includes('reuni') || t.includes('pauta') || t.includes('ata')) return 'reuniao';
  if (t.includes('/task') || t.includes('fazer') || t.includes('tarefa') || t.includes('urgente')) return 'tarefa';
  if (t.includes('preço') || t.includes('proposta') || t.includes('orçamento')) return 'lead';
  if (t.includes('áudio') || t.includes('audio')) return 'audio';
  return 'geral';
}

// REST Endpoints
app.get('/api/status', (req, res) => {
  res.json(state);
});

app.get('/api/qr', (req, res) => {
  res.json({
    status: state.status,
    qr_image: state.lastQrImage,
    qr_raw: state.lastQrRaw
  });
});

app.post('/api/mode', (req, res) => {
  const { mode } = req.body;
  if (['monitor', 'react'].includes(mode)) {
    state.mode = mode;
    return res.json({ success: true, mode: state.mode });
  }
  res.status(400).json({ error: 'Modo inválido. Use "monitor" ou "react".' });
});

app.get('/api/feed', (req, res) => {
  res.json({ messages: state.recentMessages });
});

// Endpoint de simulação / mock de teste para desenvolvimento local
app.post('/api/simulate-message', (req, res) => {
  const { text, sender } = req.body;
  const msg = {
    id: `sim_${Date.now()}`,
    sender: sender || '5511999999999@s.whatsapp.net',
    text: text || 'Exemplo de mensagem de teste',
    timestamp: new Date().toISOString(),
    category: categorizeMessage(text || '')
  };
  recordMessage(msg);
  res.json({ success: true, message: msg });
});

app.listen(PORT, () => {
  console.log(`WhatsApp Bridge running on http://127.0.0.1:${PORT}`);
  initBaileys();
});
