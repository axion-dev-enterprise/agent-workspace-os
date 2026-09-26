---
name: whatsapp-baileys-bot-ops
description: >-
  Operational skill for WhatsApp bot engineering, Baileys socket lifecycle management, multi-device
  authentication state persistence, QR and pairing code generation, connection error handling (401, 428, 515),
  webhook dispatching, rate limit defense, and high-availability keeper processes across AXION nodes.
---

# WhatsApp Baileys Bot Ops Skill — Enterprise Organization

Guia canônico e operacional para sustentação, resiliência e desenvolvimento de robôs e conectores de mensageria WhatsApp via biblioteca **Baileys (Multi-Device API)** em infraestrutura de contêineres na **Enterprise Organization**.

---

## 1. Princípios de Confiabilidade & Anti-Ban

1. **Persistência Segura do Auth State**: As chaves criptográficas (`creds.json`) devem ser gravadas em volume montado ou banco de dados relacional / Redis. A perda de chaves invalida a sessão e força re-escaneamento de QR Code.
2. **Backoff Exponencial em Desconexões**: Nunca tente reconectar em loop infinito sem jitter. Erros 428 (Precondition Required) ou 515 (Restart Required) exigem pausas controladas (2s, 5s, 10s, max 30s).
3. **Respeito aos Limites de Taxa (Rate Limits)**:
   - Delay randômico humano entre mensagens (mínimo de 1200ms a 3500ms).
   - Simulação de presença: disparar `sendPresenceUpdate('composing')` antes de enviar mensagens de texto.

---

## 2. Ciclo de Vida do Socket Baileys

### 2.1 Inicialização Canônica com `useMultiFileAuthState`
```typescript
import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeInMemoryStore,
} from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';

async function startWhatsAppBot() {
  const { state, saveCreds } = await useMultiFileAuthState('/data/sessions/auth_info');
  const { version, isLatest } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    logger: pino({ level: 'warn' }),
    printQRInTerminal: true,
    auth: state,
    connectTimeoutMs: 60000,
    defaultQueryTimeoutMs: 60000,
    keepAliveIntervalMs: 10000,
    browser: ['Enterprise Organization', 'Chrome', '124.0.0.0'],
  });

  // Salvar credenciais sempre que atualizadas
  sock.ev.on('creds.update', saveCreds);

  // Monitorar mudanças no status de conexão
  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('[WHATSAPP] Novo QR Code gerado.');
    }

    if (connection === 'close') {
      const statusCode = (lastDisconnect?.error as Boom)?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      console.log(`[WHATSAPP] Conexão encerrada (Status: ${statusCode}). Reconectando: ${shouldReconnect}`);

      if (shouldReconnect) {
        setTimeout(startWhatsAppBot, 5000);
      } else {
        console.error('[WHATSAPP] Deslogado pelo dispositivo mestre. Necessário novo pareamento.');
      }
    } else if (connection === 'open') {
      console.log('[WHATSAPP] Conexão estabelecida com sucesso!');
    }
  });

  return sock;
}
```

---

## 3. Tratamento de Erros e Códigos de Status

| Código de Erro | Causa Comum | Ação Recomendada |
| :--- | :--- | :--- |
| **`401`** (`loggedOut`) | Usuário desconectou pelo WhatsApp móvel ou sessão expirada | Limpar pasta `auth_info/` e disparar alerta de novo QR Code |
| **`428`** (`connectionLost`) | Queda de rede transitória ou timeout do WhatsApp | Reconectar imediatamente com backoff de 2s |
| **`515`** (`restartRequired`) | O servidor WhatsApp solicitou reinicialização de stream | Reiniciar o socket imediatamente mantendo as credenciais |
| **`408`** (`timedOut`) | Congestionamento na rede ou socket sem ping | Fechar socket anterior e reiniciar handshake |

---

## 4. Arquitetura de Contêineres: Keeper Pattern

Em ambientes Docker de produção:
1. **Health Check Endpoint (`/healthz`)**: O processo Express expõe uma rota HTTP 200 reportando o estado do socket (`CONNECTED`, `CONNECTING`, `DISCONNECTED`).
2. **Watchdog Externo**: Se o endpoint não responder por 3 ciclos consecutivos de 15 segundos, o container é reiniciado automaticamente pelo Docker (`restart: unless-stopped` ou orchestrator).
3. **Despacho Assíncrono via Filas**: O bot nunca processa lógica pesada (LLM, RAG, banco) síncronamente na thread do socket. Recebe a mensagem, envia ACK, e despacha o payload para uma fila Redis/BullMQ.
