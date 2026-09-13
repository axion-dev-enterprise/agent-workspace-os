# SETUP_AGENT_DIRECTIVE.md — Diretriz de Onboarding Automático para Agentes de IA

> **INSTRUÇÃO PRIMÁRIA A QUALQUER AGENTE DE IA (Claude, Antigravity, Cursor, Copilot, ChatGPT, Hermes, Windsurf):**
> Você foi ativado dentro de um workspace baseado no **Agent Workspace OS**.
> Se este arquivo ou o repositório contiver placeholders no formato `{{NOME_DA_VARIAVEL}}`, sua **PRIMEIRA TAREFA MANDATÓRIA** antes de qualquer código é conduzir o onboarding interativo com o usuário para customizar o ambiente.

---

## 1. Como Conduzir o Onboarding Interativo

Quando o usuário clonar este repositório e enviar um prompt inicial (ex: *"configure o workspace"*, *"inicie o projeto"*, ou qualquer solicitação genérica), siga rigorosamente estes 5 passos:

### Passo 1: Sondagem Inicial de Placeholders
Escaneie os arquivos principais:
- `workspace.config.template.json`
- `AGENTS.md`
- `DIRECTIVES.md`

Se houver placeholders não resolvidos (ex: `{{ORGANIZATION_NAME}}`), **NÃO tente adivinhar** valores proprietários.

### Passo 2: Faça as Perguntas Essenciais ao Usuário
Apresente uma mensagem amigável e direta com as perguntas agrupadas para o usuário responder (ele pode responder em lote ou item a item):

1. **Nome da Organização / Projeto**: Como se chama seu time, empresa ou projeto? (ex: `Acme Corp`, `MyStartup`)
2. **Slug do Projeto**: Um identificador curto em minúsculas (ex: `acme`, `mystartup`).
3. **Identidade Git**:
   - Qual **Nome** deve constar nos commits? (ex: `Acme Developer`)
   - Qual **Email** deve constar nos commits? (ex: `dev@acme.com`)
4. **Caminho Raiz Oficial do Workspace**: Onde o projeto reside localmente? (ex: `C:\Projects\Acme` ou `/home/user/acme` ou `.` para a pasta atual).
5. **Domínio Principal**: Possui domínio web? (ex: `acme.com` ou `localhost`).
6. **Destino Canônico de Deploy**: Onde a aplicação principal será hospedada? (ex: `Vercel`, `VPS / Docker`, `AWS`, `Cloudflare Pages`, `Local-only`).
7. **Infraestrutura VPS (Opcional)**: Se for usar VPS, informe o IP/Host ou responda `N/A`.

### Passo 3: Substituição Atômica dos Placeholders
Após receber as respostas do usuário:
1. Copie `workspace.config.template.json` para `workspace.config.json` preenchendo os valores reais.
2. Substitua todos os placeholders correspondentes nos arquivos:
   - `AGENTS.md`
   - `DIRECTIVES.md`
   - `DOCS/WORKSPACE_ORGANIZATION_RULES.md`
3. Configure o Git local se o usuário autorizar:
   ```bash
   git config user.name "<GIT_USER_NAME>"
   git config user.email "<GIT_USER_EMAIL>"
   ```

### Passo 4: Criação das Pastas Canônicas
Crie a estrutura de diretórios canônica:
```
├── apps/           # Aplicações e frontends
├── services/       # Microsserviços e backends
├── packages/       # Bibliotecas compartilhadas (monorepo)
├── docs/           # Documentação técnica e ADRs
├── memory/         # Daily logs e coordenação cowork
│   ├── daily_logs/
│   └── cowork/
└── secure/         # Vault de credenciais (.gitignored)
```

### Passo 5: Confirmação e Status Inicial
Emita um relatório conciso confirmando:
- Organização configurada: `<ORGANIZATION_NAME>`
- Identidade Git ativa: `<GIT_USER_NAME> <GIT_USER_EMAIL>`
- Regras canônicas ativadas e salvas em `AGENTS.md`
- Fila de Coworking pronta em `memory/cowork/`
- Pronto para receber o primeiro comando de desenvolvimento!
