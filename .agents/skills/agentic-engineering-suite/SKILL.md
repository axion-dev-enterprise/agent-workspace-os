---
name: agentic-engineering-suite
description: >-
  Operational engineering skill for advanced agent workflows: geospatial lead extraction and OSM geocoding, extreme Docker container optimization (multi-stage and distroless), high-performance UI motion and micro-transitions, local agent workspace orchestration (PI-Desktop), and neural video generation acceleration (ComfyUI VSA).
---

# Agentic Engineering Suite — Operational Skill

Skill operacional canônica que consolida ferramentas modernas e padrões de engenharia de ponta para agentes autônomos no ecossistema AXION. Cobre cinco pilares fundamentais:
1. **Inteligência Geoespacial & Extração de Leads Locais**: Geocodificação OSM Nominatim resiliente, extração de POIs e enriquecimento social com zero custo em tokens LLM.
2. **Otimização Extrema de Containers Docker**: Redução de ~90% em imagens através de Multi-Stage Builds, bases mínimas (`alpine`/`distroless`) e governança de `.dockerignore`.
3. **Motion, Micro-Interações & Design Editorial**: Biblioteca de transições CSS puras (Transitions.dev/Godly) com curvas cúbicas refinadas, guarda de acessibilidade `prefers-reduced-motion` e zero CLS.
4. **Workspaces de Agentes Locais & Orquestração Multi-Agente**: Arquitetura do PI-Desktop (`vastsa/PI-Desktop`), persistência de sessões, integração MCP e ritmos Agent/Plan/Goal.
5. **Aceleração de Vídeo Neural & Difusão com Atenção Esparsa**: Diretrizes de alocação de VRAM, atenções esparsas (VSA/Ref2VA) no ComfyUI e avaliação empírica de viabilidade de hardware.

---

## 1. Visão Geral & Os Cinco Pilares

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AGENTIC ENGINEERING SUITE (AXION)                    │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. LEADS & GEO    │ 2. DOCKER SLIM    │ 3. MOTION & UI                 │
│ • Nominatim OSM   │ • Multi-Stage     │ • Transitions.dev Recipes      │
│ • Regex Socials   │ • Alpine / Slim   │ • Bezier(0.16, 1, 0.3, 1)      │
│ • Zero LLM Tokens │ • .dockerignore   │ • prefers-reduced-motion       │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 4. LOCAL WORKSPACE│ 5. NEURAL VIDEO   │ HARDWARE AUDITOR               │
│ • PI-Desktop / MCP│ • ComfyUI VSA     │ • Sonda GPU/VRAM/CUDA          │
│ • Agent/Plan/Goal │ • Ref2VA Gating   │ • Proteção de Blast Radius     │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

---

## 2. Regras Operacionais de Ouro

1. **Preflight de Hardware Obrigatório Antes de Modelos Pesados**:
   - Nunca disparar o download de modelos de difusão de vídeo (>10 GB) ou tensores densos sem antes rodar `system_agent_preflight.py`.
   - Se a máquina física não possuir GPU NVIDIA com suporte a CUDA e VRAM suficiente (ex: ambiente com GPU AMD ou iGPU de 1 GB), o agente DEVE documentar factualmente a restrição e recomendar a execução em instâncias de nuvem.

2. **Zero-Token Social Enrichment**:
   - A extração de perfis sociais (Instagram, LinkedIn, Facebook) a partir de websites obtidos em raspagens DEVE ser feita exclusivamente por expressões regulares compiladas via Python stdlib, jamais queimando tokens de modelo de linguagem para tarefas puramente determinísticas de parsing.

3. **Multi-Stage e .dockerignore Mandatórios**:
   - Todo container construído para produção deve isolar dependências de compilação em um estágio `builder` e utilizar imagens de base ultraleves (`alpine` ou `slim`), reduzindo o footprint em ~90%.
   - É terminantemente proibido construir containers sem verificar a existência de `.dockerignore` contendo `.git`, `.env*` e `node_modules/`.

4. **Acessibilidade e Curvas Refinadas de Transição (Regras #6 e #7)**:
   - Toda animação ou micro-transição deve possuir guardrails para usuários com sensibilidade motora via `@media (prefers-reduced-motion: reduce)`.
   - Proibido o uso de curvas lineares ou transições abruptas. Padronize em `cubic-bezier(0.16, 1, 0.3, 1)` ou `cubic-bezier(0.22, 1, 0.36, 1)` com durações entre 150ms e 250ms.

---

## 3. Utilitários Canônicos da Skill

Todos os utilitários estão implementados com zero dependências externas (Python 3 standard library pura) no diretório `scripts/`:

### 3.1 Auditor de Ambiente & Capacidade de Hardware
Examina vendor de GPU, capacidade de VRAM, presença de CUDA, runtimes (Node, Python, Git, Docker, Cargo) e repositórios locais clonados.
```bash
# Execução padrão com relatório formatado no terminal
python .agents/skills/agentic-engineering-suite/scripts/system_agent_preflight.py

# Saída estruturada em JSON para pipelines automatizados
python .agents/skills/agentic-engineering-suite/scripts/system_agent_preflight.py --json
```

### 3.2 Otimizador & Auditor de Containers Docker
Analisa Dockerfiles em busca de causas de bloat (imagens base pesadas, ausência de multi-stage, falta de `.dockerignore`) e gera templates otimizados.
```bash
# Auditar um Dockerfile existente
python .agents/skills/agentic-engineering-suite/scripts/docker_slimmer.py services/axion-flow/Dockerfile

# Gerar Dockerfile multi-stage otimizado e .dockerignore para Node.js
python .agents/skills/agentic-engineering-suite/scripts/docker_slimmer.py --generate node ./apps/nova-app

# Gerar Dockerfile multi-stage otimizado para Python FastAPI
python .agents/skills/agentic-engineering-suite/scripts/docker_slimmer.py --generate python ./services/novo-servico
```

### 3.3 Extrator de Leads Geoespaciais & Enriquecimento Social
Executa buscas de estabelecimentos por categoria e localização via OpenStreetMap Nominatim/Overpass, detecta se o daemon Docker do gosom está ativo na porta 8080 e enriquece contatos sociais via regex.
```bash
# Buscar cafeterias em Curitiba e exportar para CSV
python .agents/skills/agentic-engineering-suite/scripts/lead_geo_scraper.py --city "Curitiba, PR" --category "cafe" --limit 10 --out temp/leads_curitiba.csv

# Buscar academias em São Paulo e exibir no terminal em formato legível
python .agents/skills/agentic-engineering-suite/scripts/lead_geo_scraper.py --city "Sao Paulo, SP" --category "academia" --limit 5
```

### 3.4 Catálogo & Motor de Micro-Interações UI (Motion Recipes)
Fornece receitas de transição refinadas (card-resize, modal com backdrop blur, skeleton shimmer, badges de pensamento, toasts flutuantes) e exporta previews HTML ou folhas de estilo CSS modulares.
```bash
# Listar todas as receitas disponíveis
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --list

# Gerar um preview visual HTML completo para inspeção em navegador
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --generate-preview temp/motion_preview.html

# Exportar todas as receitas modulares para a pasta do frontend
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --export-all apps/web/src/styles/transitions/
```

---

## 4. Portão de Verificação (Verification Gate)

Antes de considerar uma tarefa envolvendo esta skill como concluída, o agente deve validar factualmente:
1. `system_agent_preflight.py` executou com exit code 0 e determinou adequadamente o nível neural da máquina (`tier_1`, `tier_2` ou `tier_3`).
2. Qualquer Dockerfile criado ou otimizado passou na auditoria do `docker_slimmer.py` com pontuação igual ou superior a 80/100.
3. Extrações de leads geraram arquivos CSV/JSON com cabeçalhos estruturados e sem erros de codificação de caracteres em terminais Windows.
4. Códigos de interface com animações incluem a diretiva `@media (prefers-reduced-motion)` e não provocam Cumulative Layout Shift (CLS = 0).

---

## 5. Documentos de Referência Profunda

Consulte a pasta `references/` para especificações técnicas detalhadas:
- [`references/docker_optimization_guide.md`](references/docker_optimization_guide.md): Guia de redução extrema de tamanho de imagens Docker.
- [`references/ui_transitions_catalog.md`](references/ui_transitions_catalog.md): Catálogo de micro-interações CSS e curvas cubic-bezier.
- [`references/neural_video_vsa_architecture.md`](references/neural_video_vsa_architecture.md): Arquitetura de tensores esparsos VSA para o MiniMax-H3 Ref2VA.
- [`references/pi_desktop_mcp_orchestration.md`](references/pi_desktop_mcp_orchestration.md): Guia de persistência e subagentes do PI-Desktop.
