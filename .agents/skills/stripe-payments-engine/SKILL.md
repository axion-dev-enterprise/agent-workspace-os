---
name: stripe-payments-engine
description: >-
  Operational skill for integrating Stripe, Pix, and multi-gateway fintech billing architectures,
  cryptographic webhook verification, strict idempotency keys, and payment state machines.
---

# Fintech Payments & Billing Engine — Master Skill

Skill operacional canonica para design, integracao e governanca de sistemas financeiros, cobrancas recorrentes, processamento de webhooks criptografados e arquitetura de pagamentos globais (Stripe) e locais (Pix / Asaas / Mercado Pago).

---

## 1. Topologia Multi-Gateway & Domínios de Pagamento

| Provedor / Modalidade | Escopo Geográfico | Liquidação | Caso de Uso Canônico |
| :--- | :--- | :--- | :--- |
| **Stripe** | Global / Internacional | D+2 a D+7 | Cartões internacionais, Apple Pay, Google Pay e faturamento SaaS em USD/EUR. |
| **Pix (Banco Central / Asaas)** | Brasil (BRL) | D+0 (Instantâneo) | Liquidação em tempo real, QR Code dinâmico, checkout local sem fricção. |
| **Cartão de Crédito Nacional** | Brasil (BRL) | D+14 a D+30 | Vendas parceladas com split de recebíveis para merchants. |

---

## 2. A Lei de Ferro da Idempotência em Cobranças

> **"NENHUMA MUTACAO FINANCEIRA DEVE SER DISPARADA SEM UMA IDEMPOTENCY-KEY UNICA E DETERMINISTICA."**

- Em caso de timeout de rede na chamada HTTP com o gateway adquirente, retries sem chave de idempotência causam **cobrança dupla imediata** no cartão do cliente.
- **Estrutura Canônica da Chave**: Combine a ação de negócio, o identificador do recurso, o ciclo de faturamento e uma entropia única:
  ```typescript
  // Exemplo para assinatura mensal:
  const idempotencyKey = `sub_${subscription.id}_cycle_${cycleNumber}_${crypto.randomUUID()}`;
  
  await stripe.charges.create(
    { amount: amountCents, currency: 'brl', customer: customerId },
    { idempotencyKey }
  );
  ```

---

## 3. Máquina de Estados Finita de Transações (FSM)

Transações financeiras devem obedecer a transições de estado estritas. **Estados terminais são irreversíveis**:

```
                 ┌───────────┐
                 │  PENDING  │
                 └─────┬─────┘
          ┌────────────┴────────────┐
          ▼                         ▼
   ┌─────────────┐           ┌─────────────┐
   │    PAID     │           │   FAILED    │ (Terminal)
   └──────┬──────┘           └─────────────┘
          ├─────────────────────────┐
          ▼                         ▼
   ┌─────────────┐           ┌─────────────┐
   │  REFUNDED   │           │ CHARGEBACK  │ (Terminal)
   └─────────────┘           └─────────────┘
```

### 3.1 Proteção Contra Ressurreição por Webhooks Tardios
Se um webhook de `PAID` chegar após uma transação ter sido marcada como `CANCELED` ou `FAILED`:
```typescript
export async function processPaymentWebhook(event: WebhookEvent) {
  const current = await db.transaction.findUnique({ where: { id: event.txId } });

  // Se ja estiver em estado terminal irreversiveis, responda ACK HTTP 200 sem alterar o banco
  if (['FAILED', 'EXPIRED', 'REFUNDED', 'CHARGEBACK'].includes(current.status)) {
    logger.warn(`Ignorando evento tardio ${event.type} para transacao em estado terminal: ${current.status}`);
    return { ack: true, status: 'ignored_terminal_state' };
  }

  // Prossegue com a atualizacao segura
  await db.transaction.update({
    where: { id: event.txId },
    data: { status: 'PAID', paidAt: new Date() }
  });
}
```

---

## 4. Verificação Criptográfica de Assinatura de Webhook

Nunca confie no corpo (`body`) de um webhook sem validar a assinatura criptográfica HMAC-SHA256 usando o payload bruto (`rawBody` em Buffer):

```typescript
import Stripe from 'stripe';

export function verifyStripeWebhook(rawBody: Buffer, signatureHeader: string, secret: string): Stripe.Event {
  // A funcao do SDK valida automaticamente o HMAC e rejeita timestamps com delta > 300 segundos (Anti-Replay Attack)
  return stripe.webhooks.constructEvent(rawBody, signatureHeader, secret);
}
```

---

## 5. Invariantes de Valores Monetários: Proibição de Floats

- **Nunca utilize tipos `float` ou `double` para manipular dinheiro**: Erros de arredondamento IEEE 754 (ex: `0.1 + 0.2 === 0.30000000000000004`) acumulam discrepâncias contábeis graves.
- **Unidade Canônica Obrigatória**: Armazene e compute todo valor financeiro como **inteiro em centavos (`amountCents`)**:
  ```typescript
  // R$ 149,90 -> 14990 centavos
  const priceCents = 14990;
  const platformFeeBps = 199; // 1.99% em basis points
  const feeCents = Math.round((priceCents * platformFeeBps) / 10000);
  const netAmountCents = priceCents - feeCents;
  ```

---

## 6. O Utilitário CLI Standalone (`scripts/webhook_signer.py`)

A skill inclui um gerador de assinaturas HMAC e despachador de webhooks para testes locais e pipelines de CI:

```bash
# Simular envio de webhook assinado localmente para endpoint de desenvolvimento
python .agents/skills/stripe-payments-engine/scripts/webhook_signer.py --url http://localhost:3000/api/webhooks/stripe --secret whsec_test_secret_12345 --event checkout.session.completed --amount-cents 10000

# Gerar exemplo de assinatura Stripe-Signature no console
python .agents/skills/stripe-payments-engine/scripts/webhook_signer.py
```

---

## 7. Portão de Verificação (Verification Gate)

1. Toda chamada de criação de cobrança ou sessão de checkout deve conter parâmetro explícito de `idempotencyKey`.
2. Handlers de webhook devem rejeitar requisições com assinatura inválida com `HTTP 400 Bad Request` antes de ler o JSON.
3. Todo campo de moeda no banco de dados e APIs deve usar sufixo explícito `Cents` (`amountCents`, `feeCents`).
