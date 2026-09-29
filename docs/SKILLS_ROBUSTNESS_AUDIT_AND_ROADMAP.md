# Relatório de Auditoria de Obviedades e Roteiro de Robustez das Skills

> **Data da Auditoria:** 27 de Setembro de 2026  
> **Escopo:** Todas as 75 skills operacionais em `.agents/skills/`  
> **Status do Catálogo:** 26 Robustas (35%) | 12 Micro-Fragmentadas (16%) | 10 Médias/Incompletas (13%) | 27 Phantom Stubs / Puras Obviedades (36%)

---

## 1. Sumário Executivo & Diagnóstico da Crise de "Obviedades"

A auditoria factual no diretório `.agents/skills/` revelou que **mais da metade do catálogo (52%) é composta por conteúdo superficial, redundante ou cascas vazias de 10 a 14 linhas**. 

Essas skills sofrem da síndrome da **"Obviedade de Wikipedia"**: afirmam conceitos genéricos que qualquer desenvolvedor ou LLM já possui em seu pré-treinamento (ex: *"use Suspense no Next.js para carregar partes lentas"*, *"use DataLoader para evitar n+1"*, *"coloque TTL no Redis"*), mas **não fornecem nenhum ferramental prático, script CLI, configuração de produção, benchmark ou matriz de gotchas reais**.

### O Impacto Negativo em Agentes Autônomos
1. **Falso Positivo de Capacidade:** O `AGENTS.md` obriga o agente a consultar a skill antes de programar. O agente lê 12 linhas genéricas, não encontra nenhum padrão do projeto e passa a improvisar.
2. **Poluição do Espaço de Atenção:** O roteador de ferramentas do LLM precisa processar 75 entradas na tabela a cada invocação, das quais 39 são ruído desnecessário.
3. **Decisão Diluída:** Um agente querendo criar um vídeo em React precisa decidir entre 12 skills do Remotion em vez de consultar uma única fonte de verdade.

---

## 2. As 5 Patologias Encontradas nas Skills

### Patologia 1: "O Stub de 11 Linhas" (Bullets Genéricos sem Substância)
Skills criadas apenas para preencher tabela, com 1 parágrafo introdutório e 3 bullets conceituais:
- `nextjs-app-router-rsc` (11 linhas)
- `kubernetes-k8s-manifests` (11 linhas)
- `redis-caching-queues` (11 linhas)
- `playwright-e2e-testing` (11 linhas)
- `pytest-mocking-fixtures` (10 linhas)
- `qdrant-vector-database` (10 linhas)
- `github-actions-cicd` (11 linhas)

### Patologia 2: A Hiper-Fragmentação Extrema (Caso Remotion)
12 pastas distintas criadas para uma única biblioteca React (`@remotion/*`):
- `remotion-best-practices`, `remotion-captions`, `remotion-create`, `remotion-docs`, `remotion-interactivity`, `remotion-maps`, `remotion-markup`, `remotion-multimedia`, `remotion-render`, `remotion-saas`, `remotion-studio`, `remotion-upgrade`.
- A skill `remotion-best-practices` é um índice de 32 linhas que apenas redireciona para as outras 11.

### Patologia 3: Duplicação Concorrente Direta
- `postgresql-advanced-optimization` (12 linhas) repete exatamente os tópicos de índices e EXPLAIN ANALYZE já abordados em `postgresql-dba-maintenance` (133 linhas).

### Patologia 4: O Bloqueio em Marca/Fornecedor (Vendor Lock Siloed)
- `stripe-payments-engine`: Focada só na Stripe, ignorando Pix, Asaas e Mercado Pago.
- `elevenlabs-tts-voiceover` (10 linhas) e `whisper-stt-neural-voice` (10 linhas): TTS e STT fatiados em 2 marcas comerciais de 10 linhas cada.
- `whatsapp-baileys-bot-ops` e `telegram-bot-ops`: Separados por lib/plataforma em vez de uma arquitetura unificada de mensageria para agentes.

### Patologia 5: Ausência de Ferramental Executável
- Das 75 skills, **apenas 7 possuem scripts operacionais executáveis em `scripts/`**.
- Uma skill de agente moderna deve ser **Executable-First**: ter scripts Python stdlib prontos para validar, auditar ou executar a tarefa no host.

---

## 3. Matriz Completa de Diagnóstico e Plano de Ação por Skill

Abaixo, a lista detalhada das skills superficiais com a "obviedade" identificada e a prescrição exata para torná-las 100% robustas.

### Bloco A: Stubs de Frontend & Mobile

| Skill | Obviedade Atual | O que Torna 100% Robusta & Útil | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| **`nextjs-app-router-rsc`** | *"Server por padrão, use Suspense para partes lentas, valide Server Actions com Zod"* (11 linhas). | Matriz de cache (`revalidatePath`, `unstable_cache`, tags), interceptors de autenticação em middleware, tratamento de streaming com SSE, proteção contra vazamento de props cliente/servidor e script CLI para auditar vazamento de bundles cliente. | **Expandir** para 150+ linhas com runbook de SSR/RSC e script `audit_rsc_boundaries.py`. |
| **`react-query-tanstack`** | *"Query keys declarativas como arrays, use mutações otimistas"* (11 linhas). | Padrão factory de Query Keys, arquitetura de invalidação seletiva, persistência offline em IndexedDB, estratégias de retry exponencial com jitter e template completo de hook customizado com tipagem estrita. | **Expandir** para guia completo de gerenciamento de estado assíncrono. |
| **`state-zustand-jotai`** | *"Crie stores modulares e exporte seletores para evitar re-render"* (11 linhas). | Middleware de persistência determinística com criptografia no storage, sincronização multi-abas via BroadcastChannel, slices de stores com TypeScript estrito e anti-padrões de ciclo infinito de re-render. | **Consolidar** junto com `react-query-tanstack` na skill **`react-state-architecture`**. |
| **`react-native-expo`** | *"Expo Router é baseado em arquivos, proteja telas nativas"* (11 linhas). | Configuração EAS Build (iOS/Android), gerenciamento de Deep Links, tratamento de permissões nativas (câmera, biometria, GPS), ciclo de vida offline-first e push notifications via APNs/FCM. | **Expandir** com receitas reais de build e scripts de checagem de prebuild. |
| **`web-vitals-performance`** | *"LCP < 2.5s, evite Cumulative Layout Shift"* (11 linhas). | Script CLI em Python para análise de bundles (`webpack-bundle-analyzer` / `source-map-explorer`), regras de fontes com `font-display: optional`, pré-conexão DNS de CDNs e checklist de inline critical CSS. | **Adicionar** script `scripts/audit_web_vitals.py` para medição via Puppeteer/Chrome headless. |

---

### Bloco B: Stubs de Backend, APIs & Dados

| Skill | Obviedade Atual | O que Torna 100% Robusta & Útil | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| **`fastapi-async-api`** | *"Use Pydantic v2, dependency injection e background tasks"* (29 linhas). | Arquitetura de lifespan events, connection pool com asyncpg, rate-limiting com Redis, middlewares de tracing OpenTelemetry e template completo de CRUD assíncrono com testes via `httpx`. | **Expandir** com scripts de scaffolding e middleware de correlação de logs. |
| **`grpc-protobuf-microservices`** | *"Contratos .proto claros e versionados"* (11 linhas). | Pipeline de geração automática de stubs TypeScript/Python, interceptors de autenticação mTLS e JWT, streaming bidirecional com backpressure e tratamento de deadlines/timeouts. | **Expandir** com script CLI de compilação e verificação de contratos `.proto`. |
| **`graphql-apollo-federation`** | *"Use DataLoader para n+1, adicione diretivas @key"* (11 linhas). | Implementação completa de DataLoader com cache LRU, cálculo de complexidade de query para proteção contra DoS, gateway Apollo Router / Rover CLI e testes de integração. | **Expandir** com utilitário de validação de subgraphs. |
| **`redis-caching-queues`** | *"Cache-Aside com TTL, use BullMQ para jobs"* (11 linhas). | Implementação do algoritmo Redlock para concorrência distribuída, pipeline de comandos atômicos via Lua scripts, estratégias de mitigação de Cache Stampede (Probabilistic Early Expiration) e monitoramento de memória/eviction. | **Adicionar** script `scripts/redis_benchmark_and_lock.py` para testes de concorrência. |
| **`mongodb-aggregation-pipeline`** | *"Coloque $match e $project no início"* (11 linhas). | Guia de indexação composta cobrindo regras ESR (Equality, Sort, Range), otimização de joins `$lookup` com pipelines aninhados, gerenciamento de Sharding e Change Streams resilientes a reconexões. | **Expandir** com templates de aggregation e validador de planos de execução. |
| **`qdrant-vector-database`** | *"Use Cosine para embeddings normalizados"* (10 linhas). | Configuração de HNSW (M, ef_construct), quantização escalar/binária (Scalar/Binary Quantization) para redução de 75% da RAM, payload indexing com filtros compostos e estratégias de backup snapshot. | **Adicionar** script CLI de benchmark de busca e ingestão vetorial. |
| **`postgresql-advanced-optimization`** | *"Índices compostos: Igualdade -> Range -> Order By"* (12 linhas). | É 100% redundante com a skill `postgresql-dba-maintenance`. | **Deletar / Fundir** imediatamente na [`postgresql-dba-maintenance`](file:///c:/workspace/.agents/skills/postgresql-dba-maintenance). |
| **`prisma-drizzle-orm`** | *"Drizzle para serverless, Prisma para enterprise"* (13 linhas). | Matriz de migração zero-downtime, regras de transação com rollback seguro, otimização de queries com prepared statements e tratamento de conexões esgotadas em ambientes serverless. | **Expandir** com runbook de migrações complexas. |

---

### Bloco C: Stubs de DevOps, Cloud & QA

| Skill | Obviedade Atual | O que Torna 100% Robusta & Útil | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| **`kubernetes-k8s-manifests`** | *"Defina resource requests e limits, use liveness probes"* (11 linhas). | Manifestos canônicos de produção (Deployment, Service, Ingress, HPA, PDB), políticas de segurança de Pod (SecurityContext, readOnlyRootFilesystem), gestão de ConfigMaps e Secrets via sealed-secrets/vault, e script de linting de YAMLs. | **Adicionar** manifestos de produção em `examples/` e script `scripts/lint_k8s_manifests.py`. |
| **`terraform-iac-automation`** | *"Remote state locking no S3 com DynamoDB"* (11 linhas). | Estrutura modular em camadas (Network, Compute, Database), gestão de drift com `terraform plan -detailed-exitcode`, automação de lock release, injeção de segredos via OIDC e políticas OPA/Conftest. | **Expandir** com boilerplates completos de AWS/GCP e Cloudflare. |
| **`github-actions-cicd`** | *"Use actions/cache e configure matrix builds"* (11 linhas). | Autenticação OIDC secretless com GCP e AWS, estratégias de cache multi-linguagem (pnpm/cargo/pip), semantic release automatizado com changelog, escaneamento de vulnerabilidades trivy/semgrep e templates modulares. | **Expandir** com workflows canônicos reutilizáveis. |
| **`prometheus-grafana-metrics`** | *"Use métricas RED: Rate, Errors, Duration"* (11 linhas). | Configuração de histogramas de latência (buckets exponenciais), queries PromQL prontas para alertas SLO/SLA (99.9%), dashboards em JSON importáveis e regras de Alertmanager com silenciamento e roteamento PagerDuty/Discord. | **Adicionar** templates de dashboard JSON em `resources/` e regras de alertas. |
| **`sentry-error-tracking`** | *"Envie source maps na esteira de build"* (10 linhas). | Configuração de `beforeSend` para higienização e mascaramento de PII (senhas, CPFs, cartões), agrupamento determinístico de erros via fingerprinting, amostragem inteligente de transações (tracesSampleRate) e alertas contextuais. | **Expandir** com snippet universal de inicialização sem vazamento de tokens. |
| **`playwright-e2e-testing`** | *"Use seletores acessíveis por papel semântico"* (11 linhas). | Arquitetura Page Object Model (POM) em TypeScript estrito, automação de login com reuso de `storageState`, mock de APIs de terceiros, gravação de traces e vídeos em falhas, e execução paralela em CI. | **Expandir** com boilerplates POM e script `scripts/run_e2e_matrix.py`. |
| **`pytest-mocking-fixtures`** | *"Use fixtures com escopo session para recursos caros"* (10 linhas). | Mock de bancos de dados via testcontainers, monkeypatching avançado de chamadas HTTP externas (`responses` / `httpx_mock`), fixtures parametrizadas com cobertura de edge-cases e testes de concorrência. | **Adicionar** templates práticos de fixtures e suíte de testes de stress. |
| **`web-scraping-crawling`** | *"Envie headers realistas com User-Agent"* (11 linhas). | Rotação de proxies residenciais, resolução de Cloudflare Turnstile/hCaptcha, parsing em streaming com selectolax/lxml, tratamento de rate-limits com backoff exponencial e persistência idempotente em SQLite/Postgres. | **Expandir** com script CLI de extração resiliente. |
| **`pdf-generation-puppeteer`** | *"Use CSS @page e configure margin"* (19 linhas). | Template HTML/CSS com grid e page-break-inside avoid, cabeçalhos e rodapés dinâmicos com numeração de página nativa, injeção de fontes locais (sem fetch web) e script CLI para renderização de relatórios. | **Adicionar** script CLI `scripts/generate_pdf_report.py`. |
| **`seo-technical-structured-data`** | *"Inclua JSON-LD Organization e WebSite"* (11 linhas). | Esquemas ricos avançados (Article, Product, FAQPage, BreadcrumbList), validação automatizada contra a especificação do Google Rich Results via script Python e geração dinâmica de `sitemap.xml` com canonical tags. | **Adicionar** script `scripts/validate_structured_data.py`. |

---

### Bloco D: Stubs de IA & Engenharia de Agentes

| Skill | Obviedade Atual | O que Torna 100% Robusta & Útil | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| **`langchain-langgraph-orchestration`** | *"StateGraph compartilha estado em canais, use checkpointers"* (11 linhas). | Arquitetura de subgrafos hierárquicos, persistência de memória com PostgresSaver, nós de decisão com ToolNode determinístico, tratamento de interrupções de aprovação humana (*human-in-the-loop*) e observabilidade via LangSmith. | **Expandir** com grafo cíclico de produção funcional e testes de estado. |
| **`rag-chunking-embeddings`** | *"Use chunking inteligente com sobreposição de 10-20%"* (11 linhas). | Divisão semântica de markdown/código baseada em AST, busca híbrida recíproca (RRF - Reciprocal Rank Fusion) combinando BM25 e vetorial, re-ranking com Cross-Encoders locais e avaliação de contexto via RAGAS. | **Adicionar** script `scripts/hybrid_rag_search.py`. |
| **`prompt-engineering-jailbreak-defense`** | *"Isole dados não confiáveis com delimitadores"* (11 linhas). | Arquitetura de prompts em múltiplas camadas (System, Developer, User), sanitização contra injeções indiretas de prompt (Data-Exfiltration via Markdown/Images), defesas Few-Shot adversárias e validador de payloads maliciosos. | **Adicionar** suite de testes com 30 vetores de injeção conhecidos. |
| **`elevenlabs-tts-voiceover`** | *"Use WebSockets para baixa latência, configure SSML"* (10 linhas). | Script CLI em Python para geração e streaming de áudio, clonagem de voz instantânea (IVC) com áudio de referência, controle fino de estabilidade/similaridade e exportação em MP3/PCM 24kHz. | **Consolidar** junto com Whisper na skill unificada **`neural-speech-audio`**. |
| **`whisper-stt-neural-voice`** | *"Converta áudio para 16kHz mono WAV"* (10 linhas). | Pipeline completo com diarização de múltiplos locutores (PyAnnote), transcrição em chunks temporizados com VAD (Voice Activity Detection), alinhamento fonético de palavras para legendas e exportação em SRT/VTT. | **Consolidar** junto com ElevenLabs na skill unificada **`neural-speech-audio`**. |

---

### Bloco E: A Suíte Remotion (12 Skills Fragmentadas)

As 12 skills atuais do Remotion (`remotion-create`, `remotion-render`, `remotion-captions`, `remotion-markup`, `remotion-studio`, `remotion-interactivity`, `remotion-maps`, `remotion-multimedia`, `remotion-saas`, `remotion-docs`, `remotion-upgrade`, `remotion-best-practices`) devem ser **imediatamente unificadas em uma única master-skill**:

**`remotion-video-studio`**
- Ponto de entrada único com seções dedicadas: Setup & Composição, React Markup & Flexbox de Vídeo, Renderização Server-Side (CLI, Lambda, SSR), Geração e Animação de Legendas, Preview Interativo no Studio.
- Todas as referências detalhadas organizadas dentro de `references/` na mesma skill.
- Deletar as outras 11 pastas redundantes, liberando 11 posições no catálogo de governança.

---

## 4. O Roteiro de Execução em 4 Fases

Para sanear o ecossistema sem interromper o trabalho diário, propõe-se a seguinte ordem de execução:

```
┌────────────────────────┐     ┌────────────────────────┐
│ FASE 1: FAXINA E FUSÃO │ ──> │ FASE 2: NÚCLEO BACKEND │
│ Eliminar 12 Remotion   │     │ Expandir Next, FastAPI │
│ Unificar Áudio e Postg.│     │ Redis e ORMs com CLI   │
└────────────────────────┘     └───────────┬────────────┘
                                           │
┌────────────────────────┐     ┌───────────▼────────────┐
│ FASE 4: IA & AGENTES   │ <── │ FASE 3: QA & DEVOPS    │
│ Expandir LangGraph,    │     │ Implementar Playwright,│
│ RAG e Prompt Defense   │     │ K8s, CI/CD e Pytest    │
└────────────────────────┘     └────────────────────────┘
```

### Fase 1: Faxina Estrutural e Fusões (Redução Imediata de Bloat)
1. **Remotion (12 ➔ 1):** Criar `remotion-video-studio` com todo o conhecimento consolidado e deletar as 11 pastas satélites.
2. **PostgreSQL (2 ➔ 1):** Deletar `postgresql-advanced-optimization` e concentrar tudo na `postgresql-dba-maintenance`.
3. **Áudio Neural (2 ➔ 1):** Criar `neural-speech-audio` (TTS + STT + Diarização) com script CLI em Python e deletar os dois stubs de 10 linhas (`elevenlabs` e `whisper`).
4. **Estado React (2 ➔ 1):** Unificar `state-zustand-jotai` e `react-query-tanstack` em `react-state-architecture`.
5. **Resultado da Fase 1:** O catálogo cai de **75 skills inchadas para ~60 skills**, eliminando 15 entradas puramente redundantes.

### Fase 2: Robustecimento de Backend, APIs & Bancos de Dados
1. **Next.js 15 (`nextjs-app-router-rsc`):** Desenvolver o runbook completo de Server Actions, cache tags, Suspense boundaries e script de auditoria de bundle.
2. **Redis (`redis-caching-queues`):** Escrever utilitário CLI em Python de distributed lock (Redlock) e monitoramento de memory leaks.
3. **FastAPI (`fastapi-async-api`):** Incluir arquitetura completa de lifespan, conexão assíncrona com Postgres e middleware de rastreamento.
4. **MongoDB & Qdrant:** Adicionar scripts de teste de agregação e benchmarking de embeddings.

### Fase 3: Robustecimento de Testes, DevOps & Infraestrutura
1. **Playwright (`playwright-e2e-testing`):** Implementar fixtures reutilizáveis, POM TypeScript e runner headless.
2. **Pytest (`pytest-mocking-fixtures`):** Criar fixtures canônicas de banco de dados e monkeypatching HTTP.
3. **Kubernetes & Terraform:** Criar templates reais de manifestos de produção e pipelines OIDC.
4. **Sentry & Observabilidade:** Adicionar sanitizadores de PII e scripts de injeção de breadcrumbs.

### Fase 4: Robustecimento de Inteligência Artificial & Agentes
1. **LangGraph (`langchain-langgraph-orchestration`):** Montar arquitetura de StateGraph cíclico com persistência e tool calling determinístico.
2. **RAG (`rag-chunking-embeddings`):** Implementar motor híbrido (BM25 + Dense) e re-ranker local.
3. **Defesa de Prompts (`prompt-engineering-jailbreak-defense`):** Incluir suíte automatizada de pentest de injeção de prompt com 30 vetores de ataque.

---

## 5. O Modelo Padrão Ouro: Como Toda Skill Deve Ser

A recém-criada [`paranoid-bug-hunter`](file:///c:/workspace/.agents/skills/paranoid-bug-hunter/SKILL.md) serve como o **blueprint canônico** do que uma skill 100% útil e robusta deve conter:

1. **Frontmatter YAML Rigoroso:** Nome kebab-case, descrição clara com gatilhos de ativação.
2. **Filosofia Operacional & Princípios:** Explicação clara do problema e modelo mental a adotar.
3. **Ciclo de Execução em Fases:** Da investigação ao portão de verificação empírica.
4. **Matriz de Vetores e Gotchas Reais:** Casos de falha reais em vez de teorias vagas.
5. **Ferramenta CLI Standalone (`scripts/`):** Utilitário em Python stdlib, zero dependências, parametrizável por perfis (`--profile`), com saída em console e JSON para CI.
6. **Catálogo de Padrões e Anti-Padrões (`references/`):** Exemplos explícitos de *"Código Quebrado vs Código Corrigido"*.
7. **Receitas de Testes de Reprodução (`references/`):** Códigos prontos para testes de estresse, concorrência e simulação.
8. **Checklist Pré-Mortem Mandatório:** Critérios de verificação antes de concluir a tarefa.

Seguindo esse padrão ouro, o ecossistema AXION deixará de ter dezenas de stubs superficiais e passará a ter uma **suíte de ferramentas e manuais de engenharia de nível cirúrgico**.

---

## 6. Relatório de Execução & Homologação Final (100% Concluído)

Todas as 4 fases do roteiro de robustecimento foram executadas com rigor cirúrgico e verificadas empiricamente:

### Resumo das Entregas por Fase:
- **Fase 1 (Faxina Estrutural e Fusões):** Concluída. Eliminação das 12 skills redundantes do Remotion (unificadas em `remotion-video-studio`), unificação de TTS/STT em `neural-speech-audio`, consolidação de estado em `react-state-architecture` e eliminação da duplicação do PostgreSQL. Catálogo reduzido de 75 para 61 skills.
- **Fase 2 (Núcleo Backend, APIs & Bancos):** Concluída. `nextjs-app-router-rsc`, `redis-caching-queues`, `fastapi-async-api`, `mongodb-aggregation-pipeline`, `qdrant-vector-database`, `prisma-drizzle-orm` e `stripe-payments-engine` expandidos com guias densos e CLIs operacionais em Python stdlib.
- **Fase 3 (QA, DevOps & Observabilidade):** Concluída. `playwright-e2e-testing`, `pytest-mocking-fixtures`, `kubernetes-k8s-manifests`, `terraform-iac-automation`, `github-actions-cicd`, `sentry-error-tracking` e `prometheus-grafana-metrics` equipados com linters de conformidade e guias de resiliência.
- **Fase 4 (IA & Agentes + Especializadas):** Concluída. `langchain-langgraph-orchestration`, `rag-chunking-embeddings`, `prompt-engineering-jailbreak-defense`, `nestjs-modular-backend`, `graphql-apollo-federation`, `grpc-protobuf-microservices`, `react-native-expo`, `web-vitals-performance`, `seo-technical-structured-data`, `content-3d-social-studio`, `pdf-generation-puppeteer` e `web-scraping-crawling` 100% transformadas em manuais operacionais com ferramentas integradas.

### Verificação Empírica Final (Regra #2 & Regra #13A):
```
================================================================================
             CANONICAL SKILL VALIDATOR -- RULE #13A AUDIT                       
================================================================================
Skills Root: C:\workspace\.agents\skills
Total Targets to Audit: 61
Strict Mode: True
--------------------------------------------------------------------------------
Summary: PASS=61 | WARN=0 | FAIL=0 (Total=61) [100% APPROVAL]
================================================================================
```

