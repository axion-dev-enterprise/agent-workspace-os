# WORKFLOW.md — Guia de Operação: Setup vs Update

Este repositório possui dois modos formais de operação. Escolha o protocolo correspondente à sua necessidade e informe ao seu agente de IA:

---

## 🚀 Opção 1: Setup Inicial (`SETUP_PROTOCOL.md`)
**Quando usar:** Você acabou de clonar este repositório pela primeira vez e precisa calibrar as regras, identidade e caminhos para o seu projeto.

**Como acionar no prompt:**
> *"Por favor, execute o SETUP_PROTOCOL.md e configure o meu workspace."*

**O que o agente fará:**
1. Fará 6 perguntas objetivas sobre seu projeto.
2. Preencherá todos os placeholders automaticamente.
3. Criará o `workspace.config.json` com sua identidade Git.
4. Inicializará a estrutura de pastas e a memória diária.

---

## 🔄 Opção 2: Update Incremental (`UPDATE_PROTOCOL.md`)
**Quando usar:** Seu repositório já está configurado e você quer buscar commits novos do upstream (novas skills, correções e melhorias) sem perder suas variáveis e arquivos locais.

**Como acionar no prompt:**
> *"Por favor, execute o UPDATE_PROTOCOL.md e atualize meu workspace com os novos commits."*

**O que o agente fará:**
1. Buscará novos commits via `git fetch` sem quebrar seu código.
2. Preservará 100% do seu `workspace.config.json` e arquivos existentes.
3. Mesclará novas skills e documentações.
4. Atualizará o contexto e a memória (`blackboard.json` e `daily_logs/`) com o resumo das novidades.
