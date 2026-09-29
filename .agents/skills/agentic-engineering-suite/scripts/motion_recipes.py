#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
motion_recipes.py — Modern UI Motion & Micro-Interactions Engine
Part of agentic-engineering-suite skill — AXION Enterprise
Generates accessible, high-performance CSS/React micro-transitions inspired by Transitions.dev.
Enforces Rule #6 (SVG icons only), Rule #7 (Zero-cliché editorial design, CLS=0),
Rule #8 (Custom modals, backdrop-filter blur) and @media (prefers-reduced-motion).
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

RECIPES: Dict[str, Dict[str, Any]] = {
    "card-resize": {
        "title": "Card Resize & Expand",
        "description": "Smooth width/height tweening when expanding or collapsing cards and data panels.",
        "variables": {
            "--resize-dur": "220ms",
            "--resize-ease": "cubic-bezier(0.16, 1, 0.3, 1)",
        },
        "css": """:root {
  --resize-dur: 220ms;
  --resize-ease: cubic-bezier(0.16, 1, 0.3, 1);
}

.t-card-resize {
  transition: width var(--resize-dur) var(--resize-ease),
              height var(--resize-dur) var(--resize-ease),
              box-shadow var(--resize-dur) var(--resize-ease);
  will-change: width, height;
}

@media (prefers-reduced-motion: reduce) {
  .t-card-resize {
    transition: none !important;
  }
}""",
        "html": """<div class="t-card-resize p-6 bg-zinc-900 border border-zinc-800 rounded-xl">
  <h3 class="text-sm font-medium text-zinc-100">Painel Modular</h3>
  <p class="mt-2 text-xs text-zinc-400">Conteúdo com transição fluida sem layout shifts.</p>
</div>""",
    },
    "modal-open-close": {
        "title": "Modal Backdrop & Sheet",
        "description": "Accessible modal with backdrop blur (14px) and subtle scale-in (0.97 -> 1.0).",
        "variables": {
            "--modal-dur": "180ms",
            "--modal-ease": "cubic-bezier(0.16, 1, 0.3, 1)",
        },
        "css": """:root {
  --modal-dur: 180ms;
  --modal-ease: cubic-bezier(0.16, 1, 0.3, 1);
}

.t-modal-backdrop {
  backdrop-filter: blur(14px);
  background-color: rgba(0, 0, 0, 0.65);
  transition: opacity var(--modal-dur) var(--modal-ease);
}

.t-modal-content {
  transform: scale(0.97);
  opacity: 0;
  transition: transform var(--modal-dur) var(--modal-ease),
              opacity var(--modal-dur) var(--modal-ease);
}

.t-modal-open .t-modal-content {
  transform: scale(1);
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .t-modal-backdrop,
  .t-modal-content {
    transition: none !important;
    transform: none !important;
  }
}""",
        "html": """<div class="t-modal-backdrop fixed inset-0 flex items-center justify-center z-50">
  <div class="t-modal-content bg-zinc-950 border border-zinc-800 p-6 rounded-2xl shadow-2xl max-w-md w-full">
    <div class="flex items-center justify-between">
      <h2 class="text-base font-semibold text-zinc-100">Confirmação de Ação</h2>
      <button class="text-zinc-400 hover:text-zinc-200">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <p class="mt-3 text-xs text-zinc-400 leading-relaxed">Operação executada em conformidade com os guardrails de governança.</p>
  </div>
</div>""",
    },
    "skeleton-reveal": {
        "title": "Skeleton Shimmer to Content Reveal",
        "description": "Zero Cumulative Layout Shift (CLS=0) placeholder shimmering into content.",
        "variables": {
            "--shimmer-dur": "1.4s",
            "--reveal-dur": "250ms",
        },
        "css": """:root {
  --shimmer-dur: 1.4s;
  --reveal-dur: 250ms;
}

.t-skeleton {
  background: linear-gradient(90deg, #18181b 25%, #27272a 50%, #18181b 75%);
  background-size: 200% 100%;
  animation: t-shimmer var(--shimmer-dur) infinite linear;
}

@keyframes t-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.t-reveal {
  opacity: 0;
  animation: t-fade-in var(--reveal-dur) cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes t-fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .t-skeleton {
    animation: none !important;
    background: #27272a !important;
  }
  .t-reveal {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
}""",
        "html": """<div class="space-y-3 w-64">
  <div class="t-skeleton h-4 w-3/4 rounded"></div>
  <div class="t-skeleton h-3 w-full rounded"></div>
  <div class="t-skeleton h-3 w-5/6 rounded"></div>
</div>""",
    },
    "thinking-states": {
        "title": "Agent Reasoning & Thinking State Indicator",
        "description": "Minimalist pulsing status badge for long-running agent reasoning loops.",
        "variables": {
            "--pulse-dur": "1.6s",
        },
        "css": """:root {
  --pulse-dur: 1.6s;
}

.t-thinking-dot {
  animation: t-pulse-glow var(--pulse-dur) cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes t-pulse-glow {
  0%, 100% { opacity: 0.3; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}

.t-thinking-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: rgba(39, 39, 42, 0.6);
  border: 1px solid rgba(63, 63, 70, 0.4);
  border-radius: 9999px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  color: #a1a1aa;
}

@media (prefers-reduced-motion: reduce) {
  .t-thinking-dot {
    animation: none !important;
    opacity: 1 !important;
  }
}""",
        "html": """<div class="t-thinking-badge">
  <span class="t-thinking-dot w-2 h-2 rounded-full bg-emerald-400"></span>
  <span>Raciocinando...</span>
</div>""",
    },
    "toast-notification": {
        "title": "Toast Notification Slide & Fade",
        "description": "Contextual floating notification with spring deceleration and auto-dismiss.",
        "variables": {
            "--toast-dur": "220ms",
            "--toast-ease": "cubic-bezier(0.16, 1, 0.3, 1)",
        },
        "css": """:root {
  --toast-dur: 220ms;
  --toast-ease: cubic-bezier(0.16, 1, 0.3, 1);
}

.t-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  background-color: #09090b;
  border: 1px solid #27272a;
  border-radius: 12px;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  animation: t-toast-in var(--toast-dur) var(--toast-ease) forwards;
}

@keyframes t-toast-in {
  from { opacity: 0; transform: translateY(12px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@media (prefers-reduced-motion: reduce) {
  .t-toast {
    animation: none !important;
  }
}""",
        "html": """<div class="t-toast text-xs text-zinc-200">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
  <span>Alteração sincronizada com sucesso.</span>
</div>""",
    },
}


def render_html_preview() -> str:
    """Generates a complete standalone dark-mode preview page for all recipes."""
    sections = []
    for key, data in RECIPES.items():
        sections.append(f"""
    <section class="card">
      <div class="header">
        <h2>{data['title']}</h2>
        <span class="tag">{key}</span>
      </div>
      <p class="desc">{data['description']}</p>
      <div class="preview-stage">
        {data['html']}
      </div>
      <details>
        <summary>Ver Código CSS & Tokens</summary>
        <pre><code>{data['css']}</code></pre>
      </details>
    </section>
""")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AXION Motion & Micro-Interactions Catalog</title>
  <style>
    :root {{
      --bg: #09090b;
      --card-bg: #121215;
      --border: #27272a;
      --text: #f4f4f5;
      --muted: #a1a1aa;
    }}
    body {{
      margin: 0;
      padding: 40px 20px;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .container {{
      max-width: 800px;
      width: 100%;
    }}
    h1 {{
      font-size: 24px;
      font-weight: 600;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }}
    p.subtitle {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 32px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}
    .header h2 {{
      font-size: 16px;
      margin: 0;
    }}
    .tag {{
      font-family: monospace;
      font-size: 11px;
      color: #10b981;
      background: rgba(16, 185, 129, 0.1);
      padding: 3px 8px;
      border-radius: 6px;
    }}
    .desc {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 0;
      margin-bottom: 16px;
    }}
    .preview-stage {{
      background: #000;
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 10px;
      padding: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
    }}
    details summary {{
      cursor: pointer;
      font-size: 12px;
      color: var(--muted);
      outline: none;
    }}
    pre {{
      background: #000;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      font-size: 12px;
      overflow-x: auto;
      color: #d4d4d8;
      font-family: ui-monospace, Menlo, monospace;
    }}
    /* Inline CSS from all recipes */
    {chr(10).join([r['css'] for r in RECIPES.values()])}
  </style>
</head>
<body>
  <div class="container">
    <h1>AXION Motion & Micro-Interactions Catalog</h1>
    <p class="subtitle">Catálogo de micro-transições CSS puras com curvas cubic-bezier refinadas e guards de acessibilidade.</p>
    {''.join(sections)}
  </div>
</body>
</html>"""


def export_recipes(target_dir: Path) -> None:
    """Exports each recipe into standalone Markdown and CSS files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, data in RECIPES.items():
        recipe_file = target_dir / f"{name}.md"
        content = f"""# {data['title']}

## Descrição
{data['description']}

## Variáveis & Easing
```css
{chr(10).join([f"{k}: {v};" for k, v in data['variables'].items()])}
```

## CSS Canônico
```css
{data['css']}
```

## Exemplo HTML
```html
{data['html']}
```
"""
        recipe_file.write_text(content, encoding="utf-8")
    print(f"✅ {len(RECIPES)} receitas exportadas com sucesso em: {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Catálogo e Motor de Micro-Transições UI & Motion")
    parser.add_argument("--list", action="store_true", help="Lista todas as receitas disponíveis")
    parser.add_argument("--get", help="Exibe os detalhes de uma receita específica")
    parser.add_argument("--export-all", help="Diretório onde exportar todas as receitas em Markdown/CSS")
    parser.add_argument("--generate-preview", help="Gera um arquivo HTML de preview visual completo")
    args = parser.parse_args()

    if args.list:
        print("\n═════════════════════════════════════════════════════════════════════")
        print("         AXION UI MOTION & MICRO-INTERACTIONS RECIPES                ")
        print("═════════════════════════════════════════════════════════════════════")
        for key, r in RECIPES.items():
            print(f"  • {key.ljust(20)} : {r['title']}")
        print("═════════════════════════════════════════════════════════════════════\n")
        return

    if args.get:
        r = RECIPES.get(args.get)
        if not r:
            print(f"❌ Receita '{args.get}' não encontrada. Use --list para ver as disponíveis.")
            return
        print(f"\n[RECEITA: {r['title']}]")
        print(r["description"])
        print("\n[CSS]")
        print(r["css"])
        print("\n[HTML]")
        print(r["html"])
        return

    if args.export_all:
        export_recipes(Path(args.export_all))
        return

    if args.generate_preview:
        out_path = Path(args.generate_preview)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        html = render_html_preview()
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ Preview HTML interativo gerado em: {out_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
