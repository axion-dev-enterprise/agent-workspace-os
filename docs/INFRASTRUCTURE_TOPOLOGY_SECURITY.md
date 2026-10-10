# Topologia Completa de Infraestrutura, Segurança & Tailnet Mesh

> **Status Global:** 🟢 **OPERACIONAL, BLINDADO & HOMOLOGADO**  
> **Data de Atualização:** 07 de Outubro de 2026  
> **Ecossistema:** AXION Enterprise Architecture  

---

## 1. Topologia da Rede Privada (Tailnet `taildb9106.ts.net`)

Rede mesh criptografada via WireGuard ponto-a-ponto, conectando a estação local de trabalho e os servidores remotos na nuvem Spaceship:

| Hostname | IP Privado Tailscale | IP Público / Origem | OS / Distribuição | Papel / Função | Status & Latência |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`poseidon`** (`desktop-1t1e46h`) | `100.64.188.73` | Localhost (SP) | Windows 10 | Estação Principal de Engenharia | 🟢 Online (Self, 35ms DERP-SP) |
| **`vps-node-01-core`** | `100.83.25.74` | `209.74.71.36` | Debian 13 (Trixie) | Nó 1: Core Gateway, Flow, Pay, Auth | 🟢 Online (166ms Direct WireGuard) |
| **`vps-node-01-clients`** | `100.93.18.70` | `209.74.86.49` | Debian 13 (Trixie) | Nó 2: Bots e Instâncias de Clientes | 🟢 Online (167ms Direct WireGuard) |

### Comandos Canônicos de Acesso via Tailnet:
```powershell
# Ping WireGuard direto
tailscale ping vps-node-01-core
tailscale ping vps-node-01-clients

# Conexão SSH segura pela rede privada Tailscale (sem expor tráfego na internet pública)
ssh root@100.83.25.74 -p 22022 -i vault/private/spaceship-ops/vps_ops_ed25519
ssh root@100.93.18.70 -p 22022 -i vault/private/spaceship-ops/vps_ops_ed25519

# Ou via Tailscale SSH Integrado
tailscale ssh root@vps-node-01-core
tailscale ssh root@vps-node-01-clients
```

---

## 2. Matriz de Defesa de Perímetro (Firewall, Fail2ban & SSH Hardening)

### 2.1 Firewall UFW (Nível de Host)
- **Política Padrão**: `Default: deny (incoming), allow (outgoing), deny (routed)`
- **Portas Liberadas**:
  - `22022/tcp` (OpenSSH porta alta com chave Ed25519)
  - `80/tcp` (HTTP Edge — roteado para `axion-gateway`)
  - `443/tcp` (HTTPS Edge — roteado para `axion-gateway` com Full Strict TLS)
- **Zero Attack Surface para Bancos de Dados**:
  - `axion-postgres` (`5432`), `axion-redis` (`6379`), `axion-auth-center` (`4000`), `axion-pay-core` (`3333`) operam estritamente dentro da bridge Docker `br-4f56fa534ce1` sem bind externo.
  - `axion-flow-core` (`3020`) e `gramaticalizando-app` (`3050`) escutam exclusivamente em `127.0.0.1` (loopback).

### 2.2 Fail2ban (Mitigação Ativa de Força Bruta)
- **Configuração Canônica**: `/etc/fail2ban/jail.local`
- **Ação de Bloqueio**: Integrado ao **UFW** (`banaction = ufw`)
- **Jail Ativa**: `sshd` monitorando a porta `22022` com `maxretry = 3`, `findtime = 10m`, `bantime = 2h`
- **Whitelist Defensiva (`ignoreip`)**: `127.0.0.1/8 ::1 100.64.0.0/10 189.62.150.126` (blindagem para que a Tailnet e o IP do operador nunca sofram drop acidental).

### 2.3 SSH Hardening
- Autenticação por senha desativada: `PasswordAuthentication no`
- Autenticação exclusiva por chave pública **Ed25519** (`vault/private/spaceship-ops/vps_ops_ed25519`)
- Porta: `22022` (mitigação de varreduras na porta 22 padrão)

---

## 3. Borda Global, CDN & Reverse Proxy

### 3.1 Cloudflare Edge WAF
- **Zona**: `example.com`
- **Roteamento Primário**:
  - `api.example.com` ➔ `209.74.71.36` (Modo Proxied, WAF e DDoS L3-L7 ativos)
  - `auth.example.com` ➔ `209.74.71.36` (Modo Proxied)
  - `api.pay.example.com` ➔ `209.74.71.36` (Modo Proxied)
  - `*.example.com` ➔ `76.76.21.21` (Vercel Anycast Edge)
- **Criptografia TLS**: Modo Full Strict com certificado Cloudflare Origin CA instalado em `/etc/nginx/ssl/origin.crt`.

### 3.2 Nginx Gateway Container (`axion-gateway`)
- Arquitetura de proxy reverso unificada sob o container `axion-gateway`:
  - `/flow/` ➔ `http://axion-flow-core:3020` (WebSockets habilitados, `Upgrade`, timeouts de 300s)
  - `/pay/` e `/v1/` ➔ `http://axion-pay-core:3333` (Motor de pagamentos AXION Pay)
  - `/healthz` ➔ Probe de integridade `200 OK`
  - `auth.example.com` ➔ `http://axion-auth-center:4000` (Handshake OAuth e PKCE)
  - `gramaticalizando.example.com` ➔ `http://gramaticalizando-app:3050`

---

## 4. Matriz de Health Checks Factuais

| Alvo / Serviço | Endpoint / Host | Método | Resposta Factual | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Nginx Edge Gateway** | `https://api.example.com/healthz` | `GET` | `HTTP 200 OK` | 🟢 HEALTHY |
| **AXION Flow Backend** | `https://api.example.com/flow/health` | `GET` | `HTTP 200 OK` | 🟢 HEALTHY |
| **AXION Flow Frontend** | `https://flow.example.com` | `GET` | `HTTP 200 OK` | 🟢 HEALTHY |
| **Central de Autenticação** | `https://auth.example.com/api/auth/me` | `GET` | `HTTP 401 Unauthorized` (Fail-closed) | 🟢 HEALTHY |
| **Gramaticalizando LMS** | `https://gramaticalizando.example.com` | `GET` | `HTTP 200 OK` | 🟢 HEALTHY |
| **Nó 1 WireGuard Mesh** | `100.83.25.74:22022` | ICMP / SSH | `166ms direct` | 🟢 HEALTHY |
| **Nó 2 WireGuard Mesh** | `100.93.18.70:22022` | ICMP / SSH | `167ms direct` | 🟢 HEALTHY |
