---
name: agent-email-social-intelligence
description: >
  Sistema de comunicação multicanal para agentes AXION. Cobre:
  (1) Cliente de e-mail IMAP/SMTP para agentes (Proton Bridge, Gmail, Google Workspace);
  (2) Registro de presença digital do agente em redes/plataformas;
  (3) Monitor de inteligência de conteúdo — GitHub Trending, HackerNews, RSS feeds AXION-curated.
  Use quando configurar caixas de e-mail de agentes, enviar alertas por e-mail,
  monitorar feeds de conteúdo relevantes ou gerenciar a identidade digital do ecossistema AXION.
---

# Skill: Agent Email, Social & Content Intelligence

## Visão Geral

Esta skill cobre três subsistemas integrados de comunicação e inteligência para agentes AXION:

1. **Sistema de E-mail** — cliente IMAP/SMTP para agentes enviarem e receberem e-mails
2. **Presença Digital** — registro canônico de contas, bots e redes onde o agente está presente
3. **Monitor de Inteligência** — rotina automática que absorve conteúdo relevante do ecossistema
4. **Twitter/X Monitor** — monitoramento via API v2 gratuita (ou mock para testar pipeline)
5. **Instagram Monitor** — monitoramento via instaloader autenticado (ou mock para testar pipeline)

---

## 1. Sistema de E-mail para Agentes

### Arquivo
`services/agent-email/agent_email_client.py`

### Contas Suportadas

| Conta | Provider | Propósito | Status |
|-------|----------|-----------|--------|
| `developer@example.com` | Gmail | Git identity, GitHub, ops | ATIVO |
| `agent@example.com` | Proton Bridge | Comunicações criptografadas | PENDING_SETUP |
| `iago@example.com` | Google Workspace | Admin formal | ATIVO (GAM) |

### Configuração via Env Vars

```env
AGENT_EMAIL_USER=developer@example.com
AGENT_EMAIL_PASSWORD=<App_Password_Gmail_16_chars>
AGENT_EMAIL_IMAP=imap.gmail.com
AGENT_EMAIL_IMAP_PORT=993
AGENT_EMAIL_SMTP=smtp.gmail.com
AGENT_EMAIL_SMTP_PORT=587
```

> **Para Proton Mail Bridge**: instale o Bridge → faça login → use `127.0.0.1:1143` (IMAP) e `127.0.0.1:1025` (SMTP) com a senha gerada pelo Bridge.

### Gmail App Password (passo-a-passo)
1. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Selecione **App: Mail** | **Dispositivo: Windows**
3. Copie a senha de 16 caracteres
4. Adicione ao secrets manager (nunca hardcode)

### Comandos CLI

```powershell
# Verificar inbox
python services/agent-email/agent_email_client.py poll

# Enviar e-mail
python services/agent-email/agent_email_client.py send "dest@email.com" "Assunto" "Corpo"

# Ver histórico
python services/agent-email/agent_email_client.py history
```

### Uso Programático

```python
from services.agent_email.agent_email_client import AgentEmailManager

mgr = AgentEmailManager()

# Enviar alerta
mgr.send_agent_email(
    agent="axion-security",
    to="iago@example.com",
    subject="[ALERTA] SSL expirando em 7 dias",
    body="api.example.com expira em 2026-10-03",
)

# Poll inbox
messages = mgr.poll_inbox()
```

### Caixas Lógicas de Agentes

| Mailbox ID | Display | Tags |
|-----------|---------|------|
| `axion-core` | AXION Core Agent | ops, infra, alerts |
| `axion-monitor` | AXION Content Monitor | content, feeds, intelligence |
| `axion-security` | AXION Security Agent | pentest, osint, alerts |

### Storage
- `memory/email/inbox.jsonl` — histórico de mensagens recebidas
- `memory/email/sent.jsonl` — histórico de e-mails enviados

---

## 2. Presença Digital do Agente

### Registro Canônico
`memory/infrastructure/AGENT_DIGITAL_PRESENCE.json`

### Canais Ativos

| Canal | Tipo | Status | Script |
|-------|------|--------|--------|
| Gmail | E-mail | ATIVO | `agent_email_client.py` |
| Google Workspace | E-mail org | ATIVO | GAM |
| GitHub | Código | ATIVO (25 repos) | monitoring |
| Telegram | Bot ops | ATIVO | `scripts/telegram_assistant_bot.py` |
| WhatsApp | Bridge | ATIVO | `scripts/whatsapp_bridge/` |
| HackerNews | Monitoring | ATIVO | `content_intelligence_monitor.py` |
| Reddit | RSS monitoring | ATIVO | `content_intelligence_monitor.py` |

### Subreddits Monitorados (via RSS)
- `r/netsec`, `r/selfhosted`, `r/homelab`
- `r/Python`, `r/MachineLearning`, `r/artificial`
- `r/docker`, `r/devops`

---

## 3. Monitor de Inteligência de Conteúdo

### Arquivo
`scripts/content_intelligence_monitor.py`

### Fontes

| Fonte | Método | Items/Execução |
|-------|--------|----------------|
| GitHub Trending (all, python, ts, js) | HTTP scraping | ~25 cada |
| HackerNews Top Stories | Firebase API | 25 |
| Cloudflare Blog | RSS | 15 |
| Proton Blog | RSS | 10 |
| The Hacker News (infosec) | RSS FeedBurner | 15 |
| GitHub Changelog | RSS | 10 |
| Vercel Blog | RSS | 15 |
| Next.js Releases | Atom/GitHub | 10 |
| Tailscale Blog | RSS | 10 |

### Keywords AXION (45 total)
Stack: cloudflare, workers, d1, r2, nextjs, fastapi, nestjs, tailwind...
Infra: docker, kubernetes, k3s, tailscale, vercel, github actions...
AI: gemini, langchain, langgraph, rag, vector, llm, agent, mcp...
Security: proton, wireguard, zero trust, osint, pentest, cve...
DBs: postgresql, redis, qdrant, mongodb, sqlite...

### Storage

```
memory/intelligence/
  daily_digest.jsonl    # uma entrada por execução (resumo)
  feeds_cache.json      # fingerprints vistos (dedup)
  keywords_hits.jsonl   # todos os hits relevantes (histórico)
```

### Executar Manualmente

```powershell
python scripts/content_intelligence_monitor.py
```

### Agendamento

| Task | Schedule | Runner |
|------|----------|--------|
| `AXION-Content-Intelligence` | Daily 08:00 | Task Scheduler / SYSTEM |
| `AXION-Agent-Email-Poll` | Every hour | Task Scheduler / SYSTEM |

---

## 4. Twitter/X Monitor

**Arquivo:** `services/agent-social/twitter_x_monitor.py`

> **Realidade de 2026:** Nitter (mirrors open-source) não funcionam mais — o Twitter bloqueou guest tokens. A única forma gratuita e legítima é a **API v2 Free Tier**.

### Setup (5 min, gratuito)

1. Acesse [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Sign in com qualquer conta Twitter/X
3. **Create Project** → nomeie (ex: `AXION Monitor`)
4. **Add App** → copie o **Bearer Token**
5. Adicione ao `c:\workspace\.env`:
   ```env
   X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAxxxxx...
   ```
6. O monitor ativa automaticamente na próxima execução

### Perfis Monitorados

`@cloudflare`, `@vercel`, `@nextjs`, `@tailscale`, `@github`, `@ProtonPrivacy`, `@docker`, `@OpenAI`, `@GoogleDeepMind`

### Queries de Busca

`cloudflare workers`, `nextjs 15`, `langchain agent`, `#rag llm`, `fastapi python`

### Comandos

```powershell
# Testar pipeline sem API key (mock data)
python services/agent-social/twitter_x_monitor.py --mock

# Executar real (com X_BEARER_TOKEN configurado)
python services/agent-social/twitter_x_monitor.py
```

### Storage
`memory/intelligence/twitter_hits.jsonl` — hits com keywords AXION

---

## 5. Instagram Monitor

**Arquivo:** `services/agent-social/instagram_monitor.py`

> **Realidade de 2026:** Instagram exige login mesmo para perfis públicos. Instaloader anônimo retorna 401.

### Setup (requer conta Instagram separada)

1. Crie uma conta Instagram específica para monitoramento (ex: `axion.monitor.bot`)
2. Adicione ao `c:\workspace\.env`:
   ```env
   IG_USERNAME=axion.monitor.bot
   IG_PASSWORD=sua_senha
   ```
3. Na primeira execução, a sessão é salva em `memory/intelligence/instagram_session/`
4. Sessão persiste — login ocorre apenas uma vez

> **Dica de segurança:** Use uma conta secundária/desposable, nunca sua conta pessoal. Instagram pode banir contas que fazem scraping.

### Perfis Monitorados

`cloudflare`, `github`, `docker`, `hashicorp`, `vercel`

### Comandos

```powershell
# Testar pipeline sem conta (mock data)
python services/agent-social/instagram_monitor.py --mock

# Executar real (com IG_USERNAME + IG_PASSWORD)
python services/agent-social/instagram_monitor.py
```

### Storage
- `memory/intelligence/instagram_hits.jsonl` — posts com keywords AXION
- `memory/intelligence/instagram_all.jsonl` — todos os posts novos
- `memory/intelligence/instagram_session/` — sessão persistida

---

## Guardrails

- **Nunca** hardcode credenciais — usar env vars ou secrets manager
- **Nunca** registrar senhas ou tokens nos logs
- Twitter/X: respeite o rate limit da API (Twitter retorna 429 se excedido — tweepy lida automaticamente)
- Instagram: `MAX_POSTS = 10` por perfil para evitar throttling; não aumente muito
- O monitor é **read-only** para todas as fontes (sem POST, sem engajamento)
- Para novos canais que exijam conta, criar via operador humano + documentar em `AGENT_DIGITAL_PRESENCE.json`

## Atualização do Registro

Ao adicionar novas fontes ou contas, atualizar:
1. `scripts/content_intelligence_monitor.py` → `RSS_FEEDS` dict
2. `services/agent-social/twitter_x_monitor.py` → `TWITTER_PROFILES` / `TWITTER_QUERIES`
3. `services/agent-social/instagram_monitor.py` → `INSTAGRAM_PROFILES`
4. `memory/infrastructure/AGENT_DIGITAL_PRESENCE.json`
5. Esta SKILL.md
6. Executar `python scripts/sync_skills_registry.py`
