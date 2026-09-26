---
name: telegram-bot-ops
description: >-
  Operational skill for Telegram Bot API engineering, BotFather profile and menu configuration,
  long polling vs webhook architecture, inline keyboards, callback query routing, HTML/MarkdownV2 formatting,
  SRE infrastructure alerting, subscriber state management, and daemon service operation across AXION nodes.
---

# Telegram Bot Ops Skill — AXION Enterprise

Guia canônico e operacional para criação, sustentação, monitoramento e automação de robôs e assistentes via **Telegram Bot API** na infraestrutura da **AXION Enterprise**.

---

## 1. Princípios de Arquitetura de Bots no Telegram

1. **Segurança de Tokens**: O token HTTP API gerado pelo `@BotFather` (`<bot_id>:<token_hash>`) confere controle total ao bot. Ele **nunca** deve ser versionado no Git; armazene exclusivamente no `.env` (ignorado por `.gitignore`).
2. **Long Polling vs Webhooks**:
   - **Long Polling (`getUpdates`)**: Recomendado para ambientes de desenvolvimento, estações locais (`desktop-1t1e46h`) ou servidores sem IP público direto. Não requer certificado SSL público nem porta aberta.
   - **Webhooks (`setWebhook`)**: Recomendado para nós em produção expostos via Cloudflare Tunnel ou edge serverless (Cloudflare Worker). A API do Telegram envia requisições `POST` diretamente para o endpoint HTTPS.
3. **Respeito aos Rate Limits**:
   - Máximo de **30 mensagens por segundo** globalmente por bot.
   - Máximo de **1 mensagem por segundo** por chat individual.
   - Máximo de **20 mensagens por minuto** para o mesmo grupo.

---

## 2. Configuração de Metadados via BotFather / HTTP API

Metadados do bot podem ser configurados via comandos no chat do `@BotFather` ou programaticamente via API:

```python
import urllib.request, json

TOKEN = "YOUR_BOT_TOKEN"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def api_call(method: str, data: dict):
    req = urllib.request.Request(
        f"{BASE_URL}/{method}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

# 1. Descrição Curta (exibida no perfil e compartilhamento)
api_call("setMyShortDescription", {
    "short_description": "Assistente Executivo e Operacional de Infraestrutura da AXION Enterprise."
})

# 2. Descrição Completa (exibida na tela inicial antes do /start)
api_call("setMyDescription", {
    "description": "Assistente Oficial da AXION Enterprise.\n\nMonitore a saúde dos servidores, rede mesh Tailnet, bancos de dados, backups em cold storage, certificados SSL e deploys Vercel em tempo real."
})

# 3. Comandos do Menu de Autocomplete
commands = [
    {"command": "start", "description": "Iniciar e ver menu do assistente"},
    {"command": "status", "description": "Visão geral da infraestrutura e alertas"},
    {"command": "health", "description": "Telemetria detalhada dos nós Tailnet e Web"},
    {"command": "ssl", "description": "Auditoria de certificados TLS/SSL e domínios"},
    {"command": "backup", "description": "Status do backup offline e retenção (E:)"},
    {"command": "infra", "description": "Mapa canônico de nós e computação"},
    {"command": "help", "description": "Guia de comandos e ajuda operacional"}
]
api_call("setMyCommands", {"commands": commands})
```

---

## 3. Padrão de Formatação: HTML vs MarkdownV2

Prefira **HTML** (`parse_mode="HTML"`) para evitar problemas de escape de caracteres especiais do MarkdownV2 (como `.`, `-`, `_`, `!`, `(`):

```html
<b>Texto em Negrito</b>
<i>Texto em Itálico</i>
<code>código_inline_ou_ip</code>
<pre><code class="language-python"># Bloco de código
print("AXION Enterprise")
</code></pre>
<a href="https://example.com">Link Seguro</a>
```

---

## 4. Teclados Interativos (Inline Keyboards & Callback Queries)

```python
def get_dashboard_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Status Geral", "callback_data": "status"},
                {"text": "🩺 Saúde & Nós", "callback_data": "health"}
            ],
            [
                {"text": "🔒 Certificados SSL", "callback_data": "ssl"},
                {"text": "💾 Backups (E:)", "callback_data": "backup"}
            ],
            [
                {"text": "🌐 Topologia Infra", "callback_data": "infra"},
                {"text": "❓ Ajuda", "callback_data": "help"}
            ]
        ]
    }
```

Ao processar `callback_query`, **sempre** responda com `answerCallbackQuery` para eliminar o estado de carregamento no cliente Telegram:
```python
api_call("answerCallbackQuery", {"callback_query_id": cb["id"]})
```

---

## 5. Padrão de Disparo Proativo de Alertas (SRE Broadcast)

Watchdogs periódicos (como `AXION-Health-Watchdog` e `AXION-SSL-Domain-Sentinel`) podem disparar mensagens proativas para administradores cadastrados:

```python
def broadcast_alert(message: str, severity: str = "WARNING"):
    subscribers_file = Path("workspace/telegram_subscribers.json")
    if not subscribers_file.exists():
        return
        
    with open(subscribers_file, "r", encoding="utf-8") as f:
        subscribers = json.load(f)
        
    icon = "🚨" if severity == "CRITICAL" else "⚠️"
    text = f"{icon} <b>ALERTA DE INFRAESTRUTURA AXION [{severity}]</b>\n\n{message}"
    
    for cid_str, sub in subscribers.items():
        if sub.get("notifications_enabled", True):
            send_message(int(cid_str), text)
```

---

## 6. Operação Contínua como Daemon / Serviço

### 6.1 No Windows (Task Scheduler na Inicialização)
```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\workspace\scripts\telegram_assistant_bot.py" -WorkingDirectory "C:\workspace"
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "AXION-Telegram-Assistant" -Action $action -Trigger $trigger -Settings $settings -Description "AXION Enterprise - Daemon do Assistente Telegram @axion_assistant_bot" -Force
```

### 6.2 No Linux (Systemd Service)
```ini
[Unit]
Description=AXION Telegram Assistant Bot Daemon
After=network.target

[Service]
Type=simple
User=axion
WorkingDirectory=/opt/axion
ExecStart=/usr/bin/python3 scripts/telegram_assistant_bot.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/axion/.env

[Install]
WantedBy=multi-user.target
```

---

## 7. Arquitetura do Co-Piloto Autônomo e Execução de Tools no PC

O assistente opera com autonomia total através do motor modular `scripts/bot_engine/`:

### 7.1 Módulos Centrais do Bot Engine (`scripts/bot_engine/`)
1. **`tool_executor.py`**: Motor de execução autônoma no PC:
   - `exec_command`: Executa comandos PowerShell / CMD em `C:\workspace`.
   - `read_file` e `write_file`: Leitura e escrita local de arquivos.
   - `list_directory`: Mapeamento de pastas e arquivos.
   - `get_system_telemetry`: Coleta em tempo real de RAM (Kernel32), Discos C: e E:, e nós WireGuard Mesh.
   - `run_health_check`: Dispara o watchdog `health_monitor_autofix.py`.
   - `run_ssl_sentinel`: Dispara a auditoria `ssl_domain_sentinel.py`.
   - `run_backup`: Dispara backups inteligentes (`enterprise_smart_backup.py`).
   - `manage_workspace_task`: Injeta, lista ou executa tarefas na esteira.

2. **`dynamic_keyboard.py`**: Sistema de Botões Dinâmicos e Sem Menus Fixos:
   - Elimina teclados estáticos fixos que poluem a tela.
   - O modelo LLM sugere de 1 a 4 botões contextuais por resposta no formato ````buttons [ ... ] ````.
   - Os botões são parseados, associados a tokens seguros e renderizados como `InlineKeyboardMarkup`.
   - Suporta ações de tool (`action: "tool:..."`), queries de continuidade (`query: "..."`) ou execução de tarefas (`action: "task:execute"`).

3. **`task_queue.py`**: Esteira de Injeção e Execução de Tarefas:
   - Injeta e sincroniza tarefas em `workspace/memory/active_tasks.json` e `memory/cowork/active_tasks.json`.
   - Ciclo de vida completo: `pending` -> `running` -> `completed` / `failed`.
   - Registro automático em `memory/cowork/blackboard.json` e `memory/daily_logs/{YYYY-MM-DD}.md`.

4. **`message_store.py`**: Persistência Local e Histórico de Mensagens:
   - Salva todas as mensagens (recebidas e enviadas) em `memory/telegram/messages.jsonl` e `memory/telegram/chats/{chat_id}.jsonl`.
   - Sincroniza diálogos diretamente no log diário Markdown `memory/daily_logs/{YYYY-MM-DD}.md`.
   - Fornece contexto conversacional multi-turn isolado por chat.

5. **`autonomous_agent.py`**: Loop ReAct de Raciocínio e Execução:
   - Orquestra chamadas autônomas de ferramentas locais (`tool_call`), observa os resultados e sintetiza a resposta final com botões sugeridos.

---

## 8. Comandos e Operação do Bot

- `/start`: Boas-vindas com apresentação de capacidades autônomas e botões iniciais dinâmicos.
- `/task add <instrução>`: Injeta tarefa na esteira do workspace com botões de execução imediata.
- `/task list`: Lista tarefas pendentes e ativas no workspace.
- `/task run <task_id>`: Executa uma tarefa pendente diretamente no PC.
- `/cmd <comando>` ou `!<comando>`: Executa comandos de terminal rápidos no PC.
- `/clear` ou `/reset`: Limpa o histórico local da conversa.
- `/help`: Guia completo de comandos e recursos.
- *Texto livre*: Qualquer mensagem é interpretada pela IA Xiaomi Mimo, executando ferramentas no PC conforme necessário.


