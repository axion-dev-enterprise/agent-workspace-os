---
name: postgresql-advanced-optimization
description: >-
  Operational skill for PostgreSQL query optimization, index tuning (B-Tree, GIN, BRIN), connection pooling with PgBouncer, and vacuum diagnostics.
---

# PostgreSQL Advanced Optimization Skill

Skill operacional para tuning de performance, indexação e escalabilidade em bancos de dados relacionais PostgreSQL.

## 1. Diretrizes de Indexação
- **Índices Compostos**: A ordem das colunas no índice deve seguir: `Igualdade -> Range/Comparação -> Ordenação (ORDER BY)`.
- **Índices Parciais**: Quando consultar frequentemente subconjuntos (ex: `WHERE status = 'active'`), crie índices parciais para economizar RAM e disco:
  `CREATE INDEX idx_orders_active ON orders (customer_id) WHERE status = 'active';`
- **Análise com EXPLAIN**: Nunca deduza lentidão sem rodar `EXPLAIN (ANALYZE, BUFFERS) <query>;`. Verifique se há `Seq Scan` em tabelas grandes.
