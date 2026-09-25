---
name: sentry-error-tracking
description: >-
  Operational skill for Sentry SDK instrumentation, frontend/backend error grouping, release tracking, source map uploads, and performance profiling.
---

# Sentry Error Monitoring & Profiling Skill

Skill operacional para rastreamento de bugs em produção com captura de pilha de execução e reprodução de sessões.

## 1. Diretrizes
- **Source Maps**: Sempre enviar source maps durante a esteira de build/CI e nunca expô-los publicamente no bundle de produção.
- **Sanitização de Dados (PII)**: Usar hooks `beforeSend` para remover senhas, dados de cartão ou tokens dos logs enviados ao Sentry.
