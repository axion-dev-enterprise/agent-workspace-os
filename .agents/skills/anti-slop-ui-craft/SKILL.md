---
name: anti-slop-ui-craft
description: >-
  Operational anti-slop frontend and UI/UX craftsmanship skill. Enforces strict prohibition of repetitive AI clichés,
  bans generic dark-mode templates, text gradients, and buzzwords, and mandates editorial typography, extreme scale contrast,
  WCAG 2.2 AA accessibility, physical micro-interactions, and real-world UI states (empty, error, loading).
---

# Anti-Slop UI & Human Craftsmanship Skill

Skill operacional canônica da **AXION Enterprise** para imunização contra interfaces genéricas geradas por IA (*AI Slop*), garantindo que qualquer aplicação ou página criada no ecossistema atinja os mais altos padrões de design editorial, conversão comercial, acessibilidade e engenharia de software humano (nível *Godly.design*, *Linear*, *Stripe Press*, *Deck Gallery*).

---

## 1. Princípio Fundamental de Imunização

Modelos de linguagem (LLMs) produzem interfaces padronizadas porque calculam a **média geométrica estatística de menor resistência** do seu dataset de treino. Sem restrições severas, todo LLM converge para o mesmo arquétipo: *fundo preto `#000000`, bordas violeta neon, gradiente roxo no H1, o ícone de estrelinha `✨`, 3 cards idênticos e centralização forçada de todo o conteúdo*.

**Esta skill proíbe categoricamente a saída padrão dos LLMs e obriga a aplicação de design intencional e human-grade.**

---

## 2. Protocolo de "Brief Inference" (Pré-Código Obrigatório)

Antes de gerar qualquer tag HTML ou classe CSS, o agente DEVE mentalmente inferir e respeitar os **Três Dials de Governança Estética**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                      OS TRÊS DIALS DE GOVERNANÇA ESTÉTICA                     │
├─────────────────────┬───────────────────┬─────────────────────────────────────┤
│ DIAL                │ ESCALA (1 a 10)   │ COMPORTAMENTO DEFINIDO              │
├─────────────────────┼───────────────────┼─────────────────────────────────────┤
│ DESIGN_VARIANCE     │ 1 (Soberbo/Clean) │ Assimetria editorial, diagramação   │
│                     │ ➔ 10 (Expressivo) │ de pôster, contraste de pesos.      │
├─────────────────────┼───────────────────┼─────────────────────────────────────┤
│ MOTION_INTENSITY    │ 1 (Estático puro) │ Feedback háptico, micro-afundamento │
│                     │ ➔ 10 (Cinemático) │ tátil, TiltCard 3D, zero confete.   │
├─────────────────────┼───────────────────┼─────────────────────────────────────┤
│ VISUAL_DENSITY      │ 1 (Arejado/Luxo)  │ Equilíbrio entre respiração e       │
│                     │ ➔ 10 (Terminal)   │ tabelas de dados de alta eficiência.│
└─────────────────────┴───────────────────┴─────────────────────────────────────┘
```

- **Padrão AXION para Landing Pages Institucionais/Educacionais:**  
  `DESIGN_VARIANCE: 7` | `MOTION_INTENSITY: 4` | `VISUAL_DENSITY: 5`
- **Padrão AXION para Dashboards B2B / Engenharia:**  
  `DESIGN_VARIANCE: 3` | `MOTION_INTENSITY: 2` | `VISUAL_DENSITY: 8`

---

## 3. Lista Negra Absoluta de Padrões de IA (BANNED TROPES)

É expressamente **PROIBIDO** gerar ou comitar qualquer um dos seguintes padrões visuais:

1. ❌ **Gradientes Fluorescentes em Texto:**  
   Proibido `bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-pink-500` (ou ciano-azul) em títulos. Títulos devem ter cores sólidas com contraste impecável.
2. ❌ **Manchas de Luz Desfocadas no Fundo (Aurora Blobs):**  
   Proibido `absolute blur-3xl bg-purple-600/20 w-96 h-96 rounded-full`. Substitua por iluminação de borda direcional ou fundos limpos com textura/ruído sutil.
3. ❌ **O Ícone de Faísca / Estrelinha (`✨` / `Sparkles`):**  
   Proibido utilizar o ícone `Sparkles` ou `✨` em botões, badges e títulos para sugerir "inteligência" ou "mágica".
4. ❌ **Falso Bento Grid Decorativo:**  
   Proibido criar grids de caixas com barras de progresso estáticas (`w-[82%]`) ou contadores fictícios desprovidos de utilidade real.
5. ❌ **Gimmicks Three.js Desconectados:**  
   Proibido instanciar esferas aramadas (`wireframe: true`) ou poeira de partículas flutuando no vazio que consumam GPU sem transmitir valor de marca.
6. ❌ **Centralização Obsessiva (`text-center` em tudo):**  
   Proibido centralizar todos os blocos de texto da página. Utilize alinhamentos intencionais à esquerda ancorados por guias visuais estruturais.
7. ❌ **Bordas Giratórias Luminosas ("Border Beam"):**  
   Proibido botões ou cards com feixe de luz rodando em gradiente cônico infinito.

---

## 4. Lista Negra de Copywriting ("AI Speak")

É terminantemente proibido utilizar o léxico clichê de marketing de IA:

| Termo Proibido | Por que é banido? | Substituição Obrigatória |
| :--- | :--- | :--- |
| **"Supercharge your..."** | Clichê #1 de IA | Verbo concreto: *"Gerencie"*, *"Aprenda"*, *"Acelere"* |
| **"Unleash the power of..."** | Frase vazia sem substância | Explicação factual do benefício em 5 palavras |
| **"Seamlessly integrate..."** | Jargão corporativo genérico | *"Conecta diretamente com Stripe e WhatsApp"* |
| **"All-in-one platform"** | Promessa vazia não verificável | Definir o escopo real e o público-alvo |
| **"Elevate your business"** | Abstração sem métrica | *"Reduza o custo de aquisição em 40%"* |
| **"99.9% Uptime / 10x Faster"** | Métricas fictícias sem auditoria | Dados factuais, casos de estudo reais ou garantias contratuais |

---

## 5. Arquitetura Tipográfica: Contraste de Escala Extrema

Para criar uma hierarquia humana refinada:
- **Títulos (H1 / H2):** Utilize fontes Display ou Serifas editoriais autoritárias (*Newsreader*, *Playfair Display*, *Fraunces*, *Cinzel*, *Clash Display*). Em desktop, o H1 deve ter presença marcante (`text-4xl sm:text-6xl lg:text-7xl font-semibold tracking-tight`).
- **Metadados e Badges:** Devem ser compactos, sóbrios e em caixa alta, preferencialmente em fonte Mono (`text-xs font-mono tracking-widest uppercase text-slate-500`).
- **Corpo de Texto:** Sans-serif de alta legibilidade (*Inter*, *Geist*, *SF Pro*), tamanho `text-base sm:text-lg`, com entrelinha confortável (`leading-relaxed`) e limitação de largura de linha para leitura (`max-w-2xl`).

---

## 6. Cores, Superfícies & Brutalismo Tátil

- **Preferência por Temas Claros Nobres (Paper White):**
  - Fundo principal: `#FFFFFF` ou mineral neutro `#FAFAF9` / `#F8FAFC`.
  - Bordas: Linhas sólidas e nítidas de 1px (`border border-slate-200`).
  - Textos: Ardósia profunda `#0F172A` (títulos) e `#334155` / `#475569` (corpo).
- **Se Tema Escuro For Mandatório:**
  - Utilize Obsidian mineral aquecido (`#0C0A09` ou `#18181B`), NUNCA preto absoluto `#000000` estéril com saturação neon.
- **Sensação Háptica e Profundidade Mecânica:**
  - Botões primários devem possuir micro-afundamento no clique (`active:translate-y-[1px] active:scale-[0.99]`).
  - Cards interativos devem utilizar elevação física discreta (`hover:border-slate-300 hover:shadow-sm transition-all duration-150`).

---

## 7. Acessibilidade Mandatória (WCAG 2.2 AA)

1. **Contraste Mínimo de 4.5:1:** Todo texto, placeholder e ícone funcional deve passar rigorosamente no cálculo de contraste contra a superfície de fundo.
2. **Semântica Estrita (Zero "Clickable Divs"):**
   - Ações que disparam mutação, modal ou lógica = `<button type="button">`.
   - Navegação para URLs externas ou internas = `<a href="...">`.
   - Todo `<button>` de ícone deve conter `aria-label` descritivo.
3. **Foco Visível para Teclado:**
   - Todos os elementos interativos devem exibir `focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-2`.
4. **Formulários e Inputs:**
   - Todo `<input>` deve ter um `<label>` correspondente via `htmlFor` ou atributo `aria-label`.
5. **Responsividade e Viewport:**
   - Altura máxima de tela móvel deve usar `min-h-[100dvh]` (Dynamic Viewport Height), NUNCA `100vh`.
   - Área mínima de toque em telas móveis: `min-h-[44px] min-w-[44px]`.
   - Zero overflow horizontal (`overflow-x-hidden` defensivo no container raiz).

---

## 8. Tratamento Obrigatório de Estados Reais

É proibido entregar interfaces que contemplem apenas o "Happy Path":
- **Skeleton Shimmers:** Ao carregar dados assíncronos, utilize skeletons que espelhem exatamente a silhueta geométrica do componente final. Proibido colocar spinners genéricos no meio do ecrã.
- **Empty States:** Quando uma lista, busca ou tabela estiver vazia, exiba um estado vazio elegante, com mensagem contextual clara e ação de recuperação recomendada.
- **Error States:** Todo erro de API ou formulário deve ser renderizado inline com explicação compreensível e botão de *"Tentar Novamente"* (`retry`).

---

## 9. Script Canônico de Auditoria

Para auditar qualquer diretório ou arquivo do workspace em busca de violações de AI Slop:

```bash
python .agents/skills/anti-slop-ui-craft/scripts/audit_ui_slop.py <caminho_do_projeto>
```
