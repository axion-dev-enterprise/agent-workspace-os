---
name: cloudflare-zero-trust-tunnels
description: >-
  Operational skill for Cloudflare Zero Trust, cloudflared daemon management, private network routing,
  ingress rules, public port closing (Zero Public Attack Surface), Access policies (SSO/mTLS/OTP),
  service tokens, and WAF protection across AXION enterprise infrastructure.
---

# Cloudflare Zero Trust Tunnels Skill — AXION Enterprise

Guia canônico e operacional para implantação de arquitetura **Zero Public Attack Surface** na infraestrutura da **AXION Enterprise**, utilizando **Cloudflare Tunnels (`cloudflared`)** e **Cloudflare Access** para conectar nós computacionais privados à borda global sem exposição de portas públicas.

---

## 1. Princípios da Arquitetura Zero Public Attack Surface

1. **Nenhuma Porta Aberta para a Internet Pública**: Portas como `80`, `443`, `8080`, `5432` ou `22` não devem aceitar conexões diretas da internet pública nos nós VPS.
2. **Conexão de Saída Criptografada (Outbound Only)**: O daemon `cloudflared` estabelece túneis quádruplos de saída para os edge datacenters da Cloudflare (via protocolo `quic` ou `http2`).
3. **WAF & DDoS Shield Obrigatórios**: Todas as requisições passam pela borda da Cloudflare, inspecionando tokens JWT, assinaturas de bots, regras de rate limit e certificados mTLS antes de atingir o servidor de origem.

---

## 2. Instalação e Configuração do `cloudflared` no Linux

### 2.1 Instalação do Pacote Debian
```bash
# Adicionar repositório oficial Cloudflare
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

sudo apt-get update && sudo apt-get install -y cloudflared
```

### 2.2 Estrutura Canônica de Configuração (`config.yml`)
```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /etc/cloudflared/<TUNNEL_UUID>.json
protocol: quic

ingress:
  # Roteamento 1: API Gateway Interno
  - hostname: api.example.com
    service: http://127.0.0.1:8080
    originRequest:
      connectTimeout: 10s
      noTLSVerify: true

  # Roteamento 2: Painel de Autenticação / SSO
  - hostname: auth.example.com
    service: http://127.0.0.1:3000

  # Roteamento 3: Tasks & Workers
  - hostname: tasks.example.com
    service: http://127.0.0.1:5000

  # Regra de Captura Obrigatória (404 Fallback)
  - service: http_status:404
```

### 2.3 Instalação como Serviço Systemd
```bash
# Instalar daemon do serviço
sudo cloudflared service install

# Iniciar e habilitar no boot
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared

# Diagnóstico de conectividade
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -f
```

---

## 3. Fechamento de Portas com Firewall (UFW / Iptables)

Uma vez que o túnel Cloudflare e a Tailnet estão operacionais, o firewall do host deve rejeitar tráfego de entrada não autorizado:
```bash
# Permitir loopback local
sudo ufw allow in on lo

# Permitir tráfego privado da interface Tailscale (tailscale0)
sudo ufw allow in on tailscale0

# Permitir conexões estabelecidas de saída
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Ativar firewall restritivo
sudo ufw enable
```

---

## 4. Políticas de Cloudflare Access (Zero Trust)

### 4.1 Proteção de Dashboards Administrativos
Para rotas internas como Traefik Dashboard (`100.64.0.1:8080`) ou pgAdmin:
1. Criar aplicação no **Zero Trust Dashboard** -> **Access** -> **Applications**.
2. **Domain**: `admin.example.com`.
3. **Políticas de Autenticação**:
   - `Allow Emails`: `*@example.com`.
   - `Two-Factor Authentication (OTP / Google SSO)` obrigatório.

### 4.2 Service Tokens (Machine-to-Machine)
Para chamadas diretas entre Cloudflare Workers e VPS:
- Utilizar cabeçalhos `CF-Access-Client-Id` e `CF-Access-Client-Secret`.
- O daemon `cloudflared` valida as credenciais na borda antes de despachar a chamada para a porta do microsserviço.
