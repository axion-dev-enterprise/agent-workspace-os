# WORKFLOW.md — Guia de Operação: Setup vs Update

Este repositório possui dois modos formais de operação.

---

## 🚀 Opção 1: Setup Inicial (`SETUP_PROTOCOL.md`)
**Quando usar:** Você acabou de clonar este repositório pela primeira vez.

**Como iniciar:**
- **Visual (Recomendado)**: Dê duplo-clique em `start.bat` (Windows) ou `./start.sh` (Linux/Mac).
- **Via Agente**: Diga ao seu agente: *"Inicie o setup do meu workspace."*
  *(O agente iniciará o servidor em `http://127.0.0.1:8765` para você preencher os dados visualmente, sem questionários no chat).*

**O que acontece:**
1. O painel visual abre no seu navegador.
2. Você confere os status das ferramentas e autenticações.
3. Preenche os dados da sua organização na aba Workspace e clica em Salvar.
4. Todos os arquivos de regras, pastas e memórias são inicializados automaticamente.

---

## 🔄 Opção 2: Update Incremental (`UPDATE_PROTOCOL.md`)
**Quando usar:** Seu repositório já está configurado e você quer buscar commits novos do upstream (novas skills, correções e melhorias) sem perder suas variáveis e arquivos locais.

**Como iniciar:**
- Diga ao seu agente: *"Execute o UPDATE_PROTOCOL.md e atualize meu workspace com os novos commits."*

**O que o agente fará:**
1. Buscará novos commits via `git fetch` sem quebrar seu código.
2. Preservará 100% do seu `workspace.config.json` e arquivos existentes.
3. Mesclará novas skills e documentações.
4. Atualizará o contexto e a memória (`blackboard.json` e `daily_logs/`).
