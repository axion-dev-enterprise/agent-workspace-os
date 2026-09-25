# Estudo Arquitetural: Skills & Tarefas Agendadas Estratégicas — AXION Enterprise

> **Data do Estudo**: 2026-09-25  
> **Status**: Proposta Arquitetural & Catálogo Operacional  
> **Classificação**: Engenharia de Confiabilidade de Sistemas (SRE) & Automação  
> **Operador do Sistema**: `AXION DEV <axionenterprise777@gmail.com>`  

---

## 1. Visão Geral & Motivação

Uma infraestrutura híbrida moderna composta por **nós locais, VPS dedicados, edge serverless na Cloudflare, frontends na Vercel e repositórios no GitHub** requer automação proativa para manter altos níveis de disponibilidade, desempenho e segurança.

Este estudo aprofunda:
1. A matriz de **skills operacionais** especializadas necessárias para operar esse ecossistema.
2. Os **mecanismos canônicos de agendamento** disponíveis em cada camada.
3. A especificação técnica de **6 tarefas agendadas estratégicas** com alto impacto em estabilidade, segurança e integridade de dados.

---

## 2. Estudo da Matriz de Skills Operacionais (43 Skills Ativas)

A matriz operacional da AXION Enterprise foi expandida para **43 skills canônicas** estruturadas em `.agents/skills/` e espelhadas globalmente no sistema:

### 2.1 Novas Skills Incorporadas
1. **[`cron-scheduled-tasks`](file:///C:/workspace/.agents/skills/cron-scheduled-tasks/SKILL.md)**:
   - **Escopo**: Windows Task Scheduler, Systemd Timers (Debian), Cloudflare Cron Triggers e GitHub Actions Scheduled Workflows.
   - **Propósito**: Padronização da criação, resiliência, captura de logs e prevenção de concorrência (file locks / mutex) em tarefas periódicas.
2. **[`vercel-deployment-ops`](file:///C:/workspace/.agents/skills/vercel-deployment-ops/SKILL.md)**:
   - **Escopo**: Vercel CLI v59.x, gestão do escopo `axion777`, 11 projetos em produção, aliases, preview branches, env pulls, edge middleware e descomissionamento seguro.
   - **Propósito**: Governança contínua dos frontends e prevenções contra rotas zumbis e Subdomain Takeover.

### 2.2 Recomendações de Próximas Skills para Scaffolding Futuro
- **`postgresql-dba-maintenance`**: Focada em performance e sustentabilidade de bancos relacionais (`hermes_db` com 135 tabelas) — planos de execução `EXPLAIN ANALYZE`, particionamento, tuning de `work_mem` e rotinas de compactação.
- **`cloudflare-zero-trust-tunnels`**: Focada em arquitetura de ingress corporativo, políticas de acesso por e-mail/OTP, gerenciamento de tokens de túnel e substituição de portas públicas abertas.
- **`whatsapp-baileys-bot-ops`**: Focada na sustentação de bots WhatsApp em produção (`hermes-whatsapp-keeper`), gestão de sessões, tratamento de desconexões 428/515, filas de despacho e conformidade com limites de mensagens.

---

## 3. As 4 Camadas de Agendamento da Infraestrutura AXION

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ECOSSISTEMA DE AGENDAMENTO AXION                     │
├────────────────────────┬───────────────────────┬───────────────────────┤
│ Camada 1: Local OS     │ Camada 2: VPS Linux   │ Camada 3: Cloudflare  │
│ (Windows Task Sched)   │ (Systemd Timers)      │ (Edge Cron Triggers)  │
│ • Health Watchdog 30m  │ • Postgres Vacuum 7d  │ • KV Prune & Log Purge│
│ • Enterprise Backup 24h│ • WhatsApp Ping 15m   │ • Token Refresh Server│
│ • Backup Rotation 7d   │ • Docker Prune 15d    │ • Distributed Tasks   │
├────────────────────────┴───────────────────────┴───────────────────────┤
│ Camada 4: Repositórios de Código (GitHub Actions Scheduled Workflows)  │
│ • Repository Audit (cron: 0 9 * * 1)                                   │
│ • Dependency & Secret Vulnerability Audit                              │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Camada 1: Windows Task Scheduler (Estação Local `desktop-1t1e46h`)
- **Vantagem Principal**: Acesso direto à unidade física de 1TB (`E:\`) para backups offline e cold storage isolado da internet.
- **Resiliência Implementada**:
  - `-AllowStartIfOnBatteries`: Garante execução contínua mesmo em perfis de economia de energia.
  - `-StartWhenAvailable`: Se o computador estiver desligado no horário do gatilho (ex: 03:00), a tarefa é executada assim que o sistema for ligado (catch-up automático).

### 3.2 Camada 2: Systemd Timers (Nó `juliana-vps` — Debian 13)
- **Vantagem Principal**: Substitui com superioridade o daemon crontab tradicional.
- **Benefícios**:
  - `RandomizedDelaySec=300`: Evita picos simultâneos de CPU.
  - `Persistent=true`: Executa tarefas perdidas caso o servidor tenha reiniciado.
  - Integração nativa de logs via `journalctl -u <service>`.

### 3.3 Camada 3: Cloudflare Edge Cron Triggers
- **Vantagem Principal**: Automações serverless sem necessidade de servidor ligado. Executam diretamente na rede global da Cloudflare.
- **Ideal para**: Manutenção de chaves nos namespaces KV (`AXION_TELEMETRY`), agregação de métricas de tráfego e limpeza de webhooks temporários.

### 3.4 Camada 4: GitHub Actions Scheduled Workflows
- **Vantagem Principal**: Execução em runners isolados do GitHub (`ubuntu-latest`) com permissão direta para inspecionar commits, gerar relatórios de código e abrir Pull Requests autônomos.

---

## 4. Especificação de 6 Tarefas Agendadas Estratégicas

### 4.1 Tarefa 1: `AXION-Health-Watchdog` *(Em Produção)*
- **Plataforma**: Windows Task Scheduler (`desktop-1t1e46h`)
- **Frequência**: A cada **30 minutos**
- **Comando**: `python.exe C:\workspace\scripts\health_monitor_autofix.py`
- **Ações**:
  - Testa pings na Tailnet (`juliana-vps`, `axion-vps`, `debian-2vcpu`).
  - Testa endpoints de produção HTTP 200 (Vercel, Tailnet Gateway).
  - Mede espaço livre nos discos C: e E:.
  - Valida data do último backup offline.
  - Executa Auto-Fix (reinicia serviço Tailscale local se inativo, regenera registros ausentes).

### 4.2 Tarefa 2: `AXION-Enterprise-Backup` *(Em Produção)*
- **Plataforma**: Windows Task Scheduler (`desktop-1t1e46h`)
- **Frequência**: Diariamente às **03:00 AM**
- **Comando**: `python.exe C:\workspace\scripts\enterprise_smart_backup.py`
- **Ações**:
  - Copia estado do workspace, 43 skills e documentação.
  - Sincroniza atas e documentos prioritários do Google Drive via GAM 7.
  - Atualiza réplicas git dos 5 repositórios centrais do GitHub.
  - Extrai dump binário criptografado do PostgreSQL 16 (`hermes_db.sql.gz`) via Tailscale SSH.
  - Gera manifesto com verificação SHA256 na pasta `E:\backups\axion_enterprise\backup_YYYY-MM-DD\`.

### 4.3 Tarefa 3: `AXION-Backup-Rotation-Prune` *(Recomendada / Especificada)*
- **Plataforma**: Windows Task Scheduler (`desktop-1t1e46h`)
- **Frequência**: Semanal aos domingos às **04:00 AM**
- **Comando**: `python.exe C:\workspace\scripts\backup_rotation_prune.py`
- **Ações**:
  - Audita todos os diretórios `backup_*` na unidade `E:\backups\axion_enterprise\`.
  - Mantém integralmente os últimos 14 backups diários.
  - Mantém 1 backup semanal para os últimos 3 meses.
  - Remove automaticamente backups legados com mais de 90 dias, prevenindo saturação do disco de 1 TB.
  - Registra a retenção e integridade no log diário.

### 4.4 Tarefa 4: `AXION-SSL-Domain-Sentinel` *(Recomendada / Especificada)*
- **Plataforma**: Windows Task Scheduler (`desktop-1t1e46h`)
- **Frequência**: Semanal às segundas-feiras às **08:00 AM**
- **Comando**: `python.exe C:\workspace\scripts\ssl_domain_sentinel.py`
- **Ações**:
  - Consulta a validade dos certificados TLS de todas as 6 zonas ativas (`axionenterprise.cloud`, `axionflow.my`, `yannascimentoads.com`, etc.).
  - Verifica tempo restante de expiração do registro dos domínios.
  - Emite aviso preventivo no painel caso qualquer certificado expire em menos de 21 dias ou renovação automática do Cloudflare falhe.

### 4.5 Tarefa 5: `postgres-maintenance.timer` *(Recomendada para Nó Juliana)*
- **Plataforma**: Systemd Timer no nó Linux `juliana-vps` (100.81.231.111)
- **Frequência**: Semanal aos domingos às **02:00 AM**
- **Comando**: `docker exec hermes-postgres psql -U hermes -d hermes_db -c "VACUUM (ANALYZE);"`
- **Ações**:
  - Atualiza as estatísticas do otimizador de consultas do PostgreSQL para todas as 135 tabelas.
  - Recupera espaço em disco de tuplas mortas geradas por operações de chat e mensagens de WhatsApp.
  - Impede inchaço (table bloat) e mantém consultas em milissegundos.

### 4.6 Tarefa 6: `whatsapp-keeper-watchdog.timer` *(Recomendada para Nó Juliana)*
- **Plataforma**: Systemd Timer no nó Linux `juliana-vps` (100.81.231.111)
- **Frequência**: A cada **15 minutos**
- **Comando**: Script bash testando `curl -s -f http://127.0.0.1:8000/healthz`
- **Ações**:
  - Testa se o gateway Express e a sessão do WhatsApp Keeper estão responsivos.
  - Se o endpoint retornar erro ou timeout (socket travado), executa `docker restart hermes-whatsapp-keeper hermes-gateway-juliana`.
  - Garante auto-recuperação do canal WhatsApp sem intervenção humana.

---

## 5. Próximos Passos Recomendados

1. **Implementar o script `scripts/backup_rotation_prune.py`** para formalizar a política de retenção na unidade `E:\`.
2. **Implementar a rotina de VACUUM periódica no PostgreSQL** via Systemd Timer no nó `juliana-vps` para preservar a saúde do banco `hermes_db`.
3. **Manter o registro de skills sincronizado** sempre que novas competências forem desenvolvidas.
