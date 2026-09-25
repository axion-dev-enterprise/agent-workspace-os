---
name: pdf-generation-puppeteer
description: >-
  Operational skill for generating pixel-perfect PDF invoices, contracts, and analytics reports from HTML/CSS using headless Chrome print styles.
---

# Pixel-Perfect PDF Generation Skill

Skill operacional para geração automatizada de relatórios comerciais, contratos e faturas em PDF de alta qualidade.

## 1. Princípios de Estilização para Impressão
- **CSS Paged Media**:
  ```css
  @page {
    size: A4;
    margin: 20mm;
  }
  .page-break {
    page-break-after: always;
  }
  ```
- **Puppeteer Flags**: Executar com `--no-sandbox` e aguardar `networkidle0` para garantir que fontes do Google e imagens estejam 100% carregadas antes do print.
