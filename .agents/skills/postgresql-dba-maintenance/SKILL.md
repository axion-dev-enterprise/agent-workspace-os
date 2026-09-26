---
name: postgresql-dba-maintenance
description: >-
  Operational DBA skill for PostgreSQL 15/16 database administration, maintenance, vacuum analyze,
  index bloat mitigation, autovacuum tuning, query performance analysis (EXPLAIN ANALYZE), connection pooling
  with PgBouncer, physical and logical backups (pg_dump, WAL archiving), and point-in-time recovery across AXION nodes.
---

# PostgreSQL DBA Maintenance Skill — AXION Enterprise

Guia canônico e operacional para administração de bancos de dados PostgreSQL em ambientes de produção da **AXION Enterprise**. Cobre rotinas preventivas de manutenção, recuperação de espaço, otimização de consultas e resiliência de dados.

---

## 1. Princípios Fundamentais de Operação DBA

1. **Nunca executar `VACUUM FULL` em produção durante horário comercial**: `VACUUM FULL` adquire `ACCESS EXCLUSIVE LOCK` na tabela, bloqueando leituras e gravações. Em vez disso, utilize `VACUUM (ANALYZE, VERBOSE)` ou a extensão `pg_repack` para compactação sem lock.
2. **Monitore Autovacuum Contínuo**: Tabelas com alta taxa de mutação (ex: mensagens, webhooks, filas de tarefas) exigem limites agressivos de autovacuum.
3. **Connection Pooling Obrigatório**: Nunca exponha o PostgreSQL diretamente a centenas de conexões serverless (Vercel / Workers). Utilize sempre PgBouncer ou Supabase Pooler em modo `transaction`.

---

## 2. Rotinas de Manutenção Periódica

### 2.1 VACUUM ANALYZE Semanal
Atualiza as estatísticas do otimizador de consultas (`pg_statistic`) e limpa tuplas mortas (*dead tuples*):
```sql
-- Executar em banco de produção periodicamente
VACUUM (ANALYZE, VERBOSE);

-- Para tabela específica com alta rotatividade
VACUUM (ANALYZE, VERBOSE) public.messages;
VACUUM (ANALYZE, VERBOSE) public.webhook_events;
```

### 2.2 Diagnóstico de Table Bloat (Tuplas Mortas)
```sql
SELECT 
    schemaname,
    relname AS table_name,
    n_live_tup AS live_tuples,
    n_dead_tup AS dead_tuples,
    round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 2) AS dead_tuple_ratio,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;
```

### 2.3 Diagnóstico de Índices Não Utilizados (Desperdício de I/O)
```sql
SELECT 
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan AS number_of_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## 3. Monitoramento de Conexões e Consultas Lentas

### 3.1 Conexões Ativas e Bloqueios
```sql
SELECT 
    pid,
    usename,
    client_addr,
    application_name,
    state,
    now() - query_start AS duration,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
```

### 3.2 Terminar Consulta Travada (Lock)
```sql
-- 1. Cancelamento suave (SIGINT)
SELECT pg_cancel_backend(<pid>);

-- 2. Término forçado da conexão (SIGTERM)
SELECT pg_terminate_backend(<pid>);
```

---

## 4. Otimização de Performance (Query Tuning)

### 4.1 Uso de `EXPLAIN (ANALYZE, BUFFERS)`
Ao depurar consultas lentas, sempre execute com buffers para mensurar hits de cache e leituras de disco:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT m.id, m.body, m.created_at, c.phone 
FROM messages m
JOIN contacts c ON m.contact_id = c.id
WHERE m.created_at >= NOW() - INTERVAL '7 days'
ORDER BY m.created_at DESC
LIMIT 50;
```
* **Seq Scan em tabelas grandes**: Indica ausência de índice nas colunas de filtro (`WHERE`) ou junção (`JOIN`).
* **Index Scan / Bitmap Index Scan**: Acesso otimizado.
* **Shared Hit Blocks**: Leituras no buffer pool de memória RAM.

---

## 5. Estratégia de Backup & Disaster Recovery

### 5.1 Dump Lógico Criptografado e Comprimido (pg_dump)
```bash
# Dump com integridade garantida e compressão gzip máxima
pg_dump -h 127.0.0.1 -U axion -d main_db --no-owner --no-acl | gzip -9 > /backup/main_db_$(date +%F).sql.gz

# Restauração limpa
gunzip -c /backup/main_db_2026-09-25.sql.gz | psql -h 127.0.0.1 -U axion -d main_db
```

### 5.2 Validação de Integridade Pós-Restore
```sql
-- Validar total de tabelas e contagem rápida
SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
SELECT pg_size_pretty(pg_database_size('main_db'));
```
