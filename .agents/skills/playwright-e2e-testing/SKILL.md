---
name: playwright-e2e-testing
description: >-
  Operational skill for cross-browser end-to-end testing with Playwright, Page Object Models,
  auto-waiting locators, visual regression, and CI execution.
---

# Playwright End-to-End Testing & Browser QA — Master Skill

Skill operacional canonica para garantia de qualidade automatizada, testes ponta a ponta (E2E), regressao visual e automacao de navegadores com **Playwright** e **TypeScript**.

---

## 1. A Lei dos Locators Acessíveis e Auto-Waiting

> **"NUNCA UTILIZE `page.waitForTimeout()` OU XPATHS FRÁGEIS."**

### 1.1 Hierarquia de Prioridade de Seletores
O Playwright prioriza locators acessíveis baseados na árvore de acessibilidade do navegador:
1. **`page.getByRole(role, { name })`**: Localiza botões, links, títulos e formulários exatamente como um usuário real ou leitor de tela interage.
2. **`page.getByLabel('E-mail')`**: Localiza inputs associados a `<label>` com atributo `for` ou aninhados.
3. **`page.getByPlaceholder('Buscar...')`**: Utilizado apenas quando não houver label semântico visível.
4. **`page.getByTestId('checkout-total')`**: Último recurso quando a semântica visual for ambígua. Nunca use classes CSS de layout (ex: `.btn-primary-2xl-flex`) que quebram com refatorações visuais.

### 1.2 O Mecanismo de Auto-Waiting
O Playwright automaticamente aguarda que os elementos satisfaçam todas as condições de ação (*Actionability Checks*):
- Visível no DOM;
- Estável (sem animações CSS ativas);
- Habilitado (não `disabled`);
- Recebendo cliques (sem elementos sobrepostos no topo do z-index).
Substitua esperas cegas (`waitForTimeout`) por asserções explícitas com auto-retry:
```typescript
// Correto: Aguarda automaticamente ate 5000ms antes de falhar
await expect(page.getByRole('alert')).toHaveText('Operacao concluida com sucesso!');
```

---

## 2. Arquitetura Page Object Model (POM) em TypeScript

Encapsule a estrutura visual das páginas em classes com métodos semânticos de negócio:

```typescript
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('E-mail');
    this.passwordInput = page.getByLabel('Senha');
    this.submitButton = page.getByRole('button', { name: 'Entrar' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, pass: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.submitButton.click();
  }

  async expectLoginError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }
}
```

---

## 3. Autenticação Global com `storageState` (Zero Login Overhead)

Fazer login pela UI antes de cada um dos 100 testes de uma suíte consome minutos preciosos e fragiliza a esteira de CI.

### 3.1 Padrão Setup de Autenticação Canônica
1. Crie um arquivo `tests/auth.setup.ts` que executa uma única vez no início da suíte:
   ```typescript
   import { test as setup } from '@playwright/test';

   setup('authenticate as merchant', async ({ page }) => {
     await page.goto('/login');
     await page.getByLabel('E-mail').fill('admin@example.com');
     await page.getByLabel('Senha').fill(process.env.TEST_PASSWORD!);
     await page.getByRole('button', { name: 'Entrar' }).click();
     await page.waitForURL('/dashboard');

     // Salva cookies e localStorage na sessao reutilizavel
     await page.context().storageState({ path: '.auth/user.json' });
   });
   ```
2. No `playwright.config.ts`, instrua os projetos de teste a utilizarem o `.auth/user.json` pré-autenticado:
   ```typescript
   use: {
     storageState: '.auth/user.json',
   }
   ```

---

## 4. Interceptação de Rede e Mocking de APIs com `page.route()`

Simule cenários adversos de borda (timeout, erro 500, gateway fora do ar) sem acionar adquirentes reais:

```typescript
test('deve exibir mensagem de erro amigavel quando o gateway retornar 502', async ({ page }) => {
  // Intercepta e simula falha HTTP 502 Bad Gateway
  await page.route('**/api/v1/payments/checkout', async (route) => {
    await route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Gateway temporariamente indisponivel.' }),
    });
  });

  await page.goto('/checkout/item-123');
  await page.getByRole('button', { name: 'Pagar com Pix' }).click();

  await expect(page.getByText('Gateway temporariamente indisponivel.')).toBeVisible();
});
```

---

## 5. Regressão Visual Determinística

Compare capturas de tela pixel a pixel com tolerância calibrada:

```typescript
test('o layout do dashboard financeiro deve corresponder ao baseline visual', async ({ page }) => {
  await page.goto('/dashboard');
  // Mascara graficos em tempo real com dados variaveis
  await expect(page).toHaveScreenshot('dashboard-baseline.png', {
    mask: [page.getByTestId('realtime-chart')],
    maxDiffPixelRatio: 0.02, // 2% de variancia permitida para anti-aliasing
  });
});
```

---

## 6. O Utilitário CLI Standalone (`scripts/playwright_runner.py`)

A skill inclui um executor de testes E2E em Python stdlib com gravação de traces:

```bash
# Executar suíte de testes Chromium em modo headless
python .agents/skills/playwright-e2e-testing/scripts/playwright_runner.py --dir apps/webapp --browser chromium

# Executar apenas testes com tag @smoke ou @critical
python .agents/skills/playwright-e2e-testing/scripts/playwright_runner.py --dir apps/webapp --grep "@critical"

# Atualizar baselines de regressão visual
python .agents/skills/playwright-e2e-testing/scripts/playwright_runner.py --dir apps/webapp --update-snapshots
```

---

## 7. Portão de Verificação (Verification Gate)

1. A suíte completa deve rodar em modo paralelo com 100% de aprovação (0 testes quebrados).
2. Em caso de falha na esteira, o arquivo `trace.zip` deve ser salvo como artefato de build para inspeção via `npx playwright show-trace`.
3. Nenhum teste deve conter esperas manuais `waitForTimeout()`.
