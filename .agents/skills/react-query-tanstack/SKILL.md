---
name: react-query-tanstack
description: >-
  Operational skill for asynchronous server state management using TanStack Query v5 (React Query), optimistic updates, caching, and prefetching.
---

# TanStack Query (React Query) v5 Skill

Skill operacional para gerenciamento de estado de servidor no frontend, cache reativo e sincronização em tempo real.

## 1. Padrões
- **Query Keys Declarativas**: Sempre estruture chaves como arrays hierárquicos: `['users', userId, 'profile']`.
- **Mutações Otimistas**: Atualizar a UI imediatamente no `onMutate` com rollback seguro no `onError`.
- **Evitar Over-fetching**: Configurar `staleTime` razoável (ex: 1 a 5 minutos) para dados que mudam com pouca frequência.
