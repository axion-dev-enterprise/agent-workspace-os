---
name: graphql-apollo-federation
description: >-
  Operational engineering skill for declarative GraphQL schemas, type-safe resolvers, DataLoader N+1 query mitigation, query complexity bounding, and Apollo Federation v2 subgraphs.
---

# GraphQL & Apollo Federation Engineering Skill

Guia operacional para projeto de schemas declarativos, unificação de supergrafos com Apollo Federation v2, mitigação de sobrecarga N+1 no banco de dados e controle de complexidade de consultas.

---

## 1. Arquitetura Apollo Federation v2

Em sistemas distribuídos, cada serviço expõe um **subgraph** especializado que contribui para um grafo unificado (**supergraph**):

### 1.1 Entidades Federadas (`@key` e `@shareable`)
Defina tipos extensíveis que outros subgrafos possam complementar:

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.3",
        import: ["@key", "@shareable", "@external"])

type User @key(fields: "id") {
  id: ID!
  email: String!
  name: String! @shareable
}

# No Subgraph de Pagamentos:
extend type User @key(fields: "id") {
  id: ID! @external
  invoices: [Invoice!]!
}
```

---

## 2. Mitigação Estrita de N+1 com DataLoader

Nunca execute consultas SQL/ORM individuais dentro de resolvedores de campo aninhados:

### 2.1 Padrão Canônico em Node.js / TypeScript
```typescript
import DataLoader from 'dataloader';

// O DataLoader DEVE ser instanciado dentro do contexto da requisição, NUNCA como singleton global!
export function createLoaders(db: DatabaseClient) {
  return {
    userLoader: new DataLoader<string, User>(async (userIds) => {
      // Uma única query SQL 'WHERE id IN (...)' para resolver múltiplos nós da árvore GraphQL
      const users = await db.users.findMany({
        where: { id: { in: [...userIds] } },
      });
      const userMap = new Map(users.map((u) => [u.id, u]));
      // A ordem do array retornado DEVE ser idêntica ao array de chaves recebido
      return userIds.map((id) => userMap.get(id) || null);
    }),
  };
}

// Resolver:
const resolvers = {
  Post: {
    author: (post, _, { loaders }) => loaders.userLoader.load(post.authorId),
  },
};
```

---

## 3. Segurança & Bounding de Consultas

GraphQL permite consultas recursivas e aninhamento infinito que podem derrubar a infraestrutura (ataque DoS):

1. **Limite de Profundidade (Depth Limit)**: Imponha um limite máximo de aninhamento (ex: 6 ou 7 níveis) via `graphql-depth-limit`.
2. **Paginação Obrigatória**: Nunca exponha listas raiz ilimitadas. Exija `first` e `after` (Cursor-based) ou `limit` e `offset`:
   ```graphql
   type Query {
     users(first: Int = 20, after: String): UserConnection!
   }
   ```
3. **Desativação de Introspecção em Produção**: Desative `introspection: false` em ambientes produtivos públicos, mantendo apenas logs de tracing com Apollo Studio/Router.

---

## 4. Ferramental Integrado

Audite arquivos de schema `.graphql` ou `.gql` com o linter embutido:
```powershell
python .agents/skills/graphql-apollo-federation/scripts/graphql_schema_linter.py <schema.graphql-ou-pasta>
```
O linter valida:
- Tipos de entidade sem diretiva `@key` em subgrafos federados.
- Consultas de raiz retornando listas sem argumentos de paginação.
- Diretivas `@deprecated` desprovidas de justificativa explícita.
