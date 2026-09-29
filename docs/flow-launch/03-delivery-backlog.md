# Backlog de Preparação e Lançamento

## Estado da execução — 2026-09-29

Legenda:

- **IMPLEMENTADO LOCALMENTE**: código e documentação existem no checkout, com validação estática; ainda requer CI, staging e revisão.
- **EM ANDAMENTO**: parte dos critérios foi implementada, mas ainda há escopo funcional obrigatório.
- **PLANEJADO**: desenho documentado, sem implementação iniciada neste ciclo.
- Nenhum cartão abaixo está marcado como concluído em produção.

## Ordem de execução

| ID | Épico | Estado | Dependência | Evidência atual / próximo gate |
| --- | --- | --- | --- | --- |
| P0-01 | Corrigir persistência e lock | **FLOW STAGING VERDE** | ADR-01 | Hardening `cf5576b` validado pelo quality gate do run `36560756085`, integrado pelo PR #147 e publicado no staging como release `23c889d4`. Health público e artifact SHA conferidos no run `36562027904`. |
| P0-02 | Perfil comercial deny-by-default | **FLOW STAGING VERDE** | nenhuma | Perfil `customer_onboarding` e grant vazio foram cobertos pela suíte do quality gate e fazem parte do release de staging `23c889d4`. Falta apenas o cenário E2E de provisioning com fixture PAY assinada. |
| P0-03 | Contrato canônico e ingress de billing | **CI VERDE — STACK STAGING PUBLICADO** | ADR-02 | Flow está em staging; AXION Pay `654df35` passou `verify-core`, `validate` e `build-and-test`. Stack isolado publicado pelo run `36605448166` (PR #152) em `https://node-arkansas-pensions-holding.trycloudflare.com`, `release=654df35` em `/health` e `openapi 3.1.0` com `POST /v1/subscriptions` e `trialDays 0..90`. Falta executar a fixture assinada PAY → FLOW. |
| P0-04 | Provisioning worker + outbox | **FLOW STAGING VERDE — FLAG OFF** | P0-01, P0-03 | Fencing, retry e concorrência passaram no gate e estão implantados, ainda desativados por padrão. Próximo gate: ingress isolado, fixture, worker e prova de criação única. |
| P0-05 | Entitlement/trial | **FLOW STAGING VERDE — E2E PENDENTE** | P0-03 | Guard compartilhado para HTTP, cron e WhatsApp está no staging `23c889d4`. Falta projetar uma entitlement real de staging e provar restrição/reconciliação ponta a ponta. |
| P1-01 | Onboarding de uso único | **PLANEJADO** | P0-04 | Cliente retoma sem duplicar recursos; implementação não iniciada. |
| P1-02 | Fachada WhatsApp segura | **PLANEJADO** | P0-02 | QR DTO, pairing code, rate limit e isolamento; implementação não iniciada. |
| P1-03 | Política de mensagens | **PLANEJADO** | P1-02, ADR-05 | Teste consentido e outbound com opt-in; implementação não iniciada. |
| P1-04 | Observabilidade e suporte | **PLANEJADO** | P0-03 | Correlação e estado existem no ledger, mas métricas/alertas não foram implementados. |
| P1-05 | Correções de UI/sessão | **PLANEJADO** | nenhuma | Auditoria anterior identificou o escopo; implementação não iniciada neste ciclo. |
| P2-01 | Cutover e retirada de QA legado | **PLANEJADO** | P1 completo | Runbook documentado; nenhuma rota/dado legado foi alterado ou excluído. |
| P2-02 | CRM/Meta CAPI | **PLANEJADO** | ADR-05, P1-04 | Implementação não iniciada. |

O registro detalhado, inclusive limitações de validação e lista de arquivos, está em [Timeline de execução](06-execution-timeline.md).

## Cartões de implementação

### P0-01 — Persistência transacional

**Arquivos candidatos:** `services/database.js`, novo `services/provisioning_store.js`, testes de concorrência.
**Critérios:** falha de disco retorna erro; evento externo tem unicidade; dois workers concorrentes não criam dois tenants; nenhuma confirmação antes de commit.

### P0-02 — Política de ferramentas

**Arquivos candidatos:** `services/database.js`, `config/tenants.js`, `services/tools_registry.js`, testes de boundary.
**Critérios:** `customer_onboarding` permite apenas capacidades comerciais aprovadas; nenhuma ferramenta privilegiada por default; escalonamento exige permissão explícita e auditoria.

### P0-03/P0-04 — Contrato canônico, billing e worker

**Arquivos candidatos:** novos `services/billing_webhook_service.js`, `services/provisioning_service.js`, `services/domain_events.js`, `server.js`.
**Critérios:** publicar no OpenAPI `POST /v1/subscriptions` com `trialDays`, metadata de correlação e idempotência persistida; `/v1/flow/billing/*` é explicitamente excluída. Exigir HMAC `X-Axion-Signature` sobre `<timestamp>.<rawBody>`; deduplicação por `event_id`; janela de replay; ACK idempotente; outbox recuperável; compensação em falha; Problem Details; testes com eventos fora de ordem.

### P0-01/P0-05 — Lock do JSON legado e restrição por entitlement

**Arquivos alterados:** `services/database.js`, `services/provisioning_store.js`, `services/provisioning_worker.js`, `services/axion_pay_webhook.js`, `middleware/tenant_auth.js`, novos `services/entitlement_policy.js` e `services/entitlement_guard.js`, `services/cron_scheduler.js`, `services/tools_executor.js`, `services/baileys_manager.js`, `docs/ARCHITECTURE.md`, `docs/BILLING_PROVISIONING.md`.
**Testes:** `tests/legacy-db-lock.test.js` (mapa de lock, contenção, PID vivo, owner token, JSON corrompido, reentrância e escrita entre processos), `tests/entitlement-restriction.test.js` (política HTTP e execução autônoma) e `tests/axion-pay-provisioning.test.js` (incluindo fencing de lease).

**Critérios P0-01:** nenhuma gravação de `axion_platform.json` ocorre fora de `withDatabaseMutationLock`; falha de lock é erro factual, nunca escrita silenciosa; processo concorrente não é sobrescrito por cache obsoleto; lock residual não sobrevive à mutação; nenhuma nova função de mutação entra sem estar em `DATABASE_MUTATION_EXPORTS`.

**Critérios P0-05:** `PAST_DUE`/`CANCELED` recusam métodos HTTP não-seguros com `403` RFC 7807 e suspendem cron/WhatsApp pelo mesmo guard compartilhado; leituras, rotas de sessão e `super_admin` permanecem operacionais; falha do store não trava tenant legítimo; `reconcileEntitlements()` reprova a projeção a partir do ledger e é idempotente.

### Auditoria cirúrgica e hardening — 2026-09-28

| Achado | Classificação final | Tratamento |
| --- | --- | --- |
| Stale takeover removia lock de processo vivo | Válido, bloqueador | Corrigido em `cf5576b` com PID vivo e owner token. |
| JSON ilegível degradava para schema vazio | Válido, bloqueador herdado | Corrigido em `cf5576b`; leitura agora falha fechada e preserva os bytes. |
| Entitlement não cobria cron/WhatsApp | Válido, bloqueador | Corrigido em `cf5576b` por guard compartilhado antes de inferência/outbound. |
| Lease sem fencing | Válido | Corrigido em `cf5576b` com token por aquisição. |
| D+14 contado desde `created_at` | Válido, financeiro | Corrigido em `803d96b` com `settled_at` canônico e migração `017`. |
| Status público aceitava cobrança de outro link | Válido | Corrigido em `803d96b`; vínculo obrigatório por `payment_link_id`. |
| Corrida idempotente duplicava webhook | Válido | Corrigido em `803d96b`; somente o vencedor do insert publica. |

**Gate atual:** suites, build Docker e quality gate do Flow passaram; o release
`23c889d4` está saudável em `https://agents.axiontemp777.buzz`. O AXION Pay
passou os três gates de CI no commit `654df35` e possui stack staging isolado
com pagamentos reais forçados para `false`. Nenhum item foi promovido a
produção (`🚀 Promoção manual para produção => skipped` em `36605426352`).

### Validação de staging integrada — 2026-09-29

| Área | Evidência | Resultado |
| --- | --- | --- |
| Orquestração Pay isolada | PRs #148, #149, #150, #151, #152 em `main` (merge `66dc4f7`) | Integrado |
| Run de publicação | `pay-staging.yml` run `36605448166` (`pay_ref=654df35`, `reset_staging_data=false`) | **SUCESSO** |
| Causa raiz das 4 falhas anteriores | `getent ahostsv4` fatal com janela fixa de 60s; propagação DNS da VPS levou ~63s (`curl: (6) Could not resolve host` em 20+ tentativas) | Corrigido no PR #152: `public-url` persistido antes da checagem + probe HTTP real (40x3s) + DNS apenas como diagnóstico de falha |
| API Pay pública | `/health` 200 `release=654df35…`; `/openapi.json` 200 `openapi 3.1.0`, `POST /v1/subscriptions`, `trialDays 0..90`, `Idempotency-Key` | Conforme |
| Erros de autenticação | `POST /v1/charges` sem chave 401; com Bearer inválido 401; `GET /v1/dashboard/me` 401; rota/método desconhecido 404 | **Zero 5xx** |
| CORS | `OPTIONS` → 204, `Access-Control-Allow-Origin` restrito a `https://flow.example.com`, `Vary: Origin`, allow-methods/headers explícitos | Conforme |
| Superfície de rede | `docker-compose.staging.yml`: única porta `127.0.0.1:3334:3333`; Postgres/Redis sem `ports:`; healthcheck em loopback | Conforme |
| Flags de pagamento | `PAYMENTS_ENABLED`, `STRIPE_ENABLED`, `STRIPE_BILLING_ENABLED`, `OPEN_FINANCE_ENABLED`, `NUBANK_WEB_ENABLED`, `ENABLE_BANK_RECONCILIATION` todos `"false"` | Conforme |
| Flow staging | `/health` e `/api/v1/platform/info` 200, `environment=staging`, `release=66dc4f73` | Conforme |
| Playwright | `chromium-desktop` (1440x900) e `chromium-mobile` (Pixel 7): 11 checagens cada, **0 falhas** — 200, HTML, título, DOM renderizado, sem overflow horizontal, sem erro de página/request, `platform/info=staging` | Conforme |

**Achados que permanecem abertos:**

1. **RFC 7807 não implementado no AXION Pay.** Os corpos de erro usam
   `{"error":"…"}` e `{"message","error","statusCode"}`; o `openapi.json` não
   declara `application/problem+json`. DIRECTIVES §3 exige Problem Details.
   Correção exige mudança de comportamento da API e novo release do Pay.
   (O AXION Flow **já** emite Problem Details corretamente em `/api/v1/webhooks/axion-pay`.)
2. ~~E2E PAY → FLOW e `schema_migrations` bloqueados por ausência de
   credencial.~~ **Resolvido em 2026-09-29** — ver a seção seguinte.

### Integração PAY → FLOW, injeção de credenciais e teardown — 2026-09-29

| Área | Evidência | Resultado |
| --- | --- | --- |
| Vault (5 passos) | `vault/payments/axion-staging/` com `.env`, `index.json`, `README.md`; catálogo mestre `vault/index.json` + `vault/README.md`; `python scripts/vault_loader.py audit` → as duas variáveis `[OK] CONFIGURADO` mascaradas, `EXIT=0` | Conforme |
| Segredos do Actions | `PAY_STAGING_TEST_KEY` e `FLOW_STAGING_WEBHOOK_SECRET` publicados; valores nunca impressos em console, log ou commit | Conforme |
| Canal de operação | PR **#153** (`9176749`, merge `7dc91bc`): `.github/workflows/staging-ops.yml` (somente `workflow_dispatch`, `permissions: contents: read`, sem job de produção) + `docker-compose.staging.yml` com `AXION_BILLING_WEBHOOK_ENABLED` (default `false`) e `AXION_PAY_WEBHOOK_SECRET` (default vazio) | Integrado |
| Validação do workflow | `js-yaml` (YAML OK, inputs/opções/permities conferidos), `bash -n` no script embutido e `node --check` no script Node inline: exit 0 nos três | Conforme |
| Injeção da chave Pay | Run `36621483892` (`target=all`) **SUCESSO**: `AXION_API_KEYS` atualizado com backup em `/opt/axion/backups/axion-pay-staging/env.staging.20260929T194549Z` | Conforme |
| Autenticação Pay | `GET /v1/sandbox/validate` **401 → 200** `authenticated:true`, `keyFingerprint=4cf5fd2412da`; sem chave 401; Bearer inválido 401; `GET /v1/charges/{id}` 404 (auth ok); `POST /v1/charges` com chave **503** (auth ok, `PAYMENTS_ENABLED=false` por política) e sem chave 401 | Conforme |
| Webhook Flow habilitado | `POST /api/v1/webhooks/axion-pay` sem assinatura: **503 → 401** (`invalid-webhook-signature`), provando flag ON e segredo configurado | Conforme |
| Contrato do webhook | 13 casos: 202 `received:true` (assinado), 200 `duplicate:true` (replay), 401 assinatura errada, 401 assinatura expirada, 400 event-id divergente, 400 evento não suportado, 400 timestamp divergente — todos em `application/problem+json` RFC 7807 | **E2E PAY → FLOW validado** |
| Schema e integridade | `schema_migrations` = **18** (`001_init` … `017_payment_intent_settlement_timestamp`); 21 índices/únicos conferidos (`secret_hash UNIQUE`, `stripe_subscription_id UNIQUE`, `portal_token UNIQUE`) | Conforme |
| Teardown | PR **#154** (`67baa2a`, merge `5763fda`) + run `36622982766`: `linhas_sinteticas_removidas=4`, `restantes=0` | **Zero poluição** |
| Auditoria final | Run `36623127798` (`db-audit`): 18 migrations; `merchant_accounts`, `merchant_api_keys`, `merchant_subscriptions`, `payment_intents`, `webhook_events` todos **0** | Conforme |

**Estado deliberadamente mantido:** `AXION_BILLING_WEBHOOK_ENABLED=true` permanece
ativo no staging (é o endpoint de integração sob segredo HMAC; assinatura inválida
retorna 401). Todas as flags de pagamento real continuam `"false"`.

### P2-01 — Cutover de QA e retirada do legado

**Escopo:** inventariar e exportar apenas metadados/redações necessários para auditoria; bloquear novas gravações no billing legado; recriar fixtures de QA exclusivamente no contrato canônico; verificar o caminho ponta a ponta; desativar rotas legadas atrás de flag reversível. Não migrar subscriptions, trials, tokens, sessões ou dados de testers como se fossem dados de produção.

**Critérios:** não há tráfego novo para `/v1/flow/billing/*`; fixtures canônicas passam pelos gates; a reversão restaura somente a flag/rota legada, sem merge de dados; exclusão definitiva de dados legados fica fora deste cartão e exige comando separado, escopo confirmado e evidência de export.

### P1-02/P1-03 — Canal WhatsApp

**Arquivos candidatos:** `services/baileys_manager.js`, novo `services/whatsapp_onboarding_service.js`, `config/whatsapp_instances.js`, `server.js`.
**Critérios:** QR bruto nunca serializado; pairing code real; tentativa limitada; modo inicial seguro; mensagem de teste exige dupla confirmação; opt-out bloqueia envio.

## Definition of Done universal

- Teste RED que reproduz o risco e teste GREEN após a mudança.
- Validação de schema e autorização por tenant.
- Logs sem segredo, cartão, QR bruto ou conteúdo desnecessário.
- Evidência de staging recente e teardown completo de dados de teste.
- Documentação e contrato atualizados no mesmo conjunto de mudanças.
