---
name: pdf-generation-puppeteer
description: >-
  Operational engineering skill for generating pixel-perfect PDF invoices, contracts, and analytics reports from HTML/CSS using headless Chrome print styles and Puppeteer/Playwright.
---

# Pixel-Perfect PDF Generation Engineering Skill

Guia operacional para renderização determinística de documentos imprimíveis (faturas, relatórios analíticos, contratos com valor legal) a partir de HTML/CSS com headless Chromium.

---

## 1. Regras de Estilização com CSS Paged Media

### 1.1 Configuração Base de Página (`@page`)
```css
@page {
  size: A4 portrait;
  margin: 15mm 20mm 20mm 20mm; /* Top, Right, Bottom, Left */
}

/* Evitar margens padrão do body do browser */
body {
  margin: 0;
  padding: 0;
  -webkit-print-color-adjust: exact; /* Força impressão de backgrounds coloridos */
  print-color-adjust: exact;
  font-family: 'Inter', sans-serif;
}
```

### 1.2 Controle de Quebras de Página (Page Breaks)
- **Tabelas sem Linhas Cortadas**:
  ```css
  table {
    width: 100%;
    border-collapse: collapse;
  }
  tr, blockquote, .card {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  thead {
    display: table-header-group; /* Repete o cabeçalho da tabela se ela quebrar para a próxima página */
  }
  ```
- **Blocos de Assinatura e Totalizadores**:
  ```css
  .signature-block, .invoice-summary {
    break-inside: avoid;
  }
  .page-break {
    break-after: page;
    page-break-after: always;
  }
  ```

---

## 2. Padrão Canônico de Execução Puppeteer

```typescript
import puppeteer from 'puppeteer';

export async function generatePdfFromHtml(htmlContent: string): Promise<Buffer> {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage', // Previne crashes de memória compartilhada em Docker
    ],
  });

  try {
    const page = await browser.newPage();
    await page.setContent(htmlContent, {
      waitUntil: 'networkidle0', // Aguarda carregamento de assets externos
    });

    // 1. Aguardar conclusão do carregamento de webfonts
    await page.evaluateHandle('document.fonts.ready');

    // 2. Renderizar PDF
    const pdfBuffer = await page.pdf({
      format: 'A4',
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate: `
        <div style="font-size: 8px; color: #71717a; width: 100%; text-align: right; padding-right: 20mm;">
          Página <span class="pageNumber"></span> de <span class="totalPages"></span>
        </div>
      `,
      margin: {
        top: '15mm',
        bottom: '20mm',
        left: '15mm',
        right: '15mm',
      },
    });

    return Buffer.from(pdfBuffer);
  } finally {
    await browser.close();
  }
}
```

---

## 3. Segurança e Sandboxing

1. **Proibição de `--disable-web-security`**: Nunca ative este parâmetro, pois ele permite que scripts HTML maliciosos carreguem arquivos do sistema operacional host (`file:///etc/passwd` ou `file:///C:/Windows`).
2. **Sanitização de HTML Injetado**: Sempre sanitize variáveis de template antes de interpolá-las no HTML para evitar ataques XSS na renderização headless.

---

## 4. Ferramental Integrado

Audite templates HTML/CSS ou scripts Puppeteer com o linter embutido:
```powershell
python .agents/skills/pdf-generation-puppeteer/scripts/pdf_template_linter.py <template.html-ou-script.ts>
```
O linter valida:
- Regras `@page` ausentes ou sem dimensões.
- Tabelas e blocos de assinatura sem `break-inside: avoid`.
- Scripts Puppeteer sem espera por fontes ou com flags inseguras.
