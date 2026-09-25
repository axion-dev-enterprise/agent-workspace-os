---
name: mongodb-aggregation-pipeline
description: >-
  Operational skill for MongoDB document modeling, high-performance aggregation pipelines ($match, $group, $lookup), indexing, and change streams.
---

# MongoDB Aggregation Pipeline Skill

Skill operacional para consultas analíticas de alta performance e modelagem de documentos no MongoDB.

## 1. Otimização de Pipelines
- Sempre coloque o estágio `$match` e `$project` no início do pipeline para reduzir o volume de dados na memória RAM.
- Verifique o uso de índices em agregações com `db.collection.explain("executionStats").aggregate([...])`.
- Evite arrays com crescimento ilimitado dentro de documentos (anti-pattern de documentos de 16MB).
