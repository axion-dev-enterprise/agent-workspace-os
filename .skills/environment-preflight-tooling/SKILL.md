---
name: environment-preflight-tooling
description: Verificação de runtimes, diagnóstico de CLIs (Git, Node, Python, GitHub, Vercel, Cloudflare) e prevenção de falhas de ambiente.
---

# Environment Preflight & Tooling

## Visão Geral
Garante que todas as ferramentas e credenciais necessárias existam antes que o agente inicie comandos destrutivos ou builds longos.

## Matriz de Ferramentas Mandatórias
| Ferramenta | Comando de Validação | Instalação Windows |
|---|---|---|
| **Python 3** | `python --version` | `winget install Python.Python.3.11` |
| **Node.js LTS** | `node -v` | `winget install OpenJS.NodeJS.LTS` |
| **Git** | `git --version` | `winget install Git.Git` |
| **GitHub CLI** | `gh --version` | `winget install GitHub.cli` |
| **Vercel CLI** | `vercel --version` | `npm install -g vercel` |
| **Wrangler** | `wrangler --version` | `npm install -g wrangler` |

## Verificação Programática
Execute:
```bash
python scripts/preflight_check.py
```
O script retorna JSON estruturado com status de cada ferramenta e estado de autenticação OAuth.
