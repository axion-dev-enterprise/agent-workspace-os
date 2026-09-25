# Auditoria de Superfície de Ataque & Arquitetura Zero Trust — AXION

> **Data/Hora**: 2026-09-25 02:18:34 (UTC: 2026-09-25T05:18:34.626958+00:00)  
> **Classificação**: Confidencial / Engenharia de Segurança & Redes  
> **Objetivo**: Fechamento de portas públicas expostas e transição para o *AXION Unified Fabric*  

---

## 1. Mapeamento da Superfície de Ataque Externa (IPs Públicos vs Tailnet)

| Servidor / Nó | IP Público | Porta | Status Público | Status Tailnet (Privado) | Risco & Ação Recomendada |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `80` | 🔴 **ABERTA** | 🟢 Aberta (Tailnet) | 🟡 **MÉDIO** — Tráfego web direto. Migrar para Cloudflare Tunnel para fechar portas públicas. |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `443` | 🔴 **ABERTA** | 🟢 Aberta (Tailnet) | 🟡 **MÉDIO** — Tráfego web direto. Migrar para Cloudflare Tunnel para fechar portas públicas. |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `8080` | 🟢 Fechada / Filtrada | 🟢 Aberta (Tailnet) | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `22` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `5432` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `axion-vps-104-207-90-167` | `104.207.90.167` | `6379` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `80` | 🔴 **ABERTA** | 🟢 Aberta (Tailnet) | 🟡 **MÉDIO** — Tráfego web direto. Migrar para Cloudflare Tunnel para fechar portas públicas. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `443` | 🔴 **ABERTA** | 🟢 Aberta (Tailnet) | 🟡 **MÉDIO** — Tráfego web direto. Migrar para Cloudflare Tunnel para fechar portas públicas. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `22` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `5432` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `6379` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `104.207.81.120` | `8000` | 🟢 Fechada / Filtrada | ⚪ Inativa | 🟢 **SEGURO** — Porta protegida contra varredura pública externa. |

---

## 2. Plano Canônico de Execução: Fechamento de Superfície (Zero Public Attack Surface)

### 2.1 Regras de Firewall UFW Recomendadas para os VPS
Executar nos servidores remotos para restringir todo tráfego de entrada não encapsulado:
```bash
# 1. Definir políticas padrão restritivas
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 2. Permitir loopback e rede privada WireGuard
sudo ufw allow in on lo
sudo ufw allow in on tailscale0

# 3. Opcional: Se mantiver HTTP/S direto, permitir apenas ranges oficiais Cloudflare
# curl -s https://www.cloudflare.com/ips-v4 | while read ip; do sudo ufw allow proto tcp from $ip to any port 80,443; done

# 4. Ativar firewall
sudo ufw --force enable
```

### 2.2 Roteamento de Dashboards Internos via Cloudflare Access
- **Traefik Dashboard (`100.95.86.83:8080`)**: Configurar túnel `cloudflared` direcionando `admin.axionenterprise.cloud` para `http://localhost:8080` com política de login por OTP para `@axionenterprise.cloud`.
- **Resultado**: Eliminação total de ataques automatizados de força bruta, port scanners e exploração de CVEs em portas de gerenciamento.

---

## Conclusão da Auditoria
O ecossistema dispõe de todos os componentes necessários (Cloudflare Tunnels, MagicDNS e Tailscale Mesh) para operar com zero superfície de ataque pública direta.
