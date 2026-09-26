---
name: meta-marketing-capi
description: >-
  Operational skill for Meta Graph API, WhatsApp Cloud API, and Meta Marketing / Conversions API (CAPI).
  Use when building automated marketing dispatchers, tracking conversion events server-side,
  managing WhatsApp business messaging, automating campaign insights, and generating UTM-tagged tracking URLs.
---

# Meta Marketing API, CAPI & WhatsApp Operations Skill

Skill operacional para integração, envio de conversões server-side (Meta CAPI), automação de anúncios e mensageria WhatsApp no ecossistema da **Enterprise Organization**.

---

## 1. Meta Conversions API (CAPI) Server-Side

O envio de eventos server-side via CAPI garante 100% de mensuração mesmo com bloqueadores de anúncios (adblockers) e políticas restritivas de cookies (iOS 14+).

### 1.1 Formato do Payload Canônico CAPI (v19.0+)
Endpoint: `https://graph.facebook.com/v19.0/<PIXEL_ID>/events?access_token=<ACCESS_TOKEN>`

```json
{
  "data": [
    {
      "event_name": "Purchase",
      "event_time": 1727222400,
      "action_source": "website",
      "event_source_url": "https://pay.example.com/checkout/success",
      "user_data": {
        "em": ["f660ab912ec121d1b1e928a0bb4bc61b15f5ad44d5efdc4e1c92a25e99b8e44a"],
        "ph": ["254aa248acb47dd654ca3ea53f48c2c26d641d23d7e2e93a1ec56258df7674c4"],
        "client_ip_address": "200.150.100.50",
        "client_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "fbc": "fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz",
        "fbp": "fb.1.1558571054389.1098115397"
      },
      "custom_data": {
        "currency": "BRL",
        "value": 297.00,
        "order_id": "ORD-2026-9812",
        "content_type": "product"
      }
    }
  ]
}
```

> **Atenção**: Dados sensíveis como e-mail (`em`) e telefone (`ph`) **devem sempre ser criptografados com SHA-256** em minúsculas antes do envio.

---

## 2. WhatsApp Cloud API (Envio Transacional & Templates)

Endpoint: `https://graph.facebook.com/v19.0/<PHONE_NUMBER_ID>/messages`

### 2.1 Envio de Template HSM Aprovado
```typescript
export async function sendWhatsAppTemplate({
  phoneNumberId,
  accessToken,
  recipientPhone,
  templateName,
  parameters,
}: {
  phoneNumberId: string
  accessToken: string
  recipientPhone: string
  templateName: string
  parameters: string[]
}) {
  const res = await fetch(`https://graph.facebook.com/v19.0/${phoneNumberId}/messages`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      to: recipientPhone,
      type: "template",
      template: {
        name: templateName,
        language: { code: "pt_BR" },
        components: [
          {
            type: "body",
            parameters: parameters.map((val) => ({ type: "text", text: val })),
          },
        ],
      },
    }),
  })
  return res.json()
}
```

---

## 3. Gestão e Rotação de Tokens de Longa Duração (System Users)

1. Nunca utilize tokens de usuário pessoal em servidores ou workers.
2. Crie sempre um **Usuário do Sistema** (*System User*) no Gerenciador de Negócios com papel de Admin ou Desenvolvedor de Anúncios.
3. Gere um token com validade **Nunca expira** (*Never*) marcando os escopos:
   - `ads_management`
   - `ads_read`
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
