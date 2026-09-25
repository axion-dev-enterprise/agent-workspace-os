---
name: prisma-drizzle-orm
description: >-
  Operational skill for modern TypeScript ORMs (Drizzle ORM & Prisma), schema migrations, edge compatibility, and relation queries.
---

# Modern ORM (Drizzle & Prisma) Skill

Skill operacional para modelagem de banco de dados, migrations determinísticas e consultas tipadas em TypeScript.

## 1. Drizzle ORM (Edge-First & SQL-Like)
- Ideal para Cloudflare Workers (D1), Vercel Edge e ambientes serverless sem overhead de binários.
- Schemas declarativos em TypeScript com zero runtime code generation.

## 2. Prisma (Enterprise & Full-Featured)
- Ideal para servidores dedicados, NestJS e serviços com múltiplos relacionamentos aninhados.
- Sempre rodar `prisma migrate dev` em desenvolvimento e `prisma migrate deploy` na esteira de CI/CD.
