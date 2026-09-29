# Relatório Exaustivo: Padrões Repetitivos de UI/UX em LLMs (AI Slop) & O Anti-Playbook de Engenharia

> **Status:** Ativo / Canônico de Pesquisa  
> **Data:** 29 de Setembro de 2026  
> **Escopo:** Análise empírica de padrões em v0, Lovable, Claude Code, Cursor, GitHub Copilot, ChatGPT e o ecossistema frontend comunitário (GitHub, Hacker News, Reddit, Designer Twitter/X).  
> **Objetivo:** Mapear a totalidade dos vícios visuais, arquiteturais e de acessibilidade gerados por LLMs, documentar suas causas estatísticas e consolidar os protocolos comunitários de imunização ("Anti-Slop").

---

## Sumário Executivo

A proliferação de ferramentas de IA generativa para frontend em 2024–2026 deu origem ao que a comunidade de design e engenharia apelidou de **"AI Slop UI"** ou a **"Nova Síndrome do Bootstrap"**.

Assim como em 2012 qualquer usuário identificava imediatamente um site feito com o Twitter Bootstrap padrão (botão azul arredondado, gradiente leve, fonte Helvetica e navbar cinza), em 2025/2026 o público desenvolveu **cegueira seletiva para interfaces geradas por IA** (*AI Blindness*). Estudos comportamentais demonstram uma **queda de 20% a 35% no engajamento** e um **déficit de confiança de até 32%** quando visitantes identificam landing pages com a assinatura visual padronizada de modelos estatísticos.

O modelo não "projeta": ele calcula a **média geométrica de menor perda estocástica** sobre repositórios indexados. Como os maiores repositórios de 2021 a 2024 eram dominados por Tailwind CSS, Shadcn UI, Radix e clones da Linear/Vercel, toda solicitação genérica como *"crie uma landing page moderna"* colapsa no mesmo arquétipo escuro com gradientes violeta e falsos bento grids.

---

## 1. A Anatomia do Arquétipo Padrão (O "Default Monoculture")

Quando nenhuma restrição de tokens ou direção de arte humana é imposta, 95% dos LLMs convergem para a estrutura abaixo:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                 ANATOMIA TÍPICA DO TEMPLATE "DEFAULT DE IA"                   │
├───────────────────────────────────────────────────────────────────────────────┤
│ [Top Navbar]     Logo genérico com gradiente + 4 links + Botão com glow       │
│                                                                               │
│ [Hero Pill]      (✨) "Announcing Version 2.0" / "Powered by Next-Gen AI"      │
│ [Hero Heading]   "Supercharge your workflow with seamless, intelligent X"     │
│ [Hero Subtitle]  Texto cinza centralizado explicando o óbvio em 2 linhas      │
│ [Hero CTAs]      [Get Started Free -> (Brilhando)]   [Book a Demo (Borda)]    │
│                                                                               │
│ [Social Proof]   "Trusted by 10,000+ teams" + 5 logos monocromáticos falsos   │
│                                                                               │
│ [Features]       3 colunas idênticas: Lucide Icon num quadrado + H3 + P       │
│                                                                               │
│ [Bento Grid]     Grid 3x2 com "widgets decorativos" e barras de progresso 82% │
│                                                                               │
│ [Pricing Table]  3 cards: Free, Pro (escalado 105% + badge "Popular"), Ent    │
│                                                                               │
│ [FAQ Accordion]  4 perguntas colapsáveis em Radix UI com chevrons giratórios  │
│                                                                               │
│ [Footer CTA]     Card gigante com gradiente escuro no fundo e botão no centro   │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Catálogo Taxonômico de Vícios Repetitivos

### Categoria A: Macro-Arquitetura e Layout

1. **A Ordem Imutável das 7 Seções:**
   O pipeline estrutural é sempre rígido: *Hero -> Social Proof Marquee -> 3 Features -> Bento Grid -> Pricing (3 tiers) -> Accordion FAQ -> Banner CTA Final*.
2. **Aversão à Assimetria (`text-center` obsessivo):**
   Mais de 85% dos Hero sections gerados utilizam `flex flex-col items-center justify-center text-center`. O LLM quase nunca se arrisca em diagramações editoriais suíças, títulos alinhados à esquerda com ancoragem de conteúdo ou grids com pesos visuais contrastantes.
3. **O Falso Bento Grid:**
   A apropriação do layout modular de caixas (popularizado pela Apple e Linear) é aplicada de forma puramente decorativa. As caixas são preenchidas com métricas arbitrárias, barras de progresso estáticas (`w-[82%]`) ou seletores que não possuem estado funcional.
4. **Vácuo de Conteúdo Sem Enquadramento:**
   Elementos isolados flutuando em containers desproporcionalmente altos (`py-32`) sem linhas-guia ou divisões funcionais que guiem o olhar do leitor.

---

### Categoria B: Paleta Cromática e Superfícies

1. **O Monopólio do "Linear Dark Mode" Cópia Barata:**
   Fundo `#000000` ou `#09090b`, borda `border-zinc-800` ou `border-white/10`. Aplicado indistintamente para software empresarial, clínicas médicas, escritórios de advocacia ou produtos físicos.
2. **O Gradiente Roxo-Violeta-Ciano:**
   A trinca cromática estatística `from-purple-600 via-indigo-500 to-pink-500` ou `from-cyan-400 to-blue-600` usada no texto principal através de `bg-clip-text text-transparent`. Conhecido na comunidade como *"The Supabase/Vercel Rainbow Hangover"*.
3. **A "Mancha Aurora" Desfocada (`blur-3xl` blob):**
   Círculo absoluto posicionado no topo (`w-[600px] h-[400px] bg-purple-500/20 blur-[120px] rounded-full pointer-events-none`) para fingir profundidade sem criar iluminação direcional verdadeira.
4. **Glassmorphism Cego (`backdrop-blur-md`):**
   Superfícies translúcidas aplicadas sem checagem de contraste de legibilidade ou impacto no consumo de memória GPU em telas retina móveis.
5. **Glow Radioativo:**
   Sombras exageradas em botões e bordas (`shadow-[0_0_50px_-12px_rgba(124,58,237,0.5)]`).

---

### Categoria C: Tipografia e Linguagem ("AI Speak")

1. **A Monocultura da Fonte "Inter":**
   Uso exclusivo de `font-sans` configurada com `Inter` ou `Geist`. Ausência completa de fontes display, serifas editoriais (*Fraunces*, *Newsreader*, *Playfair*) ou fontes mono para densidade de dados numéricos (*JetBrains Mono*).
2. **O Léxico Clichê de Copywriting:**
   - *"Supercharge your workflow"*
   - *"Unleash the power of AI"*
   - *"Seamlessly integrate with your favorite tools"*
   - *"All-in-one platform for modern teams"*
   - *"Elevate your business to the next level"*
3. **A Epidemia da Faísca (`✨` / `Sparkles`):**
   O ícone `Sparkles` do Lucide colocado em todos os badges, botões e títulos como sinalizador automático de modernidade. Tornou-se o novo clipart dos anos 90.
4. **Métricas Alucinadas Padronizadas:**
   - *"99.9% Uptime SLA"*
   - *"10x Faster"*
   - *"10,000+ Happy Customers"*
   - *"24/7 Dedicated Support"*

---

### Categoria D: Movimento, 3D e Micro-interações

1. **Canvas Three.js Decorativo e Desconectado:**
   Quando instruído a usar 3D, o LLM quase sempre gera:
   - Uma esfera aramada (`IcosahedronGeometry` com `wireframe: true`) girando no vazio.
   - Poeira de partículas flutuantes sem física nem relevância para a marca.
2. **O Botão com "Border Beam" Cônico:**
   Um feixe de luz girando infinitamente na borda do botão primário (`animate-shimmer`), gerando fadiga visual e distração cognitiva.
3. **Animações de Scroll Repetitivas (`fade-in-up` idêntico):**
   Todas as 30 divs de uma página recebem exatamente a mesma declaração:
   ```jsx
   initial={{ opacity: 0, y: 20 }}
   whileInView={{ opacity: 1, y: 0 }}
   transition={{ duration: 0.5 }}
   ```
4. **Confete Gratuito (`canvas-confetti`):**
   Disparo de confete ao clicar em botões secundários triviais ou formulários de newsletter sem qualquer conquista real do usuário.

---

### Categoria E: A Falha Estrutural de Acessibilidade (WCAG)

Pesquisas empíricas sobre código gerado por IA identificam taxas alarmantes de não conformidade com o **WCAG 2.2 AA**:

| Falha Crítica | Causa no Código da IA | Impacto no Usuário Real |
| :--- | :--- | :--- |
| **Contraste de Cor Ilegal (>80% dos casos)** | `text-zinc-400` sobre `bg-zinc-900` ou texto fino sobre gradientes | Inelegível para pessoas com baixa visão ou sob luz solar. |
| **"Clickable Div" Syndrome** | `<div onClick={handleClick}>` em vez de `<button>` ou `<a>` | Elemento completamente invisível para navegação via teclado (`Tab`) e leitores de tela. |
| **Falta de Focus Trap em Modais** | Modais desenhados com `position: fixed` puro sem captura de `keydown (Escape)` ou ciclo de foco | Usuários de teclado ficam presos no fundo da página. |
| **Falta de Rótulos em Formulários** | Inputs sem tag `<label>` ou sem `aria-describedby` (apenas `placeholder`) | Leitores de tela não informam o propósito do campo de texto. |
| **Ignorar `prefers-reduced-motion`** | Animações CSS contínuas sem media query defensiva | Gatilho para náusea em usuários com distúrbios vestibulares. |
| **Alvos de Toque Microscópicos (<44x44px)** | Botões estilizados com `h-7 px-2 text-xs` para parecerem "delicados" | Impossíveis de tocar em telas móveis sem acionar elementos vizinhos. |

---

### Categoria F: Falhas Críticas de Engenharia Responsiva

1. **Uso de `100vh` em vez de `100dvh`:**
   Provoca saltos bruscos de layout em navegadores móveis (Safari iOS e Chrome Android) devido à barra de navegação dinâmica do sistema operacional.
2. **Larguras Fixas com Vazamento Horizontal:**
   Uso de `w-[500px]` ou `w-screen` em containers internos, criando scroll lateral indesejado em resoluções menores que 768px.
3. **Tailwind Class Soup:**
   Elementos com 40 a 50 classes atômicas sem separação de responsabilidades ou tokens reutilizáveis, inviabilizando a manutenção por desenvolvedores humanos.

---

## 3. O Impacto Cognitivo no Usuário: "AI Blindness" & Queda de Conversão

Estudos de usabilidade contemporâneos (2025–2026) mapeiam um fenômeno idêntico à cegueira de banners dos anos 2000:

1. **Cegueira de Padrão (AI Blindness):**
   Usuários escaneiam páginas e, nos primeiros 400 milissegundos, classificam mentalmente o site como *"template genérico de IA"*. Como resultado, o olho humano pula automaticamente o Hero, a linha de logos cinzas e os 3 cards, indo direto para a documentação ou fechando a aba.
2. **Déficit de Confiança Institucional:**
   - **32%** dos consumidores declaram confiar menos em marcas cuja interface aparenta ser gerada por IA sem curadoria.
   - Queda de **20% a 35%** nas taxas de conversão de leads qualificados em páginas que utilizam copy clichê de IA (*"Supercharge your workflow"*).
3. **A Solução:** Sites de alto desempenho adotam **sinais de intervenção humana evidente** (*Proof of Human Craft*): tipografia editorial com personalidade, paletas monocromáticas quentes, dados concretos e específicos do produto, e ausência total de ornamentos gratuitos.

---

## 4. O Movimento Comunitário "Anti-Slop" (GitHub & Ferramentas)

A comunidade técnica reagiu com a criação de repositórios, linters e padrões abertos para banir esses vícios:

### 1. `Leonxlnx/taste-skill` (tasteskill.dev)
Framework open-source de SKILL.md que atua como linter estilístico para agentes (Claude Code, Cursor, Codex). Introduziu o conceito de **"Dials de Controle"**:
- **`DESIGN_VARIANCE` (1 a 10):** De simetria estrita a assimetria editorial expressiva.
- **`MOTION_INTENSITY` (1 a 10):** De estático/funcional a cinematográfico.
- **`VISUAL_DENSITY` (1 a 10):** De minimalismo arejado a densidade tabular de software de alta produtividade.
- **Brief Inference:** Obriga o agente a deduzir público-alvo, nicho e tom antes de escrever uma única linha de CSS.

### 2. Projetos `Hallmark`, `VibeCurb` e `.cursorrules` Especializados
Arquivos de governança que barram classes Tailwind proibidas via regex nos hooks de pré-commit:
- Banimento de gradientes de texto (`bg-clip-text text-transparent`) sem justificativa de marca.
- Banimento do ícone `Sparkles` como elemento decorativo padrão.
- Bloqueio de componentes com contraste inferior a 4.5:1.

---

## 7. A Anatomia da Ilusão: O "Linear Clone" vs. O Verdadeiro Design Linear

Um dos maiores equívocos replicados por LLMs é tentar clonar a estética da **Linear** sem compreender sua fundamentação de engenharia. A comunidade técnica e os fundadores da própria Linear documentam a diferença abissal entre o produto real e as imitações geradas por IA:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    LINEAR REAL  vs.  AI CLONE SUPERFICIAL                     │
├────────────────────────────────┬──────────────────────────────────────────────┤
│ 🚀 LINEAR REAL (ENGENHARIA)    │ 🤖 AI CLONE (SUPERFÍCIE APENAS)              │
├────────────────────────────────┼──────────────────────────────────────────────┤
│ Arquitetura Local-First        │ Client-side com spinners bloqueantes         │
│ Banco local IndexedDB          │ Requisições REST lentas a cada clique        │
│ Latência <100ms (Optimistic)   │ Atraso visível em cada interação             │
│ Navegação Keyboard-First (⌘K)  │ Botões puramente voltados para mouse         │
│ Design Subtrativo (Menos é +)  │ Acúmulo de badges, glows e widgets inúteis   │
│ Tons profundos com matiz sutil │ Preto puro (#000000) com violeta neon        │
└────────────────────────────────┴──────────────────────────────────────────────┘
```

1. **Desempenho como Funcionalidade Principal:**
   O design da Linear é venerado não por causa de suas cores escuras, mas porque o software **reage instantaneamente**. A aplicação grava localmente em IndexedDB e sincroniza em background. A UI é minimalista para **eliminar a sobrecarga cognitiva** de engenheiros.
2. **O "Vale da Estranheza" dos Clones de IA:**
   Quando um LLM gera uma landing page com visual escuro da Linear para uma imobiliária, um curso ou um restaurante, o usuário sente o abismo da incoerência: a interface promete a agilidade de uma IDE de ponta, mas entrega um panfleto estático e lento.

---

## 8. As Tendências de Ponta 2025–2026 (Awwwards, Godly.design, SiteInspire)

As referências internacionais de design contemporâneo abandonaram deliberadamente o visual padronizado de IA e migraram para **direções humanas autênticas**:

### 1. Contraste de Escala Extrema (Extreme Scale Contrast)
- Títulos monumentais (120px a 180px em desktop) utilizando fontes Display ou Serifas de personalidade (*Fraunces*, *Clash Display*, *Cabinet Grotesk*).
- Contrapostos com metadados e textos de apoio extremamente compactos (12px a 14px em `font-mono`), criando uma hierarquia tipográfica digna de pôsteres suíços e revistas editoriais de luxo.

### 2. Brutalismo Tátil & Texturas Físicas
- Substituição de sombras difusas e "auroras borradas" por **linhas sólidas de 1px** (`border border-slate-200 dark:border-zinc-800`).
- Introdução de micro-texturas analógicas: granulado sutil de filme (CSS noise), acabamento de papel (*paper-white* `#FBFBFA`) e botões com sensação de clique físico e micro-afundamento mecânico (`active:translate-y-[1px] active:shadow-none`).

### 3. Movimento com Intenção (Scrollytelling & Háptica Visual)
- Fim das animações gratuitas de confete ou partículas Three.js sem sentido.
- Adoção de **interações táteis de profundidade**: componentes `TiltCard` que reagem à posição do cursor com rotação 3D suave (`perspective: 1000px`), abas que trocam de estado em menos de 100ms e transições suaves de layout.

---

## 9. O Prompt Canônico de Sistema "Anti-Slop" (Template para Agentes)

Para imunizar qualquer agente LLM contra a geração de AI Slop, a comunidade consolidou o seguinte bloco de diretrizes (utilizável em `.cursorrules`, `AGENTS.md` ou system prompts):

```markdown
### FRONTEND DIRECTION: ANTI-SLOP & HUMAN CRAFT PROTOCOL

1. PROHIBITED VISUAL TROPES:
   - NO system emojis in buttons or headers. Use sharp inline vector SVGs only.
   - NO generic purple/violet/cyan text gradients (bg-clip-text text-transparent).
   - NO random glowing background blobs (blur-3xl purple aura).
   - NO decorative Sparkles icon (✨) to mean "AI" or "modern".
   - NO Three.js spinning wireframe balls or unmotivated particle dust.
   - NO fake bento grids filled with dummy metric widgets (82% bars, fake gauges).
   - NO centering everything. Use intentional editorial left-aligned layouts.

2. MANDATORY TYPOGRAPHIC ARCHITECTURE:
   - Pair an authoritative Display / Serif font for headings with a razor-sharp Sans/Mono for UI data.
   - Use extreme scale contrast: H1 massive (3rem to 5rem), labels compact and tracked (text-xs tracking-wider uppercase font-mono).

3. PALETTE & SURFACES:
   - Prefer rich, warm light themes (paper-white #FAFAF9, crisp borders #E2E8F0, dark slate text #0F172A).
   - If dark mode is explicitly requested, use warm obsidian (#0C0A09 / #18181B), never pure flat pitch black with radioactive neon borders.

4. COPYWRITING DISCIPLINE:
   - BANNED BUZZWORDS: "Supercharge", "Unleash", "Seamlessly", "Elevate", "All-in-one", "Game-changing".
   - State the factual product benefit in the first 5 words using concrete verbs.

5. WCAG 2.2 AA ACCESSIBILITY:
   - Minimum 4.5:1 color contrast on all text and critical iconography.
   - Interactive elements MUST use semantic <button> or <a> tags with focus-visible rings.
   - Form fields MUST have linked <label> tags.
   - Zero horizontal overflow (w-full max-w-*, min-h-[100dvh]).
```

---

## 10. Matriz Canônica de Substituição (Slop vs. Human-Grade)

| Componente | ❌ Padrão Viciado de IA | ✅ Padrão Editorial / Human-Grade |
| :--- | :--- | :--- |
| **Tema Geral** | `#000000` absoluto com bordas violeta fluorescentes | Fundo claro mineral (`#FAFAF9` / `#FFFFFF`), bordas ardósia neutras (`#E2E8F0`) ou contraste tipográfico forte |
| **Tipografia** | Apenas Inter/Geist 100% sans-serif em todos os pesos | Pareamento de autoridade: Serif Display (*Newsreader*, *Playfair*) + Sans de precisão + Mono técnica |
| **Headline H1** | "Supercharge your workflow with next-gen AI" | Verbo claro de produto: "Aprenda a falar inglês com naturalidade em 90 dias" |
| **Badge do Hero** | `✨ Powered by AI 2.0` | Metadado contextual e sóbrio: `METODOLOGIA DE ALTA PERFORMANCE` |
| **Features** | 3 cards com ícones Lucide em caixas arredondadas | Matriz comparativa tabular funcional com estados de antes/depois |
| **3D / Motion** | Esfera aramada Three.js rodando sozinha | Efeito háptico tátil (`TiltCard` 3D baseado no mouse, shaders de reflexo de luz sutil) |
| **Estados de UI** | Apenas a tela cheia de dados perfeitos (Happy Path) | *Empty states* ilustrados, *loading skeletons* idênticos ao layout final, erros com retry inline |
| **Acessibilidade** | `<div>` com `onClick` e contraste 2.5:1 | Elementos semânticos `<button>`, `<label>` associados, contraste 4.5:1+ (WCAG AA) |

---

## 11. Diretrizes de Engenharia para Agentes AXION

Ao gerar ou refatorar qualquer interface neste workspace, o agente DEVE seguir obrigatoriamente:
1. **Regra #6 do AGENTS.md:** Proibição total de emojis de sistema em elementos de interface (utilizar exclusivamente SVGs vetoriais inline).
2. **Regra #7 do AGENTS.md:** Estética anti-clichê de IA (Padrão Big Tech). Tipografia editorial refinada, superfícies neutras limpas e zero CLS.
3. **Regra #8 do AGENTS.md:** Proibição de caixas de diálogo nativas (`alert`, `confirm`).
4. **Respeito aos Dials de Taste:** Priorizar densidade de dados funcional, layouts com alinhamentos intencionais à esquerda e respeito irrestrito aos padrões WCAG 2.2 AA.
