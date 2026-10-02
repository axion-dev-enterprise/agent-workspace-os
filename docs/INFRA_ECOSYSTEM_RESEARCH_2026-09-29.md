# Pesquisa de Ecossistema: Vercel, Cloudflare, Tailnet, Docker e GitHub

> **Data da varredura**: 2026-09-29 (21:00–21:40 UTC)
> **Natureza**: somente leitura. Nenhuma mutação foi executada (nenhum commit, push, deploy, invite, DNS change ou flag alterada).
> **Escopo**: verificar se os recursos existentes resolvem as lacunas restantes para o staging AXION Flow + AXION Pay ficar 100% funcional.

---

## 0. Método de coleta

| Eixo | Ferramenta | Restrição respeitada |
| :--- | :--- | :--- |
| GitHub | `gh api`, `gh run list`, `gh workflow view` | só leitura |
| Vercel | `vercel whoami`, `vercel project ls`, `vercel teams ls` | só leitura, sem token impresso |
| Cloudflare | API v4 `GET /zones`, `GET /cfd_tunnel`, `GET /dns_records` via `CLOUDFLARE_API_TOKEN` do vault | token injetado em `os.environ`, nunca logado |
| Tailnet | `tailscale ping`, `tailscale status --json` | sem `ssh` executado |
| HTTP | `curl.exe -s -o NUL -w '%{http_code}'` e `-m 15` | só status/body curto |
| Código | leitura local + `grep`/`Select-String` | sem build local (preflight) |

Host Windows sem Docker e sem `rg`; a ferramenta `glob` do ambiente não retorna resultados (usado PowerShell/`gh api`).

---

## 1. Topologia Tailnet e VPS

Domínio MagicDNS: `taildb9106.ts.net`. Documentação base: `docs/TAILNET_AND_VERCEL_INFRASTRUCTURE.md` (varredura de 2026-09-25).

| Nó | Tailscale | Público | Estado | Função |
| :--- | :--- | :--- | :--- | :--- |
| `desktop-1t1e46h` | `100.64.188.73` | — | local | estação de engenharia |
| `vps-node-01-104-207-90-167` | `100.64.0.1` | `104.207.90.167` | online (pong 193 ms) | gateway/proxy Traefik v3, Docker |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `100.64.0.2` | `104.207.81.120` | online (pong 161 ms) | DB, agentes, Flow (produção + staging) |
| `sensix-ai-studio-vps` | `100.69.94.49` | — | offline ~32d | standby |
| `sensix-black-vps` | `100.86.168.13` | — | offline ~13d | standby |
| ~~`juliana-vps`~~ | ~~`100.81.231.111`~~ | — | descomissionado 2026-09-25 | arquivado em cold vault |

**Confirmado empiricamente**: `agents.example.com/health` → `environment=production`, release `4839e57101310c1a684851fe12ee0892d8f6d7eb`; `agents.axiontemp777.buzz/health` → `environment=staging`, release `5763fdab96fd4c6751a1ae5b8de94596f242519b`.

**Co-localização**: produção e staging do Flow rodam no mesmo host `104.207.81.120` como containers distintos (`axion-agents-platform` porta 3020 / `axion-agents-platform-staging` porta 3021, data dirs `/opt/axion/data/agents_platform` e `/opt/axion/data/agents_platform_staging`).

**Canal de acesso à VPS**: `~/.ssh` local contém apenas `known_hosts`; porta 22022 recusa `publickey,password`; `tailscale ssh` falha na porta 22. Único canal operacional comprovado = steps `appleboy/ssh-action@v1.0.3` e `appleboy/scp-action@v0.1.7` dos workflows (fallback `100.64.0.2:22022`, user `root`, secrets `VPS_*`).

---

## 2. Ecossistema Vercel

- Time: `your-team-slug` ("AXION DEV"), plano **hobby**. Sessão local autenticada como `axionenterprise777-1846`.
- 14 projetos: `spapharma-oauth-bridge`, `breno-english`, `alice-garden`, `landing-page-teste-w-solucoes`, `landing-page-teste`, `ifood-dashboard`, `meta-gpt-worker`, `vps-node-01-api-contingencia`, `axion-flow`, `axion-flow-homepage`, `axion-conferencia-pecas`, `growth-accelerator-main`, `rosireis-atelier`, `vercel-ai-gateway-demo`.
- Projeto `axion-flow` tem último deploy de produção há 120 dias — o alvo real de release é o VPS.

### 2.1 Check `Vercel | failure` (causa raiz identificada)

- Não é `check_run`: é um **commit status** de contexto `Vercel` anexado a `9176749`.
- Descrição: `Git author developeratexample must have access to the project on Vercel to create deployments.`
- Check-runs do mesmo commit: `Quality Gate & Syntax Audit` = success, `Vercel Preview Comments` = success, `Deploy e homologação em staging` = skipped, `Promoção manual para produção` = skipped. Estado agregado: `failure`.
- Causa raiz: identidade git canônica `AXION DEV <developer@example.com>` mapeia no GitHub para o usuário `developeratexample`, que não tem acesso ao projeto Vercel `axion-flow`.

### 2.2 Por que `axion-pay` não sofre desse problema

`.github/workflows/deploy.yml` do `axion-pay` não usa Git integration: grava `.vercel/project.json` a partir de `VERCEL_ORG_ID`/`VERCEL_PROJECT_ID`, faz `vercel pull`, `vercel build --prod` e `vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN`. O deploy é authorizado pelo token, não pelo autor do commit.

### 2.3 Pré-requisito descoberto: nenhum membro do time tem GitHub vinculado

Consulta de membros do time `your-team-slug` via API (somente leitura, token do CLI local, e-mails mascarados):

- Conta conectada: `axionenterprise777-1846`, papel **OWNER**.
- Membros: **1**, e o campo `githubUsername` está **ausente** (`<nao vinculado>`).

A própria falha revela como o Vercel resolve o autor: o status aponta `Git author developeratexample` para um commit cujo e-mail era `developer@example.com` — ou seja, `developer` + `at` + `example`, sem `@` e sem pontos. O Vercel normaliza o **e-mail** do autor e o compara com os membros do time; não depende de login GitHub. Usar o e-mail do membro OWNER deve, portanto, satisfazer a validação.

### 2.4 Opções de correção

| Opção | Ação | Efeito colateral |
| :--- | :--- | :--- |
| A | remover a Git integration do projeto Vercel `axion-flow` | status some; perde-se preview automático (já inutilizado há 120d) |
| B | dar acesso ao usuário `developeratexample` no time/projeto | exige convite (mutação com destinatário) |
| C | trocar a identidade git pelo e-mail do membro OWNER | escolhida pelo operador; depende de commit de teste para confirmar |

**Opção C aplicada em 2026-09-29 (apenas configuração, sem commit):**

- `workspace.config.json` → `git.user_email = developer@example.com`; `git.user_name` permanece `AXION DEV`.
- Override local removido nos repositórios `C:/workspace`, `C:/workspace/services/axion-flow` e `C:/workspace/apps/axion-pay` (os três estavam forçando `developer@example.com` por cima do escopo global, que já estava correto; os repositórios em `temp/` nunca tiveram override).
- Verificação: `git var GIT_AUTHOR_IDENT` devolve `AXION DEV <developer@example.com>` nos três repositórios.
- **Executado com autorização em 2026-09-29**: commit de teste `6c9d0ad` + push (resultado em §2.5).

### 2.5 Resultado empírico do commit de teste (`6c9d0ad`)

- Commit `6c9d0ad` na branch `feat/staging-worker-flag` de `services/axion-flow`, autor `AXION DEV <developer@example.com>`, alteração inocua: `docker-compose.staging.yml` +3 linhas (`AXION_PROVISIONING_WORKER_ENABLED: ${AXION_PROVISIONING_WORKER_ENABLED:-false}` + comentário), YAML validado. Push aceito pelo `origin`.
- `ci-cd.yml` só dispara em push para `main` e em PR para `main` → **nenhum deploy foi acionado**.
- Status do commit: `state=failure`, `description="Deployment was blocked"`, `target_url=https://vercel.com/axion12/axion-flow/7o1edmVCqoFSuxXkcVcg5qBcJYdK`. Check-run `Vercel Preview Comments` = success.

| | Antes (`developer@example.com`) | Depois (`developer@example.com`) |
| :--- | :--- | :--- |
| Autor do commit | `AXION DEV <developer@example.com>` → `developeratexample` | `AXION DEV <developer@example.com>` |
| `description` | `Git author developeratexample must have access to the Project` | `Deployment was blocked` |
| `state` | `failure` | `failure` (inalterado) |

- A mensagem deixou de citar o autor → indício factual de que a **checagem de identidade foi superada** (opção C confirmada). O bloqueio remanescente vem de outro lugar: a **integração Git do repositório pertence ao time Vercel `axion12`**, que devolve **HTTP 403 `Not authorized`** para a conta local em todos os endpoints consultados (`/v2/teams/axion12`, `/v9/projects?teamId=axion12`, `/v6/deployments/7o1edm...?teamId=axion12`; `404` sem `teamId`). A conta `axionenterprise777-1846` só enxerga o time **`your-team-slug`** (hobby), onde existe um segundo projeto `axion-flow` **desconectado** do Git (`link=null`, `prj_ADPDrQfAsY2FE852jK4ScemNwZMX`, aliases `axion-flow-gamma.vercel.app` / `axion-flow-your-team-slug.vercel.app`).
- Conclusão: identidade git resolvida; resta a **posse da integração** (opções em §8.1).

---

## 3. Ecossistema Cloudflare

- **6 zonas ativas**: `example.com`, `axionflow.my`, `axiontemp777.buzz`, `icesvaliant.shop`, `psicologaednagrahl.com.br`, `yannascimentoads.com`.
- Vault `vault/cloud/cloudflare/`: `CLOUDFLARE_API_TOKEN` = CONFIGURADO (obrigatório), `CLOUDFLARE_ACCOUNT_ID` = CONFIGURADO, `CLOUDFLARE_ZONE_ID` = **PENDENTE** (a coleta descobriu o zone id por fallback na API).
- `cloudflared` **ausente** no host local; `wrangler` e `vercel` CLIs presentes.

### 3.1 Túneis: 15 cadastrados, nenhum ativo

`Automação AXION`, `Terço de Noiva - Desiree`, `axion-auth`, `axion-oauth`, `axion-osint-tunnel`, `axion-poseidon`, `axion-ssh`, `axion-ssh-fixed`, `axion-ssh-new`, `axion-tunnel`, `ig-webhook`, `mimo-demo`, `pontotecc-web`, `simonello`, `trydelta` — todos `down` ou `inactive`.

Probe empírico (apenas status):

```
200  https://login.example.com     (registro CNAME para cfargotunnel)
530  https://ssh.example.com
530  https://n8n.example.com
530  https://admin.example.com
200  https://flow.example.com      (Vercel)
200  https://pay.example.com       (Vercel)
```

`530` = erro de origem do Cloudflare → hostnames com túnel morto estão indisponíveis.

### 3.2 Zona `example.com` (100 registros retornados = limite de página)

- **A diretos para VPS**: `agents`, `db`, `tasks`, `voice`, `hermes`, `waba`, `jose`, `imap`, `mail`, `pop`, `smtp` → `104.207.81.120`; `api`, `auth`, `casa`, `casa-preview`, `preview.casa`, `hooks`, `registry` → `104.207.90.167`.
- **CNAME para `cname.vercel-dns.com`**: apex, `www`, `flow`, `pay`, `api.pay`, `data`, `status`, `vps`, `workspace`, `gateway`, `hub`, `pdv`, `financeiro`, `os`, `sensix`, `sicrety`, `models`, `dev`, `google-oauth`, `gramaticalizando`, `brain` (para `api.example.com`), `events` (idem) e outros.
- **CNAME para `*.cfargotunnel.com`** (túneis mortos, §3.1): `admin`, `login`, `oauth`, `dashboard-aps`, `n8n`, `siebraflow`, `ssh`, `osint`, `ig-webhook`, `bipador`, `mimo`, `pontotec`, `pontotecc`, `desiree`, `api.desiree`, `simonello`, `api.simonello`, `bot`, `bot.simonello`, `storage`.
- **Workers/Pages**: `qr` e `poseidon` → `*.workers.dev`; `landing` → `axion-landing.pages.dev`; `painel` → `painel-axion.pages.dev`; `facebusca-routes` → `*.pages.dev`.
- **DNS-only (sem proxy)**: `mail`, `smtp`, `imap`, `pop` → `104.207.81.120`; `vpn` → `104.207.81.41`; DKIM Brevo (`brevo1/2._domainkey`); `meta-oauth`.
- **Wildcard** `*.example.com` → `76.76.21.21` (anycast Vercel, proxied).
- **Anomalia**: apex `axiontemp777.buzz` aponta para `192.0.2.1` (TEST-NET-1, endereço de documentação) somado a `34.216.117.25`.

### 3.3 Zona `axiontemp777.buzz` (7 registros)

`agents` → `104.207.81.120` proxied (**URL estável do staging**), `www` → apex, `models` → `cname.vercel-dns.com` DNS-only, `trydelta`/`trydelta-api` → `62.72.63.194`, apex → `192.0.2.1` + `34.216.117.25`.

### 3.4 Implicações

1. O plano de unificação híbrida (`docs/HYBRID_ARCHITECTURE_UNIFICATION_PLAN.md`) de fechar 80/443 com túnel **não está implementado**: os serviços principais seguem expostos por A record proxied e as portas seguem abertas (cf. `docs/ZERO_TRUST_PORT_AUDIT.md`).
2. ~20 hostnames estão quebrados (530) por túnel desligado enquanto o registro DNS permanece.
3. `db.example.com` é público através do proxy Cloudflare.
4. Mail entrega direto na origem, sem proxy (esperado para SMTP, mas confirma origin exposta).
5. `GET /accounts/{id}/workers/routes` retorna 400 (endpoint/escopo incorreto) — rotas de Worker não foram inventariadas nesta rodada.

---

## 4. Docker, stacks e imagens

- **Sem Docker no host local** (`docker` não reconhecido) → toda inspeção de containers exige os steps dos workflows ou leitura de arquivos.
- 11 arquivos de stack locais: `services/axion-flow/{docker-compose.yml, docker-compose.staging.yml, Dockerfile, infra/lucas-lucavei/, packages/axion-omniroute/, packages/hermes-agent-vnext/{docker-compose.yml, docker-compose.windows.yml, Dockerfile}}` e `apps/axion-pay/packages/axion-pay-core/{docker-compose.yml, docker-compose.staging.yml, Dockerfile}`.
- Compose de produção do Flow (`services/axion-flow/docker-compose.yml`): imagem `axion-agents-platform:10.1.1`, `env_file: .runtime.env` com `format: raw` (preserva `$` de senhas), healthcheck `wget /healthz`, `security_opt: no-new-privileges`, `cap_drop: ALL`, volumes `/opt/axion/data/agents_platform`, `/opt/axion/vault/nous_portal.env:ro`, `/opt/axion/vault/lucas_flow_bridge.env:ro`, log rotativo 20 MB x5.
- `ci-cd.yml` (405 linhas): Quality Gate executa `docker build -t axion-flow-test .` e `node -c` de `services/tools_registry.js` e `config/identity_registry.js`; deploy usa `scp-action` + `ssh-action` com fallback `100.64.0.2:22022`; publica `public/release.json` e valida `artifactRelease` igual ao SHA.
- **`AXION_PROVISIONING_WORKER_ENABLED`** só aparece em `services/axion-flow/server.js:1780` e `services/axion-flow/docs/BILLING_PROVISIONING.md:34`. **Não existe em nenhum compose ou `.env` versionado** → default `false`.
- **Evidência empírica de worker desligado**: a linha de `provisioning_outbox` criada pelo caso B1 (~19:45 UTC) ainda existia no teardown (~20:0x UTC), intervalo de ~15 minutos contra `AXION_PROVISIONING_WORKER_INTERVAL_MS` padrão de 2000 ms.
- `docker-compose.staging.yml` do Flow define `AXION_BILLING_WEBHOOK_ENABLED: ${AXION_BILLING_WEBHOOK_ENABLED:-false}` e `AXION_PAY_WEBHOOK_SECRET: ${AXION_PAY_WEBHOOK_SECRET:-}`; não declara a flag do worker.

---

## 5. GitHub

- Conta autenticada: `axion-dev-enterprise` (é **user**, não org — `gh api orgs/...` retorna 404).
- 25 repositórios acessíveis: `axion-flow` (privado), `axion-pay` (público), `axion-monorepo`, `axion-client-apps`, `agent-workspace-os`, `har-content-extractor`, `axion-financeiro`, `gads-mail-engine`, `vps-node-01`, `vr-sso-portal-clone`, `axion-voice`, `axion-data`, `sensix`, `axion-security`, `axion-observability`, `axion-pdv`, `axion-hub`, `axion-comm`, `axion-pdv-system`, `google-oauth-gateway`, `axion-main-api`, `axion-agencia-hub`, `axion-status`, `axion-auth`, `axion-docs`.
- Apenas 6 são públicos (`axion-pay`, `axion-client-apps`, `agent-workspace-os`, `har-content-extractor`, `gads-mail-engine`, `vr-sso-portal-clone`).

### 5.1 Workflows

| Repo | Workflow | Arquivo |
| :--- | :--- | :--- |
| axion-flow | AXION Flow — CI/CD Pipeline & VPS Deploy | `.github/workflows/ci-cd.yml` |
| axion-flow | AXION Flow — Hardening Branch CI | `.github/workflows/hardening-ci.yml` |
| axion-flow | AXION Pay — Staging isolado | `.github/workflows/pay-staging.yml` |
| axion-flow | AXION Staging — Operações governadas | `.github/workflows/staging-ops.yml` |
| axion-pay | AXION Pay Core / CI / CI/CD Pipeline & Vercel Deploy / Release | `axion-pay-core.yml`, `ci.yml`, `deploy.yml`, `release.yml` |

- **`hardening-ci.yml` está registrada como ativa, mas o arquivo não existe em `main`.** `git log --all -- .github/workflows/hardening-ci.yml` mostra 6 commits todos na branch `fix/runtime-guardrails-20260827`; últimos runs em 2026-08-27 (5, todos `success` exceto um `cancelled`). É uma workflow órfã de branch antiga.
- `staging-ops.yml`: 3 execuções, todas `success` (`36621483892` all, `36622982766` webhook-teardown, `36623127798` db-audit).
- Runs com falha recentes no `axion-flow`: somente os 4 runs antigos de `AXION Pay — Staging isolado` (pré-correção do PR #152).

### 5.2 Secrets por repositório (nomes apenas)

- `axion-flow`: `AXION_CREDENTIALS_KEY`, `AXION_PROD_ADMIN_PASSWORD`, `AXION_PROD_BENCHMARK_PASSWORD`, `AXION_PROD_JOSE_PASSWORD`, `AXION_PROD_JULIANA_PASSWORD`, `AXION_PROD_LUCAS_PASSWORD`, `AXION_SESSION_SECRET`, `FLOW_STAGING_WEBHOOK_SECRET`, `PAY_STAGING_TEST_KEY`, `VPS_HOST`, `VPS_PORT`, `VPS_SSH_KEY`, `VPS_SSH_PASSWORD`, `VPS_USER`.
- `axion-pay`: `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `VERCEL_TOKEN`.
- `axion-monorepo`: `VERCEL_TOKEN`.
- `vps-node-01` e `agent-workspace-os`: sem secrets acessíveis.

### 5.3 Proteção de branch: bloqueada pelo plano

`gh api .../branches/main/protection` retorna HTTP 403: *"Upgrade to GitHub Pro or make this repository public to enable this feature"* para `axion-flow` e `axion-monorepo`. Não há required checks, nem merge queue, nem regra de review. `axion-pay` (público) simplesmente **não tem proteção configurada**.

### 5.4 PRs abertos (7)

| Repo | PR | Título | Estado |
| :--- | :--- | :--- | :--- |
| axion-flow | #130 | fix: conectar planos AXION Flow ao billing real | DIRTY, criado 2026-09-04 |
| axion-flow | #87 | [agente][ci-cd] tornar descoberta do artefato portável | aberto |
| axion-flow | #73 | [P0][AUTH] Recuperar env de credenciais do container anterior | aberto |
| axion-flow | #70 | [P0][REGRESSION] Estabilizar gate de saúde do deploy | aberto |
| axion-flow | #58 | [Agent Engine] ReAct dinâmico, streaming progressivo e gate empírico | aberto |
| axion-pay | #29 | feat: harden trial settlement and staging delivery | **CLEAN**, `codex/staging-hardening`, +5305/−1065, criado 2026-09-29 |
| axion-monorepo | #8 | [codex][axion-auth] fix: enforce HttpOnly shared session | aberto |

PR #29 toca `app.ts`, `config.ts`, `openapi.ts`, `flow-billing.service.ts`, `docker-compose.staging.yml` e migrations `016`/`017`, mas **não** introduz RFC 7807 (única referência a `PAYMENTS_ENABLED` no patch é o valor `"false"` no compose).

---

## 6. Estado da integração AXION Pay → AXION Flow (já comprovado)

- Canal de ops criado no PR #154 (merge `5763fda`): `staging-ops.yml` com modos `all`, `pay-key`, `flow-webhook`, `db-audit`, `webhook-teardown`; `permissions: contents: read`; guarda de canal; backup + `chmod 600` do `.env` alvo.
- Auth da API do Pay no staging: `AXION_API_KEYS` formatado `segredo:merchantId:escopos`, merchant `staging-e2e`, fingerprint `4cf5fd2412da`; `GET /v1/sandbox/validate` devolve `200` com `authenticated:true`.
- 13 casos E2E manuais conformes: Pay 401/200/503/404/401 e webhook 401/202/200/401/401/400/400/400, todos RFC 7807 emitido pelo Flow.
- `AXION_PROVISIONING_WORKER_ENABLED` continua `false` (§4): evento chega ao `provisioning_outbox` e **não** gera tenant.
- Teardown executado (`36622982766`): `linhas_sinteticas_removidas=4`, `restantes=0`; auditoria final (`36623127798`): `schema_migrations`=18, contagens do Pay todas 0.

---

## 7. Veredito: o que os achados resolvem para 100%

| # | Lacuna | Resolve com o que foi achado? | Caminho |
| :--- | :--- | :--- | :--- |
| 1 | P0-04 `AXION_PROVISIONING_WORKER_ENABLED=false` | **Sim** | novo modo no `staging-ops` (`set_kv` + `docker compose up -d --force-recreate` + drenagem da outbox); canal já provado 3× |
| 2 | Fixture assinada automatizada em CI | **Sim** | job de workflow já existente (mesmo padrão dos modos atuais) |
| 3 | RFC 7807 no `axion-pay` | **Não** | mudança de código em `app.ts:833`/`:845` (hoje `{error: ...}`) |
| 4 | Ligar `PAYMENTS_ENABLED` | **Parcial** | provider é somente `woovi` com base sandbox (`config.ts:45,52`); `WOOVI_APP_ID` é exigido só em produção (`config.ts:104`), mas **não existe credencial Woovi no vault** |
| 5 | Fixture de merchant | **Sim** | SQL via modo `db-audit`/novo modo |
| 6 | Emissor dos eventos `subscription.*` | **Parcial** | dispatcher de merchant-webhooks do próprio Pay quando pagamentos ligados, ou job de CI |
| 7 | Backlog P1/P2 | **Não** | trabalho de produto |
| 8a | `Vercel \| failure` | **Parcial** | §2.4/§2.5 — identidade trocada e commit `6c9d0ad` enviado; checagem de autor superada, mas a integração Git está presa ao time `axion12` (HTTP 403) e mantém `state=failure` |
| 8b | Branch protection / required checks | **Não** | exige upgrade para GitHub Pro/Team ou repositório público |
| 9 | Commitar os 106 arquivos alterados (vault, docs, log) | **Decisão sua** | pendente de autorização explícita |

### Riscos novos identificados

1. ~20 hostnames da zona principal respondem 530 por túnel desligado.
2. 80/443 seguem abertos na origem; Zero Trust não implementado.
3. `db.example.com` público via proxy.
4. Apex `axiontemp777.buzz` aponta para `192.0.2.1` (endereço de documentação).
5. `hardening-ci.yml` órfã registrada como workflow ativa.
6. Nenhuma proteção de branch possível no plano atual.
7. `vps-node-01` versiona `node_modules/` e `dist-bundle.zip` no Git.

---

## 8. Decisões pendentes do operador

1. **Vercel (opção C executada e comprovada parcialmente)**: identidade trocada para `developer@example.com` (§2.4) e validada pelo commit de teste `6c9d0ad` (§2.5) — a checagem de autor desapareceu, mas `state=failure` continua por causa da integração Git presa ao time `axion12` (403 para a conta local). Escolher: **(i)** obter acesso/convite à conta `axion12`; **(ii)** remover a integração antiga (GitHub → Settings → Integrations, ou o dashboard `axion12`) e reconectar o repositório ao time `your-team-slug` — **mutação que exige autorização explícita**; **(iii)** ignorar o status (não há branch protection exigindo checks, §7).
2. **Pagamentos**: fornecer `WOOVI_APP_ID` de sandbox se quiser `PAYMENTS_ENABLED=true` no staging.
3. **Worker**: autorizar o modo `worker-enable` no `staging-ops` (exige commit + push).
4. **Commit do repositório raiz**: segue **sem autorização** — **operador respondeu "nada por enquanto"**. Só o commit de teste `6c9d0ad` em `services/axion-flow` foi autorizado. Observação: um processo externo (exportador whitelabel) versionou o workspace no branch `axion` durante esta sessão (`7bc6b99`, `7b1152a`), sem intervenção deste agente.
5. **Túneis**: decidir entre reativar túneis, remover registros DNS órfãos ou seguir para fechamento de portas.

---

## 9. Anexo — comandos reproduzíveis

```powershell
# Tailnet
tailscale ping -c 2 100.64.0.1
tailscale ping -c 2 100.64.0.2

# Status HTTP (nunca Invoke-WebRequest)
curl.exe -s -o NUL -w '%{http_code}' -m 15 -L https://agents.axiontemp777.buzz/health
curl.exe -s -m 15 -L https://agents.example.com/health

# GitHub
gh api repos/axion-dev-enterprise/axion-flow/commits/9176749/status
gh run list --repo axion-dev-enterprise/axion-flow --workflow 344095849 --limit 5
git log --all --oneline -- .github/workflows/hardening-ci.yml

# Vercel (somente leitura)
vercel whoami
vercel project ls

# Cloudflare (token do vault, sem imprimir valor)
python scripts/vault_loader.py audit
```
