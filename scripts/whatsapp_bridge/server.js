/**
 * WhatsApp Client Bridge — Agent Workspace OS
 * Production-ready Baileys Bridge with:
 * - Real QR Code generation via Baileys & qrcode (Zero Mock)
 * - Self-chat & Note-to-Self message capture (fromMe handling)
 * - Automatic Audio Download & Instant Whisper Transcription (Groq / OpenAI)
 * - Local inbox storage (JSONL + Media) & Reactive Task Queue
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

const PORT = parseInt(process.env.WHATSAPP_PORT || '4114', 10);
const WORKSPACE_ROOT = path.resolve(__dirname, '../../');
const INBOX_DIR = path.join(WORKSPACE_ROOT, 'workspace', 'inbox', 'whatsapp');
const MEDIA_DIR = path.join(INBOX_DIR, 'media');
const TASKS_FILE = path.join(WORKSPACE_ROOT, 'workspace', 'memory', 'active_tasks.json');
const CONFIG_FILE = path.join(WORKSPACE_ROOT, 'workspace.config.json');

try { fs.mkdirSync(INBOX_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(MEDIA_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(path.dirname(TASKS_FILE), { recursive: true }); } catch (_) {}

// ── State ──────────────────────────────────────────────────
let state = {
  status: 'offline', // 'offline' | 'installing' | 'qr_ready' | 'connected' | 'disconnected'
  connectedNumber: null,
  mode: 'monitor', // 'monitor' | 'react'
  lastQrRaw: null,
  lastQrImage: null,
  recentMessages: [],
  transcriptionProvider: 'none', // 'groq' | 'openai' | 'none'
  message: ''
};

// ── Resolve Transcription API Keys ───────────────────────────
function resolveApiKeys() {
  let groqKey = process.env.GROQ_API_KEY || '';
  let openaiKey = process.env.OPENAI_API_KEY || '';

  // 1. Check workspace.config.json
  if (fs.existsSync(CONFIG_FILE)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      groqKey = groqKey || cfg.ai?.groq_api_key || cfg.transcription?.groq_api_key || cfg.groq_api_key || '';
      openaiKey = openaiKey || cfg.ai?.openai_api_key || cfg.openai_api_key || '';
    } catch (_) {}
  }

  // 2. Check local .env in workspace root
  const envFile = path.join(WORKSPACE_ROOT, '.env');
  if (fs.existsSync(envFile)) {
    try {
      const lines = fs.readFileSync(envFile, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('GROQ_API_KEY=')) {
          groqKey = groqKey || trimmed.split('=')[1].trim().replace(/^["']|["']$/g, '');
        }
        if (trimmed.startsWith('OPENAI_API_KEY=')) {
          openaiKey = openaiKey || trimmed.split('=')[1].trim().replace(/^["']|["']$/g, '');
        }
      }
    } catch (_) {}
  }

  // 3. Check development host vault (D:/WORKSPACE/SECURE/VAULT/tokens/llm/groq.env)
  const vaultGroq = 'D:/WORKSPACE/SECURE/VAULT/tokens/llm/groq.env';
  if (!groqKey && fs.existsSync(vaultGroq)) {
    try {
      const lines = fs.readFileSync(vaultGroq, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('GROQ_API_KEY=')) {
          groqKey = trimmed.split('=')[1].trim().replace(/^["']|["']$/g, '');
          break;
        }
      }
    } catch (_) {}
  }

  if (groqKey) {
    state.transcriptionProvider = 'groq';
  } else if (openaiKey) {
    state.transcriptionProvider = 'openai';
  } else {
    state.transcriptionProvider = 'none';
  }

  return { groqKey, openaiKey };
}

// ── Audio Transcription via Whisper ──────────────────────────
async function transcribeAudioBuffer(audioBuffer, filename, mimetype = 'audio/ogg') {
  const { groqKey, openaiKey } = resolveApiKeys();

  // Try Groq Whisper (Ultra-fast, high accuracy, whisper-large-v3-turbo)
  if (groqKey) {
    try {
      console.log(`[WHISPER] Transcrevendo áudio ${filename} via Groq API...`);
      const formData = new FormData();
      const blob = new Blob([audioBuffer], { type: mimetype });
      formData.append('file', blob, filename);
      formData.append('model', 'whisper-large-v3-turbo');
      formData.append('language', 'pt');
      formData.append('response_format', 'json');

      const resp = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${groqKey}`
        },
        body: formData
      });

      if (resp.ok) {
        const result = await resp.json();
        if (result.text && result.text.trim()) {
          console.log(`[WHISPER GROQ SUCESSO]: "${result.text.trim()}"`);
          return result.text.trim();
        }
      } else {
        const errText = await resp.text();
        console.error(`[WHISPER GROQ ERRO ${resp.status}]:`, errText);
      }
    } catch (err) {
      console.error('[WHISPER GROQ EXCEPTION]:', err.message);
    }
  }

  // Fallback to OpenAI Whisper
  if (openaiKey) {
    try {
      console.log(`[WHISPER] Transcrevendo áudio ${filename} via OpenAI API...`);
      const formData = new FormData();
      const blob = new Blob([audioBuffer], { type: mimetype });
      formData.append('file', blob, filename);
      formData.append('model', 'whisper-1');
      formData.append('language', 'pt');

      const resp = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiKey}`
        },
        body: formData
      });

      if (resp.ok) {
        const result = await resp.json();
        if (result.text && result.text.trim()) {
          console.log(`[WHISPER OPENAI SUCESSO]: "${result.text.trim()}"`);
          return result.text.trim();
        }
      }
    } catch (err) {
      console.error('[WHISPER OPENAI EXCEPTION]:', err.message);
    }
  }

  return null;
}

// ── Message handling & Persistence ────────────────────────────
function recordMessage(msg) {
  // Add to in-memory list (unique by ID)
  const existingIdx = state.recentMessages.findIndex(m => m.id === msg.id);
  if (existingIdx >= 0) {
    state.recentMessages[existingIdx] = msg;
  } else {
    state.recentMessages.unshift(msg);
    if (state.recentMessages.length > 100) state.recentMessages.pop();
  }

  // Append to daily log
  const today = new Date().toISOString().slice(0, 10);
  const logFile = path.join(INBOX_DIR, `${today}.jsonl`);
  try {
    fs.appendFileSync(logFile, JSON.stringify(msg) + '\n', 'utf8');
  } catch (err) {
    console.error('[LOG ERROR]', err);
  }

  // React mode triggers
  if (state.mode === 'react' && msg.text) {
    const textLower = msg.text.toLowerCase();
    if (msg.text.startsWith('/task') || textLower.includes('@agente') || textLower.includes('urgente') || textLower.includes('tarefa:')) {
      enqueTask(msg);
    }
  }
}

function updateMessage(msgId, updates) {
  const target = state.recentMessages.find(m => m.id === msgId);
  if (target) {
    Object.assign(target, updates);
    // Also rewrite in log file if needed, or append update entry
    const today = new Date().toISOString().slice(0, 10);
    const logFile = path.join(INBOX_DIR, `${today}.jsonl`);
    try {
      fs.appendFileSync(logFile, JSON.stringify({ update_for_id: msgId, ...updates, updated_at: new Date().toISOString() }) + '\n', 'utf8');
    } catch (_) {}

    if (state.mode === 'react' && target.text) {
      const textLower = target.text.toLowerCase();
      if (target.text.startsWith('/task') || textLower.includes('@agente') || textLower.includes('urgente') || textLower.includes('tarefa:')) {
        enqueTask(target);
      }
    }
  }
}

function enqueTask(msg) {
  try {
    let tasks = [];
    if (fs.existsSync(TASKS_FILE)) {
      try { tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8')); } catch (_) { tasks = []; }
    }
    const cleanInstruction = msg.text.replace(/^\/task\s*/i, '').replace(/@agente\s*/i, '').trim();
    const newTask = {
      id: `task_${Date.now()}`,
      source: 'whatsapp',
      from: msg.sender,
      instruction: cleanInstruction || msg.text,
      raw_message_id: msg.id,
      media_file: msg.media_file || null,
      status: 'pending',
      created_at: new Date().toISOString()
    };
    tasks.push(newTask);
    fs.writeFileSync(TASKS_FILE, JSON.stringify(tasks, null, 2), 'utf8');
    console.log(`[REACT] Nova tarefa enfileirada via WhatsApp: "${newTask.instruction}"`);
  } catch (err) {
    console.error('[REACT ERROR]', err);
  }
}

function categorizeMessage(text) {
  const t = (text || '').toLowerCase();
  if (t.includes('reuni') || t.includes('pauta') || t.includes('ata') || t.includes('call') || t.includes('meet')) return 'reuniao';
  if (t.includes('/task') || t.includes('fazer') || t.includes('tarefa') || t.includes('urgente') || t.includes('prioridade')) return 'task';
  if (t.includes('preço') || t.includes('proposta') || t.includes('orçamento') || t.includes('cliente') || t.includes('venda')) return 'lead';
  if (t.startsWith('[áudio') || t.startsWith('[audio') || t.includes('transcrito')) return 'audio';
  return 'info';
}

// ── Real Baileys Integration ──────────────────────────────────
let sock = null;
let isBaileysInitializing = false;

async function initBaileys() {
  if (isBaileysInitializing) return;
  isBaileysInitializing = true;

  try {
    resolveApiKeys();

    let makeWASocket, useMultiFileAuthState, DisconnectReason, downloadMediaMessage;
    let QRCode, pino;

    try {
      const baileysMod = require('@whiskeysockets/baileys');
      makeWASocket = baileysMod.default || baileysMod;
      useMultiFileAuthState = baileysMod.useMultiFileAuthState;
      DisconnectReason = baileysMod.DisconnectReason;
      downloadMediaMessage = baileysMod.downloadMediaMessage;
      QRCode = require('qrcode');
      pino = require('pino');
    } catch (depErr) {
      console.error('[BAILEYS DEP WARNING] Dependências não encontradas:', depErr.message);
      state.status = 'missing_dependencies';
      state.lastQrRaw = null;
      state.lastQrImage = null;
      state.message = 'Dependências do WhatsApp não instaladas. O setup server as instalará automaticamente.';
      isBaileysInitializing = false;
      return;
    }

    state.status = 'initializing';
    state.message = 'Conector Baileys inicializando...';

    const authDir = path.join(__dirname, 'auth_info_baileys');
    fs.mkdirSync(authDir, { recursive: true });
    const { state: authState, saveCreds } = await useMultiFileAuthState(authDir);

    const logger = pino({ level: 'silent' });

    sock = makeWASocket({
      auth: authState,
      printQRInTerminal: false,
      logger: logger,
      browser: ['Agent Workspace OS', 'Chrome', '1.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        state.status = 'qr_ready';
        state.lastQrRaw = qr;
        try {
          state.lastQrImage = await QRCode.toDataURL(qr, { width: 320, margin: 2 });
        } catch (qrErr) {
          console.error('[QRCODE ERROR]', qrErr);
          state.lastQrImage = null;
        }
      }

      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
        state.status = 'disconnected';
        state.connectedNumber = null;
        state.lastQrRaw = null;
        state.lastQrImage = null;
        console.log(`[BAILEYS] Conexão fechada (statusCode: ${statusCode}). Reconectar: ${shouldReconnect}`);
        if (shouldReconnect) {
          setTimeout(() => {
            isBaileysInitializing = false;
            initBaileys();
          }, 3000);
        } else {
          isBaileysInitializing = false;
        }
      } else if (connection === 'open') {
        state.status = 'connected';
        state.connectedNumber = sock.user?.id?.split(':')[0] || 'Conectado';
        state.lastQrRaw = null;
        state.lastQrImage = null;
        state.message = `Conectado ao WhatsApp como ${state.connectedNumber}`;
        console.log(`[BAILEYS OPEN] Conectado com sucesso! Número: ${state.connectedNumber}`);
      }
    });

    // Handle incoming and outgoing messages
    sock.ev.on('messages.upsert', async (m) => {
      if (!m.messages || !m.messages.length) return;

      const myNumber = sock.user?.id?.split(':')[0] || '';
      const myJid = myNumber ? `${myNumber}@s.whatsapp.net` : '';

      for (const msg of m.messages) {
        if (!msg.message) continue;

        const remoteJid = msg.key.remoteJid || '';
        const fromMe = Boolean(msg.key.fromMe);

        // Ignore contact status broadcasts
        if (remoteJid.includes('@broadcast') || remoteJid === 'status@broadcast') {
          continue;
        }

        // Check if message was sent to self (note-to-self chat or personal number)
        const isSelfChat = Boolean(
          (myNumber && remoteJid.startsWith(myNumber)) ||
          remoteJid.includes('@lid') ||
          (myJid && remoteJid === myJid)
        );

        // Build human-friendly sender label
        let senderDisplay = remoteJid.split('@')[0];
        if (fromMe && isSelfChat) {
          senderDisplay = 'Você (Anotações)';
        } else if (fromMe) {
          senderDisplay = 'Você';
        } else if (msg.pushName) {
          senderDisplay = `${msg.pushName} (${senderDisplay})`;
        }

        const msgId = msg.key.id;
        const msgTimestamp = msg.messageTimestamp ? new Date(Number(msg.messageTimestamp) * 1000).toISOString() : new Date().toISOString();

        // ── Detect Media & Audio ────────────────────────────
        const audioMsg = msg.message.audioMessage || msg.message.ptvMessage;
        const textContent = msg.message.conversation ||
                            msg.message.extendedTextMessage?.text ||
                            msg.message.imageMessage?.caption ||
                            msg.message.videoMessage?.caption ||
                            msg.message.documentMessage?.caption;

        if (audioMsg) {
          const duration = audioMsg.seconds || 0;
          const isPtt = Boolean(audioMsg.ptt);
          const ext = (audioMsg.mimetype || '').includes('ogg') ? 'ogg' : 'mp3';
          const filename = `audio_${Date.now()}_${msgId}.${ext}`;
          const filePath = path.join(MEDIA_DIR, filename);

          console.log(`[AUDIO RECEBIDO] De: ${senderDisplay} | Duração: ${duration}s | PTT: ${isPtt}`);

          // Register initial placeholder entry
          const initialText = `[Áudio: ${duration}s - Baixando e transcrevendo...]`;
          const entry = {
            id: msgId,
            sender: senderDisplay,
            fromMe: fromMe,
            isSelfChat: isSelfChat,
            text: initialText,
            timestamp: msgTimestamp,
            category: 'audio',
            is_audio: true,
            audio_duration: duration,
            media_file: filename,
            transcription: null
          };
          recordMessage(entry);

          // Asynchronously download and transcribe
          (async () => {
            try {
              const buffer = await downloadMediaMessage(
                msg,
                'buffer',
                {},
                {
                  logger: pino({ level: 'silent' }),
                  reuploadRequest: sock.updateMediaMessage
                }
              );

              fs.writeFileSync(filePath, buffer);
              console.log(`[AUDIO SALVO] Arquivo gravado em: ${filePath} (${buffer.length} bytes)`);

              // Perform transcription
              const transcribed = await transcribeAudioBuffer(buffer, filename, audioMsg.mimetype || 'audio/ogg');
              if (transcribed) {
                const displayText = `[Áudio]: "${transcribed}"`;
                updateMessage(msgId, {
                  text: displayText,
                  transcription: transcribed,
                  category: categorizeMessage(transcribed)
                });
              } else {
                const keys = resolveApiKeys();
                let hint = '';
                if (!keys.groqKey && !keys.openaiKey) {
                  hint = ' (Adicione GROQ_API_KEY no painel de controle para transcrição instantânea)';
                }
                updateMessage(msgId, {
                  text: `[Áudio: ${duration}s salvo em media/${filename}]${hint}`
                });
              }
            } catch (mediaErr) {
              console.error(`[MEDIA DOWNLOAD ERROR ${msgId}]:`, mediaErr.message);
              updateMessage(msgId, {
                text: `[Áudio: ${duration}s - Falha no download da mídia]`
              });
            }
          })();

        } else {
          // Regular Text Message
          const text = textContent || '[Mídia / Documento sem legenda]';
          const entry = {
            id: msgId,
            sender: senderDisplay,
            fromMe: fromMe,
            isSelfChat: isSelfChat,
            text: text,
            timestamp: msgTimestamp,
            category: categorizeMessage(text)
          };
          recordMessage(entry);
        }
      }
    });

    console.log('[BAILEYS] Conector Baileys inicializado com suporte a áudio e note-to-self.');
  } catch (err) {
    console.error('[BAILEYS INIT ERROR]', err);
    state.status = 'offline';
    state.message = err.message;
  } finally {
    isBaileysInitializing = false;
  }
}

// ── HTTP Request Handler (Native Node.js, zero dependencies) ──
function handleRequest(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://127.0.0.1:${PORT}`);
  const pathname = parsedUrl.pathname;

  function sendJson(data, status = 200) {
    const body = JSON.stringify(data);
    res.writeHead(status, {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Length': Buffer.byteLength(body)
    });
    res.end(body);
  }

  if (req.method === 'GET') {
    if (pathname === '/api/status') {
      resolveApiKeys();
      return sendJson(state);
    }
    if (pathname === '/api/qr') {
      return sendJson({
        status: state.status,
        qr_image: state.lastQrImage,
        qr_raw: state.lastQrRaw
      });
    }
    if (pathname === '/api/feed') {
      return sendJson({ messages: state.recentMessages });
    }

    // Serve saved media files (audio files)
    if (pathname.startsWith('/api/media/')) {
      const filename = path.basename(pathname.replace('/api/media/', ''));
      const filePath = path.join(MEDIA_DIR, filename);
      if (fs.existsSync(filePath)) {
        const ext = path.extname(filePath).toLowerCase();
        const contentType = ext === '.ogg' ? 'audio/ogg' : ext === '.mp3' ? 'audio/mpeg' : 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
        return;
      }
      return sendJson({ error: 'Media not found' }, 404);
    }
  }

  if (req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let parsed = {};
      try { parsed = JSON.parse(body || '{}'); } catch (_) {}

      if (pathname === '/api/mode') {
        const mode = parsed.mode;
        if (['monitor', 'react'].includes(mode)) {
          state.mode = mode;
          return sendJson({ success: true, mode: state.mode });
        }
        return sendJson({ error: 'Modo inválido. Use "monitor" ou "react".' }, 400);
      }

      if (pathname === '/api/init' || pathname === '/api/start') {
        initBaileys();
        return sendJson({ success: true, status: state.status });
      }

      if (pathname === '/api/simulate-message') {
        const msg = {
          id: `sim_${Date.now()}`,
          sender: parsed.sender || 'Você (Anotações)',
          fromMe: Boolean(parsed.fromMe),
          isSelfChat: Boolean(parsed.isSelfChat),
          text: parsed.text || 'Exemplo de mensagem de teste via WhatsApp Bridge',
          timestamp: new Date().toISOString(),
          category: categorizeMessage(parsed.text || '')
        };
        recordMessage(msg);
        return sendJson({ success: true, message: msg });
      }

      sendJson({ error: 'Not Found' }, 404);
    });
    return;
  }

  sendJson({ error: 'Not Found' }, 404);
}

// ── Start Server ───────────────────────────────────────────
const server = http.createServer(handleRequest);
server.listen(PORT, '0.0.0.0', () => {
  console.log(`WhatsApp Bridge running on http://127.0.0.1:${PORT}`);
  resolveApiKeys();
  initBaileys();
});
