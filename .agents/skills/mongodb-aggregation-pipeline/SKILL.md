---
name: mongodb-aggregation-pipeline
description: >-
  Operational skill for high-performance MongoDB aggregation pipelines, compound index design
  via the ESR rule, memory spill prevention, and real-time Change Streams.
---

# MongoDB Aggregation Pipeline & Data Modeling — Master Skill

Skill operacional canonica para construcao, otimizacao e governanca de pipelines analiticos de agregacao, modelagem de documentos e gestao de indices compostos no **MongoDB 6.0+**.

---

## 1. A Regra ESR para Índices Compostos

A performance de qualquer consulta ou estágio de `$match`/`$sort` depende estritamente da ordenação dos campos no índice composto:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 1. EQUALITY (E) │ ────> │ 2. SORT (S)     │ ────> │ 3. RANGE (R)    │
│ Campos com match│       │ Campos de       │       │ Operadores >, <,│
│ exato ($eq)     │       │ ordenacao       │       │ $in, $gte       │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Exemplo Prático:
Consulta: `db.orders.find({ status: "PAID", createdAt: { $gte: ISODate("2026-01-01") } }).sort({ amountCents: -1 })`
- **Ordem Correta do Índice (ESR)**: `{ status: 1, amountCents: -1, createdAt: 1 }`
- **Por que funciona?** O MongoDB filtra primeiro pela igualdade exata (`status`), aproveita os nós B-Tree pré-ordenados para o `$sort` sem ordenar em memória RAM, e finalmente aplica a fatia de intervalo (`createdAt`).

---

## 2. Otimização de Estágios do Aggregation Pipeline

### 2.1 Ordem Canônica de Estágios
1. **`$match` e `$geoNear` Imediato**: Reduza o conjunto de trabalho no primeiro milissegundo. Pipelines sem `$match` inicial forçam um *Full Collection Scan* para a RAM.
2. **`$project` Precoce**: Descarte campos pesados ou arrays não utilizados antes de agregações complexas.
3. **`$sort` Indexado**: Posicione o `$sort` imediatamente após o `$match` para que o MongoDB utilize índices em vez de despejar tuplas na memória temporária.
4. **`$group` e `$facet`**: Estágios de acumulação bloqueantes devem operar apenas sobre os dados já filtrados e projetados.

### 2.2 Limite de 100 MB de RAM e Despejo em Disco
Cada estágio de agregação possui um limite estrito de **100 MB de memória RAM**.
- Se um estágio de `$group` ou `$sort` não indexado ultrapassar 100 MB, a consulta falhará com erro: `QueryExceededMemoryLimitNoDiskUseAllowed`.
- Para relatórios de grande porte, passe explicitamente: `{ allowDiskUse: true }`.

---

## 3. Relacionamentos com `$lookup` e Sub-Pipelines

Evite `$lookup` ingênuo com `localField`/`foreignField` simples quando apenas alguns campos forem necessários. Utilize sub-pipelines com projeção:

```javascript
db.orders.aggregate([
  { $match: { status: "DELIVERED" } },
  {
    $lookup: {
      from: "users",
      let: { orderUserId: "$userId" },
      pipeline: [
        { $match: { $expr: { $eq: ["$_id", "$$orderUserId"] } } },
        { $project: { name: 1, email: 1, _id: 0 } } // Traz somente os campos necessarios
      ],
      as: "customer"
    }
  },
  { $unwind: "$customer" }
]);
```

---

## 4. Modelagem de Documentos: Anti-Padrão dos 16 MB

O MongoDB impõe um limite rígido de **16 MB por documento BSON**.
- **Antipadrão Crítico**: Inserir arrays ilimitados dentro de um mesmo documento (ex: `user.loginHistory = [...]` ou `post.comments = [...]`). Com o tempo, o documento atinge 16 MB ou fragmenta espaço de disco com realocações contínuas.
- **Padrão Canônico (Bucket Pattern / 1-to-N)**: Mova registros de alta cardinalidade para uma coleção separada referenciada por `userId`, ou use agrupamento em lotes de 100 itens.

---

## 5. Change Streams com Resume Tokens para Resiliência

Para processamento de eventos em tempo real, sempre capture e persista o `_id` do token de resumo (*resume token*) para permitir recuperação transparente após quedas de rede:

```javascript
const changeStream = db.orders.watch(
  [{ $match: { "operationType": "insert", "fullDocument.status": "PAID" } }],
  { resumeAfter: lastSavedResumeToken }
);

changeStream.on("change", async (change) => {
  await processPaymentNotification(change.fullDocument);
  await saveResumeTokenToDisk(change._id);
});
```

---

## 6. O Utilitário CLI Standalone (`scripts/mongo_pipeline_optimizer.py`)

A skill inclui um linter estático em Python stdlib para auditar pipelines antes de rodar em produção:

```bash
# Validar pipeline de agregacao salvo em arquivo JSON
python .agents/skills/mongodb-aggregation-pipeline/scripts/mongo_pipeline_optimizer.py --file pipelines/sales_report.json

# Teste rapido via string JSON
python .agents/skills/mongodb-aggregation-pipeline/scripts/mongo_pipeline_optimizer.py --json-str '[{"$unwind": "$items"}, {"$match": {"status": "PAID"}}]'
```

---

## 7. Portão de Verificação (Verification Gate)

1. Toda agregação em produção deve ser precedida por inspeção de plano de execução:
   `db.collection.explain("executionStats").aggregate([...])`.
2. O estágio `executionStats.totalDocsExamined` deve ser proporcional a `nReturned` (proporção próxima a 1:1, indicando cobertura total por índice).
3. Pipelines de agregação não devem disparar avisos de `$unwind` prematuro no linter estático.
