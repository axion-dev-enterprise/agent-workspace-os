# SETUP_PROTOCOL.md — Protocolo Canônico de Setup Inicial

> **PROPÓSITO**: Configurar um workspace recém-clonado do zero, substituindo todos os placeholders genéricos pelas informações reais do projeto do usuário através de uma entrevista guiada por IA.

---

## 1. Quando Executar Este Protocolo
- O usuário acabou de clonar este repositório (`git clone`).
- Os arquivos `AGENTS.md`, `DIRECTIVES.md` e `workspace.config.template.json` ainda contêm placeholders no formato `{{NOME_DA_VARIAVEL}}`.
- O arquivo `workspace.config.json` ainda não existe.

---

## 2. Instruções Passo a Passo para o Agente de IA

### Passo 1: Detectar Estado Atual
1. Verifique se o arquivo `workspace.config.json` já existe.
   - Se já existir e estiver preenchido, alerte o usuário: *"Este workspace já foi configurado anteriormente. Se você deseja apenas sincronizar melhorias e novas skills do repositório upstream, utilize o **UPDATE_PROTOCOL.md**."*
2. Escaneie os placeholders pendentes em `workspace.config.template.json`.

### Passo 2: Entrevista Guiada (6 Perguntas Objetivas)
Envie uma mensagem clara solicitando ao usuário as informações essenciais:

1. **Nome da Organização / Projeto**: (ex: `Acme Corp`, `DevStudio`, `Meu App`)
2. **Slug do Projeto**: (ex: `acme`, `devstudio`, `meu-app`)
3. **Identidade Git Oficial**:
   - Nome para commits: (ex: `Acme Bot` ou o nome do usuário)
   - Email para commits: (ex: `dev@acme.com` ou o email do usuário)
4. **Caminho Raiz Oficial do Workspace**: Onde o projeto roda localmente? (ex: `C:/Projects/Acme` ou `/home/user/acme` ou `.` para a pasta atual)
5. **Domínio Principal**: (ex: `acme.com` ou `localhost` caso ainda não possua domínio)
6. **Destino Canônico de Deploy**: (ex: `Vercel`, `VPS / Docker`, `Cloudflare Pages`, `AWS`, `Local-only`)
7. *(Opcional)* **Infraestrutura VPS**: IP do servidor de produção ou `N/A` se não aplicável.

### Passo 3: Criação de Configuração & Substituição Atômica
Assim que o usuário responder:
1. Crie `workspace.config.json` copiando a estrutura de `workspace.config.template.json` com os valores preenchidos.
2. Adicione ao `workspace.config.json`:
   ```json
   "setup_completed_at": "<ISO-TIMESTAMP>",
   "setup_agent": "<NOME_DO_AGENTE>",
   "last_synced_commit": "<HASH_DO_COMMIT_ATUAL>"
   ```
3. Substitua atômica e precisamente todos os placeholders `{{...}}` em:
   - `AGENTS.md`
   - `DIRECTIVES.md`
   - `docs/WORKSPACE_ORGANIZATION_RULES.md`
   - `README.md` (seção de clone/quickstart)

### Passo 4: Inicialização da Estrutura de Diretórios & Memória
Crie as pastas canônicas caso ainda não existam:
```
├── apps/               # Aplicações e frontends
├── services/           # APIs, workers e backends
├── packages/           # Bibliotecas compartilhadas (monorepo)
├── docs/               # Documentação técnica e ADRs
├── memory/             # Registros e colaboração multi-agente
│   ├── daily_logs/     # Logs cronológicos diários
│   └── cowork/         # active_tasks.json, blackboard.json, handoffs/
└── secure/             # Credenciais e cofre de chaves (.gitignored)
```

Inicialize os arquivos base de cowork:
- `memory/cowork/active_tasks.json` com `{"tasks": []}`.
- `memory/cowork/blackboard.json` com registro de setup inicial.
- `memory/cowork/agent_registry.json` registrando o agente atual como `ACTIVE`.

### Passo 5: Registro no Daily Log
Crie ou anexe ao log diário em `memory/daily_logs/YYYY-MM-DD.md`:
```markdown
## [HH:mm:ss] [agent-setup] Setup Inicial do Workspace Concluído com Sucesso
- **Organização**: <ORGANIZATION_NAME> (<ORGANIZATION_SLUG>)
- **Identidade Git**: <GIT_USER_NAME> <<GIT_USER_EMAIL>>
- **Destino de Deploy**: <PRIMARY_DEPLOY_TARGET>
- **Agente Executor**: <NOME_DO_AGENTE>
```

### Passo 6: Confirmação ao Usuário
Emita um resumo conciso confirmando a conclusão do setup, listando as pastas criadas e informando que o workspace está 100% calibrado para receber os primeiros comandos de desenvolvimento.
