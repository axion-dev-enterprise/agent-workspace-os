---
name: desktop-agents-watcher
description: >-
  Supervisão e observabilidade em tempo real de tarefas em andamento e concluídas dos agentes desktop
  (Antigravity, Codex, OpenCode), emitindo alertas proativos e estruturados ao CEO / Operador Executivo
  via WhatsApp e Telegram com ledger anti-fadiga e deduplicação.
---

# Desktop Agents Watcher Skill — Autonomous Agent Workspace OS

Guia operacional canônico para a supervisão contínua, auditoria e emissão de alertas de conclusão de tarefas executadas por agentes de IA no ambiente desktop (**Google Antigravity**, **OpenAI Codex** e **OpenCode**) para a liderança técnica e executiva.

---

## 1. Escopo & Topologia dos Agentes Desktop

No ecossistema de engenharia do Workspace OS, três classes de agentes de IA desktop atuam de forma concorrente e autônoma na estação de trabalho do operador:

| Agente Desktop | Local de Execução | Fontes de Observabilidade & Estado | Identificadores de Tarefa |
| :--- | :--- | :--- | :--- |
| **Google Antigravity** | Host Windows / IDE Antigravity | `~/.gemini/antigravity/brain/<conv_id>/.system_generated/` (transcripts `transcript.jsonl`, tasks `task-*.log`) | `antigravity_<conv_id>_<task_id>` |
| **OpenAI Codex** | CLI / VS Code Extension / Workspaces | `memory/cowork/active_tasks.json`, `workspace/memory/active_tasks.json`, processos `codex.exe` | `task_<timestamp>_<id>`, `source: codex` |
| **OpenCode** | CLI / Interpreter Host | `memory/cowork/active_tasks.json`, sessões locais em `temp/`, processos `opencode` | `task_<timestamp>_<id>`, `source: opencode` |

---

## 2. Diretrizes Mandatórias de Observabilidade para a Liderança Executiva

1. **Visibilidade Proativa Imediata**: O operador ou CEO não precisa consultar terminais ou logs manualmente para saber se um agente desktop concluiu sua entrega. O agente sentinel emite a notificação no momento exato do término.
2. **Canais Oficiais de Entrega**:
   - **WhatsApp Executivo**: Configurado via `WHATSAPP_ADMIN_NUMBER` (ou `WHATSAPP_ADMIN_LID`), roteado pela porta `4114` via `/send-internal` (bypass seguro anti-ban para comunicação corporativa interna).
   - **Telegram Executivo**: Configurado via `TELEGRAM_ADMIN_CHAT_ID`, transmitido via `broadcast_alert` ou API nativa do bot (`sendMessage`).
3. **Ledger Anti-Fadiga & Deduplicação Estrita**:
   - Todo alerta emitido deve registrar a assinatura da tarefa em `workspace/memory/desktop_watcher_state.json`.
   - É terminantemente PROIBIDO disparar alertas duplicados ou spam para a mesma tarefa já notificada.

---

## 3. Padrão Canônico de Formatação de Alertas

Todo alerta de conclusão de tarefa deve seguir estritamente o layout executivo de alta densidade informativa:

### 3.1 Formato WhatsApp (Markdown)
```markdown
🖥️ *[AXION Desktop Agents Watcher] Tarefa Finalizada!*
━━━━━━━━━━━━━━━━━━━━━━
• *Agente:* Antigravity (ou Codex / OpenCode)
• *Tarefa:* Refatoração do Motor RAG FTS5 (`task_179045`)
• *Status:* ✅ *Concluída com Sucesso*
• *Horário:* `13:42:10`
• *Duração:* `45.2s`
• *Resultado:* 33 testes unitários validados com 100% de sucesso. Documentação e índices FTS5 sincronizados.
━━━━━━━━━━━━━━━━━━━━━━
_Notificação proativa executiva enviada ao CEO Executive Operator._
```

### 3.2 Formato Telegram (HTML)
```html
🖥️ <b>[AXION Desktop Agents Watcher] Tarefa Finalizada!</b>
━━━━━━━━━━━━━━━━━━━━━━
• <b>Agente:</b> Antigravity
• <b>Tarefa:</b> Refatoração do Motor RAG FTS5 (<code>task_179045</code>)
• <b>Status:</b> ✅ <b>Concluída com Sucesso</b>
• <b>Horário:</b> <code>13:42:10</code>
• <b>Resultado:</b> <code>33 testes unitários validados com 100% de sucesso.</code>
━━━━━━━━━━━━━━━━━━━━━━
<i>Notificação proativa executiva enviada ao CEO Executive Operator.</i>
```

---

## 4. Arquitetura de Runtime & Integração no Sistema

O motor de observabilidade está implementado no módulo central:
- **`scripts/bot_engine/desktop_watcher.py`**
- **Tentáculo #8 no `scripts/bot_engine/tentacles.py`**: A thread mestra executa `sweep_desktop_agents()` em ciclos contínuos de 20 a 25 segundos.
- **Ferramenta de Diagnóstico no `tool_executor.py`**:
  - `check_desktop_agent_tasks(notify_ceo=True)`: Executa uma varredura imediata sob demanda e reporta status dos agentes desktop.

### 4.1 Registro Explícito de Conclusão por Outros Agentes
Agentes em execução podem invocar programaticamente o sentinel para registrar conclusão instantânea:
```python
from bot_engine import desktop_watcher

desktop_watcher.record_desktop_task_completion(
    agent="codex",
    task_id="task_deploy_landing_spapharma",
    title="Build & Deploy da Landing Page SpaPharma",
    status="completed",
    result="Build Next.js concluído e deploy na Vercel ativo em produção."
)
```

---

## 5. Resolução de Incidentes & Diagnóstico Operacional

1. **Verificação de Saúde do Watcher**:
   ```powershell
   python -c "from bot_engine import desktop_watcher; print(desktop_watcher.get_desktop_watcher_status())"
   ```
2. **Forçar Varredura Manual e Notificação**:
   ```powershell
   python scripts/bot_engine/desktop_watcher.py
   ```
3. **Limpeza ou Reset do Ledger Anti-Fadiga**:
   - Arquivo: `C:\workspace\workspace\memory\desktop_watcher_state.json`.
   - Se uma tarefa precisar ser re-notificada para testes, remova a chave correspondente de `notified_task_ids`.
