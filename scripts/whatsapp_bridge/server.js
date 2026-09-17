/**
 * WhatsApp Client Bridge — Agent Workspace OS (v2.5)
 * Issue #1 Complete Implementation:
 * 1. Zero-cloud local transcription with faster-whisper + serial lock queue & fallback
 * 2. Persistent operational mode (monitor / react) across reboots
 * 3. Intent & Confidence Engine: task, needs_confirmation, question, info
 * 4. Interactive WhatsApp Confirmation Flow: SIM <id> / NÃO <id>
 * 5. Autonomous Task Queue Dispatch & Active Task Execution
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn, execFile } = require('child_process');

const PORT = parseInt(process.env.WHATSAPP_PORT || '4114', 10);
const WORKSPACE_ROOT = path.resolve(__dirname, '../../');
const INBOX_DIR = path.join(WORKSPACE_ROOT, 'workspace', 'inbox', 'whatsapp');
const MEDIA_DIR = path.join(INBOX_DIR, 'media');
const TASKS_FILE = path.join(WORKSPACE_ROOT, 'workspace', 'memory', 'active_tasks.json');
const CONFIG_FILE = path.join(WORKSPACE_ROOT, 'workspace.config.json');
const LOCAL_TRANSCRIBE_SCRIPT = path.join(WORKSPACE_ROOT, 'scripts', 'transcribe_local.py');
const TASK_WORKER_SCRIPT = path.join(WORKSPACE_ROOT, 'scripts', 'task_worker.py');

try { fs.mkdirSync(INBOX_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(MEDIA_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(path.dirname(TASKS_FILE), { recursive: true }); } catch (_) {}

// ── Persistent Mode Helper ─────────────────────────────────
function loadInitialMode() {
  if (fs.existsSync(CONFIG_FILE)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      if (cfg.whatsapp?.mode) {
        return cfg.whatsapp.mode;
      }
    } catch (_) {}
  }
  return 'monitor';
}

function persistMode(newMode) {
  if (fs.existsSync(CONFIG_FILE)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      if (!cfg.whatsapp) cfg.whatsapp = {};
      cfg.whatsapp.mode = newMode;
      fs.writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2), 'utf8');
      console.log(`[CONFIG] Modo persistido no workspace.config.json: ${newMode}`);
    } catch (err) {
      console.error('[CONFIG ERROR] Falha ao persistir modo:', err);
    }
  }
}

// ── State ──────────────────────────────────────────────────
let state = {
  status: 'offline', // 'offline' | 'installing' | 'qr_ready' | 'connected' | 'disconnected'
  connectedNumber: null,
  mode: loadInitialMode(), // Persisted between reboots
  lastQrRaw: null,
  lastQrImage: null,
  recentMessages: [],
  transcriptionProvider: 'faster-whisper-local', // 'faster-whisper-local' | 'groq' | 'openai' | 'none'
  message: '',
  pendingConfirmationsCount: 0
};

// ── Pending Confirmations Map ──────────────────────────────
// confId -> { confId, instruction, remoteJid, sender, timestamp, expiresAt }
const pendingConfirmations = new Map();
let confSequence = 1;

function cleanExpiredConfirmations() {
  const now = Date.now();
  for (const [id, item] of pendingConfirmations.entries()) {
    if (now > item.expiresAt) {
      pendingConfirmations.delete(id);
    }
  }
  state.pendingConfirmationsCount = pendingConfirmations.size;
}
setInterval(cleanExpiredConfirmations, 60000);

// ── Intent & Confidence Engine ─────────────────────────────
function classifyIntent(rawText) {
  const text = (rawText || '').trim();
  const textLower = text.toLowerCase();

  // 1. Explicit /task prefix: Unambiguous task (100% confidence)
  if (text.startsWith('/task') || text.startsWith('!task')) {
    const instruction = text.replace(/^(\/|!)task\s*/i, '').trim();
    return {
      intent: 'task',
      confidence: 1.0,
      instruction: instruction || text,
      category: 'task'
    };
  }

  // 2. High-risk or highly ambiguous actions requiring explicit confirmation
  const dangerousPatterns = [
    /\b(apague|apagar|delete|deletar|destrua|destruir|limpar tudo|dropar|remover tudo|drop table)\b/i,
    /\b(formate|formatar|resetar tudo|reset total)\b/i
  ];
  for (const pattern of dangerousPatterns) {
    if (pattern.test(textLower)) {
      return {
        intent: 'needs_confirmation',
        confidence: 0.5,
        instruction: text,
        category: 'task',
        reason: 'Ação de alto risco identificada'
      };
    }
  }

  // 3. Clear direct imperative action requests (e.g. "Crie uma imagem de um cachorro")
  const imperativeVerbs = [
    'crie', 'criar', 'gere', 'gerar', 'faça', 'fazer', 'desenvolva', 'desenvolver',
    'instale', 'instalar', 'execute', 'executar', 'rode', 'rodar', 'compile', 'compilar',
    'atualize', 'atualizar', 'configure', 'configurar', 'publique', 'publicar', 'deploy',
    'adicione', 'adicionar', 'escreva', 'escrever', 'busque', 'buscar', 'pesquise', 'pesquisar'
  ];

  const words = textLower.split(/\s+/);
  const firstWord = words[0] || '';
  const secondWord = words[1] || '';

  const startsWithImperative = imperativeVerbs.includes(firstWord) || (['por favor', 'favor'].includes(firstWord) && imperativeVerbs.includes(secondWord));
  const isQuestion = text.endsWith('?') || /^(como|qual|quando|onde|quem|por\s*que|quanto)\b/i.test(textLower);

  if (startsWithImperative && !isQuestion) {
    // If command has substantial specific payload (> 10 chars)
    if (text.length >= 12) {
      return {
        intent: 'task',
        confidence: 0.9,
        instruction: text,
        category: 'task'
      };
    } else {
      // Short or ambiguous command ("Crie isso")
      return {
        intent: 'needs_confirmation',
        confidence: 0.6,
        instruction: text,
        category: 'task',
        reason: 'Instrução curta ou ambígua'
      };
    }
  }

  // 4. Questions
  if (isQuestion) {
    return {
      intent: 'question',
      confidence: 0.88,
      instruction: text,
      category: (textLower.includes('reuni') || textLower.includes('meet')) ? 'reuniao' : 'info'
    };
  }

  // 5. Commercial leads / budgets
  if (/\b(preço|valor|proposta|orçamento|contratar|custo|comprar)\b/i.test(textLower)) {
    return {
      intent: 'info',
      confidence: 0.85,
      instruction: text,
      category: 'lead'
    };
  }

  // 6. Generic conversational / info
  return {
    intent: 'info',
    confidence: 0.95,
    instruction: text,
    category: 'info'
  };
}

// ── Audio Transcription Pipeline ───────────────────────────
// Serial Queue for local faster-whisper to guarantee single model load & no race conditions
let isLocalTranscriptionBusy = false;
const transcriptionQueue = [];

function processLocalTranscriptionQueue() {
  if (isLocalTranscriptionBusy || transcriptionQueue.length === 0) return;
  isLocalTranscriptionBusy = true;

  const item = transcriptionQueue.shift();
  const { audioPath, resolve, reject } = item;

  console.log(`[WHISPER LOCAL SERIAL] Processando áudio: ${path.basename(audioPath)} (restantes na fila: ${transcriptionQueue.length})`);

  const proc = spawn('python', [LOCAL_TRANSCRIBE_SCRIPT, '--audio', audioPath, '--language', 'pt', '--model', 'base']);
  let stdout = '';
  let stderr = '';

  proc.stdout.on('data', chunk => { stdout += chunk.toString(); });
  proc.stderr.on('data', chunk => { stderr += chunk.toString(); });

  proc.on('close', code => {
    isLocalTranscriptionBusy = false;
    // Trigger next item immediately
    setTimeout(processLocalTranscriptionQueue, 50);

    if (code === 0) {
      try {
        const parsed = JSON.parse(stdout.trim());
        if (parsed.ok && parsed.text) {
          console.log(`[WHISPER LOCAL SUCESSO]: "${parsed.text}" (${parsed.duration}s, tomou ${parsed.elapsed_seconds}s)`);
          return resolve(parsed.text);
        }
      } catch (_) {}
    }

    console.warn(`[WHISPER LOCAL FALHA/FALLBACK]: code=${code}, err=${stderr.slice(0, 150)}`);
    // Fallback to Groq Whisper if local had an exception
    transcribeViaCloudFallback(audioPath).then(resolve).catch(reject);
  });

  proc.on('error', err => {
    isLocalTranscriptionBusy = false;
    setTimeout(processLocalTranscriptionQueue, 50);
    console.warn(`[WHISPER LOCAL SPAWN ERROR]: ${err.message}. Tentando cloud fallback...`);
    transcribeViaCloudFallback(audioPath).then(resolve).catch(reject);
  });
}

function transcribeAudioLocally(audioPath) {
  return new Promise((resolve, reject) => {
    transcriptionQueue.push({ audioPath, resolve, reject });
    processLocalTranscriptionQueue();
  });
}

// Cloud fallback (Groq / OpenAI) only if local faster-whisper script fails
async function transcribeViaCloudFallback(audioPath) {
  const { groqKey, openaiKey } = resolveApiKeys();
  if (!fs.existsSync(audioPath)) return null;
  const audioBuffer = fs.readFileSync(audioPath);
  const filename = path.basename(audioPath);

  if (groqKey) {
    try {
      const formData = new FormData();
      formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), filename);
      formData.append('model', 'whisper-large-v3-turbo');
      formData.append('language', 'pt');
      formData.append('response_format', 'json');

      const resp = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${groqKey}` },
        body: formData
      });
      if (resp.ok) {
        const data = await resp.json();
        return data.text ? data.text.trim() : null;
      }
    } catch (_) {}
  }

  if (openaiKey) {
    try {
      const formData = new FormData();
      formData.append('file', new Blob([audioBuffer], { type: 'audio/ogg' }), filename);
      formData.append('model', 'whisper-1');
      formData.append('language', 'pt');

      const resp = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${openaiKey}` },
        body: formData
      });
      if (resp.ok) {
        const data = await resp.json();
        return data.text ? data.text.trim() : null;
      }
    } catch (_) {}
  }

  return null;
}

function resolveApiKeys() {
  return {
    groqKey: process.env.GROQ_API_KEY || '',
    openaiKey: process.env.OPENAI_API_KEY || ''
  };
}

// ── Task Queue Dispatcher ──────────────────────────────────
function enqueTask(instruction, sourceInfo = {}) {
  try {
    let tasks = [];
    if (fs.existsSync(TASKS_FILE)) {
      try { tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8')); } catch (_) { tasks = []; }
    }
    const cleanInstruction = instruction.replace(/^\/task\s*/i, '').trim();
    const newTask = {
      id: `task_${Date.now()}`,
      source: 'whatsapp',
      from: sourceInfo.sender || 'whatsapp_user',
      from_jid: sourceInfo.remoteJid || null,
      instruction: cleanInstruction || instruction,
      raw_message_id: sourceInfo.id || null,
      media_file: sourceInfo.media_file || null,
      confirmed_by: sourceInfo.confirmedBy || null,
      status: 'pending',
      created_at: new Date().toISOString()
    };
    tasks.push(newTask);
    fs.writeFileSync(TASKS_FILE, JSON.stringify(tasks, null, 2), 'utf8');
    console.log(`[TASK ENQUEUED] Nova tarefa na fila: "${newTask.instruction}" (ID: ${newTask.id})`);

    // Trigger local task worker asynchronously
    spawn('python', [TASK_WORKER_SCRIPT, '--once'], {
      detached: true,
      stdio: 'ignore'
    }).unref();

    return newTask;
  } catch (err) {
    console.error('[TASK QUEUE ERROR]', err);
    return null;
  }
}

// ── Message handling & Persistence ─────────────────────────
function recordMessage(msg) {
  const existingIdx = state.recentMessages.findIndex(m => m.id === msg.id);
  if (existingIdx >= 0) {
    state.recentMessages[existingIdx] = msg;
  } else {
    state.recentMessages.unshift(msg);
    if (state.recentMessages.length > 100) state.recentMessages.pop();
  }

  const today = new Date().toISOString().slice(0, 10);
  const logFile = path.join(INBOX_DIR, `${today}.jsonl`);
  try {
    fs.appendFileSync(logFile, JSON.stringify(msg) + '\n', 'utf8');
  } catch (err) {
    console.error('[LOG ERROR]', err);
  }
}

function updateMessage(msgId, updates) {
  const target = state.recentMessages.find(m => m.id === msgId);
  if (target) {
    Object.assign(target, updates);
    const today = new Date().toISOString().slice(0, 10);
    const logFile = path.join(INBOX_DIR, `${today}.jsonl`);
    try {
      fs.appendFileSync(logFile, JSON.stringify({ update_for_id: msgId, ...updates, updated_at: new Date().toISOString() }) + '\n', 'utf8');
    } catch (_) {}
  }
}

// ── WhatsApp Outbound Sender ───────────────────────────────
let sock = null;

async function sendWhatsAppText(remoteJid, text) {
  if (!sock || state.status !== 'connected') {
    console.log(`[WHATSAPP SEND SIMULATION] to ${remoteJid}: "${text}"`);
    return { ok: true, simulated: true };
  }
  try {
    await sock.sendMessage(remoteJid, { text });
    console.log(`[WHATSAPP OUTBOUND] Mensagem enviada para ${remoteJid}: "${text.slice(0, 60)}..."`);
    return { ok: true };
  } catch (err) {
    console.error(`[WHATSAPP SEND ERROR to ${remoteJid}]:`, err.message);
    return { ok: false, error: err.message };
  }
}

// ── Real Baileys Integration ───────────────────────────────
let isBaileysInitializing = false;

async function initBaileys() {
  if (isBaileysInitializing) return;
  isBaileysInitializing = true;

  try {
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
      console.error('[BAILEYS DEP WARNING] Dependências ausentes:', depErr.message);
      state.status = 'missing_dependencies';
      state.lastQrRaw = null;
      state.lastQrImage = null;
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
        state.message = `Conectado como ${state.connectedNumber}`;
        console.log(`[BAILEYS OPEN] Conectado! Número: ${state.connectedNumber}`);
      }
    });

    // ── Incoming Messages & Actions ─────────────────────────
    sock.ev.on('messages.upsert', async (m) => {
      if (!m.messages || !m.messages.length) return;

      const myNumber = sock.user?.id?.split(':')[0] || '';
      const myJid = myNumber ? `${myNumber}@s.whatsapp.net` : '';

      for (const msg of m.messages) {
        if (!msg.message) continue;

        const remoteJid = msg.key.remoteJid || '';
        const fromMe = Boolean(msg.key.fromMe);

        if (remoteJid.includes('@broadcast') || remoteJid === 'status@broadcast') {
          continue;
        }

        const isSelfChat = Boolean(
          (myNumber && remoteJid.startsWith(myNumber)) ||
          remoteJid.includes('@lid') ||
          (myJid && remoteJid === myJid)
        );

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

        // ── Check if message is a confirmation reply (SIM <id> / NÃO <id>) ──
        const rawTextContent = (
          msg.message.conversation ||
          msg.message.extendedTextMessage?.text ||
          ''
        ).trim();

        const confMatch = rawTextContent.match(/^(sim|não|nao)\s*([a-z0-9_-]*)$/i);
        if (confMatch) {
          const decision = confMatch[1].toLowerCase();
          const targetConfId = confMatch[2].toUpperCase().trim();

          // Find pending confirmation (by ID or the single pending for this sender)
          let pendingItem = null;
          if (targetConfId && pendingConfirmations.has(targetConfId)) {
            pendingItem = pendingConfirmations.get(targetConfId);
          } else if (!targetConfId && pendingConfirmations.size === 1) {
            pendingItem = Array.from(pendingConfirmations.values())[0];
          }

          if (pendingItem) {
            if (decision === 'sim') {
              enqueTask(pendingItem.instruction, {
                sender: senderDisplay,
                remoteJid: remoteJid,
                confirmedBy: senderDisplay
              });
              sendWhatsAppText(remoteJid, `✅ *Tarefa [${pendingItem.confId}] Aprovada!*\nAdicionada à fila de execução e em processamento.`);
              pendingConfirmations.delete(pendingItem.confId);
            } else {
              sendWhatsAppText(remoteJid, `❌ *Tarefa [${pendingItem.confId}] Cancelada.*`);
              pendingConfirmations.delete(pendingItem.confId);
            }
            state.pendingConfirmationsCount = pendingConfirmations.size;

            recordMessage({
              id: msgId,
              sender: senderDisplay,
              fromMe: fromMe,
              isSelfChat: isSelfChat,
              text: `[Confirmação ${decision.toUpperCase()}]: Tarefa ${pendingItem.confId}`,
              timestamp: msgTimestamp,
              category: 'task'
            });
            continue;
          }
        }

        // ── Detect Media & Audio ────────────────────────────
        const audioMsg = msg.message.audioMessage || msg.message.ptvMessage;
        const textContent = rawTextContent ||
                            msg.message.imageMessage?.caption ||
                            msg.message.videoMessage?.caption ||
                            msg.message.documentMessage?.caption;

        if (audioMsg) {
          const duration = audioMsg.seconds || 0;
          const ext = (audioMsg.mimetype || '').includes('ogg') ? 'ogg' : 'mp3';
          const filename = `audio_${Date.now()}_${msgId}.${ext}`;
          const filePath = path.join(MEDIA_DIR, filename);

          console.log(`[AUDIO RECEBIDO] De: ${senderDisplay} | Duração: ${duration}s`);

          const initialText = `[Áudio: ${duration}s - Transcrevendo localmente...]`;
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

          // Asynchronous local download + serial transcription
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
              console.log(`[AUDIO SALVO] Arquivo gravado em: ${filePath}`);

              // Transcribe via Local faster-whisper Queue
              const transcribed = await transcribeAudioLocally(filePath);
              if (transcribed) {
                const displayText = `[Áudio]: "${transcribed}"`;
                const intentInfo = classifyIntent(transcribed);

                updateMessage(msgId, {
                  text: displayText,
                  transcription: transcribed,
                  category: intentInfo.category,
                  intent: intentInfo.intent,
                  confidence: intentInfo.confidence
                });

                // Handle task dispatch or confirmation in react mode
                handleMessageAction(transcribed, intentInfo, {
                  id: msgId,
                  sender: senderDisplay,
                  remoteJid: remoteJid,
                  media_file: filename
                });
              } else {
                updateMessage(msgId, {
                  text: `[Áudio: ${duration}s salvo em media/${filename}]`
                });
              }
            } catch (mediaErr) {
              console.error(`[MEDIA DOWNLOAD ERROR ${msgId}]:`, mediaErr.message);
              updateMessage(msgId, {
                text: `[Áudio: ${duration}s - Falha no download]`
              });
            }
          })();

        } else {
          // Regular Text Message
          const text = textContent || '[Mídia / Documento]';
          const intentInfo = classifyIntent(text);

          const entry = {
            id: msgId,
            sender: senderDisplay,
            fromMe: fromMe,
            isSelfChat: isSelfChat,
            text: text,
            timestamp: msgTimestamp,
            category: intentInfo.category,
            intent: intentInfo.intent,
            confidence: intentInfo.confidence
          };
          recordMessage(entry);

          handleMessageAction(text, intentInfo, {
            id: msgId,
            sender: senderDisplay,
            remoteJid: remoteJid
          });
        }
      }
    });

    console.log('[BAILEYS] Conector Baileys inicializado com Intent Engine e Confirmação Segura.');
  } catch (err) {
    console.error('[BAILEYS INIT ERROR]', err);
    state.status = 'offline';
    state.message = err.message;
  } finally {
    isBaileysInitializing = false;
  }
}

// ── Reactive Action & Confirmation Handler ─────────────────
function handleMessageAction(text, intentInfo, sourceInfo) {
  if (state.mode !== 'react') return;

  const { intent, confidence, instruction } = intentInfo;

  if (intent === 'task') {
    // Unambiguous high-confidence task
    const task = enqueTask(instruction, sourceInfo);
    if (task && sourceInfo.remoteJid) {
      sendWhatsAppText(sourceInfo.remoteJid, `⚡ *Tarefa Enfileirada [${task.id}]*\n"${task.instruction}"\n_Em execução pelo worker local..._`);
    }
  } else if (intent === 'needs_confirmation') {
    // Requires confirmation
    const confId = `CONF-${confSequence++}`;
    const confirmationItem = {
      confId,
      instruction,
      remoteJid: sourceInfo.remoteJid,
      sender: sourceInfo.sender,
      timestamp: Date.now(),
      expiresAt: Date.now() + 15 * 60 * 1000 // 15 minutes
    };
    pendingConfirmations.set(confId, confirmationItem);
    state.pendingConfirmationsCount = pendingConfirmations.size;

    console.log(`[CONFIRMATION REQUESTED] [${confId}]: "${instruction}" para ${sourceInfo.remoteJid}`);

    if (sourceInfo.remoteJid) {
      const confirmPrompt =
        `⚠️ *Confirmação de Tarefa [${confId}]*\n\n` +
        `Detectei a seguinte ação para o Agent Workspace OS:\n` +
        `"${instruction}"\n\n` +
        `Para aprovar e executar, responda:\n` +
        `*SIM ${confId}*\n\n` +
        `Para cancelar:\n` +
        `*NÃO ${confId}*\n\n` +
        `_(Expira automaticamente em 15 minutos)_`;
      sendWhatsAppText(sourceInfo.remoteJid, confirmPrompt);
    }
  }
}

// ── HTTP Request Handler ───────────────────────────────────
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
      state.pendingConfirmationsCount = pendingConfirmations.size;
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
    if (pathname === '/api/confirmations') {
      return sendJson({
        confirmations: Array.from(pendingConfirmations.values())
      });
    }

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

      // Toggle & Persist Mode
      if (pathname === '/api/mode') {
        const mode = parsed.mode;
        if (['monitor', 'react'].includes(mode)) {
          state.mode = mode;
          persistMode(mode);
          return sendJson({ success: true, mode: state.mode });
        }
        return sendJson({ error: 'Modo inválido. Use "monitor" ou "react".' }, 400);
      }

      if (pathname === '/api/send-message') {
        const to = parsed.to;
        const text = parsed.text;
        if (!to || !text) {
          return sendJson({ error: 'Campos "to" e "text" obrigatórios.' }, 400);
        }
        sendWhatsAppText(to, text);
        return sendJson({ success: true, queued: true });
      }

      if (pathname === '/api/simulate-message') {
        const rawText = parsed.text || 'Exemplo de mensagem de teste via WhatsApp Bridge';
        const intentInfo = classifyIntent(rawText);
        const sender = parsed.sender || 'Você (Anotações)';
        const fromMe = Boolean(parsed.fromMe);
        const isSelfChat = Boolean(parsed.isSelfChat);

        const msg = {
          id: `sim_${Date.now()}`,
          sender: sender,
          fromMe: fromMe,
          isSelfChat: isSelfChat,
          text: rawText,
          timestamp: new Date().toISOString(),
          category: intentInfo.category,
          intent: intentInfo.intent,
          confidence: intentInfo.confidence
        };
        recordMessage(msg);

        // Process action in simulation if requested
        if (parsed.processAction) {
          handleMessageAction(rawText, intentInfo, {
            id: msg.id,
            sender: sender,
            remoteJid: parsed.remoteJid || '5521999999999@s.whatsapp.net'
          });
        }

        return sendJson({ success: true, message: msg, intent: intentInfo });
      }

      if (pathname === '/api/simulate-confirmation-reply') {
        const confId = (parsed.confId || '').toUpperCase().trim();
        const decision = (parsed.decision || 'sim').toLowerCase().trim();
        const remoteJid = parsed.remoteJid || '5521999999999@s.whatsapp.net';

        if (!pendingConfirmations.has(confId)) {
          return sendJson({ error: `Confirmação [${confId}] não encontrada ou expirada.` }, 404);
        }

        const pendingItem = pendingConfirmations.get(confId);
        let task = null;
        if (decision === 'sim') {
          task = enqueTask(pendingItem.instruction, {
            sender: 'Você (Anotações)',
            remoteJid: remoteJid,
            confirmedBy: 'Simulação'
          });
          sendWhatsAppText(remoteJid, `✅ *Tarefa [${confId}] Aprovada!* Adicionada à fila.`);
        } else {
          sendWhatsAppText(remoteJid, `❌ *Tarefa [${confId}] Cancelada.*`);
        }
        pendingConfirmations.delete(confId);
        state.pendingConfirmationsCount = pendingConfirmations.size;

        return sendJson({ success: true, decision, task });
      }

      sendJson({ error: 'Not Found' }, 404);
    });
    return;
  }

  sendJson({ error: 'Not Found' }, 404);
}

// ── Start Server ───────────────────────────────────────────
const server = http.createServer(handleRequest);
server.listen(PORT, process.env.WHATSAPP_BIND_ADDRESS || '127.0.0.1', () => {
  console.log(`WhatsApp Bridge (v2.5) running on http://127.0.0.1:${PORT}`);
  console.log(`[BOOT] Modo operacional ativo: "${state.mode}" (persistido)`);
  initBaileys();
});
