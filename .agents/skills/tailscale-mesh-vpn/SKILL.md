---
name: tailscale-mesh-vpn
description: >-
  Operational skill for Tailscale Mesh VPN and Tailnet infrastructure operations.
  Use when connecting to remote VPS nodes, managing MagicDNS, Tailscale SSH,
  secure peer-to-peer file transfer (Taildrop), private mesh routing, and public ingress via Tailscale Funnel.
---

# Tailscale & Tailnet Operations Skill

Skill operacional para gerenciamento de rede mesh privada, nós computacionais remotos, MagicDNS, túneis WireGuard e acesso seguro via **Tailscale** no ecossistema da **Enterprise Organization**.

---

## 1. Topologia da Tailnet (`{{TAILNET_DOMAIN}}`)

- **Conta / Administrador**: `admin@example.com`
- **Domínio MagicDNS**: `{{TAILNET_DOMAIN}}`
- **Nó Local**: `{{LOCAL_NODE_NAME}}` (`100.64.0.1` - Windows / Linux)
- **DERP Primário**: São Paulo (11.9ms latency)

### 1.1 Tabela de Nós Conectados
| Hostname | IP Tailscale | IP Público / Origem | OS | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`desktop-1t1e46h`** | `100.64.188.73` | Localhost | Windows | 🟢 Online (Self) |
| **`primary-gateway-node`** | `100.64.0.1` | `198.51.100.1` | Linux | 🟢 Online (212ms) |
| **`primary-db-node`** | `100.64.0.2` | `198.51.100.2` | Linux | 🟢 Online (171ms) |
| **`legacy-app-node`** | `100.64.0.3` | `198.51.100.3` | Linux | 🟢 Online (7ms) |
| **`sensix-ai-studio-vps`** | `100.69.94.49` | - | Linux | 🔴 Offline |
| **`sensix-black-vps`** | `100.86.168.13` | - | Linux | 🔴 Offline |

---

## 2. Comandos Operacionais Essenciais

### 2.1 Diagnóstico & Status da Rede
```powershell
# Verificar status de todos os nós da tailnet
tailscale status

# Testar conectividade direta WireGuard com um nó
tailscale ping primary-gateway-node
tailscale ping legacy-app-node

# Verificar latência dos servidores DERP e roteamento UDP
tailscale netcheck
```

### 2.2 Conexão SSH Segura (Tailscale SSH)
Conectar a qualquer nó Linux sem necessidade de gerenciar ou expor portas SSH na internet aberta:
```powershell
# Conectar diretamente ao VPS da AXION
tailscale ssh root@primary-gateway-node
# Ou pelo IP Tailscale
tailscale ssh root@100.64.0.1
```

### 2.3 Compartilhamento de Arquivos Seguro (Taildrop)
Transferir arquivos diretamente e criptografados entre máquinas da tailnet:
```powershell
# Enviar arquivo para o VPS
tailscale file cp ./build.tar.gz primary-gateway-node:

# Receber arquivos enviados no Windows
tailscale file get .
```

### 2.4 Exposição de Serviços Locais (Tailscale Serve & Funnel)
```powershell
# Compartilhar porta local 3000 de forma privada para a Tailnet com HTTPS automático
tailscale serve https / http://127.0.0.1:3000

# Expor serviço local publicamente para a internet com certificado TLS válido (ótimo para webhooks)
tailscale funnel 3000 on

# Desativar exposição
tailscale serve reset
tailscale funnel reset
```
