---
name: executive-notification-governance
description: >-
  Protocolo mandatório de governança de notificações executivas, eliminação de spam e ruído operacional,
  filtro de tarefas efêmeras/scratch, histerese e deadband de telemetria de RAM e formatação de entregas executivas.
---

# Executive Notification Governance & Anti-Noise Protocol — Autonomous Agent Workspace OS

Guia canônico e operacional para garantir que toda notificação push enviada à liderança técnica/executiva (Telegram, WhatsApp e canais executivos) possua alto valor executivo, densidade técnica, evidências factuais e zero ruído ou flapping.

---

## 1. Princípios Invioláveis (Zero-Noise Mandate)

### 1.1 Proibição Terminante de Alertas de Tarefas Efêmeras (Anti-Scratch Shield)
- O sentinela de tarefas (`desktop_watcher.py`, `watcher.py` e rotinas de polling) **NUNCA** deve notificar o operador sobre execuções internas de terminal, comandos transitórios ou scripts de apoio:
  - ❌ Tarefas com padrão `task-*.log` oriundas do runner interno do Antigravity (logs de 200 a 800 bytes gerados por comandos corriqueiros do shell).
  - ❌ Tarefas com logs menores que 150 bytes sem entregáveis explicitados.
  - ❌ Tarefas rotuladas como `antigravity_..._task-XXXX` com mensagens genéricas do tipo *"Processo finalizado (log: 232 bytes)"*.
- **Comportamento Obrigatório**: Tarefas internas efêmeras devem ser registradas silenciosamente no cache de deduplicação (`silent_scratch: True`), sem emissão de push notification.

### 1.2 Critérios Mandatórios de Elegibilidade Executiva
Para que uma tarefa gere notificação ativa à liderança, ela **DEVE** cumprir pelo menos um dos requisitos:
1. **Marcador Explícito de Marco de Negócio**: O log ou saída deve conter tags como `[executive_delivery]`, `deploy_success`, `liberado_ok`, `produção` ou `release_completed`.
2. **Entregável Técnico Factual Comprovado**: Deve apresentar pelo menos um artefato verificável:
   - URL pública ou de staging (`https://...example.com`, Vercel, Cloudflare, etc.).
   - Porta de serviço ativamente escutando (ex: `http://localhost:8765`, `3000`, `8080`).
   - Hash de commit Git ou branch entregue.
   - Migração de banco de dados executada com sucesso comprovado.
3. **Execução Longa de Alto Impacto**: Tarefa solicitada formalmente com tempo superior a 15 segundos e saída estruturada substancial (> 500 bytes de relatório conclusivo).

---

## 2. Protocolo de Histerese e Deadband de Telemetria de Hardware

Flutuações naturais da memória RAM e CPU do host Windows (working set de browsers, compiladores e containers) não devem gerar disparos repetitivos ou alarmes falso-positivos de alternância (ping-pong).

### 2.1 Limiares Canônicos de Alerta de RAM
- **Normalização (`NORM`)**: $\le 80.0\%$ (sinaliza restabelecimento da estabilidade).
- **Alerta Amarelo (`WARNING`)**: $\ge 92.0\%$ (requer atenção executiva).
- **Alerta Crítico (`CRITICAL`)**: $\ge 96.0\%$ (risco iminente de OOM / congelamento do host).

### 2.2 Zona Morta (Deadband Hysteresis)
- Na faixa intermediária entre $80.0\%$ e $92.0\%$, o sistema **MANTÉM** o estado anterior sem disparar nenhum alerta:
  - Se estava normal, continua silencioso mesmo que suba de 82% para 89%.
  - Se estava em alerta, só envia mensagem de recuperação quando cair estritamente abaixo de 80.0%.

### 2.3 Cooldown e Enriquecimento Diagnóstico Obrigatório
- **Cooldown Mínimo**: Intervalo de **4 horas (14.400 segundos)** entre alertas repetidos do mesmo nível de severidade.
- **Top Consumidores de RAM**: Nenhum alerta de RAM pode ser despachado com valores zerados (ex: `0 GB de 11.96 GB`). É compulsório:
  1. Calcular o uso real: `used_gb = total_gb - free_gb`.
  2. Identificar e listar os **Top 3 Processos Consumidores** via `tasklist` nativo (ex: `chrome.exe [1.8 GB]`, `node.exe [620 MB]`, `python.exe [410 MB]`).
  3. Apresentar recomendação técnica acionável (ex: *"Feche abas do Chrome ou reinicie containers inativos via PM2"*).

---

## 3. Formatação Canônica de Entrega Executiva

Toda entrega de tarefa autônoma ou relatório despachado ao CEO via Telegram ou WhatsApp deve obedecer rigorosamente à estrutura corporativa:

```html
🚀 <b>[AXION ENTREGA EXECUTIVA]</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 <b>Projeto / Contexto:</b> {nome_do_projeto}
🤖 <b>Agente Responsável:</b> {nome_do_agente_ou_cli}
🎯 <b>Entregáveis Realizados:</b>
  • {entregavel_1}
  • {entregavel_2}
🌐 <b>Evidências / URLs:</b>
  • {url_ou_porta_ou_commit}
⏱️ <b>Tempo de Execução:</b> {duracao}s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👉 <b>Ação do CEO:</b> Nenhuma ação necessária no momento. Sistema operacional.
```

---

## 4. Linguagem Amigável nos Passos de Execução (`_friendly_step_description`)

Em conversas interativas via chat, comandos de terminal brutos (`git status`, `tasklist /FO CSV`, `netstat -ano`) não devem ser despejados crus no canal executivo. Eles devem ser mapeados para descrições semânticas de alto nível:

| Comando / Ação Bruta | Descrição Semântica Executiva |
| :--- | :--- |
| `git status`, `git diff` | Auditoria de estado do repositório Git |
| `pm2 status`, `pm2 restart` | Gestão de processos e daemons PM2 |
| `tasklist`, `wmic`, `Get-Process` | Mapeamento de recursos e processos do sistema |
| `netstat`, `curl`, `Invoke-RestMethod` | Verificação de conectividade e portas de rede |
| `python scripts/test_*.py` | Execução de bateria automatizada de testes |

---

## 5. Script Standalone de Auditoria e Validação

A skill disponibiliza o utilitário nativo em `scripts/audit_notification_eligibility.py` para inspecionar filas de tarefas, logs e configurações de telemetria sem dependências externas.
