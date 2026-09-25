---
name: github-actions-cicd
description: >-
  Operational skill for designing automated GitHub Actions CI/CD pipelines, caching dependencies, semantic releases, and OIDC secretless deployments.
---

# GitHub Actions CI/CD Automation Skill

Skill operacional para automação de testes, validações de qualidade e entrega contínua com GitHub Actions.

## 1. Boas Práticas
- **Cache de Dependências**: Utilizar `actions/cache` ou `actions/setup-node` com `cache: 'npm'` para acelerar execuções de minutos para segundos.
- **OIDC Secretless**: Utilizar OpenID Connect (OIDC) para autenticar no AWS/GCP/Cloudflare sem precisar armazenar chaves de longa duração nos secrets do repositório.
- **Branch Protection**: Bloquear merges na `main` sem que a suíte de testes e linter aprovem o Pull Request.
