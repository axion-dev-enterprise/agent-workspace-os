---
name: desktop-agents-orchestrator
description: >-
  Orquestração executiva e despacho inteligente de tarefas para os agentes desktop
  (OpenAI Codex, Google Antigravity e OpenCode), balanceamento por modelo neural,
  controle de quotas de uso, failover automático e modo Maestro no ecossistema AXION.
---

# Desktop Agents Orchestrator & Maestro Dispatcher Skill — AXION Enterprise

Guia canônico e operacional para o funcionamento do modo Maestro do ecossistema AXION. Estabelece a governança de delegação e despacho de tarefas para os 3 agentes desktop de engenharia no host Windows (`codex`, `antigravity`, `opencode`), considerando afinidade técnica, modelos neurais, limites de rate limit (429), quotas de uso e tolerância a falhas.

---

## 1. Princípios Operacionais do Modo Maestro

### 1.1 Papel Central do Co-piloto Conversacional
- O agente que interage com o CEO ou operadores nos canais (WhatsApp, Telegram, Brain Server) opera primordialmente como um **Maestro Orquestrador**.
- Em vez de tentar codificar sozinho ou executar comandos soltos e improvisados no terminal, o agente deve **delegar e solicitar** a execução para os agentes desktop através da ferramenta `dispatch_desktop_task`.
- O agente orquestrador mantém visibilidade, acompanha o ciclo de vida da tarefa, avalia o resultado, sintetiza os entregáveis e reporta ao usuário com transparência total de passos.

### 1.2 Matriz de Especialização e Afinidade Técnica

| Agente Desktop | CLI Command | Modelo Neural & Tier | Especialidade Principal | Critérios de Roteamento |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI Codex** | `codex exec` | OpenAI o1 / GPT-4o (Premium) | Engenharia de código e testes | Refatorações complexas, correção de bugs, TDD (`pytest`, `vitest`), code review (`codex review`), alterações pontuais em arquivos |
| **Google Antigravity** | `agy --print` | Gemini 2.0 / 1.5 Pro (Enterprise) | Arquitetura, RAG e Governança | Planejamento de workspace, governança de regras (`AGENTS.md`), criação/auditoria de skills, fluxos multi-agente, infraestrutura, MCP |
| **OpenCode** | `opencode run` | mimo-v2.6-flash-free (Free Tier) | Execução ágil e custo zero | Scripts rápidos, inspeções pontuais, formatações, extração rápida de dados, ou fallback quando outros agentes atingirem limite |

---

## 2. Governança de Quotas, Rate Limits (429) e Failover Automático

### 2.1 Detecção de Restrições e Cooldowns
O módulo `desktop_orchestrator.py` inspeciona continuamente as saídas e erros das CLIs:
- **Rate Limit (429 / TPM / RPM)**: Ativa cooldown automático de 15 minutos (900s) para o respectivo agente.
- **Quota Esgotada (`insufficient_quota` / `quota exceeded`)**: Ativa cooldown automático de 2 horas (7.200s).
- **Falhas Consecutivas**: Três falhas consecutivas marcam o agente como `degraded`, reduzindo seu score de prioridade.

### 2.2 Cadeia de Fallback Sem Aborto Prematuro
É terminantemente proibido devolver erro ao usuário ou abortar uma demanda por restrição de um único agente. A esteira deve:
1. Identificar a falha ou bloqueio do agente primário selecionado.
2. Registrar o status no ledger `memory/desktop_agents/quota_status.json`.
3. Disparar failover imediato para o próximo agente elegível da cadeia (ex: `Codex` ➔ `Antigravity` ➔ `OpenCode`).
4. Retornar o resultado com o sinalizador `failover_occurred: True` detalhando a trilha de execução.

---

## 3. Ferramentas Disponíveis no Ecossistema

- `dispatch_desktop_task(task_description=..., preferred_agent='auto', timeout=180)`: Delega a demanda com seleção inteligente ou agente preferencial.
- `get_desktop_orchestrator_status()`: Painel em tempo real de quotas, modelos, processos ativos e saúde operacional de cada CLI.
- `get_desktop_clis_status()`: Inventário de binários, versões e caminhos executáveis no host Windows.
- `run_codex_cli`, `run_antigravity_cli`, `run_opencode_cli`: Execução direta de subcomandos pontuais (`review`, `doctor`, `models`, `stats`).

---

## 4. Endpoints HTTP no Brain Server

O Brain Server expõe os serviços de orquestração via API REST:
- `POST /v1/desktop/dispatch`: Recebe JSON `{"task_description": "...", "preferred_agent": "auto", "timeout": 180}`.
- `GET /v1/desktop/quotas` / `GET /v1/desktop/orchestrator`: Retorna o resumo das quotas e agentes.
- `GET /v1/desktop/clis`: Retorna as versões e status de inventário das CLIs instaladas.

---

## 5. Auditoria e Validação Canônica

A skill disponibiliza o utilitário `scripts/audit_desktop_orchestrator.py` para testar o algoritmo de afinidade semântica, o ledger de quotas e a resiliência do failover em tempo de execução.
