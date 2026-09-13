# SETUP_AGENT_DIRECTIVE.md — Diretriz de Entrada Rápida para Agentes de IA

> **AVISO AO AGENTE DE IA (Claude, Antigravity, Cursor, Codex, Hermes, Copilot, Windsurf):**
> Este repositório opera através de dois protocolos canônicos definidos em **[WORKFLOW.md](WORKFLOW.md)**:
> 1. **[SETUP_PROTOCOL.md](SETUP_PROTOCOL.md)**: Para inicialização e personalização de um workspace recém-clonado.
> 2. **[UPDATE_PROTOCOL.md](UPDATE_PROTOCOL.md)**: Para sincronização incremental de novos commits preservando a memória e contexto local.

---

## Como Decidir Qual Protocolo Executar

1. **Se o usuário disser "setup", "iniciar", "configurar" ou for um workspace novo (com placeholders `{{...}}` pendentes):**
   ➔ Execute imediatamente o **[SETUP_PROTOCOL.md](SETUP_PROTOCOL.md)**.
   ➔ Faça as 6 perguntas de onboarding ao usuário e configure o ambiente.

2. **Se o usuário disser "update", "atualizar", "sincronizar", "puxar commits" ou `workspace.config.json` já existir:**
   ➔ Execute imediatamente o **[UPDATE_PROTOCOL.md](UPDATE_PROTOCOL.md)**.
   ➔ Busque os novos commits via `git fetch`, preserve as customizações locais e sincronize o contexto no Daily Log e no Blackboard.
