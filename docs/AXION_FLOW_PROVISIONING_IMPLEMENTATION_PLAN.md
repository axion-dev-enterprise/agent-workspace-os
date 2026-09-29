# AXION FLOW como Plataforma de Provisionamento

**Tipo:** plano técnico de implementação, contratos e critérios de aceite.  
**Escopo:** consolidar aquisição, trial, provisionamento e onboarding no AXION FLOW; preservar somente os serviços úteis do legado AGENTS.  
**Status:** pronto para refinamento técnico; não autoriza deploy, cobrança, envio de mensagens, alteração de DNS ou migração de dados.  
**Data:** 2026-09-27.

## 1. Decisão de produto

O AXION FLOW será o **control plane** do produto. Ele passará a concentrar a conversão comercial, o estado do trial/assinatura, a criação do tenant e o onboarding. O runtime de agentes e o Baileys continuarão como capacidades internas do FLOW, sem manter uma interface AGENTS independente para novas funcionalidades.

```text
Visitante
   │
   ▼
FLOW: landing, lead e oferta
   │
   ▼
AXION Pay: tokenização, trial/assinatura e webhook assinado
   │
   ▼
FLOW: provisionamento idempotente do tenant
   │
   ▼
FLOW: onboarding autenticado → WhatsApp → primeiro valor
```

`agents.example.com` deve ser tratado como legado: congelar features, preservar runtime e dados necessários e migrar a experiência por etapas. Nenhum redirecionamento, desligamento ou exclusão faz parte deste plano sem inventário e autorização específicos.

## 2. Componentes existentes a reutilizar

| Capacidade | Evidência no FLOW | Reuso proposto |
| --- | --- | --- |
| SSO e sessão federada | `services/central_auth.js`, `middleware/tenant_auth.js`, rotas `/api/v1/auth/sso/*` | Identidade do comprador e administrador do tenant. |
| Onboarding de conta | `/api/v1/auth/onboarding/status` e `/api/v1/auth/onboarding/setup` | Base para o wizard pós-trial; separar aprovação humana de ativação paga. |
| Provisionamento de tenant | `services/database.js` (`provisionTenantDb`) e rotas administrativas | Reaproveitar internamente, sem expor a função administrativa ao browser. |
| Isolamento | `tenantAuthMiddleware`, `allowedTenants`, conectores e instâncias por tenant | Garantir que todo novo recurso tenha `tenant_id` obrigatório. |
| WhatsApp multi-instância | `services/baileys_manager.js`, QR, sessão em disco e estado por tenant/instância | Usar no onboarding, com API sanitizada e consentimento explícito. |
| Guardrails e evidências | `services/guardrails/*`, `services/qa/*` | Cobrir provisionamento, webhooks e mensagens com auditoria. |

## 3. Limites de responsabilidade

| Domínio | Responsável | Não pode fazer |
| --- | --- | --- |
| FLOW | Lead, identidade, tenant, onboarding, estado de ativação | Processar PAN/CVV, guardar segredos de campanha no browser ou cobrar diretamente. |
| AXION Pay | Tokenização, cobrança, assinatura, reembolso e webhook de pagamento | Criar tenant sem pedido autenticado ao FLOW. |
| Runtime de agente | Executar a política e ferramentas daquele tenant | Acessar dados, sessões ou conectores de outro tenant. |
| Baileys | Estado da conexão e transporte de mensagens | Disparar mensagem comercial sem opt-in, limite e consentimento registrados. |

## 4. Estados canônicos

### 4.1 Lifecycle comercial e de provisionamento

```text
lead
 └─ checkout_pending
     ├─ checkout_failed
     └─ trial_authorized | subscription_active
          └─ provisioning
               ├─ provisioning_failed (recuperável)
               └─ onboarding_pending
                    ├─ channel_pending
                    ├─ active
                    └─ cancelled
```

Regras:

- Toda transição é registrada como evento imutável com `event_id`, `tenant_id` quando disponível, `correlation_id` e horário UTC.
- Uma reentrega do mesmo webhook deve retornar sucesso sem recriar assinatura, lead, tenant ou instância.
- `active` exige tenant provisionado e onboarding mínimo concluído; conexão WhatsApp é configurável conforme a modalidade do produto, não um pressuposto universal.

### 4.2 Modalidades iniciais

| Código | Produto | Cobrança inicial | Após 30 dias |
| --- | --- | --- | --- |
| `bring_your_number` | Cliente conecta número próprio | Trial da plataforma | Cobrança do plano contratado |
| `dedicated_number` | Linha/número dedicado fornecido | Componente da linha conforme catálogo aprovado | Plataforma + componente da linha conforme contrato |

Valores, moedas, prazo e política de cancelamento devem vir de um catálogo versionado do PAY; não devem ser fixados na UI.

## 5. Contratos de API

Todos os endpoints mutáveis exigem autenticação, validação de payload, `Idempotency-Key` quando criam estado e retornam erros no formato RFC 7807. IDs são opacos; o frontend não escolhe `tenant_id` definitivo.

### 5.1 Criar solicitação de provisionamento

`POST /api/v1/internal/provisioning/requests`

**Chamador:** somente AXION Pay ou worker interno autenticado por credencial de serviço e assinatura.  
**Idempotência:** `Idempotency-Key` único por `payment_event_id`.

```json
{
  "schema_version": 1,
  "payment_event_id": "evt_pay_01J...",
  "customer": {
    "external_customer_id": "cus_01J...",
    "email": "admin@empresa.example",
    "name": "Responsável da empresa"
  },
  "entitlement": {
    "product_code": "bring_your_number",
    "status": "trial_authorized",
    "starts_at": "2026-09-27T19:00:00Z",
    "trial_ends_at": "2026-10-27T19:00:00Z"
  },
  "lead_id": "lead_01J...",
  "correlation_id": "cor_01J..."
}
```

**Resposta `202 Accepted`:**

```json
{
  "request_id": "prv_01J...",
  "status": "provisioning",
  "correlation_id": "cor_01J..."
}
```

### 5.2 Consultar estado de ativação

`GET /api/v1/activation/status`

**Chamador:** administrador autenticado do tenant ou sessão de onboarding de uso único.

```json
{
  "tenant_id": "acme-01j",
  "activation_status": "onboarding_pending",
  "entitlement_status": "trial_authorized",
  "next_step": "connect_whatsapp",
  "onboarding_url_expires_at": "2026-09-27T20:00:00Z"
}
```

### 5.3 Criar vínculo de onboarding

`POST /api/v1/internal/onboarding-links`

Gera um token aleatório, de uso único, com expiração curta e hash persistido. O token nunca é armazenado em texto claro e nunca aparece em telemetria.

### 5.4 Criar instância WhatsApp

`POST /api/v1/onboarding/whatsapp/instances`

```json
{
  "display_name": "Atendimento ACME",
  "operating_mode": "copilot",
  "consent_to_connect": true,
  "consent_to_test_message": false
}
```

**Resposta:** somente `instance_id`, estado e `qr_code_data_url` de curta duração. Nunca retornar `qr_raw`, credenciais Baileys ou caminhos de disco.

### 5.5 Solicitar pairing code e consultar conexão

`POST /api/v1/onboarding/whatsapp/instances/{instance_id}/pairing-code`  
`GET /api/v1/onboarding/whatsapp/instances/{instance_id}/connection`

O número informado é normalizado e mantido apenas pelo tempo operacional necessário. O polling tem rate limit; o frontend prefere SSE autenticado para transições de estado.

### 5.6 Webhook do PAY

`POST /api/v1/webhooks/axion-pay`

Obrigatório: verificação HMAC sobre payload bruto, timestamp com janela de tolerância, identificador de evento persistido antes do processamento e resposta segura a replay. Eventos mínimos: `checkout.authorized`, `trial.activated`, `subscription.active`, `payment.failed`, `subscription.cancelled`.

## 6. Persistência e schemas internos

O repositório atual mantém estruturas em `services/database.js`. Para a primeira entrega, os novos registros devem ser adicionados sob um único writer atômico. Antes de múltiplas réplicas/containers, migrar esses registros críticos para SQLite/PostgreSQL com transações e índice único de idempotência.

```json
{
  "provisioning_requests": {
    "prv_01J...": {
      "id": "prv_01J...",
      "idempotency_key_hash": "sha256:...",
      "payment_event_id": "evt_pay_01J...",
      "lead_id": "lead_01J...",
      "tenant_id": "acme-01j",
      "status": "onboarding_pending",
      "attempt_count": 1,
      "correlation_id": "cor_01J...",
      "created_at": "2026-09-27T19:00:00Z",
      "updated_at": "2026-09-27T19:00:03Z"
    }
  },
  "entitlements": {
    "tenant:acme-01j": {
      "tenant_id": "acme-01j",
      "product_code": "bring_your_number",
      "status": "trial_authorized",
      "trial_ends_at": "2026-10-27T19:00:00Z",
      "pay_subscription_id": "sub_01J..."
    }
  },
  "domain_events": [{
    "event_id": "dom_01J...",
    "type": "tenant.provisioned",
    "tenant_id": "acme-01j",
    "correlation_id": "cor_01J...",
    "occurred_at": "2026-09-27T19:00:03Z"
  }]
}
```

Dados de cartão, chaves do PAY, QR bruto, credenciais WhatsApp e token CAPI não pertencem a esse schema. Segredos ficam exclusivamente no vault/secret manager; dados de campanha devem ser criptografados e acessíveis somente ao tenant autorizado.

## 7. Backlog de implementação no repositório `axion-flow`

| Épico | Implementação principal | Arquivos esperados | Testes mínimos |
| --- | --- | --- | --- |
| E1: contrato e eventos | Normalizadores, schemas e RFC 7807 | `services/provisioning/contracts.js`, `services/domain_events.js` | validação de schema e serialização de erros |
| E2: billing ingress | Verificador de assinatura, replay guard e idempotência | `services/billing_webhook_service.js`, `server.js` | assinatura inválida, replay, ordem invertida, reentrega |
| E3: provisionamento | Worker/serviço com compensação | `services/provisioning_service.js`, `services/database.js` | criação única, falha parcial e recuperação |
| E4: entitlement | Estado de trial/assinatura por tenant | `services/entitlement_service.js`, `services/database.js` | bloqueio após expiração, cancelamento e reativação |
| E5: onboarding | Link único e wizard de estado | `services/onboarding_service.js`, `public/*` ou frontend existente | expiração, uso único, autorização e retomada |
| E6: WhatsApp | Fachada segura sobre `baileys_manager` | `services/whatsapp_onboarding_service.js`, `server.js` | isolamento, QR expirado, pairing rate limit, reconexão |
| E7: observabilidade | Ledger e métricas de ativação | `services/telemetry.js`, `services/qa/*` | correlação, redação de PII e alertas |
| E8: legado | Banner/redirect gradual e inventário de rotas AGENTS | `docs/migration/*`, camada de roteamento aprovada | regressão de sessão e plano de reversão |

## 8. Features do MVP de ativação

1. Catálogo de planos fornecido pelo PAY; sem preço hardcoded na landing.
2. Lead com origem/UTM e consentimento de analytics.
3. Checkout tokenizado incorporado, sem PAN/CVV no FLOW.
4. Webhook assinado e idempotente.
5. Tenant + usuário administrador provisionados uma vez.
6. Link de onboarding de uso único e retomada segura.
7. QR/pairing, estado em tempo real e desconexão segura por tenant.
8. Confirmação explícita antes de mensagem de teste.
9. Painel de estado: trial, data de renovação, canal, próximos passos e suporte.
10. Ledger de eventos e rastreio por `correlation_id`.

Ficam fora do MVP: migração automática de todo legado, disparo comercial em massa, automação sem revisão de opt-in, multi-canal adicional e reformulação do motor de agentes.

## 9. Critérios de aceite

### Segurança e isolamento

- [ ] Nenhuma rota interna de billing/provisionamento é chamável por browser sem credencial de serviço.
- [ ] Dois webhooks idênticos geram uma única solicitação e um único tenant.
- [ ] Um administrador não consegue consultar, trocar ou desconectar uma instância de outro tenant.
- [ ] Não há PAN, CVV, token de webhook, QR bruto, sessão Baileys ou CAPI token em logs, HTML, `localStorage` ou resposta de API.

### Produto e confiabilidade

- [ ] Trial válido produz onboarding; pagamento falho não produz tenant ativo.
- [ ] O cliente pode retomar onboarding sem duplicar recursos.
- [ ] Estados de erro orientam uma ação concreta e preservam a correlação para suporte.
- [ ] Cancelamento ou expiração altera o entitlement sem apagar dados de forma irreversível.

### Integração e qualidade

- [ ] Suítes RED/GREEN para webhook, provisionamento, isolamento e onboarding passam em staging.
- [ ] Contratos são versionados e testes de compatibilidade cobrem PAY ↔ FLOW.
- [ ] Fluxo completo em staging usa tenant e dados de teste com teardown comprovado.
- [ ] Produção só é considerada após evidência fresca de health, logs limpos e validação funcional autorizada.

## 10. Sequência de entrega e rollback

1. **Contratos e ADR:** aprovar payloads, política do trial, catálogo e ownership.
2. **Staging isolado:** criar schemas, feature flags e testes sem alterar produção.
3. **Webhook + provisionamento:** ativar apenas para um produto/piloto interno; validar idempotência e compensação.
4. **Onboarding:** habilitar para tenants piloto, sem mensagens automáticas.
5. **WhatsApp:** liberar QR/pairing por tenant aprovado e monitorar estabilidade.
6. **FLOW oficial:** migrar tráfego gradualmente; manter AGENTS somente em manutenção.

Rollback é por feature flag e estado: desabilitar novas ativações, manter tenants já criados legíveis, parar worker de provisionamento e reconciliar eventos pendentes. Nunca apagar tenant, assinatura ou sessão como estratégia de rollback.

## 11. Decisões pendentes antes da implementação

1. AXION Pay fornece tokenização hospedada, subscriptions, webhooks HMAC e ambiente de staging? Quais são os contratos oficiais?
2. A aprovação de contas do FLOW continua manual, torna-se automática após pagamento ou usa regra híbrida?
3. Qual produto/valor/catalogo é oficial para cada modalidade?
4. Qual banco transacional é aprovado para substituir o writer JSON antes de escalar réplicas?
5. Qual política de consentimento, opt-out, retenção e suporte será aplicada aos canais WhatsApp e Meta?

