/**
 * WhatsApp Client Bridge — AXION Enterprise (v3.0)
 * Integrated with AXION Brain Server, Baileys Multi-Device Pairing,
 * Team/Roles Management, Automatic Lead Intake, and Meta Anti-Ban Protection.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const PORT = parseInt(process.env.WHATSAPP_PORT || '4114', 10);
const PAIRING_NUMBER = (process.env.WHATSAPP_PAIRING_NUMBER || '551151041784').replace(/[^0-9]/g, '');
const ADMIN_NUMBER = (process.env.WHATSAPP_ADMIN_NUMBER || '5511988045139').replace(/[^0-9]/g, '');
const ADMIN_LID = (process.env.WHATSAPP_ADMIN_LID || '36735559962762').replace(/[^0-9]/g, '');
const BRAIN_URL = process.env.BRAIN_URL || 'http://127.0.0.1:8765';

const WORKSPACE_ROOT = path.resolve(__dirname, '../../');
const INBOX_DIR = path.join(WORKSPACE_ROOT, 'workspace', 'inbox', 'whatsapp');
const MEDIA_DIR = path.join(INBOX_DIR, 'media');
const TEAM_FILE = path.join(WORKSPACE_ROOT, 'workspace', 'whatsapp_team.json');
const LEADS_FILE = path.join(WORKSPACE_ROOT, 'workspace', 'whatsapp_leads.json');
const LOCAL_TRANSCRIBE_SCRIPT = path.join(WORKSPACE_ROOT, 'scripts', 'transcribe_local.py');
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

try { fs.mkdirSync(INBOX_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(MEDIA_DIR, { recursive: true }); } catch (_) {}
try { fs.mkdirSync(AUTH_DIR, { recursive: true }); } catch (_) {}

// ── State ──────────────────────────────────────────────────
let sock = null;
let generateCombinedButtons = null;
let generateWAMessageFromContent = null;
let proto = null;
const lastMenuByNumber = new Map();

let state = {
  status: 'offline', // 'offline' | 'initializing' | 'pairing_ready' | 'connected' | 'disconnected'
  connectedNumber: null,
  pairingNumber: PAIRING_NUMBER,
  adminNumber: ADMIN_NUMBER,
  pairingCode: null,
  lastQrRaw: null,
  lastQrImage: null,
  recentMessages: [],
  transcriptionProvider: 'faster-whisper-local',
  message: 'Iniciando bridge...',
  leadsCount: 0,
  teamCount: 0,
  startedAt: new Date().toISOString()
};

// ── Team & Roles Registry ──────────────────────────────────
function getTeam() {
  if (fs.existsSync(TEAM_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(TEAM_FILE, 'utf8'));
    } catch (_) {}
  }
  return {
    [ADMIN_NUMBER]: {
      phone: ADMIN_NUMBER,
      name: 'Administrador Principal',
      role: 'ADMIN',
      permissions: ['all'],
      created_at: new Date().toISOString()
    }
  };
}

function saveTeam(teamData) {
  try {
    fs.writeFileSync(TEAM_FILE, JSON.stringify(teamData, null, 2), 'utf8');
    state.teamCount = Object.keys(teamData).length;
  } catch (err) {
    console.error('[TEAM ERROR] Falha ao salvar equipe:', err);
  }
}

function isAdmin(cleanNumber) {
  if (cleanNumber === ADMIN_NUMBER || cleanNumber === ADMIN_LID) return true;
  const team = getTeam();
  return team[cleanNumber]?.role?.toUpperCase() === 'ADMIN';
}

function isTeamMember(cleanNumber) {
  const team = getTeam();
  return Boolean(team[cleanNumber]);
}

// ── Leads Registry ─────────────────────────────────────────
function getLeads() {
  if (fs.existsSync(LEADS_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(LEADS_FILE, 'utf8'));
    } catch (_) {}
  }
  return {};
}

function saveLeads(leadsData) {
  try {
    fs.writeFileSync(LEADS_FILE, JSON.stringify(leadsData, null, 2), 'utf8');
    state.leadsCount = Object.keys(leadsData).length;
  } catch (err) {
    console.error('[LEADS ERROR] Falha ao salvar leads:', err);
  }
}

function recordInboundLead(phone, pushName, text) {
  const clean = phone.replace(/[^0-9]/g, '');
  if (isAdmin(clean) || isTeamMember(clean)) return; // Team is not a lead

  const leads = getLeads();
  const nowIso = new Date().toISOString();

  if (!leads[clean]) {
    leads[clean] = {
      phone: clean,
      name: pushName || `Lead ${clean.slice(-4)}`,
      first_interaction: nowIso,
      last_interaction: nowIso,
      inbound_messages_count: 1,
      outbound_messages_count: 0,
      status: 'novo',
      tags: ['lead_whatsapp'],
      last_message: (text || '').slice(0, 200),
      history: [{ role: 'lead', text: (text || '').slice(0, 200), timestamp: nowIso }]
    };
    console.log(`[LEAD] Novo lead capturado: ${clean} (${pushName || 'Sem nome'})`);
  } else {
    leads[clean].last_interaction = nowIso;
    leads[clean].inbound_messages_count = (leads[clean].inbound_messages_count || 0) + 1;
    if (pushName && (!leads[clean].name || leads[clean].name.startsWith('Lead '))) {
      leads[clean].name = pushName;
    }
    leads[clean].last_message = (text || '').slice(0, 200);
    if (!leads[clean].history) leads[clean].history = [];
    leads[clean].history.push({ role: 'lead', text: (text || '').slice(0, 200), timestamp: nowIso });
    if (leads[clean].history.length > 20) leads[clean].history.shift();
  }

  saveLeads(leads);
}

function recordOutboundLead(phone) {
  const clean = phone.replace(/[^0-9]/g, '');
  const leads = getLeads();
  if (leads[clean]) {
    leads[clean].outbound_messages_count = (leads[clean].outbound_messages_count || 0) + 1;
    leads[clean].last_outbound = new Date().toISOString();
    saveLeads(leads);
  }
}

// ── Meta Anti-Ban Outbound Protection ──────────────────────
function canSendOutbound(targetPhone, force = false) {
  const clean = targetPhone.replace(/[^0-9]/g, '');

  if (force) {
    return { allowed: true, reason: 'forced_override_caution' };
  }

  // 1. Team & Admin are always allowed
  if (isAdmin(clean) || isTeamMember(clean)) {
    return { allowed: true, reason: 'team_member' };
  }

  // 2. Leads: MUST HAVE PREVIOUS INBOUND INTERACTION
  const leads = getLeads();
  const lead = leads[clean];
  if (lead && (lead.inbound_messages_count || 0) > 0) {
    return { allowed: true, reason: 'opt_in_verified', inboundCount: lead.inbound_messages_count };
  }

  // 3. Blocked: Virgin outbound to unknown number without prior inbound message
  return {
    allowed: false,
    reason: 'meta_anti_ban_blocked',
    message: `⚠️ [SEGURANÇA META ANTI-BAN] Disparo bloqueado: O número ${clean} nunca enviou uma mensagem prévia para este WhatsApp (sem opt-in registrado). Disparos promocionais ou utilitários para números virgens causam denúncia de SPAM e banimento imediato da conta pela Meta.`
  };
}

// ── Human-like WhatsApp Sender ─────────────────────────────
async function sendWhatsAppText(remoteJid, text, options = {}) {
  if (!sock || state.status !== 'connected') {
    return { success: false, error: 'WhatsApp socket não conectado.' };
  }

  const cleanNumber = remoteJid.replace(/[^0-9]/g, '');
  const isInternalReply = options.isInternalReply || false;
  const force = options.force || false;
  const buttons = Array.isArray(options.buttons) && options.buttons.length > 0 ? options.buttons : null;

  // Verify anti-ban unless this is an internal reply to an incoming message
  if (!isInternalReply) {
    const check = canSendOutbound(cleanNumber, force);
    if (!check.allowed) {
      console.warn(`[ANTI-BAN BLOQUEIO] Para: ${cleanNumber} | Motivo: ${check.message}`);
      return { success: false, blocked_by_anti_ban: true, message: check.message };
    }
  }

  try {
    // 0. Check if editing an existing message (fast in-place edit)
    if (options.editKey) {
      try {
        const keyToEdit = typeof options.editKey === 'string'
          ? { remoteJid, fromMe: true, id: options.editKey }
          : options.editKey;

        const editRes = await sock.sendMessage(remoteJid, {
          text: text,
          edit: keyToEdit
        });
        console.log(`[WHATSAPP EDIT] Mensagem editada para ${cleanNumber} (id: ${keyToEdit.id})`);
        return {
          success: true,
          messageId: keyToEdit.id,
          key: keyToEdit,
          edited: true
        };
      } catch (editErr) {
        console.warn(`[WHATSAPP EDIT FALLBACK] Falha ao editar (${editErr.message}), enviando como nova mensagem...`);
      }
    }

    // 1. Send composing presence (simulating human typing)
    try {
      await sock.sendPresenceUpdate('composing', remoteJid);
    } catch (_) {}

    // 2. Random human typing delay (0.8s to 1.8s)
    const delay = Math.floor(Math.random() * 1000) + 800;
    await new Promise(r => setTimeout(r, delay));

    let res = null;

    const list = options.list || null;
    const carousel = Array.isArray(options.carousel) && options.carousel.length > 0 ? options.carousel : null;
    const poll = options.poll || null;
    const react = options.react || null;

    // 3. Dispatch according to payload feature
    if (react && react.text && react.key) {
      res = await sock.sendMessage(remoteJid, {
        react: { text: react.text, key: react.key }
      });
      console.log(`[WHATSAPP REACT] Reação "${react.text}" enviada para ${cleanNumber}`);
    } else if (poll && poll.name && Array.isArray(poll.values)) {
      res = await sock.sendMessage(remoteJid, {
        poll: {
          name: poll.name,
          values: poll.values,
          selectableCount: poll.selectableCount || 1
        }
      });
      console.log(`[WHATSAPP POLL] Enquete "${poll.name}" enviada para ${cleanNumber} (${poll.values.length} opções)`);
    } else if (carousel && generateWAMessageFromContent && typeof sock.relayMessage === 'function') {
      try {
        const cards = carousel.map(c => ({
          header: {
            title: c.title || '',
            hasMediaAttachment: Boolean(c.hasMediaAttachment)
          },
          body: {
            text: c.body || c.text || ''
          },
          footer: c.footer ? { text: c.footer } : { text: 'AXION Solutions' },
          nativeFlowMessage: {
            buttons: (c.buttons || []).map(b => {
              const bText = String(b.text || b.displayText || 'Ver Mais').trim().slice(0, 25);
              if (b.type === 'url' || b.url) {
                return {
                  name: 'cta_url',
                  buttonParamsJson: JSON.stringify({ display_text: bText, url: b.url })
                };
              }
              if (b.type === 'copy' || b.copyCode) {
                return {
                  name: 'cta_copy',
                  buttonParamsJson: JSON.stringify({ display_text: bText, copy_code: b.copyCode || bText })
                };
              }
              return {
                name: 'quick_reply',
                buttonParamsJson: JSON.stringify({ display_text: bText, id: b.id || b.query || bText })
              };
            })
          }
        }));

        const carouselPayload = {
          interactiveMessage: {
            body: { text: text || '✨ *Destaques AXION Enterprise*' },
            footer: { text: options.footer || 'Deslize horizontalmente para navegar nos cards' },
            carouselMessage: {
              cards,
              messageVersion: 1
            }
          }
        };

        const msg = generateWAMessageFromContent(remoteJid, {
          viewOnceMessage: {
            message: {
              messageContextInfo: { deviceListMetadata: {}, deviceListMetadataVersion: 2 },
              ...carouselPayload
            }
          }
        }, {});

        res = await sock.relayMessage(remoteJid, msg.message, { messageId: msg.key.id });
        console.log(`[WHATSAPP CAROUSEL] Carrossel enviado com sucesso para ${cleanNumber} (${cards.length} cards)`);
      } catch (cErr) {
        console.warn(`[WHATSAPP CAROUSEL FALLBACK] Erro no carrossel (${cErr.message}), enviando mensagem padrão...`);
        res = await sock.sendMessage(remoteJid, { text });
      }
    } else if (list && generateWAMessageFromContent && typeof sock.relayMessage === 'function') {
      try {
        const sections = (list.sections || []).map(s => ({
          title: s.title,
          rows: (s.rows || []).map(r => ({
            title: String(r.title).slice(0, 24),
            description: r.description ? String(r.description).slice(0, 72) : '',
            id: r.id || r.rowId || r.title
          }))
        }));

        const listPayload = {
          interactiveMessage: {
            body: { text: text || list.title || '📋 *Selecione uma opção:*' },
            footer: { text: list.footer || 'AXION Enterprise' },
            nativeFlowMessage: {
              buttons: [
                {
                  name: 'single_select',
                  buttonParamsJson: JSON.stringify({
                    title: list.buttonText || 'Ver Opções',
                    sections
                  })
                }
              ]
            }
          }
        };

        const msg = generateWAMessageFromContent(remoteJid, {
          viewOnceMessage: {
            message: {
              messageContextInfo: { deviceListMetadata: {}, deviceListMetadataVersion: 2 },
              ...listPayload
            }
          }
        }, {});

        res = await sock.relayMessage(remoteJid, msg.message, { messageId: msg.key.id });
        console.log(`[WHATSAPP LIST] Lista suspensa enviada com sucesso para ${cleanNumber} (${sections.length} seções)`);
      } catch (lErr) {
        console.warn(`[WHATSAPP LIST FALLBACK] Erro na lista (${lErr.message}), enviando texto padrão...`);
        res = await sock.sendMessage(remoteJid, { text });
      }
    } else if (buttons && generateCombinedButtons && generateWAMessageFromContent && typeof sock.relayMessage === 'function') {
      try {
        const nativeButtons = buttons.slice(0, 8).map((btn, idx) => {
          const label = String(btn.text || `Opção ${idx + 1}`).trim().slice(0, 25);
          if (btn.type === 'copy' || btn.copyCode) {
            return {
              type: 'copy',
              displayText: label,
              copyCode: btn.copyCode || btn.text
            };
          }
          if (btn.type === 'call' || btn.phoneNumber) {
            return {
              type: 'call',
              displayText: label,
              phoneNumber: btn.phoneNumber
            };
          }
          if (btn.type === 'url' || btn.url) {
            return {
              type: 'url',
              displayText: label,
              url: btn.url
            };
          }
          const idValue = btn.query || (typeof btn.action === 'string' ? btn.action : JSON.stringify(btn.action || {})) || btn.text || `opt_${idx + 1}`;
          return {
            type: 'reply',
            displayText: label,
            id: String(idValue)
          };
        });

        const interactivePayload = generateCombinedButtons(text, nativeButtons, {
          footer: options.footer || 'AXION Enterprise Co-pilot'
        });

        const msg = generateWAMessageFromContent(remoteJid, {
          viewOnceMessage: {
            message: {
              messageContextInfo: {
                deviceListMetadata: {},
                deviceListMetadataVersion: 2
              },
              ...interactivePayload
            }
          }
        }, {});

        res = await sock.relayMessage(remoteJid, msg.message, { messageId: msg.key.id });
        lastMenuByNumber.set(cleanNumber, { buttons, timestamp: Date.now() });
        console.log(`[WHATSAPP BUTTONS] Botões interativos enviados para ${cleanNumber} (${nativeButtons.length} botões)`);
      } catch (btnErr) {
        console.warn(`[WHATSAPP BUTTONS FALLBACK] Erro ao enviar botões interativos (${btnErr.message}), enviando mensagem padrão...`);
        res = await sock.sendMessage(remoteJid, { text });
        lastMenuByNumber.set(cleanNumber, { buttons, timestamp: Date.now() });
      }
    } else {
      res = await sock.sendMessage(remoteJid, { text });
      if (buttons) {
        lastMenuByNumber.set(cleanNumber, { buttons, timestamp: Date.now() });
      }
    }

    // 4. Update presence to paused
    try {
      await sock.sendPresenceUpdate('paused', remoteJid);
    } catch (_) {}

    // Record outbound stat in lead
    recordOutboundLead(cleanNumber);

    return {
      success: true,
      messageId: res?.key?.id || res?.messageId || 'ok',
      key: res?.key || { remoteJid, fromMe: true, id: res?.key?.id }
    };
  } catch (err) {
    console.error(`[SEND ERROR] Falha ao enviar para ${remoteJid}:`, err);
    return { success: false, error: err.message };
  }
}

// ── Local Whisper Queue ────────────────────────────────────
let isLocalTranscriptionBusy = false;
const transcriptionQueue = [];

function processLocalTranscriptionQueue() {
  if (isLocalTranscriptionBusy || transcriptionQueue.length === 0) return;
  isLocalTranscriptionBusy = true;
  const { audioPath, resolve, reject } = transcriptionQueue.shift();

  if (!fs.existsSync(LOCAL_TRANSCRIBE_SCRIPT)) {
    isLocalTranscriptionBusy = false;
    return resolve(null);
  }

  const proc = spawn('python', [LOCAL_TRANSCRIBE_SCRIPT, audioPath]);
  let stdout = '';
  let stderr = '';

  proc.stdout.on('data', chunk => { stdout += chunk.toString(); });
  proc.stderr.on('data', chunk => { stderr += chunk.toString(); });

  proc.on('close', code => {
    isLocalTranscriptionBusy = false;
    setTimeout(processLocalTranscriptionQueue, 50);

    if (code === 0) {
      try {
        const parsed = JSON.parse(stdout.trim());
        if (parsed.ok && parsed.text) {
          console.log(`[WHISPER SUCESSO]: "${parsed.text}"`);
          return resolve(parsed.text);
        }
      } catch (_) {}
    }
    console.warn(`[WHISPER FALHA]: code=${code}`);
    resolve(null);
  });

  proc.on('error', err => {
    isLocalTranscriptionBusy = false;
    setTimeout(processLocalTranscriptionQueue, 50);
    console.warn(`[WHISPER SPAWN ERROR]: ${err.message}`);
    resolve(null);
  });
}

function transcribeAudioLocally(audioPath) {
  return new Promise((resolve, reject) => {
    transcriptionQueue.push({ audioPath, resolve, reject });
    processLocalTranscriptionQueue();
  });
}

// ── Baileys Multi-Device Initialization ────────────────────
let isBaileysInitializing = false;
let pairingRequested = false;

async function initBaileys() {
  if (isBaileysInitializing) return;
  isBaileysInitializing = true;

  try {
    let makeWASocket, useMultiFileAuthState, DisconnectReason, downloadMediaMessage;
    let QRCode, pino, Browsers;

    try {
      let baileysMod;
      try {
        baileysMod = require('baileys-joss');
        console.log('[BAILEYS] Inicializando fork Baileys-Joss (v2.0.1 - Suporte nativo a botões e flow)');
      } catch (_) {
        baileysMod = require('@whiskeysockets/baileys');
        console.log('[BAILEYS] Inicializando @whiskeysockets/baileys padrão');
      }
      makeWASocket = baileysMod.default || baileysMod;
      useMultiFileAuthState = baileysMod.useMultiFileAuthState;
      DisconnectReason = baileysMod.DisconnectReason;
      downloadMediaMessage = baileysMod.downloadMediaMessage;
      Browsers = baileysMod.Browsers;
      generateCombinedButtons = baileysMod.generateCombinedButtons;
      generateWAMessageFromContent = baileysMod.generateWAMessageFromContent;
      proto = baileysMod.proto;
      QRCode = require('qrcode');
      pino = require('pino');
    } catch (depErr) {
      console.error('[BAILEYS DEP ERROR]', depErr.message);
      state.status = 'missing_dependencies';
      isBaileysInitializing = false;
      return;
    }

    state.status = 'initializing';
    state.message = 'Inicializando socket Baileys com Pairing Code...';

    const { state: authState, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const logger = pino({ level: 'silent' });

    sock = makeWASocket({
      auth: authState,
      printQRInTerminal: false,
      logger: logger,
      browser: Browsers.ubuntu('Chrome'),
      connectTimeoutMs: 60000,
      defaultQueryTimeoutMs: 60000,
      keepAliveIntervalMs: 15000
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      // QR Code fallback if pairing not requested
      if (qr && !pairingRequested) {
        state.lastQrRaw = qr;
        try {
          state.lastQrImage = await QRCode.toDataURL(qr, { width: 320, margin: 2 });
        } catch (_) {}
      }

      // Check if pairing code is needed
      if (!authState.creds.registered && !pairingRequested && state.status !== 'connected') {
        pairingRequested = true;
        console.log(`[*] Dispositivo não pareado. Gerando Pairing Code para ${PAIRING_NUMBER}...`);
        setTimeout(async () => {
          try {
            if (sock && !authState.creds.registered) {
              const code = await sock.requestPairingCode(PAIRING_NUMBER);
              state.pairingCode = code;
              state.status = 'pairing_ready';
              state.message = `Pairing Code gerado: ${code}`;

              console.log('\n' + '='.repeat(64));
              console.log('   🔑 WHATSAPP PAIRING CODE PARA ' + PAIRING_NUMBER);
              console.log('   👉 CÓDIGO DE PAREAMENTO: [ ' + code + ' ]');
              console.log('   Passos no celular (' + PAIRING_NUMBER + '):');
              console.log('   1. Abra o WhatsApp no telefone com número ' + PAIRING_NUMBER + ';');
              console.log('   2. Toque em ⋮ (três pontos) > Aparelhos Conectados;');
              console.log('   3. Toque em "Conectar um aparelho" > "Conectar com número de telefone";');
              console.log('   4. Digite o código de 8 dígitos: ' + code);
              console.log('='.repeat(64) + '\n');
            }
          } catch (pairErr) {
            console.error('[PAIRING ERROR] Falha ao solicitar pairing code:', pairErr.message);
            pairingRequested = false;
          }
        }, 4000);
      }

      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const isLoggedOut = (statusCode === DisconnectReason.loggedOut) || (statusCode === 401);
        const shouldReconnect = !isLoggedOut;
        state.status = 'disconnected';
        state.connectedNumber = null;
        pairingRequested = false;

        console.log(`[WHATSAPP] Conexão fechada (Status: ${statusCode}). Reconectando: ${shouldReconnect}`);
        if (shouldReconnect) {
          setTimeout(() => {
            isBaileysInitializing = false;
            initBaileys();
          }, 3000);
        } else {
          isBaileysInitializing = false;
          console.error('[WHATSAPP] Sessão deslogada/inválida. Limpando credenciais e reiniciando...');
          try {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
            fs.mkdirSync(AUTH_DIR, { recursive: true });
          } catch (_) {}
          setTimeout(() => {
            initBaileys();
          }, 3000);
        }
      } else if (connection === 'open') {
        state.status = 'connected';
        state.connectedNumber = (sock.user?.id?.split(':')[0] || PAIRING_NUMBER).replace(/[^0-9]/g, '');
        state.connectedLid = (sock.user?.lid?.split(':')[0] || '').replace(/[^0-9]/g, '');
        state.pairingCode = null;
        state.lastQrRaw = null;
        state.lastQrImage = null;
        state.message = `Conectado como ${state.connectedNumber}`;

        console.log('\n' + '='.repeat(64));
        console.log(`   🟢 WHATSAPP CONECTADO COM SUCESSO!`);
        console.log(`   Número Ativo: ${state.connectedNumber}${state.connectedLid ? ` (LID: ${state.connectedLid})` : ''}`);
        console.log(`   Admin Configurado: ${ADMIN_NUMBER}`);
        console.log('='.repeat(64) + '\n');
      }
    });

    // ── Incoming Messages Handler ───────────────────────────
    sock.ev.on('messages.upsert', async (m) => {
      if (m.type !== 'notify') return;

      for (const msg of m.messages) {
        if (!msg.message) continue;
        const fromMe = Boolean(msg.key.fromMe);
        const remoteJid = msg.key.remoteJid || '';
        if (remoteJid.endsWith('@g.us') || remoteJid === 'status@broadcast') continue; // Ignore groups and status

        const cleanNumber = remoteJid.replace(/[^0-9]/g, '');
        const pushName = msg.pushName || '';

        // Known internal account identifiers (phone, pairing number, LIDs of WhatsApp Web/Desktop clients)
        const selfNumbers = new Set([
          state.connectedNumber,
          PAIRING_NUMBER,
          state.connectedLid,
          '170613498998835',
          '145200714383388',
          '271652537499830'
        ].filter(Boolean));

        const participantNumber = (msg.key.participant || msg.participant || '').replace(/[^0-9]/g, '');

        // CRITICAL FIX: Ignore all messages sent by the account owner / operator
        // from WhatsApp Web, desktop, or mobile app to prevent auto-reply loops.
        if (fromMe || selfNumbers.has(cleanNumber) || (participantNumber && selfNumbers.has(participantNumber))) {
          if (cleanNumber && !selfNumbers.has(cleanNumber)) {
            recordOutboundLead(cleanNumber);
          }
          continue;
        }

        // If pushName matches the bot account's profile name and comes from a LID, it is the operator typing on Web/Desktop
        const botName = (sock?.user?.name || '').trim();
        const isOperatorName = pushName && (pushName === 'Axion Comm' || (botName && pushName.toLowerCase() === botName.toLowerCase()));
        if (isOperatorName && remoteJid.endsWith('@lid') && cleanNumber !== ADMIN_LID) {
          console.log(`[WHATSAPP SELF-IGNORE] Ignorando mensagem do operador no WhatsApp Web (LID: ${cleanNumber}, PushName: ${pushName})`);
          continue;
        }

        // 1. Unwrap container messages (viewOnce, ephemeral)
        let unwrapped = msg.message;
        if (unwrapped.viewOnceMessage?.message) unwrapped = unwrapped.viewOnceMessage.message;
        if (unwrapped.viewOnceMessageV2?.message) unwrapped = unwrapped.viewOnceMessageV2.message;
        if (unwrapped.viewOnceMessageV2Extension?.message) unwrapped = unwrapped.viewOnceMessageV2Extension.message;
        if (unwrapped.ephemeralMessage?.message) unwrapped = unwrapped.ephemeralMessage.message;

        // 2. Extract button or interactive reply
        let buttonAction = null;
        if (unwrapped.interactiveResponseMessage) {
          const nativeResp = unwrapped.interactiveResponseMessage.nativeFlowResponseMessage;
          if (nativeResp?.paramsJson) {
            try {
              const parsed = JSON.parse(nativeResp.paramsJson);
              buttonAction = parsed.id || parsed.selectedId || parsed.command || null;
            } catch (_) {
              buttonAction = nativeResp.paramsJson;
            }
          }
          if (!buttonAction && unwrapped.interactiveResponseMessage.body?.text) {
            buttonAction = unwrapped.interactiveResponseMessage.body.text;
          }
        }
        if (!buttonAction && unwrapped.buttonsResponseMessage) {
          buttonAction = unwrapped.buttonsResponseMessage.selectedButtonId || unwrapped.buttonsResponseMessage.selectedDisplayText;
        }
        if (!buttonAction && unwrapped.templateButtonReplyMessage) {
          buttonAction = unwrapped.templateButtonReplyMessage.selectedId || unwrapped.templateButtonReplyMessage.selectedDisplayText;
        }
        if (!buttonAction && unwrapped.listResponseMessage) {
          buttonAction = unwrapped.listResponseMessage.singleSelectReply?.selectedRowId || unwrapped.listResponseMessage.title;
        }

        // 3. Extract text
        const rawText = (
          buttonAction ||
          unwrapped.conversation ||
          unwrapped.extendedTextMessage?.text ||
          unwrapped.imageMessage?.caption ||
          unwrapped.videoMessage?.caption ||
          ''
        ).trim();

        // 4. Check for audio
        const audioMsg = unwrapped.audioMessage || unwrapped.ptvMessage;
        let incomingText = rawText;

        if (audioMsg) {
          const duration = audioMsg.seconds || 0;
          const filename = `audio_${Date.now()}_${msg.key.id}.ogg`;
          const filePath = path.join(MEDIA_DIR, filename);

          try {
            const buffer = await downloadMediaMessage(msg, 'buffer', {}, {
              logger: pino({ level: 'silent' }),
              reuploadRequest: sock.updateMediaMessage
            });
            fs.writeFileSync(filePath, buffer);
            const transcribed = await transcribeAudioLocally(filePath);
            if (transcribed) {
              incomingText = transcribed;
              console.log(`[WHATSAPP AUDIO TRANSCRIÇÃO] ${cleanNumber}: "${transcribed}"`);
            }
          } catch (audioErr) {
            console.error('[AUDIO DOWNLOAD ERROR]:', audioErr.message);
          }
        }

        if (!incomingText) continue;

        // 5. Check for numbered menu selection fallback (e.g. user typed "1", "2", "1️⃣", etc.)
        const trimmed = incomingText.trim();
        const numMatch = trimmed.match(/^(?:([1-9][0-9]?)|([1-9])️⃣)$/);
        if (numMatch) {
          const numVal = parseInt(numMatch[1] || numMatch[2], 10);
          const menu = lastMenuByNumber.get(cleanNumber);
          if (menu && (Date.now() - menu.timestamp < 3600000) && Array.isArray(menu.buttons)) {
            const btnIdx = numVal - 1;
            if (menu.buttons[btnIdx]) {
              const chosen = menu.buttons[btnIdx];
              const resolved = chosen.query || (typeof chosen.action === 'string' ? chosen.action : null) || chosen.text;
              if (resolved) {
                console.log(`[WHATSAPP SHORTCUT] Resposta numérica "${trimmed}" de ${cleanNumber} mapeada para ação: "${resolved}"`);
                incomingText = resolved;
              }
            }
          }
        }

        console.log(`[WHATSAPP INBOUND] [${cleanNumber} - ${pushName || 'N/A'}]: "${incomingText.slice(0, 80)}"`);

        // Check sender type
        const userIsAdmin = isAdmin(cleanNumber);
        const userIsTeam = isTeamMember(cleanNumber);

        // 1. Record lead if not team/admin
        if (!userIsAdmin && !userIsTeam) {
          recordInboundLead(cleanNumber, pushName, incomingText);
        }

        // 2. Admin Quick Slash Commands
        if (userIsAdmin && incomingText.startsWith('/')) {
          const words = incomingText.split(/\s+/);
          const cmd = words[0].toLowerCase();
          const args = incomingText.slice(words[0].length).trim();

          if (cmd === '/equipe' || cmd === '/membros') {
            const team = getTeam();
            const lines = ['👥 *EQUIPE CORPORATIVA AXION*', '━━━━━━━━━━━━━━━━━━━━━━'];
            for (const [p, u] of Object.entries(team)) {
              lines.push(`• *${u.name}* (${u.role})\n  📱 \`${p}\``);
            }
            lines.push('━━━━━━━━━━━━━━━━━━━━━━\n_Use /cadastrar <num> <cargo> <nome> para adicionar_');
            await sendWhatsAppText(remoteJid, lines.join('\n'), { isInternalReply: true });
            continue;
          }

          if (cmd === '/cadastrar' || cmd === '/add') {
            const parts = args.split(/\s+/);
            if (parts.length >= 3) {
              const newNum = parts[0].replace(/[^0-9]/g, '');
              const newRole = parts[1].toUpperCase();
              const newName = parts.slice(2).join(' ');
              const team = getTeam();
              team[newNum] = {
                phone: newNum,
                name: newName,
                role: newRole,
                permissions: [newRole.toLowerCase()],
                created_at: new Date().toISOString()
              };
              saveTeam(team);
              await sendWhatsAppText(remoteJid, `✅ *Membro cadastrado com sucesso!*\n\n• Nome: *${newName}*\n• Cargo: *${newRole}*\n• Número: \`${newNum}\``, { isInternalReply: true });
            } else {
              await sendWhatsAppText(remoteJid, '⚠️ *Uso correto:* `/cadastrar <numero> <cargo> <nome>`\nExemplo:\n`/cadastrar 5511999998888 SUPORTE Carlos Silva`', { isInternalReply: true });
            }
            continue;
          }

          if (cmd === '/remover') {
            const targetNum = args.replace(/[^0-9]/g, '');
            const team = getTeam();
            if (targetNum === ADMIN_NUMBER) {
              await sendWhatsAppText(remoteJid, '❌ *Operação negada:* O Administrador Principal não pode ser removido.', { isInternalReply: true });
            } else if (team[targetNum]) {
              const remName = team[targetNum].name;
              delete team[targetNum];
              saveTeam(team);
              await sendWhatsAppText(remoteJid, `🗑️ *Membro removido:* ${remName} (\`${targetNum}\`).`, { isInternalReply: true });
            } else {
              await sendWhatsAppText(remoteJid, `⚠️ Número \`${targetNum}\` não encontrado na equipe.`, { isInternalReply: true });
            }
            continue;
          }

          if (cmd === '/leads') {
            const leads = getLeads();
            const list = Object.values(leads).slice(-8);
            if (list.length === 0) {
              await sendWhatsAppText(remoteJid, '📋 *Nenhum lead registrado ainda.*', { isInternalReply: true });
            } else {
              const lines = ['🎯 *ÚLTIMOS LEADS DO WHATSAPP*', '━━━━━━━━━━━━━━━━━━━━━━'];
              for (const l of list) {
                const t = (l.last_interaction || '').slice(11, 16);
                lines.push(`• *${l.name}* (\`${l.phone}\`)\n  Msgs: ${l.inbound_messages_count} | Última: ${t}\n  _"${l.last_message || ''}"_`);
              }
              lines.push('━━━━━━━━━━━━━━━━━━━━━━');
              await sendWhatsAppText(remoteJid, lines.join('\n'), { isInternalReply: true });
            }
            continue;
          }
        }

        // 3. Forward to AXION Brain Server
        try {
          const brainPayload = {
            chat_id: remoteJid,
            message: incomingText,
            username: pushName || cleanNumber,
            first_name: pushName || (userIsAdmin ? 'Admin' : (userIsTeam ? 'Equipe' : 'Lead')),
            source: 'whatsapp',
            is_admin: userIsAdmin,
            is_lead: !userIsAdmin && !userIsTeam
          };

          const resp = await fetch(`${BRAIN_URL}/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(brainPayload)
          });

          if (!resp.ok) {
            console.error(`[BRAIN ERROR] HTTP ${resp.status} ao encaminhar mensagem do WhatsApp.`);
          }
        } catch (fwdErr) {
          console.error('[BRAIN FWD ERROR] Falha ao comunicar com Brain Server:', fwdErr.message);
          if (userIsAdmin) {
            await sendWhatsAppText(remoteJid, `🔴 *Brain Server Offline:* \`${fwdErr.message}\``, { isInternalReply: true });
          }
        }
      }
    });

  } catch (err) {
    console.error('[BAILEYS INIT ERROR]', err);
    state.status = 'offline';
    state.message = err.message;
  } finally {
    isBaileysInitializing = false;
  }
}

// ── HTTP API Server ────────────────────────────────────────
function handleHttpRequest(req, res) {
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

  function readJsonBody(callback) {
    let bodyStr = '';
    req.on('data', chunk => { bodyStr += chunk.toString(); });
    req.on('end', () => {
      try {
        const parsed = JSON.parse(bodyStr || '{}');
        callback(null, parsed);
      } catch (e) {
        callback(e, null);
      }
    });
  }

  // GET /status or /api/status
  if (req.method === 'GET' && (pathname === '/status' || pathname === '/api/status' || pathname === '/health')) {
    state.teamCount = Object.keys(getTeam()).length;
    state.leadsCount = Object.keys(getLeads()).length;
    return sendJson(state);
  }

  // GET /pairing-code or /api/pairing-code
  if (req.method === 'GET' && (pathname === '/pairing-code' || pathname === '/api/pairing-code')) {
    return sendJson({
      status: state.status,
      number: PAIRING_NUMBER,
      admin_number: ADMIN_NUMBER,
      pairing_code: state.pairingCode,
      message: state.pairingCode
        ? `Digite o código [ ${state.pairingCode} ] no WhatsApp móvel (${PAIRING_NUMBER}).`
        : 'Pairing code não ativo ou já conectado.'
    });
  }

  // GET /leads
  if (req.method === 'GET' && (pathname === '/leads' || pathname === '/api/leads')) {
    return sendJson({
      total: Object.keys(getLeads()).length,
      leads: Object.values(getLeads())
    });
  }

  // GET /team
  if (req.method === 'GET' && (pathname === '/team' || pathname === '/api/team')) {
    return sendJson({
      total: Object.keys(getTeam()).length,
      team: Object.values(getTeam())
    });
  }

  // POST /send-internal (called by Brain Server or test scripts)
  if (req.method === 'POST' && pathname === '/send-internal') {
    readJsonBody(async (err, body) => {
      if (err || !body.to) {
        return sendJson({ error: 'Parâmetro "to" obrigatório' }, 400);
      }
      const remoteJid = body.to.includes('@') ? body.to : `${body.to.replace(/[^0-9]/g, '')}@s.whatsapp.net`;
      const resSend = await sendWhatsAppText(remoteJid, body.message || '', {
        isInternalReply: true,
        editKey: body.edit_key || body.editKey || body.edit_message_id || null,
        buttons: Array.isArray(body.buttons) && body.buttons.length > 0 ? body.buttons : null,
        carousel: Array.isArray(body.carousel) && body.carousel.length > 0 ? body.carousel : null,
        list: body.list || null,
        poll: body.poll || null,
        react: body.react || null,
        footer: body.footer || null
      });
      return sendJson(resSend, resSend.success ? 200 : 500);
    });
    return;
  }

  // POST /whatsapp/send (Commercial / Promotional / Utility with Meta Anti-Ban check)
  if (req.method === 'POST' && (pathname === '/whatsapp/send' || pathname === '/api/send')) {
    readJsonBody(async (err, body) => {
      if (err || !body.to || !body.message) {
        return sendJson({ error: 'Parâmetros "to" e "message" obrigatórios' }, 400);
      }

      const targetNumber = body.to.replace(/[^0-9]/g, '');
      const remoteJid = body.to.includes('@') ? body.to : `${targetNumber}@s.whatsapp.net`;
      const force = Boolean(body.force);

      // Validate Meta Anti-Ban
      const antiBanCheck = canSendOutbound(targetNumber, force);
      if (!antiBanCheck.allowed) {
        return sendJson({
          success: false,
          blocked_by_anti_ban: true,
          reason: antiBanCheck.reason,
          message: antiBanCheck.message
        }, 403);
      }

      const resSend = await sendWhatsAppText(remoteJid, body.message, { force });
      return sendJson(resSend, resSend.success ? 200 : 500);
    });
    return;
  }

  // POST /pair (request pairing code for phone number)
  if (req.method === 'POST' && (pathname === '/pair' || pathname === '/api/pair')) {
    readJsonBody(async (err, body) => {
      const targetPhone = (body.number || ADMIN_NUMBER).replace(/[^0-9]/g, '');
      if (!sock) {
        return sendJson({ error: 'Socket não inicializado' }, 500);
      }
      try {
        const code = await sock.requestPairingCode(targetPhone);
        state.pairingCode = code;
        state.pairingNumber = targetPhone;
        state.status = 'pairing_ready';
        return sendJson({ success: true, number: targetPhone, pairing_code: code });
      } catch (pErr) {
        return sendJson({ success: false, error: pErr.message }, 500);
      }
    });
    return;
  }

  sendJson({ error: 'Not Found' }, 404);
}

// ── Startup ────────────────────────────────────────────────
const server = http.createServer(handleHttpRequest);
const BIND_HOST = process.env.WHATSAPP_BRIDGE_HOST || '127.0.0.1';
server.listen(PORT, BIND_HOST, () => {
  console.log(`[WHATSAPP BRIDGE] Servidor HTTP ativo em http://${BIND_HOST}:${PORT}`);
  console.log(`[WHATSAPP BRIDGE] Admin Configurado: ${ADMIN_NUMBER}`);
  initBaileys();
});
