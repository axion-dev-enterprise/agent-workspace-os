# Inventário de Infraestrutura, Repositórios e Serviços

> **Template Canônico**: Este documento serve como referência e modelo padronizado para catalogação de ativos, repositórios, serviços cloud e nós de computação gerenciados pelo ecossistema do **Agent Workspace OS**.

---

## 1. Repositórios GitHub (`{{GITHUB_ORG}}`)

| Repositório | Visibilidade | Stack Principal | Descrição / Papel no Ecossistema |
| :--- | :---: | :--- | :--- |
| `{{WORKSPACE_SLUG}}-monorepo` | Privado | TypeScript / Node | Monorepo central — aplicações, serviços e pacotes compartilhados |
| `agent-workspace-os` | Público | Python / Markdown | The Deterministic Operating Framework for Autonomous AI Software Engineering |
| `{{WORKSPACE_SLUG}}-flow` | Privado | Python / FastAPI | Plataforma de agentes autônomos e orquestração de workflows |
| `{{WORKSPACE_SLUG}}-web` | Público | Next.js / React | Frontend institucional e portal do usuário |
| `{{WORKSPACE_SLUG}}-infra` | Privado | Terraform / Docker | Infraestrutura como Código, playbooks de automação e nós compute |

---

## 2. Frontends & Serveless Edge (`{{PRIMARY_DOMAIN}}`)

| Aplicação / Projeto | Provedor | Framework | Domínio / Alias Canônico |
| :--- | :---: | :---: | :--- |
| **Portal Principal** | Edge / Vercel | Next.js 15 | `https://app.{{PRIMARY_DOMAIN}}` |
| **Landing Page** | Edge / Pages | Tailwind / HTML | `https://www.{{PRIMARY_DOMAIN}}` |
| **API Gateway** | Cloudflare Workers | TypeScript | `https://api.{{PRIMARY_DOMAIN}}` |
| **Status Page** | Cloudflare Pages | Estático | `https://status.{{PRIMARY_DOMAIN}}` |

---

## 3. Rede Mesh & Conectividade Privada (Zero Public Attack Surface)

| Nó / Servidor | IP Privado Mesh | OS / Kernel | Função Canônica |
| :--- | :---: | :---: | :--- |
| `primary-gateway-node` | `100.x.y.z` | Linux (Debian/Ubuntu) | Gateway de microsserviços, Traefik Reverse Proxy e Ingress privado |
| `primary-db-node` | `100.x.y.z` | Linux (Debian/Ubuntu) | Instância dedicada de Banco de Dados Relacional (PostgreSQL 16) e Cache |
| `agent-worker-node` | `100.x.y.z` | Linux (Debian/Ubuntu) | Workers de processamento assíncrono, background daemons e filas |

---

## 4. Google Workspace & Serviços de Produtividade

| Recurso | Identificador / Domínio | Configuração & Auditoria |
| :--- | :---: | :--- |
| **Domínio Conectado** | `{{PRIMARY_DOMAIN}}` | Gerenciado via GAM 7 com Service Account e Domain-wide Delegation |
| **Storage & Drive** | Google Drive | Estrutura de pastas compartilhadas e backup corporativo |
| **Admin de Governança** | `admin@{{PRIMARY_DOMAIN}}` | Credenciais isoladas no cofre de segredos local |

---

## 5. Boas Práticas de Governança
- **Zero Hardcoded Secrets**: Nunca registre chaves de API, credenciais de banco ou tokens de acesso neste inventário.
- **Isolamento de Tenant**: Todo identificador de servidor, IP público ou segredo deve residir em `workspace.config.json` ou gerenciador de segredos.
