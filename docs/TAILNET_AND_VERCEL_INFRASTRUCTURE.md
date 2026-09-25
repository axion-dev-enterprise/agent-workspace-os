# Mapeamento Completo de Hardware, OS, Stack e Serviços: Tailnet & Vercel

> **Data de Varredura**: 2026-09-25  
> **Status de Conectividade**: Testado e Validado via Sondas de Rede e APIs  
> **Domínio MagicDNS**: `taildb9106.ts.net`  
> **Time Vercel**: `axion777`  

---

## 1. Topologia da Tailnet (Nós, Hardware, OS & Serviços)

### 1.1 `desktop-1t1e46h` (Estação de Engenharia Local)
- **IP Tailscale**: `100.64.188.73`
- **Sistema Operacional**: Windows 10 Pro 64-bit (Build 19045)
- **Processador (CPU)**: Intel(R) Core(TM) i5-3470 CPU @ 3.20GHz (4 Cores / 4 Threads)
- **Memória RAM**: 12 GB DDR3 (6.66 GB livres)
- **Armazenamento**:
  - `C:` SSD 223 GB (178 GB livres) — Sistema Operacional & Workspaces
  - `E:` HD 1 TB (931 GB livres) — Armazenamento Pesado & Backups
- **Stack & Tooling**:
  - Python 3.11.9 & Python 3.14.7
  - Node.js LTS v24.19.0 & npm
  - Git v2.55.0.3, GitHub CLI v2.101.0
  - Wrangler CLI v4.138.0 (Cloudflare)
  - Vercel CLI v59.26.0
  - GAM 7.48.12 (Google Apps Manager)
  - Tailscale v1.102.4 (WireGuard Mesh)
- **Função**: Estação de desenvolvimento, orquestração de agentes e execução local de scripts.

---

### 1.2 `axion-vps-104-207-90-167` (Gateway & Proxy Primário AXION)
- **IP Tailscale**: `100.95.86.83`
- **IP Público**: `104.207.90.167` (Vultr Cloud Compute)
- **Sistema Operacional**: Linux x86_64
- **Portas Abertas**: `80` (HTTP), `443` (HTTPS), `8080` (Traefik Dashboard/API)
- **Latência WireGuard**: 212 ms
- **Stack de Infraestrutura**:
  - **Reverse Proxy**: Traefik Proxy v3 (Roteamento dinâmico via Docker labels)
  - **Container Engine**: Docker & Docker Compose
- **Serviços & Subdomínios DNS Vinculados**:
  - `api.axionenterprise.cloud` — API Principal AXION
  - `auth.axionenterprise.cloud` — Gateway Unificado de Autenticação
  - `casa.axionenterprise.cloud` & `preview.casa.axionenterprise.cloud` — Portal Casa
  - `hooks.axionenterprise.cloud` — Receptor de Webhooks de Alta Velocidade
  - `registry.axionenterprise.cloud` — Registry Privado de Imagens Docker
  - `gramaticalizando.axionenterprise.cloud` — Serviço Gramaticalizando

---

### 1.3 `debian-2vcpu-amd-4gb-us-6tb9d` (Serviços Centrais, DB & Agentes)
- **IP Tailscale**: `100.73.36.87`
- **IP Público**: `104.207.81.120` (Vultr US)
- **Sistema Operacional**: Debian GNU/Linux
- **Hardware**: 2 vCPU AMD, 4 GB RAM, 6 TB Transferência
- **Portas Abertas**: `80` (HTTP), `443` (HTTPS)
- **Latência WireGuard**: 171 ms
- **Serviços & Subdomínios DNS Vinculados**:
  - `db.axionenterprise.cloud` — Banco de Dados Relacional Principal (PostgreSQL)
  - `agents.axionenterprise.cloud` — Plataforma Autônoma de Agentes (Setor Flow)
  - `tasks.axionenterprise.cloud` — Filas de Tarefas Assíncronas (Celery / BullMQ)
  - `voice.axionenterprise.cloud` — Runtime Neural TTS/STT & WebRTC (Setor Voice)
  - `hermes.axionenterprise.cloud` — Hermes Research Agent
  - `waba.axionenterprise.cloud` — WhatsApp Business API Gateway
  - `mail.axionenterprise.cloud`, `smtp.axionenterprise.cloud`, `imap.axionenterprise.cloud` — Servidor de E-mail Spacemail

---

### 1.4 `juliana-vps` (Hermes Central — W Soluções Tecnologia)
- **IP Tailscale**: `100.81.231.111`
- **IP de Origem**: `179.197.237.20` (Conexão dedicada Brasil, Provedor Claro/Net)
- **Sistema Operacional**: Linux x86_64
- **Portas Abertas**: `22` (Tailscale SSH Ativo), `80` (HTTP)
- **Latência WireGuard**: **7 ms** (Ultra-baixa latência nacional)
- **Web Server**: Nginx v1.31.4
- **Aplicação Ativa**:
  - **Hermes Central** (`W Soluções Tecnologia`)
  - Painel com tema escuro, autenticação para `Juliana`
  - Módulos: Agente Central Executivo, Conectores Omnichannel, Cofre Seguro de Integrações

---

### 1.5 Nós Sensix (Em Standby / Offline)
- **`sensix-ai-studio-vps`** (`100.69.94.49` - Linux): Nó de inferência e estúdio de modelos Sensix (offline há 27d).
- **`sensix-black-vps`** (`100.86.168.13` - Linux): Nó da operação Sensix Black (offline há 8d).

---

## 2. Ecossistema Vercel (`axion777`) — 12 Projetos Mapeados

Varredura de stack, status HTTP e frameworks de cada deployment de produção:

| Projeto | URL de Produção | Framework / Stack | Status HTTP | Descrição / Título Identificado |
| :--- | :--- | :--- | :--- | :--- |
| `landing-page-teste-w-solucoes` | [Link](https://landing-page-teste-w-solucoes.vercel.app) | HTML / Tailwind | 🟢 200 OK | AXION Enterprise — Inovação & Automação |
| `landing-page-teste` | [Link](https://landing-page-teste-woad.vercel.app) | HTML / Tailwind | 🟢 200 OK | AXION Enterprise — Inovação & Automação |
| `ifood-dashboard` | [Link](https://ifood-dashboard-tau.vercel.app) | HTML / Dashboard SPA | 🟢 200 OK | Empório Caraíva — Dashboard iFood & Planilhas |
| `meta-gpt-worker` | [Link](https://meta-gpt-worker.vercel.app) | Tailwind CSS / SPA | 🟢 200 OK | Positive Mind — Gestão de Marketing |
| ~~`proxion-hub`~~ | *Descomissionado* | HTML / Estático | ⚪ REMOVIDO | *Projeto e domínio proxionmidia.com removidos em 2026-09-25* |
| `axion-vps-api-contingencia` | [Link](https://axion-vps-api-contingencia.vercel.app) | API Serverless | 🟡 404 | Endpoint de contingência / fallback |
| `axion-flow` | [Link](https://axion-flow-gamma.vercel.app) | **Next.js (React)** | 🟢 200 OK | AXION FLOW — Sistema Comercial Autônomo |
| `axion-flow-homepage` | [Link](https://axion-flow-homepage.vercel.app) | HTML / Landing | 🟢 200 OK | AXION FLOW — Automação Comercial com IA |
| `axion-conferencia-pecas` | [Link](https://axion-conferencia-pecas.vercel.app) | Google AI Studio App | 🟢 200 OK | App utilitário de conferência de peças |
| `growth-accelerator-main` | [Link](https://yannascimentoads.com) | **Vite / React** | 🟢 200 OK | Yan Nascimento — Gestor de Tráfego Pago |
| `rosireis-atelier` | [Link](https://rosireis.com.br) | E-commerce SPA | 🟢 200 OK | Loja online de Atelier Rosi Reis |
| `vercel-ai-gateway-demo` | [Link](https://vercel-ai-gateway-demo-axion777.vercel.app) | **Next.js (React)** | 🟢 200 OK | Demonstração Vercel AI Gateway |
