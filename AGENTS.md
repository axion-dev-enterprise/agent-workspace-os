# AGENTS.md — Regras Canônicas de Governança para Agentes de IA

## 1. Escopo e Propósito
- Este documento rege **todos os agentes de IA** atuando no ecossistema de engenharia da **{{ORGANIZATION_NAME}}** (`{{ORGANIZATION_SLUG}}`).
- Leitura obrigatória antes de qualquer ação ou alteração em código.
- Aplica-se a Antigravity, Claude, Cursor, Codex, Hermes, Copilot, Windsurf e subagentes.

---

## 2. Topologia Canônica do Workspace
- **Raiz Oficial**: `{{WORKSPACE_ROOT}}`
- **Aplicações e Frontends**: `{{WORKSPACE_ROOT}}/apps/`
- **Serviços e Backends**: `{{WORKSPACE_ROOT}}/services/`
- **Pacotes Compartilhados (Monorepo)**: `{{WORKSPACE_ROOT}}/packages/`
- **Documentação & ADRs**: `{{WORKSPACE_ROOT}}/docs/`
- **Memória & Coworking**: `{{WORKSPACE_ROOT}}/memory/`
- **Armazenamento de Builds e Cache Pesado**: `{{HEAVY_STORAGE_PATH}}`
- **Cofre Seguro de Credenciais**: `{{VAULT_PATH}}`

> **Regra Fundamental de Paths**: Nunca referenciar ou criar arquivos fora da raiz canônica acima. Sempre utilizar caminhos canônicos estruturados.

---

## 3. Identidade Git Obrigatória
Todo e qualquer commit, deploy ou operação Git DEVE utilizar obrigatoriamente a identidade oficial configurada:
- `user.name="{{GIT_USER_NAME}}"`
- `user.email="{{GIT_USER_EMAIL}}"`
- Padrão semântico de commits: `[<agente>][<módulo>] <tipo>: <descrição clara e factual>` (ex: `[claude][auth] feat: implement JWT refresh token rotation`).

---

## 4. Regras Gerais de Engenharia & Governança

### Regra #1: Zero Root Clutter (Organização Estrita da Raiz)
- A raiz do repositório deve conter apenas os arquivos fundamentais permitidos: `AGENTS.md`, `DIRECTIVES.md`, `README.md`, `SETUP_AGENT_DIRECTIVE.md`, `workspace.config.json`, `.gitignore` e lockfiles de pacote.
- Proibido criar scripts soltos, rascunhos ou arquivos de teste na raiz. Usar pastas dedicadas em `apps/`, `services/` ou `temp/`.

### Regra #2: Verificação Empírica, Objetividade e Proibição de Falsos Afirmativos
- **Proibição Estrita de Falsos Afirmativos**: É terminantemente PROIBIDO declarar que uma tarefa, teste ou deploy foi concluído com sucesso sem verificação empírica e factual do resultado.
- **Validação de Endpoints e URLs**: Sempre inspecionar a resposta HTTP real, o corpo retornado (`curl -s -L`) e verificar se os elementos esperados foram de fato renderizados.

### Regra #3: Purga Obrigatória de Dados de Teste (Zero Test Pollution)
- Sempre após executar testes funcionais, de integração ou simulações, o agente DEVE excluir imediatamente todos os registros de teste criados.
- Bancos de dados, tabelas e dashboards devem retornar ao estado limpo (teardown obrigatório em blocos `finally`).

### Regra #4: Pre-Commit Guard & Zero Credential Logging
- Proibido commitar arquivos `.env`, chaves privadas SSH, tokens de API ou credenciais de banco.
- Toda credencial deve ser injetada via variáveis de ambiente ou lida a partir do cofre `{{VAULT_PATH}}`.
- Proibido registrar senhas, tokens de autorização ou cookies brutos em logs diários ou outputs de console.

### Regra #5: Sonda Prévia de Validação (Whoami Probe First)
- Antes de disparar deploys ou mutações críticas em serviços externos (GitHub, Cloudflare, Vercel, Stripe, AWS, VPS), o agente DEVE executar uma sonda leve (`whoami` ou verify token) para validar a autenticidade e o tenant antes de prosseguir.

### Regra #6: Proibição Total de Emojis em UI (SVG Icons Only)
- É terminantemente PROIBIDO utilizar emojis de sistema (ex: 🚀, ⚙️, 🧠, 📊, ❌, ✅) como ícones visuais em botões, topbars, sidebars e tabelas em aplicações web.
- Utilizar exclusivamente ícones vetoriais SVG profissionais (Lucide Icons, Heroicons, Material Symbols) inline ou via componentes leves.

### Regra #7: UI/UX Anti-Clichê de IA (Padrão Big Tech)
- PROIBIDO utilizar estética clichê de IA: gradientes neon radioativos, animações circulares psicodélicas, robôs flutuantes e badges excessivos com estrelas ("✨ Powered by AI").
- Foco em design minimalista, tipografia editorial de alta precisão (Inter, Roboto, SF Pro, JetBrains Mono para números), superfícies escuras refinadas (Obsidian/Zinc) ou claras neutras, e transições fluidas de 150-200ms (`cubic-bezier(0.16, 1, 0.3, 1)`).
- Zero Cumulative Layout Shift (CLS = 0) com uso de Skeleton Shimmers idênticos ao layout final.

### Regra #8: Modais e Notificações Customizadas (Zero Alert / Dialog)
- Proibido invocar caixas de diálogo nativas do navegador (`alert()`, `confirm()`, `prompt()`).
- Utilizar modais customizados HTML/CSS com `backdrop-filter: blur(14px)` e notificações flutuantes (Toasts) contextuais.

---

### Regra #9: Pre-flight Checks Mandatórios, Aprendizado de Erros e Proibição de Retries Cegos
- **Proibição Estrita de Retries Cegos (Blind Retry Loop)**: Quando um comando de deploy ou build falhar, é proibido reexecutá-lo repetidamente ou apagar pastas de configuração (como `.vercel` ou `.next`) sem antes diagnosticar a causa raiz da mensagem de erro.
- **Pre-flight Vercel**: Antes de rodar `vercel deploy`, certificar que o projeto está linkado (`.vercel/project.json` existente via `vercel link --yes`). Nunca deletar `.vercel` para tentar resolver erros de build. Nunca imprimir tokens de ambiente com `echo $env:TOKEN`.
- **Pre-flight Git & Docker**: Validar identidade Git antes de commits e validar portas livres e `.env` antes de subir containers Docker.
- **Aprendizado Contínuo**: Registrar lições aprendidas em `memory/cowork/blackboard.json` e documentar na skill `execution-preflight-learning` para que futuros agentes não repitam a mesma falha.

---

## 5. Protocolo de Coworking Multi-Agente & Timeline Diária

### 5.1 Registro Obrigatório em Timeline Diária
Todo trabalho realizado por qualquer agente deve ser registrado sequencialmente no arquivo cronológico diário em `{{WORKSPACE_ROOT}}/memory/daily_logs/YYYY-MM-DD.md` contendo:
1. `[HH:mm:ss] Timestamp` local.
2. `[PROMPT]` Solicitação exata do usuário.
3. `[DIAGNÓSTICO]` Causa raiz e descoberta técnica.
4. `[SOLUÇÃO]` Arquivos alterados, commits e testes executados.
5. `[RESULTADO]` Evidências factuais de sucesso.

### 5.2 Coordenação via Arquivos em `memory/cowork/`
- **Locks Anti-Colisão**: Registrar intenção em `memory/cowork/active_tasks.json` antes de iniciar alterações compartilhadas.
- **Blackboard Compartilhado**: Postar descobertas e status em `memory/cowork/blackboard.json`.
- **Handoffs Formais**: Documentar transferências em `memory/cowork/handoffs/YYYY-MM-DD_HHMMSS_<origem>_to_<destino>.md`.
