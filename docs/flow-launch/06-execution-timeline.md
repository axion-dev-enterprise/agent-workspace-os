# Timeline de execução — AXION Flow + AXION Pay

**Corte deste registro:** 2026-09-29.
**Estado:** Flow e AXION Pay integrados e saudáveis em staging — Flow release
`66dc4f73` em `https://agents.axiontemp777.buzz` e AXION Pay `654df35` em
`https://node-arkansas-pensions-holding.trycloudflare.com`, publicado pelo run
`36605448166` (PR #152). O teste integrado PAY → FLOW e a verificação de
`schema_migrations` seguem pendentes por falta de credencial de staging.
Nenhuma promoção de produção foi executada.

## Escopo e locais de trabalho

| Sistema | Checkout usado | Observação |
| --- | --- | --- |
| Workspace e documentação | `C:/workspace` | branch operacional `axion`, já continha mudanças do usuário. |
| AXION Pay | `C:/workspace/apps/axion-pay` | branch `codex/staging-hardening`, PR #29, head `654df35` publicado como release de staging pelo run `36605448166`. |
| AXION Flow | `C:/workspace/services/axion-flow` | PRs #147 a #152 integrados em `main` (merges `23c889d4` e `66dc4f7`); staging validado em `66dc4f73`. |

As edições foram cirúrgicas e preservaram alterações preexistentes. Nenhum arquivo foi descartado, nenhum dado foi apagado e nenhuma identidade Git divergente foi usada para criar commit.

## 1. Descoberta, auditoria e decisões

1. Foram lidos o handoff anexado, o transcript operacional indicado, a documentação local, o OpenAPI do AXION Pay, a estrutura de API do Flow, os repositórios locais e os logs diários relevantes.
2. Foram comparadas as superfícies `agents.example.com` e `flow.example.com` com o código disponível e com o estado dos repositórios.
3. A decisão arquitetural foi consolidada: Flow é o control plane e a interface do produto; AXION Pay continua como fonte de verdade financeira; o runtime útil de Agents fica atrás do Flow.
4. O billing específico `/v1/flow/billing/*` foi classificado como legado de QA. Não será evoluído nem terá dados de testers migrados como produção.
5. Foram produzidos/revisados os documentos `01` a `05` deste pacote, o gap audit e o plano de implementação. O backlog passou a separar implementação local de conclusão em staging/produção.

## 2. AXION Pay — contrato genérico de assinatura e trial

### Alterações realizadas

- Criada a migração `packages/axion-pay-core/sql/016_canonical_subscription_trials.sql` com idempotency key persistida, request hash, `trial_days`, `trial_ends_at`, checkout URL e índices.
- Estendido `POST /v1/subscriptions` para aceitar `trialDays` entre 0 e 90, metadata somente de strings e limite de 20 chaves.
- Implementada idempotência determinística por merchant + key, incluindo conflito `409` quando a mesma chave chega com payload diferente.
- Propagadas chaves de idempotência às operações Stripe de customer, price, payment method, update, subscription e checkout.
- Propagado trial tanto para assinatura direta quanto para `subscription_data` do checkout.
- Corrigido o processamento de `checkout.session.completed`: trial confirmado vira `TRIALING` e não gera fatura paga, payment intent pago ou transação financeira fictícia.
- Eventos `subscription.created`, `subscription.renewed`, `subscription.past_due` e `subscription.canceled` passaram a carregar o estado necessário; o evento de trial inclui término, metadata e identidade do cliente.
- Atualizados `API_REFERENCE.md` e `CUSTOM_CHECKOUT_GUIDE.md` com o contrato real de assinatura e verificação HMAC.

### OpenAPI

- Atualizada a fonte `packages/axion-pay-core/src/openapi.ts` para versão `0.2.0` com schemas de assinatura e webhook.
- Criado `packages/axion-pay-core/scripts/export-openapi.mjs` e o comando `openapi:export`.
- Regenerados deterministicamente `docs/openapi.json` e `docs/openapi.yaml`, eliminando divergência entre fonte e artefatos publicados.

### Testes preparados

- Adicionado `packages/axion-pay-core/tests/canonical-subscription-trial.test.mjs` para trial, replay idempotente, conflito de payload e ausência de contabilização paga durante trial.

## 3. AXION Flow — ingress assinado, ledger e provisionamento

### Ingress de webhook

- Criado `services/axion_pay_webhook.js`.
- Adicionada `POST /api/v1/webhooks/axion-pay` antes do parser JSON global para preservar bytes exatos.
- Implementadas verificação HMAC-SHA256 em tempo constante, janela de replay, validação de envelope, concordância do event ID e allowlist de eventos.
- Respostas de erro usam RFC 7807 e não registram body, assinatura ou secret.
- A flag `AXION_BILLING_WEBHOOK_ENABLED` nasce desativada.

### Control plane transacional

- Criado `services/provisioning_store.js` com SQLite WAL, foreign keys e `BEGIN IMMEDIATE`.
- Criadas as tabelas `billing_events`, `entitlements`, `provisioning_requests` e `provisioning_outbox`.
- Implementadas deduplicação por provider/event ID, projeção versionada, prevenção de regressão temporal e proteção contra ressurreição de subscription cancelada.
- Implementados lease recuperável, retry exponencial, limite de cinco tentativas, conclusão transacional e consulta de ativação por tenant.

### Worker e segurança de tenant

- Criado `services/provisioning_worker.js` com consumo serial da outbox e recuperação idempotente após crash.
- O tenant ID é validado ou derivado deterministicamente; conflito parcial de tenant/usuário falha fechado.
- O worker nasce desativado via `AXION_PROVISIONING_WORKER_ENABLED` e só cria tenant após evento elegível persistido.
- `provisionTenantDb` agora usa `customer_onboarding` por padrão, sem terminal, filesystem, browser, API genérica, WhatsApp ou spawn.
- Corrigido `selectToolsForIntent`: grant vazio permanece vazio em vez de expandir silenciosamente para todas as ferramentas.
- `saveDatabase` deixou de engolir erros de persistência e agora os propaga ao boundary chamador.
- Adicionada `GET /api/v1/activation/status` para o tenant autenticado.

### Documentação e testes preparados

- Criado `docs/BILLING_PROVISIONING.md` no Flow com contrato, flags, metadata, estados, recuperação e rollout.
- Adicionado `tests/axion-pay-provisioning.test.js` para assinatura inválida, replay, ordem, outbox e status.
- Adicionado teste deny-by-default em `tests/agent_runs.test.js`.

## 4. Incremento P0-01 e P0-05 — commit `29bd93a`

### P0-01 — lock abrangente do JSON legado

- `services/database.js` ganhou `withDatabaseMutationLock`: lock por arquivo
  (`data/.db-mutation.lock` com `wx`), reentrante por profundidade, releitura
  do banco na aquisição mais externa (fingerprint `size:mtimeNs`) e espera
  bloqueante limitada por `AXION_DB_LOCK_WAIT_MS` (default 5 s) com stale
  takeover por `AXION_DB_LOCK_STALE_MS` (default 30 s).
- As 26 funções públicas que gravam o JSON entram por wrap no `module.exports`,
  com a lista `DATABASE_MUTATION_EXPORTS` conferida no `require` (mutação nova
  fora do mapa derruba a subida do servidor).
- `loadDatabase` faz leitura+migração+escrita inicial sob lock **opcional**:
  a leitura degrada para "sem lock" em vez de lançar, enquanto toda gravação
  continua falhando fechado.
- `saveDatabase` se auto-protege com `{ reload: false }` e é o único caminho
  para `persistDatabase`.
- `cron_scheduler`, `tools_executor` e `baileys_manager` envolvem seus
  ler-modificar-escrever em `withDatabaseMutationLock`.

### P0-05 — restrição efetiva por entitlement

- Criado `services/entitlement_policy.js` (puro): métodos seguros, isenções
  `/api/v1/auth/` e `/api/v1/activation/`, papéis, motivos e construção do Problem
  Details `https://flow.example.com/problems/entitlement-restricted`.
- `middleware/tenant_auth.js` aplica a decisão em um único ponto, depois da
  sessão resolvida; só consulta o store em métodos não-seguros e faz fail-open
  com log `[ENTITLEMENT]` se o control plane falhar.
- `services/provisioning_store.js` ganhou índice por `tenant_id`,
  `getTenantRestriction()` (join `provisioning_requests` → `entitlements`,
  sem ativação = sem restrição) e `reconcileEntitlements()` (replay do ledger
  com o mesmo gate de ingress, reparo de `status` em transação `BEGIN
  IMMEDIATE`, idempotente).
- `mapEntitlementStatus` do webhook agora delega para
  `deriveEntitlementStatus`, eliminando regra duplicada.

## 5. Evidência de verificação executada

| Verificação | Resultado |
| --- | --- |
| `node --check` nos módulos e testes novos/alterados (11 arquivos) | passou. |
| Varredura estática de `database.js`: funções que chamam `saveDatabase` ⊆ `DATABASE_MUTATION_EXPORTS ∪ {loadDatabase, readAndMigrateDatabase}` | 27/27 conformes; `persistDatabase` alcançável só por `saveDatabase`. |
| Varredura dos serviços externos com `saveDatabase(` sem `withDatabaseMutationLock` | nenhuma ocorrência. |
| `git diff --check` no staging | passou; apenas avisos de normalização LF/CRLF. |
| Varredura de credenciais no diff (`sk_live`, `whsec_`, chaves AWS, PEM) | nenhuma ocorrência. |
| Transpilação sintática das fontes TypeScript alteradas do AXION Pay | passou, sem executar typecheck/build. |
| Exportação OpenAPI executada duas vezes e comparação SHA-256 | saída determinística. |
| Comparação semântica fonte OpenAPI ↔ JSON | correspondência confirmada. |
| Parse do OpenAPI JSON | válido. |

Testes escritos mas **não executados localmente** (Regra: `docs/REPOSITORY_PREFLIGHT.md`
exige CI): `tests/legacy-db-lock.test.js`, `tests/entitlement-restriction.test.js`,
`tests/axion-pay-provisioning.test.js`, `packages/axion-pay-core/tests/canonical-subscription-trial.test.mjs`.

O YAML foi produzido pelo serializador determinístico, mas não houve parser YAML disponível no ambiente para uma validação independente.

## 7. Limitações e ações deliberadamente não executadas

- Builds, suites de teste e testes locais não foram executados porque `docs/REPOSITORY_PREFLIGHT.md` proíbe esse tipo de validação local e exige CI aprovado.
- Não houve teste integrado PAY → FLOW, teste de concorrência real, crash recovery real ou staging.
- Nenhuma secret foi criada, lida ou exibida; o webhook do merchant Flow ainda precisa ser cadastrado no AXION Pay em staging.
- As flags de ingress e worker continuam desativadas por padrão.
- Não houve push, Pull Request, deploy, alteração de domínio, cobrança, mensagem externa ou exclusão do billing legado.
- A branch local `main` do Flow guarda `3e64d59` (commit anterior, feito sob instrução explícita) e **não foi empurrada**; o trabalho novo está na branch `feat/p0-01-p0-05-lock-and-entitlement-restriction`, conforme `DIRECTIVES.md` §6.
- A restrição por entitlement não tem feature flag: só afeta tenant com linha em `entitlements` em `PAST_DUE`/`CANCELED`, e a isenção é uma constante única em `services/entitlement_policy.js`.

## 8. Auditoria final e correções — 2026-09-28

### Diagnóstico

A revisão adversarial confirmou sete achados: stale takeover sem validação do
proprietário, release sem ownership, fallback destrutivo para JSON corrompido,
entitlement limitado ao HTTP, lease sem fencing, D+14 baseado em criação da
intenção, ownership público permissivo e duplicação de evento no concorrente
idempotente. Os dois primeiros compõem o mesmo defeito de lock.

### Commit Flow `cf5576b`

- lock registra PID e owner token; processo vivo nunca perde lock somente por
  idade e o release não remove lock de outro proprietário;
- JSON existente e ilegível falha fechado, sem criar schema vazio em memória;
- outbox recebe fencing token exigido em `completeOutbox` e `failOutbox`;
- `entitlement_guard` passa a atender middleware HTTP, cron, auto-reply e envio
  direto de WhatsApp;
- testes de regressão foram adicionados para PID vivo, ownership, corrupção,
  fencing e execução autônoma;
- documentação arquitetural do Flow foi atualizada no mesmo commit.

### Commit AXION Pay `803d96b`

- migração `017_payment_intent_settlement_timestamp.sql` cria `settled_at`,
  faz backfill por `updated_at` e registra a primeira transição para pago;
- saldo e solvência usam `settled_at`, nunca `created_at`, para D+N;
- status público exige `metadata.payment_link_id` correspondente;
- somente o vencedor do insert idempotente publica `subscription.created`;
- o bug hunt log deixa explícito que a nova rodada aguarda CI.

### Evidência desta rodada

| Verificação | Resultado |
| --- | --- |
| `git diff --check` nos dois repositórios antes dos commits | passou; somente avisos LF/CRLF. |
| `node --check` nos 10 JS alterados do Flow | passou. |
| Scanner fintech do AXION Pay | zero achados. |
| Scanner de concorrência do Flow | um falso positivo preexistente em `chatpro_auditor.js`; nenhuma ocorrência no código alterado. |
| Sonda de segredos nos staged diffs | nenhuma credencial encontrada. |
| Suites, typecheck, build e migração executável | não executados localmente por política; CI pendente. |

### Estado de prontidão

O código está **pronto para o próximo gate de CI**, não para lançamento. O CI
verde anterior do PR #147 não pode ser reutilizado como evidência dos novos
commits. Nenhum push ou deploy foi autorizado/executado nesta rodada.

## 9. Próxima sequência controlada

1. Enviar `cf5576b` para a branch do PR #147 e publicar uma branch/PR do AXION Pay contendo `ac47e36` + `803d96b`; submeter ambos ao CI autorizado: lint, typecheck, testes unitários, migração efêmera, integração e concorrência.
2. Corrigir qualquer falha do CI sem retries cegos e anexar a evidência ao backlog.
3. Revisar os escopos de restrição com o operador: `POST /api/v1/agent/chat` e `POST /api/v1/sessions/sync` estão bloqueados por `PAST_DUE`/`CANCELED` por regra ampla; ampliar a isenção é uma constante.
4. Criar o webhook do merchant Flow no staging, armazenar a secret no vault e validar tenant/conta antes de qualquer chamada autenticada.
5. Habilitar apenas o ingress; enviar fixture assinada e conferir ledger/deduplicação.
6. Habilitar o worker; provar criação única, recuperação após falha e perfil mínimo.
7. Executar `reconcileEntitlements({ repair: false })` no staging como gate de divergência PAY ↔ FLOW.

## 10. Execução de staging — 2026-09-29

1. O hardening Flow `cf5576b` foi publicado na branch do PR #147. O quality
   gate do run `36560756085` passou sobre esse SHA.
2. O PR #147 foi integrado sem promoção de produção. O push de `main` gerou o
   run `36562027904`: quality gate verde, deploy staging verde e job de
   produção explicitamente ignorado.
3. As sondas públicas retornaram HTTP 200 em `/health` e
   `/api/v1/platform/info`, ambas com `environment=staging` e
   `artifactRelease=23c889d4b77cebf029dd79fe1dbdd44dcff61d6c`.
4. O AXION Pay foi publicado na branch `codex/staging-hardening` e no PR #29.
   Os gates `verify-core`, `validate` e `build-and-test` passaram no commit
   `154ef47`. Os previews Vercel foram criados com sucesso, mas exigem login da
   equipe Vercel e não constituem evidência pública anônima.
5. Foi criado `docker-compose.staging.yml` para o core Pay com Postgres, Redis
   e API isolados, bind em loopback e todos os provedores financeiros reais
   forçados para `false`. O health agora carrega o SHA em `release`.
6. Foi preparado no Flow o workflow manual `AXION Pay — Staging isolado`, que
   valida um SHA público do Pay, publica o stack via canal SSH já governado e
   expõe a API por Cloudflare Quick Tunnel, validando health/OpenAPI antes de
   registrar a URL.
7. O commit local do orquestrador é `00a03c1`. Seu push está pendente porque o
   token GitHub atual não possui o escopo OAuth `workflow`; esse bloqueio não
   foi contornado e nenhuma credencial foi exposta.

### Próximo gate exato

- autorizar o escopo GitHub `workflow`, publicar `00a03c1` e disparar o
  workflow com o SHA Pay após a rodada final de CI;
- comprovar HTTP 200 e SHA do core Pay no endpoint HTTPS emitido;
- habilitar ingress/worker Flow somente para a fixture de staging, executar o
  contrato assinado, verificar ledger/outbox/entitlement e remover os dados de
  teste no teardown.

## 11. Hardening do staging e publicação do AXION Pay — 2026-09-29

1. Foram integrados em `main` os PRs #148 (orquestração isolada do Pay), #149
   (diagnósticos do container), #150 (reset protegido de volumes) e #151
   (espera de propagação DNS do Quick Tunnel), todos pelo mesmo branch de
   entrega.
2. Os runs `36586777197`, `36587473127`, `36588234001` e `36588763719` falharam
   todos no mesmo step `Publicar stack isolado e configurar tunnel HTTPS`.
3. **Causa raiz:** a checagem de prontidão exigia `getent ahostsv4` como
   pre-requisito fatal com janela fixa de 60 segundos. O loop estourava e o
   script saía antes de verificar o HTTPS público e antes de gravar
   `/opt/axion/staging/pay/public-url`. A stack em si subia e ficava
   saudável — confirmado porque `https://ottawa-rated-mall-foto.trycloudflare.com/health`
   retornou `200` com `release=654df35` mesmo com o run marcado como falho.
4. O PR #152 (`0867af5`, merge `66dc4f7`) corrigiu a causa: o arquivo
   `public-url` passou a ser gravado imediatamente após a descoberta da URL, a
   prontidão passou a medir o requisito real (`GET /health` público com o
   `release` esperado, 40 tentativas x 3s com log por tentativa) e a diagnóstica
   de DNS migrou para o ramo de falha, sem `exit`.
5. O run `36605448166` (`pay_ref=654df35`, `reset_staging_data=false`)
   terminou **SUCESSO**. O log prova a causa raiz: `curl: (6) Could not resolve
   host` em 20+ tentativas antes de resolver, ou seja, a propagação DNS da VPS
   levou mais de 60s. A URL final publicada é
   `https://node-arkansas-pensions-holding.trycloudflare.com`.
6. O push de `main` gerou o run `36605426352`: quality gate verde, deploy de
   staging verde e `🚀 Promoção manual para produção => skipped`.
7. Validação pública executada por `curl.exe`: `/health` e `/openapi.json` do
   Pay com `200`; `401` para chamadas sem chave e com Bearer inválido; `404`
   para rota e método desconhecidos; **zero respostas 5xx**; `OPTIONS` com
   `204` e CORS restrito a `https://flow.example.com`.
8. Auditoria do `docker-compose.staging.yml`: única porta publicada é
   `127.0.0.1:3334:3333`, Postgres e Redis sem `ports:`, healthcheck em
   loopback e as seis flags de pagamento real em `"false"`.
9. Playwright `1.63.0` com `chromium-desktop` (1440x900) e `chromium-mobile`
   (Pixel 7): 11 checagens por perfil, **0 falhas**, `platform/info` com
   `environment=staging` e `release=66dc4f73`. Os dois `401` observados
   (`/api/v1/auth/me` e `/api/v1/auth/sso/exchange`) são o contrato exigido
   pelo `verify-sso-contract` do CI (`anonymous exchange must be denied`).

### Achados abertos

1. **RFC 7807 ausente no AXION Pay**: os erros retornam `{"error":"…"}` e o
   OpenAPI não declara `application/problem+json`, contrariando DIRECTIVES §3.
   O AXION Flow já emite Problem Details corretamente.
2. ~~E2E PAY → FLOW e conferência de `schema_migrations` bloqueados~~ —
   **resolvido na seção 12.**

## 12. Injeção de credenciais e E2E integrado PAY → FLOW — 2026-09-29

1. **Vault (protocolo de 5 passos).** Nova categoria `payments/` com a
   plataforma `axion-staging`: `AXION_PAY_STAGING_TEST_API_KEY` (API key de
   teste) e `AXION_FLOW_STAGING_WEBHOOK_SECRET` (HMAC do webhook) foram geradas
   por CSPRNG, gravadas em `vault/payments/axion-staging/.env` (UTF-8 sem BOM),
   documentadas em `index.json` + `README.md`, registradas no catálogo mestre
   `vault/index.json` e `vault/README.md`. `python scripts/vault_loader.py audit`
   retornou `EXIT=0` com as duas variáveis `[OK] CONFIGURADO` **mascaradas**
   (`axp_…` e `whse…`) e a mensagem `Nenhuma credencial foi exposta em texto plano`.
2. **Publicação como secrets.** Ambos os valores foram gravados em
   `PAY_STAGING_TEST_KEY` e `FLOW_STAGING_WEBHOOK_SECRET` no repositório
   `axion-dev-enterprise/axion-flow`; nenhum valor foi impresso em console,
   log ou commit.
3. **PR #153** (`9176749`, merge `7dc91bc`) — canal de operação governado:
   - `.github/workflows/staging-ops.yml`: somente `workflow_dispatch`,
     `permissions: contents: read`, `concurrency` sem cancelamento, modo
     `target` (`all`/`pay-key`/`flow-webhook`/`db-audit`), guarda de canal de
     acesso (falha explícita se `VPS_SSH_KEY` e `VPS_SSH_PASSWORD` estiverem
     vazios), backup dos `.env` antes de qualquer escrita e `chmod 600`.
   - `docker-compose.staging.yml`: `AXION_BILLING_WEBHOOK_ENABLED`
     (`${…:-false}`) e `AXION_PAY_WEBHOOK_SECRET` (`${…:-}`) repassados ao
     container — comportamento inalterado enquanto o flag não for setado.
   - Validação: `js-yaml` (YAML OK), `bash -n` (exit 0).
4. **Run `36621483892` (`target=all`) = SUCESSO.** Evidências extraídas do log:
   - `AXION_API_KEYS atualizado (merchant=staging-e2e, backup=/opt/axion/backups/axion-pay-staging/env.staging.20260929T194549Z)`;
   - `GET /v1/sandbox/validate` → `200`
     `{"environment":"sandbox","authenticated":true,…,"keyFingerprint":"4cf5fd2412da"}`;
   - `webhook do Flow habilitado em staging (backup=/opt/axion/backups/agents-platform-staging/env.20260929T194556Z)`;
   - `POST /api/v1/webhooks/axion-pay` com assinatura inválida → **HTTP 401**
     (era **503** `webhook-disabled` antes da ativação);
   - `schema_migrations` = 18 linhas; 21 índices/únicos; contagens do Pay todas
     em 0 (nenhum merchant em staging — a autenticação é por variável de
     ambiente, conforme `authenticateApiKey`).
5. **PR #154** (`67baa2a`, merge `5763fda`) — modo `webhook-teardown`: inputs
   `subscription_id` e `event_id` obrigatórios e deleção escopada em
   `provisioning_outbox`, `provisioning_requests`, `entitlements` e
   `billing_events` via `node:sqlite` dentro do próprio container. Validação:
   `js-yaml`, `bash -n` e `node --check` nos três exit 0.
6. **E2E executado com `curl.exe` contra os endpoints públicos** (corpos em
   arquivo UTF-8 sem BOM, assinatura HMAC-SHA256 calculada sobre
   `"<ts>." + rawBody` exatamente como em `verifySignature`):

   | Caso | HTTP | Resultado |
   | --- | --- | --- |
   | Pay sem chave | 401 | Contrato de auth |
   | Pay com chave de teste | **200** | `authenticated:true`, fingerprint `4cf5fd2412da` |
   | `POST /v1/charges` com chave | **503** | Autenticou e passou do guard; `PAYMENTS_ENABLED=false` por política |
   | `GET /v1/charges/{id}` com chave | 404 | Auth + scope ok |
   | Pay com Bearer inválido | 401 | Contrato de auth |
   | Webhook sem assinatura | **401** | Era 503; flag ON + segredo setado |
   | Envelope assinado `subscription.created` | **202** | `received:true, duplicate:false, queued:true, requestId` |
   | Replay do mesmo envelope | **200** | `duplicate:true` — persistência e dedupe comprovados |
   | Assinatura errada | 401 | `invalid-webhook-signature` |
   | Assinatura expirada (−1000s) | 401 | `expired-webhook-signature` |
   | `X-Axion-Event-Id` divergente | 400 | `webhook-event-id-mismatch` |
   | Evento `invoice.paid` | 400 | `unsupported-webhook-event` |
   | `timestamp` do envelope ≠ assinatura | 400 | `webhook-timestamp-mismatch` |

   Todos os erros do Flow vieram em `application/problem+json` com
   `type/title/status/detail/instance/traceId` (RFC 7807).
7. **Teardown (run `36622982766`)**: `linhas_sinteticas_removidas=4`,
   `restantes=0` para `sub_e2e_113f33e840f943` / `evt_e2e_648ea18c535a47`.
8. **Auditoria final (run `36623127798`, `db-audit`)**: 18 migrations
   aplicadas e `merchant_accounts`, `merchant_api_keys`,
   `merchant_subscriptions`, `payment_intents`, `webhook_events` todos **0**.

### Estado mantido deliberadamente

- `AXION_BILLING_WEBHOOK_ENABLED=true` no staging do Flow (endpoint de
  integração protegido por HMAC; assinatura inválida → 401).
- `PAYMENTS_ENABLED`, `STRIPE_ENABLED`, `STRIPE_BILLING_ENABLED`,
  `OPEN_FINANCE_ENABLED`, `NUBANK_WEB_ENABLED` e
  `ENABLE_BANK_RECONCILIATION` continuam `"false"`.
- Nenhum job de produção foi disparado (`🚀 Promoção manual para produção => skipped`).

