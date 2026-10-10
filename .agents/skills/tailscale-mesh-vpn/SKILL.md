---
name: tailscale-mesh-vpn
description: >-
  Operational skill for Tailscale Mesh VPN and Tailnet infrastructure operations.
  Use when connecting to remote VPS nodes, managing MagicDNS, Tailscale SSH,
  secure peer-to-peer file transfer (Taildrop), private mesh routing, and public ingress via Tailscale Funnel.
---

# Tailscale & Tailnet Operations Skill

Skill operacional para gerenciamento de rede mesh privada, nós computacionais remotos, MagicDNS, túneis WireGuard e acesso seguro via **Tailscale** no ecossistema da **AXION Enterprise**.

---

## 1. Topologia da Tailnet (`taildb9106.ts.net`)

- **Conta / Administrador**: `Operator@example.com`
- **Domínio MagicDNS**: `taildb9106.ts.net`
- **Nó Local**: `desktop-1t1e46h` (`100.64.188.73` - Windows 10)
- **DERP Primário**: São Paulo (11.9ms latency)

### 1.1 Tabela de Nós Conectados
| Hostname | IP Tailscale | IP Público / Origem | OS | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`poseidon`** (`desktop-1t1e46h`) | `100.64.188.73` | Localhost | Windows | 🟢 Online (Self) |
| **`vps-node-01-core`** | `100.83.25.74` | `209.74.71.36` | Linux (Debian 13) | 🟢 Online (166ms direct) |
| **`vps-node-01-clients`** | `100.93.18.70` | `209.74.86.49` | Linux (Debian 13) | 🟢 Online (167ms direct) |
| **`vps-node-01-104-207-90-167`** | `100.64.0.1` | `104.207.90.167` | Linux | 🟢 Online (212ms) |
| **`debian-2vcpu-amd-4gb-us-6tb9d`** | `100.64.0.2` | `104.207.81.120` | Linux | 🟢 Online (171ms) |
| **`juliana-vps`** | `100.81.231.111` | `179.197.237.20` | Linux | 🟢 Online (7ms) |
| **`sensix-ai-studio-vps`** | `100.69.94.49` | - | Linux | 🔴 Offline |
| **`sensix-black-vps`** | `100.86.168.13` | - | Linux | 🔴 Offline |

---

## 2. Comandos Operacionais Essenciais

### 2.1 Diagnóstico & Status da Rede
```powershell
# Verificar status de todos os nós da tailnet
tailscale status

# Testar conectividade direta WireGuard com um nó
tailscale ping vps-node-01-104-207-90-167
tailscale ping juliana-vps

# Verificar latência dos servidores DERP e roteamento UDP
tailscale netcheck
```

### 2.2 Conexão SSH Segura (Tailscale SSH)
Conectar a qualquer nó Linux sem necessidade de gerenciar ou expor portas SSH na internet aberta:
```powershell
# Conectar diretamente ao VPS da AXION
tailscale ssh root@vps-node-01-104-207-90-167
# Ou pelo IP Tailscale
tailscale ssh root@100.64.0.1
```

### 2.3 Compartilhamento de Arquivos Seguro (Taildrop)
Transferir arquivos diretamente e criptografados entre máquinas da tailnet:
```powershell
# Enviar arquivo para o VPS
tailscale file cp ./build.tar.gz vps-node-01-104-207-90-167:

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
