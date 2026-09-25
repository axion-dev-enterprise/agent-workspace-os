---
name: redis-caching-queues
description: >-
  Operational skill for high-speed caching strategies, Redis 7 data structures, background job queues with BullMQ, and distributed locks with Redlock.
---

# Redis Caching & Queue Engineering Skill

Skill operacional para estratégias de cache resiliente, filas de tarefas em segundo plano e bloqueios distribuídos.

## 1. Padrões de Cache
1. **Cache-Aside com TTL**: Todo valor em cache deve ter um TTL (*Time-To-Live*) definido para evitar vazamento de memória.
2. **Prevenção de Cache Stampede**: Usar locking distribuído ou *probabilistic early expiration* quando recomputar caches caros.
3. **Filas Confiáveis**: Utilizar BullMQ com backoff exponencial para retries de envio de e-mails, webhooks e geração de relatórios.
