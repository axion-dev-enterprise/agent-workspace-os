# Fundação da Plataforma

## 1. Arquitetura alvo

```text
FLOW web + API (control plane)
  ├─ aquisição e lead
  ├─ catálogo e checkout tokenizado
  ├─ billing webhook ingress
  ├─ entitlement e provisionamento
  ├─ onboarding e estado do cliente
  └─ observabilidade e suporte
          │
          ├─ AXION Pay: tokenização, cobrança, assinatura e eventos
          └─ runtime interno: tenant, agente, Baileys e conectores
```

O FLOW é a única interface de produto nova. O domínio `agents` permanece em manutenção enquanto o runtime útil é absorvido atrás de APIs internas do FLOW.

O billing específico histórico do FLOW no AXION Pay é legado de QA. Ele não é uma alternativa de arquitetura, nem recebe novas features: o novo caminho comercial nasce em um contrato canônico, publicado e testado no AXION Pay. A base atual não impõe compatibilidade de cliente real; dados de QA são recriáveis.

## 2. Bounded contexts

| Contexto | Fonte de verdade | Responsabilidade |
| --- | --- | --- |
| Acquisition | FLOW | lead, campanha, UTM e consentimento. |
| Billing | AXION Pay | token de pagamento, assinatura, cobrança, reembolso e evento financeiro. |
| Entitlement | FLOW | direito de uso, prazo de trial, estado de conta e bloqueio. |
| Provisioning | FLOW | criar tenant, usuário admin, políticas mínimas e onboarding link. |
| Channel | Runtime FLOW | instância WhatsApp, estado da sessão, QR/pairing e política de envio. |
| Agent execution | Runtime FLOW | agente, ferramentas permitidas e evidências da execução. |

Nenhum contexto escreve diretamente na persistência de outro. Integrações usam evento assinado, API interna autenticada ou worker durável.

## 3. Modelo de estado

```text
lead → checkout_pending → entitlement_pending
                         ├─ failed
                         └─ trial_active | subscription_active
                                  → provisioning
                                  → onboarding_pending
                                  → active | suspended | cancelled
```

Estados terminais não podem ser “ressuscitados” por evento antigo. Cada transição exige `event_id`, `correlation_id`, ator, horário UTC e motivo.

## 4. Segurança obrigatória

- Checkout com campos hospedados/tokenização. O FLOW nunca recebe PAN ou CVV.
- Credenciais de serviço e chaves de webhook somente no vault/secret manager.
- Tenant comercial nasce com perfil `customer_onboarding`: deny-by-default, sem terminal, escrita de arquivos, browser privilegiado ou subagentes de infraestrutura.
- O QR é um segredo de curta duração: expor apenas Data URL autorizado; nunca `qrRaw`, socket ou caminhos de sessão.
- Todo endpoint mutável usa autenticação, autorização, validação de schema e proteção CSRF quando a sessão for baseada em cookie.
- Exclusão é substituída por desativação/tombstone; purge é uma operação administrativa posterior e auditável.

## 5. Persistência e consistência

O armazenamento JSON atual pode sustentar protótipos de processo único, mas não um domínio financeiro distribuído. Antes de várias réplicas, o domínio de billing/provisioning deve residir em SQLite WAL ou PostgreSQL com:

- unicidade em `provider + external_event_id`;
- transação para evento, entitlement, pedido e outbox;
- índice por `tenant_id`, `status`, `created_at` e `correlation_id`;
- worker que consome a outbox sem duplicar efeitos.

Enquanto ocorrer transição, deve haver writer único, lock abrangente e propagação de qualquer erro de persistência; sucesso somente depois do commit confirmado.

## 6. ADRs a aprovar

| ADR | Decisão necessária |
| --- | --- |
| ADR-01 | banco transacional do domínio billing/provisioning. |
| ADR-02 | contrato oficial e modelo de assinatura do AXION Pay. |
| ADR-03 | política de aprovação: automática, manual ou híbrida. |
| ADR-04 | autorização e ferramenta mínima do tenant comercial. |
| ADR-05 | consentimento, retenção e opt-out para WhatsApp/Meta. |

**Decisão já tomada para ADR-02:** `/v1/flow/billing/*` é legado somente de compatibilidade técnica e será desativado após o contrato genérico `POST /v1/subscriptions` passar em staging. Não há migração de contratos, trials ou assinaturas de QA para ele. O FLOW opera como merchant autenticado e correlaciona o produto por metadata validada.

## 7. Ownership mínimo

| Decisão/ação | Papel responsável | Evidência exigida |
| --- | --- | --- |
| Catálogo, preços e política de trial | Produto/Financeiro | versão do catálogo e aprovação registrada. |
| Contrato e chave de webhook do PAY | Engenharia de pagamentos | contrato assinado, teste de assinatura em staging. |
| Storage, worker e release | Engenharia de plataforma | migração, plano de rollback e health do staging. |
| Copy, consentimento e eventos Meta | Produto/Legal/Marketing | texto aprovado e matriz de consentimento. |
| Piloto, suporte e incidentes | Operações | owner de plantão, runbook e canal de escalonamento. |

Os nomes das pessoas, SLAs e janelas de mudança são decisões operacionais a preencher antes do Go/No-Go; não devem ser inferidos pelo código.
