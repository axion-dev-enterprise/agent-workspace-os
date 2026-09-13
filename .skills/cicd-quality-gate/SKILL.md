---
name: cicd-quality-gate
description: Pipeline de qualidade e decisão Go/No-Go para agentes de IA. Valida build, typecheck, lint, logs de runtime e renderização sem erros.
---

# CI/CD Quality Gate Skill

## Quando Usar
Utilize esta skill antes de declarar qualquer tarefa de desenvolvimento como concluída, antes de criar pull requests ou antes de disparar deploys para produção.

## 5 Quality Gates Mandatórios
1. **Typecheck & Strict Lint**: Zero erros de compilação ou linter (`tsc --noEmit`, `eslint`, `biome check`, `ruff`).
2. **Runtime Logs Limpos**: Inspecionar os logs de execução e certificar zero exceções não tratadas.
3. **Validação Live Empírica**: Fazer requisições reais (`curl` ou teste em navegador) e certificar resposta HTTP 200 com HTML válido.
4. **Layout Responsivo**: Garantir ausência de barras de rolagem horizontais espúrias (`overflow-x: hidden / visible; scrollbar-width: none`).
5. **Zero Segredos Expostos**: Confirmar que nenhuma credencial ou chave privada foi incluída no commit.

## Veredito
- Se **qualquer** teste falhar: **NO-GO** (corrigir a causa raiz).
- Se **todos** passarem: **GO** (liberar para merge/deploy).
