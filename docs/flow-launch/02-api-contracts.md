# Contratos de API e Eventos

## Convenções

- Prefixo: `/api/v1`.
- Payloads em JSON UTF-8; webhook valida assinatura no corpo bruto antes do parse.
- Criações usam `Idempotency-Key`; resposta repete `X-Correlation-ID`.
- Erros seguem RFC 7807: `type`, `title`, `status`, `detail`, `instance`, `trace_id`.
- APIs internas exigem credencial de serviço, audience, expiração e escopo; não usam sessão do navegador.

## 0. Baseline de contrato e integração existente

O adaptador do FLOW deve tratar a especificação publicada do AXION Pay como contrato externo. O caminho canônico é a API genérica de merchant: `POST /v1/subscriptions` com `Idempotency-Key`, `trialDays` e metadata de correlação; o FLOW registra seu destino em `POST /v1/merchant/webhooks`.

O repositório local também contém uma integração específica histórica para FLOW: `GET /v1/flow/billing`, `POST /v1/flow/billing/checkout` e `POST /v1/flow/billing/portal`. Ela usa planos com trial de 7/14/30 dias e webhooks Stripe internos, mas é legado de QA e não será migrada ou estendida. Esses endpoints e seus schemas ainda não estão no OpenAPI versionado.

P0-03 publica e valida essa superfície genérica no OpenAPI, incluindo schemas, autenticação, idempotência, eventos e fixtures de staging. A rota legada não pode ser escolhida como contrato novo.

Até essa decisão, o FLOW não assume formato de payload, identificador de entrega, timestamp ou evento de trial que não esteja documentado no contrato selecionado. Seus eventos de domínio são internos e normalizados após a validação do adaptador.

## 1. Webhook de billing

`POST /api/v1/webhooks/axion-pay`

Headers confirmados pelo dispatcher: `X-Axion-Signature: t=<unix>,v1=<hmac>` e `X-Axion-Event-Id`. O HMAC SHA-256 assina `<timestamp>.<rawBody>` e deve ser comparado em tempo constante. O segredo retornado em `POST /v1/merchant/webhooks` é mantido no vault.

```json
{
  "id": "provider-event-id-when-specified",
  "event": "subscription.created",
  "timestamp": 1790535600,
  "data": {
    "subscriptionId": "sub_opaque",
    "metadata": {
      "flow_request_id": "req_opaque",
      "product_code": "bring_your_number"
    }
  }
}
```

O contrato deve congelar fixtures reais desse envelope. Eventos implementados incluem `subscription.created`, `subscription.renewed`, `subscription.past_due`, `subscription.canceled`, `payment.succeeded` e `payment.failed`. O mapeamento inicial é: assinatura `TRIALING` confirmada → trial ativo; `subscription.renewed`/`payment.succeeded` → renovação ou ativação conforme estado persistido; `subscription.past_due` → restrição definida por política; `subscription.canceled` → cancelamento ao fim do período ou imediato conforme payload. Nenhum evento sozinho autoriza transição sem conferir o estado e a versão persistidos.

Processamento: verificar HMAC, registrar evento, identificar duplicata, criar outbox e retornar ACK. O worker executa o provisionamento; o handler HTTP não cria tenant diretamente.

### Protocolo de replay e ordem

1. A rota recebe o corpo bruto com limite de tamanho antes de qualquer parser JSON.
2. Extrai o timestamp autenticado de `X-Axion-Signature`, rejeita janela de replay expirada e compara o HMAC em tempo constante.
3. Em uma transação, tenta inserir `provider + event_id` com índice único usando o `id` do envelope, conferido com `X-Axion-Event-Id`.
4. Se já existir, responde ACK sem executar novo efeito.
5. Se o evento for novo, grava também a outbox e confirma a transação.
6. O worker decide a transição por versão/precedência de estado; evento anterior não pode desfazer estado posterior.

O handler só pode retornar sucesso depois de persistir o recibo de evento. Falha de storage deve produzir erro recuperável para que o PAY reentregue o webhook.

## 2. Solicitação interna de provisionamento

`POST /api/v1/internal/provisioning/requests`

Header obrigatório: `Idempotency-Key`; credencial de serviço com escopo `provisioning:write`.

```json
{
  "payment_event_id": "evt_opaque",
  "checkout_id": "chk_opaque",
  "product_code": "bring_your_number",
  "admin": { "email": "admin@example.com", "name": "Responsável" },
  "correlation_id": "cor_opaque"
}
```

Resposta `202`:

```json
{ "request_id": "prv_opaque", "status": "queued", "correlation_id": "cor_opaque" }
```

O worker deve ser idempotente por `payment_event_id`; se a execução já terminou, retornar o mesmo `request_id` e estado final.

## 3. Fronteira com as rotas atuais do FLOW

As novas rotas ficam sob `/api/v1` e não alteram a semântica das rotas existentes sem migração explícita:

| Rota existente | Papel atual | Papel após a entrega |
| --- | --- | --- |
| `POST /api/v1/flow/session` | cria sessão SSO do FLOW | autentica o cliente depois de entitlement/provisionamento; não cria direito de uso. |
| `GET|POST /api/v1/auth/onboarding/*` | consulta/configura onboarding administrativo | permanece compatível; o novo onboarding comercial deve ter estado e token próprios. |
| `POST /api/v1/admin/provision/*` | provisionamento administrativo/manual | não recebe webhooks nem expõe fluxo público; o worker passa por uma camada idempotente. |
| `POST /api/v1/whatsapp/*` | gestão de canal já existente | é encapsulado pela fachada de onboarding; respostas cruas não são expostas ao cliente. |

## 4. API de ativação do cliente

| Rota | Acesso | Finalidade |
| --- | --- | --- |
| `GET /activation/status` | tenant admin/onboarding token | estado e próximo passo, sem segredos. |
| `POST /onboarding/whatsapp/instances` | tenant admin | criar instância em `read_only`. |
| `POST /onboarding/whatsapp/instances/{id}/pairing-code` | tenant admin | solicitar código com rate limit. |
| `GET /onboarding/whatsapp/instances/{id}/connection` | tenant admin | DTO seguro com estado/expiração. |
| `POST /onboarding/whatsapp/instances/{id}/test-message` | tenant admin | mensagem ao próprio número, requer confirmação explícita. |

### Ciclo de vida do onboarding link

O link é criado apenas pelo worker depois do provisionamento. O banco armazena hash do token, `tenant_id`, `admin_user_id`, expiração, contador de uso e estado. A troca do token por sessão exige SSO do mesmo e-mail ou uma verificação adicional aprovada. Após consumo, o token é invalidado; retomada usa sessão autenticada, nunca reutiliza o token.

## 5. DTO seguro de conexão

```json
{
  "instance_id": "wa_opaque",
  "status": "qr_ready",
  "qr_code_data_url": "data:image/png;base64,...",
  "expires_at": "2026-09-27T19:05:00Z",
  "connected_phone_e164": null,
  "retry_after_seconds": 20
}
```

Campos proibidos: `qrRaw`, `authState`, socket, paths locais, JID interno não necessário e tokens de sessão.

## 6. Eventos de domínio

| Evento | Produtor | Consumidor | Idempotência |
| --- | --- | --- | --- |
| `lead.created` | FLOW | analytics | `lead_id` |
| `billing.entitlement_activated` | webhook worker | provisioning | evento financeiro externo |
| `tenant.provisioned` | provisioning worker | onboarding | `tenant_id + request_id` |
| `whatsapp.connected` | channel runtime | activation/analytics | `tenant_id + instance_id + connection_id` |
| `activation.completed` | onboarding | analytics/support | `tenant_id + lifecycle_version` |

## 7. Versionamento e compatibilidade

Schemas são versionados por campo `version`. Campos novos são opcionais até uma janela de migração acordada; mudança incompatível cria versão/rota nova. Fixtures de PAY e FLOW vivem em testes e são apagadas após a validação integrada.

## 8. Exemplo de erro RFC 7807

```json
{
  "type": "https://flow.example.com/problems/invalid-webhook-signature",
  "title": "Assinatura de webhook inválida",
  "status": 401,
  "detail": "A autenticação do evento não pôde ser confirmada.",
  "instance": "/api/v1/webhooks/axion-pay",
  "trace_id": "trace_opaque"
}
```

O `detail` não inclui segredo, assinatura recebida, payload integral ou stack trace.
