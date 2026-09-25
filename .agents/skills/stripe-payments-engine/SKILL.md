---
name: stripe-payments-engine
description: >-
  Operational skill for integrating Stripe payments, recurring subscriptions, webhook cryptographic signature verification, customer portal, and idempotency.
---

# Stripe Payments & Subscriptions Engine Skill

Skill operacional para integração de pagamentos, cobrança recorrente e processamento de webhooks com Stripe.

## 1. Regras de Ouro
1. **Idempotência**: Sempre enviar header `Idempotency-Key` em operações de cobrança para prevenir cobranças duplicadas em caso de retry.
2. **Verificação de Webhook**: NUNCA confiar no payload do webhook sem validar a assinatura criptográfica com `stripe.webhooks.constructEvent(payload, sig, endpointSecret)`.
3. **Persistência de Customer ID**: Vincular sempre o `stripeCustomerId` ao registro do usuário no banco local.

## 2. Validador de Webhook Canônico (Node.js)
```typescript
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: "2024-06-20" });

export async function handleStripeWebhook(rawBody: Buffer, signature: string) {
  const event = stripe.webhooks.constructEvent(rawBody, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  switch (event.type) {
    case "checkout.session.completed":
      const session = event.data.object as Stripe.Checkout.Session;
      await activateSubscription(session.customer as string, session.client_reference_id!);
      break;
    case "invoice.payment_failed":
      await notifyPaymentFailed(event.data.object);
      break;
  }
  return { received: true };
}
```
