# Mapa Canônico Mestre da Infraestrutura — AXION Enterprise

> **Última Varredura Exhaustiva**: 2026-09-25 02:19:41 (UTC: 2026-09-25T05:19:41.274610+00:00)  
> **Classificação**: Confidencial / Arquitetura e Ativos Corporativos  
> **Operador do Sistema**: `AXION DEV <axionenterprise777@gmail.com>`  

---

## Resumo Executivo dos Ativos Digitais

| Camada / Ecossistema | Recurso Primário | Quantidade Total | Status |
| :--- | :--- | :--- | :--- |
| **GitHub** (`axion-dev-enterprise`) | Repositórios de Código | **25** (19 privados, 6 públicos) | 🟢 Ativo |
| **Cloudflare** (`AXION`) | Zonas & Domínios DNS | **6** zonas (**158** registros DNS) | 🟢 Ativo |
| **Cloudflare Edge** | Tunnels, Workers, Pages | **15** túneis, **15** workers, **5** pages | 🟢 Ativo |
| **Cloudflare Storage** | D1 Databases & KV | **1** D1 DB, **3** KV namespaces | 🟢 Ativo |
| **Vercel** (`axion777`) | Projetos em Produção | **11** projetos (**20** aliases/domínios) | 🟢 Ativo |
| **Tailnet Mesh** (`taildb9106.ts.net`) | Servidores & Nós | **3** nós online / **1** nó descomissionado / **2** nós standby | 🟢 Ativo |
| **Google Workspace** | Contas & Ativos no Drive | **141** arquivos mapeados via GAM | 🟢 Autorizado (DwD) |
| **Armazenamento Offline** | Unidade de Backup `E:\` | **928.06 GB** livres (Dump PostgreSQL & Git) | 🟢 Operacional |

---

## 1. Mapeamento Completo do GitHub (`axion-dev-enterprise`)

- **Conta**: `AXION DEV` (`axion-dev-enterprise`)
- **E-mail**: `axionenterprise777@gmail.com` | **Site**: [https://axionenterprise.cloud](https://axionenterprise.cloud)

| Repositório | Visibilidade | Linguagem | Branch | Último Push | Descrição |
| :--- | :---: | :---: | :---: | :---: | :--- |
| [axion-monorepo](https://github.com/axion-dev-enterprise/axion-monorepo) | 🔒 Privado | `JavaScript` | `main` | 2026-09-21 | Monorepo AXION â€” apps, services, packages |
| [agent-workspace-os](https://github.com/axion-dev-enterprise/agent-workspace-os) | 🌐 Público | `HTML` | `main` | 2026-09-18 | The Deterministic Operating Framework for Autonomous AI Software Engineering. |
| [axion-client-apps](https://github.com/axion-dev-enterprise/axion-client-apps) | 🌐 Público | `TypeScript` | `main` | 2026-09-17 | [MONOREPO DEV] Sites e Aplicativos de Clientes AXION Enterprise (Estuda Junto, Edna Grahl, PositiveMind, etc.) |
| [har-content-extractor](https://github.com/axion-dev-enterprise/har-content-extractor) | 🌐 Público | `Python` | `main` | 2026-09-12 | ExtraÃ§Ã£o inteligente de conteÃºdo de qualquer site via anÃ¡lise de HAR com IA |
| [axion-financeiro](https://github.com/axion-dev-enterprise/axion-financeiro) | 🔒 Privado | `HTML` | `master` | 2026-09-12 | — |
| [axion-pay](https://github.com/axion-dev-enterprise/axion-pay) | 🌐 Público | `TypeScript` | `main` | 2026-09-12 | [SETOR PAY] Portal Frontend SPA & Checkout de Pagamentos (pay.axionenterprise.cloud) |
| [gads-mail-engine](https://github.com/axion-dev-enterprise/gads-mail-engine) | 🌐 Público | `TypeScript` | `main` | 2026-09-12 | Plataforma de disparo transacional via Brevo, cloaker defensivo, open tracking 1x1, UTMs e Meta CAPI |
| [axion-flow](https://github.com/axion-dev-enterprise/axion-flow) | 🔒 Privado | `Python` | `main` | 2026-09-09 | [SETOR FLOW] Plataforma AutÃ´noma de Agentes & IA Multi-Tenant (agents.axionenterprise.cloud) |
| [axion-vps](https://github.com/axion-dev-enterprise/axion-vps) | 🔒 Privado | `JavaScript` | `main` | 2026-09-05 | [SETOR VPS] Infraestrutura CanÃ´nica, Docker Compose, AutomaÃ§Ãµes e Scripts de Deploy VPS |
| [vr-sso-portal-clone](https://github.com/axion-dev-enterprise/vr-sso-portal-clone) | 🌐 Público | `TypeScript` | `main` | 2026-09-04 | — |
| [axion-voice](https://github.com/axion-dev-enterprise/axion-voice) | 🔒 Privado | `TypeScript` | `main` | 2026-09-03 | [SETOR VOICE] Runtime Neural TTS/STT, FastMCP Server, WebRTC & Agente de Voz AutÃƒÂ´nomo |
| [axion-data](https://github.com/axion-dev-enterprise/axion-data) | 🔒 Privado | `TypeScript` | `main` | 2026-09-03 | [SETOR DATA] App Data â€” Pipelines de Dados, Analytics, BI e RelatÃ³rios Automatizados |
| [sensix](https://github.com/axion-dev-enterprise/sensix) | 🔒 Privado | `HTML` | `master` | 2026-09-03 | [MONOREPO SENSIX] Ecossistema Completo Sensix (Storefront, Models, OP Black, AtacadÃ£o, Bots Telegram e AXION HOT) |
| [axion-security](https://github.com/axion-dev-enterprise/axion-security) | 🔒 Privado | `Python` | `main` | 2026-09-03 | [SETOR SECURITY] Painel de Auditoria de Vulnerabilidades, Relays e TÃƒÂºneis Defensivos |
| [axion-observability](https://github.com/axion-dev-enterprise/axion-observability) | 🔒 Privado | `HTML` | `main` | 2026-09-03 | [SETOR OPS] Telemetria IsomÃƒÂ³rfica, Coletor RFC 7807, Grafana, Prometheus e Kuma |
| [axion-pdv](https://github.com/axion-dev-enterprise/axion-pdv) | 🔒 Privado | `JavaScript` | `main` | 2026-09-03 | [SETOR PDV] Sistema Offline-First para Varejo FÃƒÂ­sico, Frente de Caixa e Retaguarda |
| [axion-hub](https://github.com/axion-dev-enterprise/axion-hub) | 🔒 Privado | `JavaScript` | `main` | 2026-09-03 | [SETOR HUB] Registry de Conectores de Agentes, Webhooks SatÃƒÂ©lites e IntegraÃƒÂ§ÃƒÂµes Externas |
| [axion-comm](https://github.com/axion-dev-enterprise/axion-comm) | 🔒 Privado | `JavaScript` | `main` | 2026-09-03 | [SETOR COMM] Gateway de Mensageria, Baileys WhatsApp Bridge, Filas de Envio & Dispatch |
| [axion-pdv-system](https://github.com/axion-dev-enterprise/axion-pdv-system) | 🔒 Privado (Arquivado) | `JavaScript` | `main` | 2026-07-30 | Auto-criado do backup mirror |
| [google-oauth-gateway](https://github.com/axion-dev-enterprise/google-oauth-gateway) | 🔒 Privado (Arquivado) | `JavaScript` | `main` | 2026-07-29 | Auto-criado do backup mirror |
| [axion-main-api](https://github.com/axion-dev-enterprise/axion-main-api) | 🔒 Privado (Arquivado) | `JavaScript` | `main` | 2026-07-28 | Auto-criado do backup mirror |
| [axion-agencia-hub](https://github.com/axion-dev-enterprise/axion-agencia-hub) | 🔒 Privado (Arquivado) | `JavaScript` | `main` | 2026-07-28 | Auto-criado do backup mirror |
| [axion-status](https://github.com/axion-dev-enterprise/axion-status) | 🔒 Privado (Arquivado) | `TypeScript` | `main` | 2026-07-28 | Auto-criado do backup mirror |
| [axion-auth](https://github.com/axion-dev-enterprise/axion-auth) | 🔒 Privado | `—` | `master` | 2026-07-28 | App Auth â€” autenticaÃ§Ã£o/autorizaÃ§Ã£o |
| [axion-docs](https://github.com/axion-dev-enterprise/axion-docs) | 🔒 Privado (Arquivado) | `—` | `main` | 2026-07-28 | Source of Truth â€” regras, arquitetura, processos, RAG |

---

## 2. Mapeamento Cloudflare (Zonas, DNS, Túneis & Edge)

### 2.1 Zonas DNS Ativas

| Zona / Domínio | ID Cloudflare | Registros DNS | Nameservers | Status |
| :--- | :--- | :---: | :--- | :--- |
| **`axionenterprise.cloud`** | `ee5ca653ddcb0ea528e3f18042bfff3c` | **100** | leia.ns.cloudflare.com, neil.ns.cloudflare.com | 🟢 active |
| **`axionflow.my`** | `cddc53eb007e17db5f91400234e5fb0e` | **16** | leia.ns.cloudflare.com, neil.ns.cloudflare.com | 🟢 active |
| **`axiontemp777.buzz`** | `7cae6d24fbb358f1c69a515ed7b57b55` | **7** | leia.ns.cloudflare.com, neil.ns.cloudflare.com | 🟢 active |
| **`icesvaliant.shop`** | `1060f59415119c4a6bf1adc175a9e17d` | **14** | leia.ns.cloudflare.com, neil.ns.cloudflare.com | 🟢 active |
| **`psicologaednagrahl.com.br`** | `2aef2e7b4257c469a8c5fba93c0de05d` | **11** | leonard.ns.cloudflare.com, tess.ns.cloudflare.com | 🟢 active |
| **`yannascimentoads.com`** | `0fda358a02c95c03bdc4659ce4ef2d04` | **10** | leia.ns.cloudflare.com, neil.ns.cloudflare.com | 🟢 active |

### 2.2 Cloudflare Zero Trust / Argo Tunnels

| Nome do Túnel | ID do Túnel | Status | Tipo | Criado Em |
| :--- | :--- | :---: | :---: | :--- |
| `Automação AXION` | `72ccd81e-bf61-4e58-b827-8db367691e9c` | ⚪ DOWN | `cfd_tunnel` | 2026-03-21 |
| `Terço de Noiva - Desiree` | `ab0ddaf0-042b-42fa-ad9a-fde3f7c2f5d5` | inactive | `cfd_tunnel` | 2026-03-27 |
| `axion-auth` | `5bc9feef-80d0-42ae-985a-4bafd334a370` | ⚪ DOWN | `cfd_tunnel` | 2026-04-05 |
| `axion-oauth` | `809186ad-e312-4d6c-b3d0-9564bc880756` | ⚪ DOWN | `cfd_tunnel` | 2026-03-26 |
| `axion-osint-tunnel` | `653798d5-1b60-4f06-acdf-1aedc2c64dea` | ⚪ DOWN | `cfd_tunnel` | 2026-07-22 |
| `axion-poseidon` | `16ca17a1-aa8d-4581-a45f-c2646d6178a3` | inactive | `cfd_tunnel` | 2026-07-21 |
| `axion-ssh` | `1836db77-219c-4dda-b729-42d30bd2c9e2` | ⚪ DOWN | `cfd_tunnel` | 2026-04-21 |
| `axion-ssh-fixed` | `9a34f331-d49d-4f13-81df-f1255c249175` | inactive | `cfd_tunnel` | 2026-05-17 |
| `axion-ssh-new` | `44d7e5a5-445b-45f8-9ca9-d2a4f149f18b` | inactive | `cfd_tunnel` | 2026-05-17 |
| `axion-tunnel` | `1bd7f753-edea-4e30-94ad-bc5fb48cfb13` | inactive | `cfd_tunnel` | 2026-03-25 |
| `ig-webhook` | `8bfda0ca-c18c-484b-b2ea-976c01f67873` | ⚪ DOWN | `cfd_tunnel` | 2026-03-27 |
| `mimo-demo` | `771a2dfc-0f22-454d-8f89-65e99e369550` | ⚪ DOWN | `cfd_tunnel` | 2026-03-27 |
| `pontotecc-web` | `28aadd71-9d58-4a0f-84cb-666da996959f` | ⚪ DOWN | `cfd_tunnel` | 2026-03-30 |
| `simonello` | `14c1ef48-273d-46b2-b576-94cd8a540cf8` | ⚪ DOWN | `cfd_tunnel` | 2026-03-23 |
| `trydelta` | `1bfbaf29-46eb-48ff-85e7-65675d65631d` | ⚪ DOWN | `cfd_tunnel` | 2026-03-27 |

### 2.3 Cloudflare Serverless: Workers & Pages

| Aplicação | Tipo | Detalhes / Subdomínio | Modificado / Criado |
| :--- | :---: | :--- | :--- |
| `ana-proxy` | Worker (Script) | Modelo: `standard` | 2026-04-28 |
| `axion-404-gateway` | Worker (Script) | Modelo: `standard` | 2026-09-09 |
| `axion-flow-homepage` | Worker (Script) | Modelo: `standard` | 2026-05-25 |
| `axion-flow-proxy` | Worker (Script) | Modelo: `standard` | 2026-05-25 |
| `axion-github-auth` | Worker (Script) | Modelo: `standard` | 2026-04-04 |
| `axion-lead-webhook` | Worker (Script) | Modelo: `standard` | 2026-07-09 |
| `axion-meta-webhook` | Worker (Script) | Modelo: `standard` | 2026-07-09 |
| `axion-qr-system` | Worker (Script) | Modelo: `standard` | 2026-06-01 |
| `axion-temp-landing` | Worker (Script) | Modelo: `standard` | 2026-05-25 |
| `axion-vps-proxy` | Worker (Script) | Modelo: `standard` | 2026-07-23 |
| `mp-payroll-worker` | Worker (Script) | Modelo: `standard` | 2026-04-04 |
| `pdv-worker` | Worker (Script) | Modelo: `standard` | 2026-06-01 |
| `poseidon` | Worker (Script) | Modelo: `standard` | 2026-07-21 |
| `sicrety-edge-proxy` | Worker (Script) | Modelo: `standard` | 2026-08-20 |
| `vps-axion-api` | Worker (Script) | Modelo: `standard` | 2026-07-22 |
| `axion-status` | Pages (Frontend) | Branch: `main` \| Domínios: axion-status.pages.dev | 2026-06-01 |
| `axion-landing` | Pages (Frontend) | Branch: `main` \| Domínios: axion-landing.pages.dev | 2026-06-01 |
| `axion-flow` | Pages (Frontend) | Branch: `master` \| Domínios: axion-flow.pages.dev | 2026-05-29 |
| `facebusca-routes-app` | Pages (Frontend) | Branch: `main` \| Domínios: facebusca-routes-app.pages.dev, facebusca-routes.axionenterprise.cloud | 2026-04-12 |
| `painel-axion` | Pages (Frontend) | Branch: `main` \| Domínios: painel-axion.pages.dev, painel.axionenterprise.cloud | 2026-04-04 |

### 2.4 Cloudflare Storage: D1 Database & KV Namespaces

| Recurso | Tipo | Identificador | Metadados |
| :--- | :---: | :--- | :--- |
| `vps-axion-db` | D1 Database | `ee34dc06-2416-405d-b717-694650f580b9` | Tabelas: 0 \| Tamanho: None bytes |
| `AXION_TELEMETRY` | KV Namespace | `12c59d643a6f4bb8b7e2a5e3b1c5953a` | Suporte URL Encoding: True |
| `QR_KV` | KV Namespace | `360ca2ef6fb0488891e9fa7e9d4be9b7` | Suporte URL Encoding: True |
| `AXION_LEADS` | KV Namespace | `b9af499f70d14796a81515e651a0f577` | Suporte URL Encoding: True |

---

## 3. Mapeamento Vercel (`axion777`)

| Projeto | Framework | URL de Produção | Título / Aplicação | Status HTTP |
| :--- | :--- | :--- | :--- | :---: |
| **`landing-page-teste-w-solucoes`** | `HTML / Estático` | [https://landing-page-teste-w-solucoes.vercel.app](https://landing-page-teste-w-solucoes.vercel.app) | AXION Enterprise — Inovação & Automação Inteligente | 🟢 200 OK |
| **`landing-page-teste`** | `HTML / Estático` | [https://landing-page-teste-woad.vercel.app](https://landing-page-teste-woad.vercel.app) | AXION Enterprise — Inovação & Automação Inteligente | 🟢 200 OK |
| **`ifood-dashboard`** | `HTML / Estático` | [https://ifood-dashboard-tau.vercel.app](https://ifood-dashboard-tau.vercel.app) | Empório Caraíva — Dashboard iFood & Plano de Ação | 🟢 200 OK |
| **`meta-gpt-worker`** | `Tailwind CSS / SPA` | [https://meta-gpt-worker.vercel.app](https://meta-gpt-worker.vercel.app) | Positive Mind - Gestão de Marketing | 🟢 200 OK |
| **`axion-vps-api-contingencia`** | `Desconhecido` | [https://axion-vps-api-contingencia.vercel.app](https://axion-vps-api-contingencia.vercel.app) | HTTP Error 404: Not Found | 🟡 Erro/Inativo |
| **`axion-flow`** | `Next.js (React)` | [https://axion-flow-gamma.vercel.app](https://axion-flow-gamma.vercel.app) | AXION FLOW — Sistema Comercial Autônomo | 🟢 200 OK |
| **`axion-flow-homepage`** | `HTML / Estático` | [https://axion-flow-homepage.vercel.app](https://axion-flow-homepage.vercel.app) | AXION FLOW — Automação Comercial com IA | Capture e Converta Leads 24/7 | 🟢 200 OK |
| **`axion-conferencia-pecas`** | `HTML / Estático` | [https://axion-conferencia-pecas.vercel.app](https://axion-conferencia-pecas.vercel.app) | My Google AI Studio App | 🟢 200 OK |
| **`growth-accelerator-main`** | `Vite / React (Vite)` | [https://yannascimentoads.com](https://yannascimentoads.com) | Yan Nascimento | Gestor de Tráfego Pago para Negócios Locais | 🟢 200 OK |
| **`rosireis-atelier`** | `HTML / Estático` | [https://rosireis.com.br](https://rosireis.com.br) | Loja online de Atelier Rosi Reis | 🟢 200 OK |
| **`vercel-ai-gateway-demo`** | `Next.js (React)` | [https://vercel-ai-gateway-demo-axion777.vercel.app](https://vercel-ai-gateway-demo-axion777.vercel.app) | Login – Vercel | 🟢 200 OK |

---

## 4. Topologia Tailnet & Nós de Computação

### 4.1 Nós da Rede Privada (Mesh WireGuard)

| Nome do Host | IP Tailscale | Sistema Operacional | Status | Conexão |
| :--- | :--- | :--- | :--- | :--- |
| **`DESKTOP-1T1E46H`** *(Local)* | `100.64.188.73` | windows | 🟢 ONLINE | Nó Local (Estação) |
| **`juliana-vps`** | `100.81.231.111` | linux | ⚪ DESCOMISSIONADO (25/09/2026) | Tailnet Peer |
| **`sensix-black-vps`** | `100.86.168.13` | linux | ⚪ OFFLINE (visto 2026-09-16) | Tailnet Peer |
| **`sensix-ai-studio-vps`** | `100.69.94.49` | linux | ⚪ OFFLINE (visto 2026-08-28) | Tailnet Peer |
| **`axion-vps-104-207-90-167`** | `100.95.86.83` | linux | 🟢 ONLINE | Tailnet Peer |
| **`debian-2vcpu-amd-4gb-us-6tb9d`** | `100.73.36.87` | linux | 🟢 ONLINE | Tailnet Peer |

### 4.2 Registro Canônico de Nós Descomissionados & Cold Vault

| Hostname | IP Anterior | Data de Descomissionamento | Backup Preservado | Status Cold Vault |
| :--- | :--- | :--- | :--- | :--- |
| **`juliana-vps`** | `100.81.231.111` | 2026-09-25 | `hermes_db_final.sql.gz` (135 tabelas, 88936 bytes) | 🟢 100% PRESERVADO |

> **Ações Realizadas no Descomissionamento**: 8 contêineres Docker encerrados, Docker daemon desabilitado (`systemctl disable --now docker`), Tailscale desautenticado (`tailscale logout`), snapshot integral do banco PostgreSQL e tarball de código salvos em `E:\backups\axion_enterprise\decommission_juliana_vps_final_archive\`.

---

## 5. Google Workspace (`axionenterprise.cloud`) & Armazenamento

- **Domínio Corporativo**: `axionenterprise.cloud`
- **Customer ID**: `C03xtme8f`
- **Administrador**: `iago@axionenterprise.cloud`
- **Delegação Global (DwD)**: 🟢 **FULLY_AUTHORIZED** (42 escopos autorizados)
- **Ativos Mapeados no Drive**: **141 documentos e atas**

### 5.1 Armazenamento Físico & Tarefas Agendadas

- **Disco do Sistema (`C:`)**: 177.75 GB livres de 222.86 GB
- **Disco de Backups (`E:`)**: 928.06 GB livres de 930.94 GB
- **Tarefas Agendadas no Windows**: `AXION-Health-Watchdog` (a cada 30 min) e `AXION-Enterprise-Backup` (diário às 03:00)

---

## Conclusão do Mapeamento
Todo o ecossistema AXION Enterprise está rigorosamente catalogado, criptograficamente assegurado e documentado em fonte canônica.
