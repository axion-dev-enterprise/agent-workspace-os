---
name: cloudflare-edge-ops
description: >-
  Operational skill for Cloudflare Edge Infrastructure via Wrangler CLI and Cloudflare API.
  Use when developing, deploying, configuring, or debugging Cloudflare Workers, Pages,
  D1 Relational SQL Databases, KV Namespaces, R2 Object Storage, Queues, and DNS routing
  for example.com.
---

# Cloudflare Edge Ops Skill

Skill operacional para gerenciamento, automação e deploy de microserviços, workers, páginas e bancos de dados edge no ecossistema Cloudflare da **AXION Enterprise**.

---

## 1. Identificadores & Ambiente

- **Conta Cloudflare**: `AXION`
- **Account ID**: `your_cloudflare_account_id`
- **Zona DNS Primária**: `example.com` (Zone ID: `73c333a9254c46fbe8522616f735d4fa`)
- **CLI Principal**: `wrangler` (Node.js LTS v24.19.0)

---

## 2. Comandos Operacionais Mais Frequentes

### 2.1 Workers (APIs & Microserviços Edge)
```powershell
# Listar todos os workers ativos na conta
wrangler workers list

# Iniciar servidor local de desenvolvimento com bindings simulados
wrangler dev --port 8787

# Publicar worker em produção
wrangler deploy

# Visualizar logs em tempo real (Tail logs)
wrangler tail <worker-name> --format=pretty
```

### 2.2 Cloudflare D1 (Bancos de Dados Relacionais SQLite Edge)
```powershell
# Listar bancos D1 existentes
wrangler d1 list

# Executar query SQL no banco local (desenvolvimento)
wrangler d1 execute <db-name> --local --command "SELECT * FROM users LIMIT 10;"

# Executar migration ou query no banco remoto de produção
wrangler d1 execute <db-name> --remote --file=./schema.sql
```

### 2.3 KV Namespaces & R2 Storage
```powershell
# Listar KV namespaces
wrangler kv namespace list

# Gravar e consultar chave/valor no KV
wrangler kv key put --namespace-id=<ID> "chave_teste" "valor_conteudo"
wrangler kv key get --namespace-id=<ID> "chave_teste"

# Gerenciar buckets R2
wrangler r2 bucket list
wrangler r2 object put <bucket-name>/arquivo.zip --file=./local.zip
```

### 2.4 Cloudflare Pages
```powershell
# Publicar diretório de build para Pages
wrangler pages deploy dist --project-name=<project-name>

# Listar deployments do Pages
wrangler pages deployment list --project-name=<project-name>
```

---

## 3. Padrão Canônico `wrangler.toml`

Todo novo Worker do ecossistema AXION deve seguir o padrão determinístico:

```toml
name = "axion-service-name"
main = "src/index.ts"
compatibility_date = "2026-09-01"
compatibility_flags = ["nodejs_compat"]

[vars]
ENVIRONMENT = "production"
AXION_API_GATEWAY = "https://api.example.com"

# Exemplo de binding D1
[[d1_databases]]
binding = "DB"
database_name = "axion-core-db"
database_id = "<DATABASE_ID>"

# Exemplo de binding KV
[[kv_namespaces]]
binding = "CACHE"
id = "<KV_NAMESPACE_ID>"
```
