---
name: qdrant-vector-database
description: >-
  Operational skill for vector similarity search, Qdrant collections, payload filtering, distance metrics (Cosine/Dot), and RAG retrieval pipelines.
---

# Qdrant Vector Search Skill

Skill operacional para indexação de embeddings, busca semântica aproximada (HNSW) e recuperação em sistemas RAG.

## 1. Configuração de Coleções
- **Métricas de Distância**: Usar `Cosine` para embeddings normalizados (OpenAI, Gemini text-embedding-004) ou `Dot` para embeddings de alta dimensão.
- **Payload Indexing**: Indexar campos de metadados (`tenant_id`, `created_at`, `category`) para permitir filtros rápidos combinados com a busca vetorial.
