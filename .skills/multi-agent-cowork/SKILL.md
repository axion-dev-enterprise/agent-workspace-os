---
name: multi-agent-cowork
description: Protocolo de coordenação, locks de arquivos, quadro compartilhado (blackboard) e handoffs formais entre múltiplos agentes de IA.
---

# Multi-Agent Cowork Skill

## Quando Usar
Sempre que dois ou mais agentes (Claude, Antigravity, Hermes, Codex) operarem no mesmo repositório, ou quando um agente delegar trabalho para outro turno.

## Fluxo Operacional
1. **Adquirir Lock de Tarefa**:
   Antes de editar código em `apps/` ou `services/`, registrar o lock em `memory/cowork/active_tasks.json`.
   Se o recurso já estiver em lock por outro agente ativo, interromper ou aguardar a liberação.
2. **Publicar no Blackboard**:
   Toda conclusão de módulo, descoberta de bug ou alteração de schema de banco deve ser registrada em `memory/cowork/blackboard.json`.
3. **Emitir Handoff Formal**:
   Ao passar o bastão, gerar um arquivo em `memory/cowork/handoffs/YYYY-MM-DD_HHMMSS_<from>_to_<to>.md` detalhando:
   - Objetivo da tarefa.
   - O que foi feito e testado.
   - Próximos passos imediatos.
   - Recursos e arquivos vinculados.
