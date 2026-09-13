# COWORK_PROTOCOL.md — Protocolo Canônico de Coworking Multi-Agente

## 1. Visão Geral
Em ambientes de desenvolvimento modernos, múltiplos agentes de IA (ex: Claude para arquitetura e documentação, Antigravity para refatoração e auditoria profunda, Hermes para integrações e bots) operam simultaneamente no mesmo workspace.
Este protocolo estabelece uma governança assíncrona **baseada em arquivos JSON e Markdown** para garantir:
1. **Zero Colisão**: Prevenção de concorrência destrutiva onde dois agentes editam os mesmos arquivos ao mesmo tempo.
2. **Visibilidade Compartilhada**: Descobertas técnicas feitas por um agente ficam imediatamente acessíveis a todos os outros.
3. **Rastreabilidade de Turnos**: Passagens de bastão formais (*handoffs*) entre agentes.

---

## 2. Estrutura de Arquivos em `memory/cowork/`

```
memory/cowork/
├── active_tasks.json       # Fila de tarefas em andamento e locks de exclusividade
├── blackboard.json         # Quadro compartilhado de descobertas e conclusões
├── agent_registry.json     # Registro de presença, status e capacidades dos agentes
└── handoffs/               # Documentos de passagem de bastão
```

### 2.1 Locks Anti-Colisão (`active_tasks.json`)
Antes de modificar um módulo, o agente registra:
```json
{
  "task_id": "task_20260913_auth_refactor",
  "title": "Refatoração do Módulo de Autenticação",
  "status": "IN_PROGRESS",
  "owner_agent": "antigravity",
  "locked_resources": [
    "services/auth",
    "packages/shared-types"
  ],
  "acquired_at": "2026-09-13T10:00:00Z"
}
```
Se outro agente tentar registrar uma tarefa sobrepondo `services/auth`, a operação DEVE ser retida até que o lock seja liberado com status `COMPLETED`.

### 2.2 Quadro Compartilhado (`blackboard.json`)
Agentes publicam fatos técnicos validados:
```json
{
  "id": "bb_001",
  "agent": "claude",
  "timestamp": "2026-09-13T10:15:00Z",
  "category": "DISCOVERY",
  "title": "Migração de Schema do Banco Validada",
  "summary": "Tabela users_v2 criada com índices otimizados. Pronta para integração no frontend.",
  "tags": ["database", "schema", "ready"]
}
```

### 2.3 Handoffs Formais (`handoffs/`)
Documento gerado ao final de um turno ou ao transferir escopo:
```markdown
# HANDOFF: Transição de Implementação de Autenticação
- **Data/Hora**: 2026-09-13T10:30:00Z
- **De (Origem)**: claude
- **Para (Destino)**: antigravity
- **Tarefa Vinculada**: task_20260913_auth_refactor

## 1. Objetivo & Contexto
Implementar rota de refresh token e testes E2E.

## 2. O que foi feito
- Schemas definidos em `services/auth/schemas.py`.
- Migration 002 executada no banco.

## 3. Próximos Passos Imediatos
- Criar endpoint `/auth/refresh`.
- Escrever suite de testes com teardown de dados de teste (Zero Test Pollution).
```
