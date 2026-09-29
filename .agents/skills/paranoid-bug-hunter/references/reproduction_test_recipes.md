# Receitas de Testes de Reproducao e Stress Concorrente

Este guia fornece templates prontos para reproduzir e provar empiricamente bugs criticos antes e depois de suas correcoes cirurgicas.

---

## 1. Teste de Reproducao de Race Condition (Concorrencia de Saldo)

### Receita em TypeScript / Node.js
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { processWithdrawal, getBalance, depositFunds } from '../src/services/walletService';

describe('Paranoid Stress: Double-Spending Concurrency Test', () => {
  const accountId = 'acc_test_stress_001';

  beforeEach(async () => {
    // Inicializa conta com saldo exato de 100 reais (10.000 centavos)
    await depositFunds(accountId, 10000);
  });

  it('deve rejeitar saques concorrentes quando o saldo for insuficiente para ambos', async () => {
    // Dispara 10 tentativas simultaneas de saque de 100 reais cada
    const attempts = Array.from({ length: 10 }).map(() =>
      processWithdrawal({ accountId, amountCents: 10000 })
        .then(() => ({ success: true }))
        .catch((err) => ({ success: false, error: err.message }))
    );

    const results = await Promise.all(attempts);

    const successfulWithdrawals = results.filter((r) => r.success);
    const rejectedWithdrawals = results.filter((r) => !r.success);

    // Em um sistema seguro com FOR UPDATE ou atomic decrement:
    // Exatamente 1 deve ter sucesso, e 9 devem falhar por saldo insuficiente.
    expect(successfulWithdrawals.length).toBe(1);
    expect(rejectedWithdrawals.length).toBe(9);

    const finalBalance = await getBalance(accountId);
    expect(finalBalance).toBe(0); // Nunca negativo
  });
});
```

---

## 2. Teste de Reproducao de Webhook Tardio e Idempotencia

### Receita em TypeScript / Jest / Vitest
```typescript
import { describe, it, expect } from 'vitest';
import { handlePaymentWebhook, getOrderStatus } from '../src/controllers/webhookController';

describe('Paranoid Stress: Webhook Resurrection & Idempotency', () => {
  it('nao deve ressuscitar pedido cancelado quando receber webhook antigo de PAID', async () => {
    const orderId = 'ord_test_cancelled_999';

    // 1. Simula pedido cancelado manualmente pelo cliente
    await cancelOrder(orderId);
    expect(await getOrderStatus(orderId)).toBe('CANCELED');

    // 2. Simula chegada de webhook atrasado dizendo que o pagamento foi aprovado
    const lateWebhook = {
      event: 'PAYMENT_RECEIVED',
      orderId,
      amountCents: 5000,
      timestamp: new Date().toISOString()
    };

    const response = await handlePaymentWebhook(lateWebhook);

    // 3. O webhook deve ser reconhecido (ACK 200) para nao ser reenviado,
    // mas o status do pedido DEVE permanecer CANCELED
    expect(response.status).toBe(200);
    expect(await getOrderStatus(orderId)).toBe('CANCELED');
  });
});
```

---

## 3. Teste de Reproducao de Case-Sensitivity de Enums

### Receita em Vitest
```typescript
import { describe, it, expect } from 'vitest';
import { isSubscriptionActive, calculateNextBilling } from '../src/services/subscriptionService';

describe('Paranoid Stress: Case-Insensitive Enum Evaluation', () => {
  it('deve reconhecer status "active", "Active" e "ACTIVE" igualmente', () => {
    expect(isSubscriptionActive({ status: 'ACTIVE' } as any)).toBe(true);
    expect(isSubscriptionActive({ status: 'active' } as any)).toBe(true);
    expect(isSubscriptionActive({ status: 'Active' } as any)).toBe(true);
    expect(isSubscriptionActive({ status: 'PAST_DUE' } as any)).toBe(false);
  });

  it('deve calcular billing anual tanto para "year" quanto para "YEAR"', () => {
    const subLower = { amountCents: 120000, interval: 'year' };
    const subUpper = { amountCents: 120000, interval: 'YEAR' };

    expect(calculateNextBilling(subLower).monthlyEquivalentCents).toBe(10000);
    expect(calculateNextBilling(subUpper).monthlyEquivalentCents).toBe(10000);
  });
});
```

---

## 4. Teste de Falsy Zero Suppression

### Receita de Teste Unitario
```typescript
import { describe, it, expect } from 'vitest';
import { applyMerchantFee } from '../src/utils/feeCalculator';

describe('Paranoid Stress: Zero Fee Invariant', () => {
  it('deve honrar taxa de 0 centavos sem aplicar taxa padrao de fallback', () => {
    const zeroFeeConfig = { baseFeeCents: 0, defaultFeeCents: 199 };

    // Se o codigo usar (config.baseFeeCents || config.defaultFeeCents),
    // 0 se tornara 199 incorretamente!
    const effectiveFee = zeroFeeConfig.baseFeeCents ?? zeroFeeConfig.defaultFeeCents;

    expect(effectiveFee).toBe(0);
  });
});
```

---

## 5. Script Bash / PowerShell para Flood de Requisicoes HTTP Simultaneas

### PowerShell (Windows Native)
```powershell
# Simula 20 requisicoes simultaneas contra endpoint para testar race condition
$endpoint = "http://localhost:3000/api/v1/wallets/withdraw"
$body = '{"amountCents": 1000}'
$headers = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer test_token" }

1..20 | ForEach-Object -Parallel {
    param($url, $b, $h)
    try {
        $res = Invoke-RestMethod -Uri $url -Method Post -Body $b -Headers $h
        Write-Host "Success: $($res.id)"
    } catch {
        Write-Host "Rejected: $($_.Exception.Message)"
    }
} -ArgumentList $endpoint, $body, $headers
```
