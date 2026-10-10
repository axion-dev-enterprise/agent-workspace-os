---
name: desktop-agents-cli
description: >-
  Orquestração, execução e diagnóstico direto das CLIs dos agentes desktop de IA (OpenAI Codex,
  Google Antigravity e OpenCode) para o agente WhatsApp e Brain Server com execução não-interativa e telemetria.
---

# Desktop Agents CLI Skill — AXION Enterprise

Guia canônico para invocação, controle headless e telemetria das 3 CLIs dos agentes desktop (**OpenAI Codex**, **Google Antigravity** e **OpenCode**) a partir do Co-piloto de WhatsApp e do Brain Server.

---

## 1. Topologia das CLIs no Host Windows

| Agente | Comando PATH | Binário Nativo | Modo Headless (Não-Interativo) |
| :--- | :--- | :--- | :--- |
| **OpenAI Codex** | `codex` / `codex.cmd` | `C:\Users\AXION\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` | `codex.cmd exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --color never "<prompt>"` |
| **Google Antigravity** | `agy` / `antigravity.cmd` | `C:\Users\AXION\AppData\Local\agy\bin\agy.exe` | `agy.exe --print "<prompt>" --dangerously-skip-permissions` |
| **OpenCode** | `opencode` / `opencode.cmd` | Node.js Global WinGet Package (`opencode-ai v1.18.34`) | `$null \| opencode.cmd run --auto "<prompt>"` (Modelo padrão: `opencode/mimo-v2.6-flash-free`) |

---

## 2. Ferramentas Disponíveis no Agente WhatsApp (`tool_executor`)

### 2.1 `run_codex_cli`
Executa comandos ou prompts diretamente no OpenAI Codex.
- **Parâmetros**:
  - `prompt`: Instrução ou prompt para o agente Codex (obrigatório para `exec`).
  - `subcommand`: Subcomando (`exec`, `review`, `doctor`, `agents`, `features`). Padrão: `exec`.
  - `extra_args`: Argumentos adicionais (ex: `--model gpt-5.4-mini`).
  - `timeout`: Tempo limite em segundos (padrão: 120s).

### 2.2 `run_antigravity_cli`
Executa comandos ou prompts no Google Antigravity (`agy`).
- **Parâmetros**:
  - `prompt`: Instrução ou prompt para o Antigravity (obrigatório para `print`).
  - `subcommand`: Subcomando (`print`, `agents`, `models`, `mcp`, `changelog`). Padrão: `print`.
  - `extra_args`: Argumentos adicionais.
  - `timeout`: Tempo limite em segundos (padrão: 120s).

### 2.3 `run_opencode_cli`
Executa comandos ou prompts no OpenCode.
- **Parâmetros**:
  - `prompt`: Instrução ou prompt para o OpenCode (obrigatório para `run`).
  - `subcommand`: Subcomando (`run`, `models`, `stats`, `session`, `export`). Padrão: `run`.
  - `extra_args`: Argumentos adicionais.
  - `timeout`: Tempo limite em segundos (padrão: 120s).

### 2.4 `get_desktop_clis_status`
Retorna status completo em formato consolidado:
- Versão instalada de cada CLI.
- Caminhos de binário e wrappers.
- Contagem de processos ativos no Windows.
- Prontidão para execução imediata.

---

## 3. Endpoints HTTP no Brain Server (`http://127.0.0.1:8765`)

1. **`GET /v1/desktop/clis`**: Retorna JSON estruturado com status e versões das 3 CLIs.
2. **`POST /v1/desktop/cli`**: Dispara execução direta em uma CLI específica:
   ```json
   {
     "agent": "codex",
     "prompt": "Revise o arquivo services/auth.js",
     "subcommand": "exec",
     "extra_args": ""
   }
   ```

---

## 4. Integração com o Sentinela Desktop Watcher
Toda tarefa executada com sucesso via ferramenta CLI registra automaticamente sua conclusão no sentinela `desktop_watcher.py`, garantindo notificação em tempo real ao CEO Executive Operator.
