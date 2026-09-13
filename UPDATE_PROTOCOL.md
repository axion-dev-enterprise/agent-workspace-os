# UPDATE_PROTOCOL.md — Protocolo Canônico de Update Incremental & Sincronização

> **PROPÓSITO**: Buscar commits novos e atualizações do repositório upstream (novas skills, melhorias de diretrizes, patches de segurança), **SEM sobrescrever as customizações e dados locais do usuário**, atualizando o contexto e a memória do workspace.

---

## 1. Quando Executar Este Protocolo
- O workspace já passou pelo setup inicial (`workspace.config.json` existe).
- O usuário pede para *"atualizar o repositório"*, *"sincronizar melhorias"*, *"puxar commits novos"* ou executar o protocolo de update.
- Existem atualizações upstream em skills (`.skills/`), protocolos (`docs/`) ou templates.

---

## 2. Princípios de Segurança do Update
1. **Zero Sobrescrita de Identidade**: NUNCA reverter ou sobrescrever o `workspace.config.json` do usuário nem reintroduzir placeholders `{{...}}` em um workspace já customizado.
2. **Preservação de Código Ativo**: Modificações feitas pelo usuário em `apps/`, `services/` ou `packages/` são sagradas e jamais devem ser descartadas.
3. **Atualização Contextual & Memória**: Toda novidade incorporada (novas skills, correções de regras) deve ser catalogada no Daily Log e no Blackboard compartilhado para que todos os agentes passem a utilizá-la imediatamente.

---

## 3. Instruções Passo a Passo para o Agente de IA

### Passo 1: Sondagem Prévia e Proteção de Estado
1. Verifique se o diretório de trabalho está limpo (`git status`).
   - Se houver arquivos modificados não commitados, faça um stash preventivo ou peça autorização para commitar:
     ```bash
     git stash push -m "WIP: pre-update backup"
     ```
2. Carregue as configurações locais de `workspace.config.json` para memória (guardando o nome da organização, identidade git e caminhos locais).

### Passo 2: Buscar Novos Commits do Remoto (Fetch)
Execute a busca sem merge imediato:
```bash
git fetch origin main
# ou 'git fetch upstream main' se for um fork
```

### Passo 3: Auditar o que Mudou (Diff Audit)
Compare o commit local atual (`HEAD`) com o que foi buscado (`FETCH_HEAD`):
```bash
git log HEAD..FETCH_HEAD --oneline
git diff --stat HEAD..FETCH_HEAD
```

Identifique quais categorias de arquivos foram atualizadas:
- **Novas Skills**: arquivos adicionados em `.skills/`
- **Melhorias de Regras**: alterações em `AGENTS.md` ou `DIRECTIVES.md`
- **Documentações & Protocolos**: alterações em `docs/` ou templates

### Passo 4: Sincronização e Merge Inteligente
1. Execute o merge das atualizações upstream:
   ```bash
   git merge FETCH_HEAD --no-edit
   ```
2. Se o merge atualizar `AGENTS.md` ou `DIRECTIVES.md` e reintroduzir algum placeholder novo (ex: uma nova variável criada pelo upstream), preencha o novo placeholder utilizando as variáveis já existentes em `workspace.config.json` ou pergunte apenas sobre o novo parâmetro ao usuário.
3. Se foi feito stash no Passo 1, restaure-o:
   ```bash
   git stash pop
   ```

### Passo 5: Atualização da Memória e Contexto do Workspace

#### A. Atualizar `workspace.config.json`
Atualize os metadados de sincronização:
```json
"last_synced_commit": "<NOVO_HASH_DO_COMMIT>",
"last_synced_at": "<ISO-TIMESTAMP>"
```

#### B. Publicar Novidades no Blackboard Compartilhado (`memory/cowork/blackboard.json`)
Registre a entrada para que outros agentes e subagentes conheçam as novas capacidades:
```json
{
  "id": "bb_sync_<TIMESTAMP>",
  "agent": "<NOME_DO_AGENTE>",
  "timestamp": "<ISO-TIMESTAMP>",
  "category": "SYSTEM_UPDATE",
  "title": "Workspace Sincronizado com Nova Versão Upstream",
  "summary": "Commits novos aplicados. Novas skills e diretrizes disponíveis: <LISTA_DE_NOVIDADES>.",
  "tags": ["update", "sync", "upstream"]
}
```

#### C. Registrar na Timeline Diária (`memory/daily_logs/YYYY-MM-DD.md`)
Anexe o log factual da atualização:
```markdown
## [HH:mm:ss] [workspace-update] Sincronização Incremental Concluída
- **Commits Aplicados**: <QUANTIDADE_DE_COMMITS>
- **Novas Skills / Módulos**: <LISTA_DE_ARQUIVOS_ATUALIZADOS>
- **Preservação de Dados**: 100% das variáveis locais mantidas intactas.
- **Status do Workspace**: Operacional e atualizado.
```

### Passo 6: Relatório Conciso ao Usuário
Apresente um resumo executivo:
- Total de novos commits aplicados.
- Novas skills prontas para uso.
- Confirmação de que as configurações e códigos do usuário foram preservados.
