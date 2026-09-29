---
name: agents-md-master-architect
description: >-
  Master meta-skill for creating, scaffolding, auditing, and evolving operational skills, AGENTS.md files, and agent governance documentation based on the official AGENTS.md open standard (Linux Foundation / AAIF).
---

# AGENTS.md Master Architect & Skill Craftsman

Skill mestra (*Master Meta-Skill*) canônica para governança de agentes, arquitetura de contexto e fabricação de novas skills operacionais no ecossistema AXION. Implementa a especificação oficial aberta **[AGENTS.md](https://agents.md)** mantida pela **Agentic AI Foundation (Linux Foundation)** e adotada por mais de 60.000 repositórios no mundo (OpenAI Codex, Jules/Google, Gemini CLI, Cursor, Windsurf, Aider, Devin).

---

## 1. Princípios Fundamentais do Padrão AGENTS.md (AAIF / Linux Foundation)

### 1.1 O Princípio da Divisão Humano vs. Agente
- **`README.md` é para humanos**: quickstart, visão geral do produto, badges, screenshots e guia de contribuição.
- **`AGENTS.md` é o README para Agentes**: o local dedicado, determinístico e padronizado para fornecer aos agentes de código instruções de ambiente, comandos de teste, convenções arquiteturais, armadilhas operacionais e regras de governança.

### 1.2 A Lei de Ouro contra o Inchaço de Contexto (*Anti-Bloat Law*)
> **"AGENTS.md DEVE SER ENXUTO, ESTRUTURADO E INDEXADO."**

- **Não transforme o `AGENTS.md` em um monólito de texto**: agentes operam com maior acurácia quando o arquivo raiz contém regras concisas e direcionamentos para documentos especializados.
- **Delegação Modular**: regras extensas de domínio, checklists de segurança e guias arquiteturais devem residir em arquivos dedicados em `docs/rules/`, `docs/architecture/` ou em `SKILL.md` especializados, mantendo o `AGENTS.md` abaixo de 20KB.
- **Hierarquia em Monorepos**: quando subprojetos ou pacotes necessitarem de instruções sob medida, utilize arquivos `AGENTS.md` aninhados nas subpastas (`packages/*/AGENTS.md`). O agente sempre prioriza o `AGENTS.md` mais próximo do arquivo em edição. Instruções explícitas do usuário no chat sobrepõem tudo.

### 1.3 O Princípio da Generalidade e Reusabilidade (*Anti-Silo Mandate*)
> **"SKILLS DEVEM SER GENÉRICAS, PARAMETRIZÁVEIS E REAPROVEITÁVEIS EM MÚLTIPLAS APLICAÇÕES."**

- **Proibição de Skills Monopropósito ou Hiper-Acopladas**: Uma skill nunca deve ser construída como um script engessado para resolver apenas a tela ou o ticket do dia. Código com regras de negócio exclusivas de um único produto pertence ao código da aplicação (`apps/<app>/src/`), jamais à biblioteca global de skills (`.agents/skills/`).
- **Separação de Mecanismo vs. Política**: O núcleo da skill (scripts e metodologias) deve ser agnóstico à stack. Use parâmetros, perfis (`--profile generic|security|concurrency`) e contratos extensíveis (ex: `--rules <custom.json>`) para que a mesma skill possa auditar ou operar qualquer frontend, backend, microsserviço ou banco de dados da organização.
- **Consolidação vs. Micro-Fragmentação**: É terminantemente proibido fragmentar uma mesma tecnologia em dezenas de micro-skills de finalidade única (ex: separar um framework em 12 skills redundantes). Priorize skills coesas, profundas e modulares com subcomandos e documentação estruturada.

---

## 2. Padrão Canônico de Construção de Novas Skills

Toda nova skill criada no repositório deve residir sob `.agents/skills/<skill-name>/` e seguir a estrutura canônica:

```
.agents/skills/<skill-name>/
├── SKILL.md                          # Ponto de entrada com YAML frontmatter
├── scripts/                          # Utilitários executáveis (Python stdlib, zero deps)
│   └── <utilitario_principal>.py
├── references/                       # Documentação técnica profunda e contratos
│   └── <guia_ou_especificacao>.md
└── examples/                         # (Opcional) Casos de uso e payloads de teste
```

### 2.1 Especificação do `SKILL.md`
1. **YAML Frontmatter Mandatório**:
   ```yaml
   ---
   name: <skill-name-em-kebab-case>
   description: >-
     Gatilho claro explicando quando e para quê o agente deve carregar esta skill.
   ---
   ```
2. **Seções Recomendadas**:
   - **Visão Geral & Escopo**: O que a skill cobre e seus limites.
   - **Regras Operacionais Determinísticas**: O que fazer e o que NUNCA fazer.
   - **Workflows e Passos Sequenciais**: Como executar a tarefa passo a passo.
   - **Ferramentas e Scripts Canônicos**: Comandos de terminal prontos para execução.
   - **Portão de Verificação (Verification Gate)**: Como provar factualmente que a tarefa foi cumprida com sucesso.
   - **Anti-Padrões & Armadilhas**: Erros comuns na tecnologia e como evitá-los.

### 2.2 Requisitos dos Scripts em `scripts/`
- **Zero Dependências Externas**: Utilizar estritamente a biblioteca padrão do Python 3 (`urllib`, `json`, `subprocess`, `pathlib`, `argparse`, `hashlib`, etc.).
- **Compatibilidade Windows & Linux**: Suporte nativo ao Windows (PowerShell/CMD) com tratamento de encoding UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')`).
- **Autonomia & CLI**: Suporte a parâmetros via `argparse`, saída formatada legível para humanos e opção `--json` para integração de dados.

---

## 3. Fluxo de Vida de uma Skill: Criar, Registrar e Sincronizar

Quando uma nova skill for solicitada ou identificada:

1. **Scaffold Automatizado**:
   Execute o utilitário fornecido por esta skill:
   ```bash
   python .agents/skills/agents-md-master-architect/scripts/scaffold_skill.py "nome-da-skill" --domain "Categoria" --description "Descrição do escopo"
   ```
2. **Desenvolvimento do Conteúdo**:
   - Preencha o `SKILL.md` com as regras de ouro, padrões e anti-padrões.
   - Adicione scripts executáveis em `scripts/` para automações complexas.
   - Documente especificações extensas em `references/`.
3. **Validação Pré-Merge Mandatória**:
   Execute o validador para auditar frontmatter, ausência de stubs e sintaxe de scripts:
   ```bash
   python scripts/validate_skill.py --skill "nome-da-skill"
   ```

4. **Sincronização Canônica**:
   Dispare o sincronizador global para propagar a nova skill para toda a infraestrutura:
   ```bash
   python scripts/sync_skills_registry.py
   ```
   *O sincronizador atualiza atomicamente:*
   - `docs/SKILLS_REGISTRY.md` (Catálogo completo de skills)
   - `AGENTS.md` (Tabela de skills operacionais entre marcadores)
   - `workspace/inventory.json` (Inventário de recursos ativos)
   - `~/.gemini/antigravity/skills/` (Espelhamento global do sistema)

---

## 4. Utilitários Python da Skill Master (`scripts/`)

### 4.1 Gerador de Skills (`scaffold_skill.py`)
Gera o esqueleto completo da nova skill, cria os subdiretórios `scripts/` e `references/`, inicializa arquivos de exemplo e executa o sincronizador:
```bash
python .agents/skills/agents-md-master-architect/scripts/scaffold_skill.py "nome-da-skill" --domain "Backend & APIs" --description "Suporte a..."
```

### 4.2 Gerenciador e Validador de AGENTS.md (`manage_agents_md.py`)
Audita o arquivo `AGENTS.md` raiz ou aninhado contra a especificação da Linux Foundation:
- Verifica integridade de links markdown para arquivos locais (`docs/rules/*.md`);
- Checa o tamanho do arquivo para alertar sobre risco de inchaço (*bloat warning*);
- Valida a sequência de leitura canônica de regras;
- Permite adicionar novas regras modulares com link automático:
```bash
# Validar AGENTS.md
python .agents/skills/agents-md-master-architect/scripts/manage_agents_md.py --audit

# Adicionar nova regra concisa vinculada a documento em docs/rules/
python .agents/skills/agents-md-master-architect/scripts/manage_agents_md.py --add-rule "Rule Title" --rule-doc "docs/rules/MY_RULE.md" --summary "Resumo em 1 linha"
```

### 4.3 Auditor Geral de Skills (`audit_skills.py`)
Varre todas as skills em `.agents/skills/`, verificando conformidade com a especificação:
- Validação sintática do YAML frontmatter;
- Verificação de presença e sintaxe de scripts Python;
- Detecção de links internos quebrados em `references/`;
- Checagem de duplicações de nomes e gaps no `DOMAIN_MAP`:
```bash
python .agents/skills/agents-md-master-architect/scripts/audit_skills.py
```

---

## 5. Curadoria de Markdowns de Governança

Para manter a documentação do workspace sustentável e de alto desempenho para LLMs:

| Tipo de Documento | Diretório Canônico | Propósito & Regra de Ouro |
| :--- | :--- | :--- |
| **AGENTS.md** | Raiz (`C:\workspace\AGENTS.md`) | Índice executivo, comandos de build/test, mapa de regras e inventário de skills. Deve ser mantido enxuto. |
| **Sub-AGENTS.md** | Subpastas (`packages/*/AGENTS.md`) | Regras contextuais específicas do subprojeto (prevalência local). |
| **Execution Guardrails** | `docs/rules/*.md` | Regras técnicas profundas, restrições de ferramentas e padrões de segurança. |
| **ADRs (Decisões)** | `docs/adr/*.md` | Decisões arquiteturais imutáveis numeradas sequencialmente (`ADR-001.md`). |
| **Guias & Manuais** | `docs/*.md` | Instruções de infraestrutura, manuais operacionais e runbooks. |
| **Skill References** | `.agents/skills/*/references/*.md` | Contratos de interface, tabelas de fórmulas, shaders, especificações de APIs. |

---

## 6. Portão de Verificação Empírica

Antes de concluir qualquer tarefa que envolva a criação de skills ou modificação do `AGENTS.md`:
1. Execute `python .agents/skills/agents-md-master-architect/scripts/audit_skills.py` e certifique-se de que a nova skill passa com **0 erros**.
2. Execute `python scripts/sync_skills_registry.py` e comprove que o registro foi atualizado.
3. Execute `python .agents/skills/agents-md-master-architect/scripts/manage_agents_md.py --audit` para validar a integridade de todos os links e regras do `AGENTS.md`.
