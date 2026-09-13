---
name: ui-anti-cliche-design
description: Diretrizes de UI/UX minimalista padrão Big Tech (Google, Stripe, Linear). Proíbe estética clichê de IA, gradientes radioativos e emojis como ícones.
---

# UI/UX Anti-Cliché Design Skill

## Proibições Estritas
- PROIBIDO usar emojis de sistema (🚀, ⚙️, 🧠, 📊) como ícones visuais em botões, tabelas e menus.
- PROIBIDO usar estética clichê "cara de IA": fundos roxos/rosas neon, animações psicodélicas, robôs flutuantes e badges de estrelas ("✨ Powered by AI").
- PROIBIDO usar `alert()`, `confirm()` ou `prompt()` nativos do navegador.

## Padrão Recomendado
- **Ícones**: Bibliotecas vetoriais SVG (Lucide, Heroicons) inline com `stroke-width: 1.5px` ou `2px`.
- **Tipografia**: Famílias neutras profissionais (`Inter`, `Roboto`, `SF Pro`, `JetBrains Mono` para dados tabulares).
- **Superfícies**: Obsidian / Zinc escuro (`#09090b`, `#121217`) com bordas sutis `1px solid rgba(255,255,255,0.08)`.
- **Transições**: Fluidas e rápidas (150ms a 200ms com curva `cubic-bezier(0.16, 1, 0.3, 1)`).
- **Loaders**: Skeleton Shimmers gradientes idênticos à geometria final para prevenir layout shift (CLS = 0).
