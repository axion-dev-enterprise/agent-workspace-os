# Modern UI Motion, Transitions & Micro-Interactions Catalog

Este catálogo reúne as diretrizes arquiteturais e receitas de movimento de ponta para aplicações web da organização, combinando referências de classe mundial (**Transitions.dev**, **Godly.design**, **Animos.app**) e respeitando rigorosamente as Regras de Governança #6, #7 e #8.

---

## 1. Princípios de Movimento Editorial & Anti-Clichê (Regra #7)

1. **Curvas de Easing Profissionais**:
   - `cubic-bezier(0.16, 1, 0.3, 1)`: Spring suave sem ricochete exagerado, ideal para modais, toasts e drawers.
   - `cubic-bezier(0.22, 1, 0.36, 1)`: Curva de desaceleração controlada para expansão de cards e acordeões.
2. **Durações Controladas (150ms – 250ms)**:
   - Micro-interações devem ser quase instantâneas para não causar atrito perceptual no operador humano.
   - Duração máxima recomendada para modais e abas: 180ms – 220ms.
3. **Zero Cumulative Layout Shift (CLS = 0)**:
   - Todo componente carregado dinamicamente deve ter um Skeleton Shimmer com altura e largura exatas ao elemento renderizado.
4. **Guarda Obrigatória de Acessibilidade (`prefers-reduced-motion`)**:
   - Todo snippet CSS que declara `transition` ou `animation` DEVE conter a guarda:
     ```css
     @media (prefers-reduced-motion: reduce) {
       .t-card-resize, .t-modal-content {
         transition: none !important;
         animation: none !important;
         transform: none !important;
       }
     }
     ```

---

## 2. Receitas Canônicas

### 2.1 Modal com Backdrop Blur e Escala Suave
- Substitui `alert()` e modais nativos por painéis HTML/CSS refinados com `backdrop-filter: blur(14px)`.
- Escala de entrada: `transform: scale(0.97)` para `scale(1)` em 180ms.

### 2.2 Card Resize
- Suporta tweening em largura e altura sem quebra de fluxo com `will-change: width, height`.

### 2.3 Skeleton Shimmer to Content Reveal
- Gradiente linear cinza/zinco (`#18181b` para `#27272a`) deslizando horizontalmente.
- Desaparece em fade-in sutil (`translateY(4px)` para `0`).

### 2.4 Agent Thinking / Reasoning Indicator
- Badge discreto em tipografia mono com ponto pulsante verde/esmeralda para indicar loops de reflexão e inferência do agente.

---

## 3. Uso do Utilitário CLI
```bash
# Listar todas as receitas
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --list

# Gerar preview visual interativo em HTML
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --generate-preview temp/preview.html

# Exportar receitas em arquivos modulares
python .agents/skills/agentic-engineering-suite/scripts/motion_recipes.py --export-all apps/web/styles/transitions/
```
