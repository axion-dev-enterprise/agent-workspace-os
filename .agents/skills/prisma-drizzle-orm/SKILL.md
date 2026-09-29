---
name: prisma-drizzle-orm
description: >-
  Operational engineering skill for TypeScript ORMs (Drizzle ORM & Prisma), zero-downtime database migrations,
  schema evolution via Expand/Contract patterns, and serverless connection pooling.
---

# Modern TypeScript ORMs (Drizzle & Prisma) — Master Skill

Skill operacional canonica para modelagem de dados, execucao de migracoes deterministas com zero-downtime e consultas type-safe de alto desempenho utilizando **Drizzle ORM** e **Prisma** em ambientes Node.js, Vercel Edge e Cloudflare Workers.

---

## 1. Matriz de Decisão: Drizzle vs. Prisma

| Critério | Drizzle ORM | Prisma ORM |
| :--- | :--- | :--- |
| **Runtime & Edge** | 0 KB de binários Rust. Executa nativamente no Vercel Edge, Cloudflare Workers e D1. | Exige binário de query engine (Rust) ou Prisma Accelerate / Driver Adapters. |
| **Filosofia de Query** | SQL-Like declarativo (`db.select().from(users).where(...)`). | Abstração em grafos de objetos relacionais (`prisma.user.findUnique({ include: ... })`). |
| **Overhead de Memória** | Ultraleve (~5 MB RAM). Ideal para microsserviços efêmeros. | Moderado (~40-80 MB RAM devido ao engine). |
| **Geração de Tipos** | Tipagem inferida diretamente do schema TypeScript em tempo de compilação. | Geração de cliente via `prisma generate` após edição de `schema.prisma`. |
| **Melhor Para** | Backends edge, Workers D1, alta concorrência e controle fino de SQL. | Monólitos corporativos, NestJS e equipes focadas em produtividade rápida de CRUD. |

---

## 2. Migrações Zero-Downtime: O Padrão Expand & Contract

Nunca execute migrações destrutivas (`DROP COLUMN`, `RENAME COLUMN` ou `ALTER TABLE ... NOT NULL`) em uma única etapa em produção. Sistemas com múltiplas instâncias quebrarão imediatamente durante o deploy canary.

### 2.1 As 5 Fases do Padrão Expand/Contract (Exemplo: Renomear Coluna)
1. **Fase 1 (Expand)**: Adicione a nova coluna como nula (`nullable`) via migration:
   ```sql
   ALTER TABLE users ADD COLUMN phone_e164 VARCHAR(20);
   ```
2. **Fase 2 (Dual Write)**: No código da aplicação, grave em ambos os campos (`phone` e `phone_e164`), mas continue lendo do campo antigo.
3. **Fase 3 (Backfill)**: Execute script em background para migrar os dados legados para a nova coluna em lotes de 1.000 registros.
4. **Fase 4 (Switch Read)**: Altere o código para ler exclusivamente de `phone_e164` e pare de gravar no campo antigo.
5. **Fase 5 (Contract)**: Remova o campo antigo `phone` apenas na release seguinte via migração de limpeza:
   ```sql
   ALTER TABLE users DROP COLUMN phone;
   ```

---

## 3. Criação de Índices Não-Bloqueantes no PostgreSQL

Por padrão, `CREATE INDEX` adquire um lock compartilhado que bloqueia todas as escritas (`INSERT`, `UPDATE`, `DELETE`) na tabela durante a indexação:
- **Obrigatório em Produção**: Utilize sempre `CREATE INDEX CONCURRENTLY`:
  ```sql
  -- Correto: Indexa sem travar operacoes de escrita concorrentes
  CREATE INDEX CONCURRENTLY idx_transactions_created_at ON transactions (created_at DESC);
  ```

---

## 4. Connection Pooling em Ambientes Serverless

Em funções serverless (AWS Lambda, Vercel Serverless, Cloudflare Pages), cada requisição pode abrir uma nova conexão com o PostgreSQL, esgotando o limite (`max_connections = 100`) em segundos.

### 4.1 Regras Mandatórias de Pooling
- **PgBouncer / Supabase Pooler**: Conecte sempre através da porta do pooler (ex: `6543`) configurado em modo `transaction`.
- **Drizzle com Neon / Hyperdrive**:
  ```typescript
  import { drizzle } from 'drizzle-orm/neon-http';
  import { neon } from '@neondatabase/serverless';

  // Usa HTTP pooling sem overhead de conexao TCP stateful
  const sql = neon(process.env.DATABASE_URL!);
  export const db = drizzle(sql);
  ```
- **Prisma Client Singleton**: Nunca instancie `new PrismaClient()` dentro de route handlers. Mantenha instância única global em `lib/prisma.ts`.

---

## 5. O Utilitário CLI Standalone (`scripts/orm_migration_guard.py`)

A skill inclui um validador estático em Python stdlib para auditar migrações antes de aplicá-las ao banco produtivo:

```bash
# Auditar migrations do Prisma antes de rodar prisma migrate deploy
python .agents/skills/prisma-drizzle-orm/scripts/orm_migration_guard.py --dir prisma/migrations

# Auditar migrations do Drizzle antes de executar drizzle-kit push
python .agents/skills/prisma-drizzle-orm/scripts/orm_migration_guard.py --dir drizzle/migrations
```

---

## 6. Portão de Verificação (Verification Gate)

1. Nenhuma migração com `DROP COLUMN`, `DROP TABLE` ou `NOT NULL` sem default deve ser aprovada sem validação via `orm_migration_guard.py`.
2. Em produção, execute estritamente `prisma migrate deploy` (nunca `prisma migrate dev` ou `prisma db push`).
3. Toda consulta com filtros em tabelas com mais de 50.000 linhas deve ser respaldada por índice verificado via `EXPLAIN (ANALYZE)`.
