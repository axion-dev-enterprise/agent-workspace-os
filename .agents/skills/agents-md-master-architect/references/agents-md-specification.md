# Especificação Oficial Aberta AGENTS.md (AAIF / Linux Foundation)

> **Documento Canônico de Referência**  
> **Fonte Oficial**: [https://agents.md](https://agents.md) e [https://github.com/agentsmd/agents.md](https://github.com/agentsmd/agents.md)  
> **Governança**: Agentic AI Foundation (Linux Foundation)  
> **Adoção**: 60.000+ repositórios open-source, OpenAI Codex, Jules (Google), Gemini CLI, Cursor, Windsurf, Aider, Devin (Cognition), Amp, Factory, UiPath.  

---

## 1. O que é o AGENTS.md?

O `AGENTS.md` é um formato simples, aberto e padronizado para guiar agentes de codificação (*coding agents*).
Pense no `AGENTS.md` como um **README para agentes**: um local dedicado, previsível e determinístico para fornecer o contexto e as instruções necessárias para que agentes autônomos de IA possam trabalhar com máxima eficácia no seu projeto.

---

## 2. Por que um arquivo separado do README.md?

1. **Separação de Audiências**:
   - `README.md` é escrito para seres humanos: onboarding rápido, proposta de valor, screenshots, arquitetura visual de alto nível e como contribuir.
   - `AGENTS.md` contém o contexto detalhado e programático que agentes precisam: comandos exatos de build e testes, regras estritas de formatação de código, comandos de CI/CD, diretrizes de segurança e peculiaridades do ecossistema que poluiriam o README humano.
2. **Previsibilidade de Carregamento**:
   - Agentes de IA modernos (OpenAI, Gemini, Anthropic, Cursor) procuram automaticamente por `AGENTS.md` na raiz do repositório para injetar contexto relevante no prompt do sistema antes de tomar qualquer ação.
3. **Padrão Aberto e Não Proprietário**:
   - Em vez de adotar formatos proprietários de uma única empresa (`.cursorrules`, `copilot-instructions.md`, etc.), o `AGENTS.md` funciona universalmente através de qualquer ferramenta ou agente.

---

## 3. Seções Canônicas Recomendadas

A especificação não exige campos obrigatórios (é puro Markdown), mas as seguintes seções compõem as melhores práticas da indústria:

### 3.1 Dicas de Ambiente de Desenvolvimento (`Dev environment tips`)
Comandos exatos de instalação, compilação, início de servidores de desenvolvimento e manipulação de monorepos.
Exemplo:
```markdown
## Dev environment tips
- Use `pnpm install` para instalar dependências.
- Execute `pnpm dev` para subir o servidor local na porta 3000.
- Em monorepos, use `pnpm --filter <pacote> <comando>` para isolar o escopo.
```

### 3.2 Instruções de Teste (`Testing instructions`)
Instruções explícitas sobre como o agente deve testar seu código e validar alterações.
Exemplo:
```markdown
## Testing instructions
- Execute `pytest tests/unit/` para testes rápidos.
- Para rodar um teste específico: `pytest tests/test_auth.py -k "test_login"`.
- O agente deve corrigir todas as falhas e garantir que a suíte passe antes de concluir.
```

### 3.3 Estilo de Código & Convenções (`Code style`)
Regras rígidas sobre tipagem, linters e padrões arquiteturais:
```markdown
## Code style
- TypeScript em strict mode.
- Funções assíncronas devem tratar timeouts explicitamente.
- Não remova validações de parâmetros existentes.
```

### 3.4 Instruções para Pull Requests & Commits (`PR & Commit instructions`)
Padrões de mensagem de commit (ex: Conventional Commits) e checklist de envio:
```markdown
## PR instructions
- Formato do título: `feat(scope): short description` ou `fix(scope): ...`.
- Execute `pnpm lint` e `pnpm test` antes de realizar o commit.
```

---

## 4. Hierarquia & Precedência em Monorepos

Em projetos grandes ou monorepos, adote arquivos `AGENTS.md` aninhados:
```
raiz/
├── AGENTS.md                  # Regras globais da organização
├── packages/
│   ├── web/
│   │   └── AGENTS.md          # Regras específicas de Next.js / Tailwind
│   └── api/
│       └── AGENTS.md          # Regras específicas de Python / FastAPI
```

### Regras de Precedência:
1. **Instrução Explícita do Usuário**: A instrução direta do usuário no prompt/chat tem prioridade máxima e sobrepõe qualquer regra em arquivo.
2. **Proximidade Geográfica no Disco**: O `AGENTS.md` mais próximo do arquivo em edição sobrepõe instruções divergentes contidas em arquivos `AGENTS.md` superiores.
3. **Raiz do Repositório**: Define a base de governança e convenções gerais.

---

## 5. A Lei de Ouro da Governança AXION: O Combate ao Inchaço (*Anti-Bloat*)

Em modelos de IA contemporâneos, colocar 100KB de texto corrido em um arquivo raiz degrada a atenção do modelo (*attention dilution*) e consome tokens desnecessariamente.

Para evitar o inchaço:
1. **Mantenha o `AGENTS.md` raiz abaixo de 25KB**:
   - Utilize-o como uma **mesa diretora** / **índice executivo**.
   - Resuma cada regra em 1 ou 2 sentenças contundentes.
2. **Linkagem Canônica para Documentos Especializados**:
   - Aprofunde regras complexas em `docs/rules/*.md`.
   - Aprofunde decisões em `docs/adr/*.md`.
   - Forneça links markdown claros (`[Nome da Regra](file:///C:/workspace/docs/rules/...)`).
3. **Delegação a Skills**:
   - Tecnologias específicas devem ser encapsuladas em skills operacionais dedicadas sob `.agents/skills/`.
