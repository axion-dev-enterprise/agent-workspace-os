---
name: graphql-apollo-federation
description: >-
  Operational skill for designing declarative GraphQL schemas, type-safe resolvers, DataLoader n+1 mitigation, and Apollo Federation subgraphs.
---

# GraphQL & Apollo Federation Skill

Skill operacional para APIs GraphQL declarativas, seguras contra problemas de N+1 e integradas em federação.

## 1. Boas Práticas
- **DataLoader**: Sempre agrupar e memorizar buscas em lote para evitar problemas de N+1 queries no banco de dados.
- **Complexity Limiter**: Limitar a profundidade e a complexidade das queries recebidas para prevenir ataques de negação de serviço (DoS).
- **Tipagem Estrita**: Gerar tipos TypeScript automaticamente a partir do schema via GraphQL Code Generator.
