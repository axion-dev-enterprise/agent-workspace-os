---
name: playwright-e2e-testing
description: >-
  Operational skill for cross-browser end-to-end testing with Playwright, Page Object Models, auto-waiting locators, visual regression, and CI execution.
---

# Playwright End-to-End Testing Skill

Skill operacional para garantia de qualidade e automação de testes em navegadores reais com Playwright.

## 1. Regras Canônicas
1. **Locators com Papéis Semânticos**: Priorize sempre seletores acessíveis: `page.getByRole('button', { name: 'Entrar' })` ou `page.getByLabel('E-mail')`. Evite XPaths frágeis.
2. **Auto-waiting**: Nunca use `page.waitForTimeout(5000)`. O Playwright espera automaticamente que os elementos estejam visíveis e clicáveis.
3. **Traces em Falhas**: Configurar `trace: 'on-first-retry'` para inspecionar screenshots e requisições de rede detalhadas quando um teste quebrar na esteira de CI.
