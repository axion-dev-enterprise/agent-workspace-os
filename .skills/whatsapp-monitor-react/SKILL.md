---
name: whatsapp-monitor-react
description: Directives and operational workflows for running the WhatsApp client bridge in monitor and react modes within Agent Workspace OS.
---

# WhatsApp Client Bridge (Monitor & React)

## Visão Geral
Esta skill rege a operação do cliente WhatsApp via Baileys conectado ao workspace canônico.

## Modos de Operação

### 1. Modo Monitor
- **Objetivo**: Escutar passivamente mensagens, áudios e transcrições de contatos ou grupos autorizados.
- **Persistência**: Grava cada mensagem em `workspace/inbox/whatsapp/YYYY-MM-DD.jsonl`.
- **Categorização Automática**:
  - `reuniao`: Pautas, atas, links de Google Meet ou Zoom.
  - `tarefa`: Demandas diretas, prazos e palavras como `#urgente` ou `fazer`.
  - `lead`: Solicitações comerciais, valores e orçamentos.
  - `audio`: Mídias e notas de voz recebidas.
  - `geral`: Conversas padrão.

### 2. Modo React
- **Objetivo**: Transformar mensagens recebidas em ações concretas de agentes de IA.
- **Disparadores**: Mensagens iniciadas com `/task` ou contendo `@agente`.
- **Fluxo de Concorrência**:
  1. Cria registro na fila `workspace/memory/active_tasks.json`.
  2. O agente Antigravity / Hermes consome a fila e inicia a execução.
  3. Ao concluir, o agente atualiza o status em `active_tasks.json` e registra na timeline diária `daily_logs/YYYY-MM-DD.md`.

## Execução da Ponte
Para iniciar a ponte e gerar o QR Code:
```bash
cd scripts/whatsapp_bridge
npm install
node server.js
```
Abra o painel web em `http://127.0.0.1:8765` para escanear o QR Code diretamente pela tela.
