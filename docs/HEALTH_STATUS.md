# Painel de Saúde & Auto-Fix da Infraestrutura

> **Última Varredura**: 2026-09-25 02:12:47 (UTC: 2026-09-25T05:12:47.726297+00:00)  
> **Status Global do Sistema**: 🟢 **OPERACIONAL E SAUDÁVEL**  

---

## 1. Nós da Rede Privada (Tailnet)

| Nó / Servidor | IP Tailscale | Função | Status | Latência |
| :--- | :--- | :--- | :--- | :--- |
| `axion-vps-104-207-90-167` | `100.95.86.83` | Traefik Gateway & API | 🟢 HEALTHY | 196ms |
| `debian-2vcpu-amd-4gb-us-6tb9d` | `100.73.36.87` | PostgreSQL & Flow Engine | 🟢 HEALTHY | 170ms |

---

## 2. Endpoints Web, Vercel & Edge

| Aplicação | URL | Status | Resposta HTTP |
| :--- | :--- | :--- | :--- |
| **AXION Flow (Vercel)** | [https://axion-flow-gamma.vercel.app](https://axion-flow-gamma.vercel.app) | 🟢 HEALTHY | `200` |
| **AXION Flow Homepage (Vercel)** | [https://axion-flow-homepage.vercel.app](https://axion-flow-homepage.vercel.app) | 🟢 HEALTHY | `200` |
| **Yan Nascimento Ads (Vite)** | [https://yannascimentoads.com](https://yannascimentoads.com) | 🟢 HEALTHY | `200` |
| **Traefik Dashboard (Tailnet Internal)** | [http://100.95.86.83:8080](http://100.95.86.83:8080) | 🟢 HEALTHY | `200` |

---

## 3. Estação de Trabalho Local & Armazenamento

- **Espaço em Disco (`C:`)**: 177.75 GB livres de 222.86 GB (79.8%) — Status: **HEALTHY**
- **Unidade de Backups (`E:`)**: 928.06 GB livres de 930.94 GB (99.7%) — Status: **HEALTHY**
- **Último Backup Offline Verificado**: `2026-09-25T05:09:38.690627+00:00` (Integridade: **COMPLETED**)
- **Ações de Auto-Fix Executadas**: Nenhuma intervenção necessária (sistema íntegro)

---

## Sincronização & Execução Contínua
Para rodar a verificação de saúde e auto-recuperação a qualquer momento:
```powershell
python scripts/health_monitor_autofix.py
```
