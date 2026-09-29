---
name: redis-caching-queues
description: >-
  Operational engineering skill for high-speed caching strategies, Redis 7 data structures,
  background job queues with BullMQ, and distributed locks with Redlock.
---

# Redis Caching, Queues & Distributed Systems — Master Skill

Skill operacional canonica para design, governanca e manutencao de camadas de cache de alta performance, filas assincronas de background (BullMQ) e bloqueios distribuidos (Redlock) em **Redis 7**.

---

## 1. Estratégias de Cache Resilientes

### 1.1 O Padrão Cache-Aside com TTL Jitter Obrigatório
Nunca defina TTLs estáticos e idênticos para múltiplas chaves geradas em lote. Adicione dispersão aleatória (*jitter*) de 10% a 20% para evitar expiração simultânea massiva:

```typescript
function getJitteredTtl(baseSeconds: number, jitterPercent: number = 0.15): number {
  const variation = baseSeconds * jitterPercent;
  const delta = (Math.random() * 2 - 1) * variation;
  return Math.round(baseSeconds + delta);
}

// Exemplo: Cache de perfil de usuário com TTL base de 1 hora + jitter
await redis.set(`user:${id}:profile`, JSON.stringify(userData), 'EX', getJitteredTtl(3600));
```

### 1.2 Mitigação de Cache Stampede (Probabilistic Early Expiration)
Para chaves computacionalmente caras de regenerar (ex: relatórios agregados, dashboards de BI), adote o algoritmo **XFetch**:
- Armazene o tempo de computação `delta` junto ao payload em cache.
- Se `currentTime - (delta * beta * ln(random())) > expiry`, recompute em background antes que a chave expire.

---

## 2. Bloqueios Distribuídos com Algoritmo Redlock

Em sistemas com múltiplas réplicas, nunca use `SETNX` simples sem expiração e sem token único de verificação de propriedade.

### 2.1 Aquisição Canônica de Lock
O lock deve ser adquirido com valor randômico único (UUID) e expiração atômica:
```typescript
import crypto from 'node:crypto';

const lockToken = crypto.randomUUID();
const acquired = await redis.set(`lock:${resourceId}`, lockToken, 'PX', 5000, 'NX');

if (!acquired) {
  throw new Error('Recurso ocupado por outra transacao concorrente.');
}
```

### 2.2 Liberação Atômica de Lock com Script Lua Obrigatório
Nunca libere o lock com `DEL key` direto, pois uma transação lenta pode apagar o lock adquirido pela transação seguinte. Use sempre o script Lua atômico:

```lua
-- Script Lua Canônico de Release
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
```

Em Node.js/TypeScript:
```typescript
const releaseScript = `
  if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
  else
    return 0
  end
`;

await redis.eval(releaseScript, 1, `lock:${resourceId}`, lockToken);
```

---

## 3. Filas Assíncronas de Background com BullMQ

### 3.1 Topologia de Filas de Produção
- **Concorrência Controlada**: Defina `concurrency: 5` no Worker para evitar saturar o banco de dados.
- **Backoff Exponencial com Jitter**:
  ```typescript
  import { Queue, Worker } from 'bullmq';

  export const emailQueue = new Queue('email-dispatch', { connection: redisConnection });

  await emailQueue.add('send-receipt', payload, {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 2000, // 2s, 4s, 8s, 16s...
    },
    removeOnComplete: { count: 1000 },
    removeOnFail: { count: 5000 }, // Preserva falhas para auditoria (Dead-Letter)
  });
  ```

### 3.2 Recuperação de Jobs Estagnados (Stalled Jobs)
Workers que sofrem `OOMKill` ou reinicialização abrupta deixam jobs em estado `active`. O BullMQ detecta isso via `stalledInterval` (padrão: 30s) e reatribui o job a outro worker ativo.

---

## 4. Estruturas de Dados Avançadas do Redis 7

| Estrutura | Caso de Uso Canônico | Complexidade |
| :--- | :--- | :--- |
| **Hashes (`HSET`, `HGETALL`)** | Armazenamento de objetos planos e sessões (reduz 60% de RAM vs JSON em string). | O(1) por campo |
| **Sorted Sets (`ZADD`, `ZRANGEBYSCORE`)** | Rate-limiting de janela deslizante (Sliding Window Log) e tabelas de classificação (*leaderboards*). | O(log N) |
| **Streams (`XADD`, `XREADGROUP`)** | Log de auditoria distribuído, pub/sub persistente e filas com grupos de consumidores. | O(1) |
| **HyperLogLog (`PFADD`, `PFCOUNT`)** | Contagem de cardinalidade aproximada (visitantes únicos diários) consumindo apenas 12 KB de RAM. | O(1) |

---

## 5. Políticas de Eviction e Governança de Memória

No arquivo `redis.conf`:
- **`maxmemory-policy volatile-lru`**: Para instâncias híbridas que compartilham cache e filas BullMQ. Garante que apenas chaves com TTL sejam descartadas, protegendo jobs de fila que não possuem TTL contra eviction acidental.
- **`maxmemory-policy allkeys-lru`**: Estritamente para instâncias dedicadas exclusivamente a cache de dados.

---

## 6. O Utilitário CLI Standalone (`scripts/redis_ops.py`)

A skill acompanha ferramenta em Python puro (sem necessidade de instalar `redis-py`):

```bash
# Diagnosticar conectividade e latencia de roundtrip
python .agents/skills/redis-caching-queues/scripts/redis_ops.py --host 127.0.0.1 --ping

# Testar aquisicao e liberacao atomica de lock distribuido
python .agents/skills/redis-caching-queues/scripts/redis_ops.py --lock-test lock:order:1234

# Inspecionar memoria e politica de eviction da instancia
python .agents/skills/redis-caching-queues/scripts/redis_ops.py --info
```

---

## 7. Portão de Verificação (Verification Gate)

1. Toda chave de cache adicionada em código deve possuir um TTL explícito verificado via `TTL <chave>` (> 0).
2. Locks distribuídos devem liberar o recurso em bloco `finally` invocando o script Lua de verificação de token.
3. Filas BullMQ devem ter configuração explícita de `removeOnComplete` e `removeOnFail` para prevenir estouro de memória da instância Redis.
