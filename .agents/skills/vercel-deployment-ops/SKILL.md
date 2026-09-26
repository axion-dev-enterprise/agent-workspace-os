---
name: vercel-deployment-ops
description: >-
  Operational skill for Vercel CLI, Project Management, Domains, Serverless RSC Deployments,
  Preview Branches, Edge Middleware, and Rollback Operations. Use when configuring, deploying,
  inspecting, managing aliases, or troubleshooting applications under team {{VERCEL_SCOPE}}.
---

# Vercel Deployment Ops Skill — Enterprise Organization

Guia canônico e operacional para orquestração de projetos, deploys em produção, gestão de domínios, aliases e resolução de incidentes no ecossistema **Vercel** da **Enterprise Organization** (Team Scope: `{{VERCEL_SCOPE}}`).

---

## 1. Contexto & Escopo Corporativo

- **Equipe / Team Scope**: `{{VERCEL_SCOPE}}`
- **Conta Primária**: `{{VERCEL_ACCOUNT_ID}}` (`AXION DEV`)
- **CLI Instalada**: `vercel` v59.26.0 (Node.js LTS v24.19.0)
- **Topologia de Produção**: 11 projetos ativos (Next.js 15, Vite/React, Tailwind SPAs e APIs serverless)

---

## 2. Comandos Operacionais Essenciais

### 2.1 Inspeção e Listagem de Projetos
```powershell
# Listar todos os projetos no escopo corporativo
vercel project ls --scope {{VERCEL_SCOPE}}

# Inspecionar configurações detalhadas de um projeto específico
vercel project inspect <project-name> --scope {{VERCEL_SCOPE}}

# Listar todos os aliases e domínios vinculados
vercel alias ls --scope {{VERCEL_SCOPE}}

# Listar domínios registrados/delegados
vercel domains ls --scope {{VERCEL_SCOPE}}
```

### 2.2 Deploy e Promoção para Produção
```powershell
# Deploy de Preview / Staging
vercel --scope {{VERCEL_SCOPE}}

# Deploy direto para Produção (com build remoto ou pré-construído)
vercel --prod --scope {{VERCEL_SCOPE}}

# Deploy pré-construído localmente (Zero Remote Build Overhead)
npm run build
vercel deploy --prebuilt --prod --scope {{VERCEL_SCOPE}}
```

### 2.3 Gestão de Variáveis de Ambiente
```powershell
# Baixar variáveis de ambiente de produção para arquivo local .env.production
vercel env pull .env.production --environment=production --scope {{VERCEL_SCOPE}}

# Adicionar uma variável de ambiente em produção
vercel env add MINHA_VARIAVEL production --scope {{VERCEL_SCOPE}}

# Listar variáveis configuradas em um projeto
vercel env ls --scope {{VERCEL_SCOPE}}
```

### 2.4 Vinculação de Domínios e Aliases Customizados
```powershell
# Adicionar domínio ao projeto
vercel domains add app.example.com --scope {{VERCEL_SCOPE}}

# Associar alias específico a uma URL de deployment
vercel alias set <deployment-url.vercel.app> app.example.com --scope {{VERCEL_SCOPE}}

# Remover alias de contingência ou projeto antigo
vercel alias rm app-antigo.example.com --scope {{VERCEL_SCOPE}}
```

### 2.5 Rollback Rápido de Produção
```powershell
# Listar deployments recentes de um projeto
vercel ls <project-name> --scope {{VERCEL_SCOPE}}

# Reverter tráfego instantaneamente para deployment saudável anterior
vercel rollback <deployment-url-ou-id> --scope {{VERCEL_SCOPE}}
```

---

## 3. Descomissionamento Seguro de Projetos

Para evitar "Subdomain Takeover" ou rotas zumbis em DNS:
1. Primeiro, listar os aliases associados via `vercel alias ls --scope {{VERCEL_SCOPE}}`.
2. Remover qualquer registro CNAME correspondente no Cloudflare / DNS antes ou logo após.
3. Excluir o projeto de forma não-interativa:
```powershell
echo y | vercel project rm <project-name> --scope {{VERCEL_SCOPE}}
```

---

## 4. Otimização de Edge Middleware & Core Web Vitals

1. **Headers de Segurança Obrigatórios (`vercel.json`)**:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```
2. **Caching no Edge**:
   - Para assets estáticos imutáveis: `Cache-Control: public, max-age=31536000, immutable`.
   - Para páginas dinâmicas com ISR no Next.js: `export const revalidate = 60;`.
