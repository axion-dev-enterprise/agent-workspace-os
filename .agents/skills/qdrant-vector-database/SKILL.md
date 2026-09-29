---
name: qdrant-vector-database
description: >-
  Operational skill for vector similarity search, Qdrant collections architecture, HNSW graph tuning,
  scalar and binary quantization for memory optimization, and payload filtering in RAG pipelines.
---

# Qdrant Vector Search & High-Scale Embeddings — Master Skill

Skill operacional canonica para design, indexacao e gestao de colecoes de embeddings de alta dimensionalidade em **Qdrant Vector Database**. Cobre ajuste fino de grafos HNSW, quantizacao para reducao de RAM, filtros de payload para sistemas multi-tenant e integracao com RAG.

---

## 1. Escolha de Dimensões e Métricas de Distância

A configuração da métrica no momento da criação da coleção é irreversível.

| Modelo de Embedding | Dimensão Canônica | Métrica Recomendada | Racional |
| :--- | :--- | :--- | :--- |
| **Google Gemini (`text-embedding-004`)** | 768 | `Cosine` | Vetores normalizados para semântica densa. |
| **OpenAI (`text-embedding-3-small/large`)** | 1536 / 3072 | `Cosine` ou `Dot` | `Dot` oferece throughput 20% maior se os vetores já forem normalizados unitariamente L2. |
| **BGE / Cohere Embed v3** | 1024 | `Cosine` | Otimizado para recuperação e busca híbrida. |

---

## 2. Ajuste Fino de Grafos HNSW (Hierarchical Navigable Small World)

O algoritmo HNSW balanceia precisão de recuperação (*Recall@K*) contra velocidade e consumo de memória:

```json
{
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 128,
    "full_scan_threshold": 10000,
    "on_disk": false
  }
}
```

- **`m: 16`** (8 a 32): Número de conexões bidirecionais por nó. Valores mais altos (ex: 32) aumentam o recall para vetores complexos, mas elevam o consumo de RAM.
- **`ef_construct: 128`** (100 a 200): Profundidade da busca durante a construção do índice. Valores maiores aumentam a qualidade do grafo ao custo de tempo de ingestão.
- **`ef` em Tempo de Busca**: Pode ser ajustado dinamicamente na query:
  `{"params": {"hnsw_ef": 64}}` garante alta velocidade para UI (< 10ms).

---

## 3. Quantização Escalar e Binária: Redução de até 90% da RAM

Em coleções com mais de 100.000 vetores, manter floats de 32 bits (`f32`) em memória RAM torna-se proibitivo.

### 3.1 Scalar Quantization (SQ) — Recomendado para Produção
Converte floats de 32 bits em inteiros de 8 bits (`int8`), **reduzindo o uso de RAM em 75% com perda inferior a 1% no Recall**:

```json
{
  "quantization_config": {
    "scalar": {
      "type": "int8",
      "quantile": 0.99,
      "always_ram": true
    }
  }
}
```

### 3.2 Binary Quantization (BQ)
Converte vetores em bits (1 bit por dimensão), reduzindo a RAM em até 95%. Recomendado estritamente para modelos de altíssima dimensão (1536+) acompanhados de etapa de re-ranking (*rescoring* com vetores originais em disco).

---

## 4. Indexação de Payloads e Isolamento Multi-Tenant

Para permitir que a busca semântica filtre apenas documentos da organização solicitante, **campos de metadados devem possuir índices dedicados de payload**:

```bash
# Criar indice de payload para tenant_id (tipo keyword)
curl -X PUT "http://localhost:6333/collections/knowledge_base/index" \
     -H "Content-Type: application/json" \
     -d '{"field_name": "tenant_id", "field_schema": "keyword"}'
```

### 4.1 Consulta Filtrada Canônica:
```json
{
  "vector": [0.021, -0.043, 0.089, ...],
  "limit": 10,
  "filter": {
    "must": [
      { "key": "tenant_id", "match": { "value": "tenant_axion_01" } },
      { "key": "visibility", "match": { "value": "public" } }
    ]
  },
  "with_payload": true
}
```

---

## 5. O Utilitário CLI Standalone (`scripts/qdrant_ops.py`)

A skill inclui ferramenta CLI em Python puro (sem necessidade do SDK `qdrant-client`):

```bash
# Verificar saude do cluster e latencia
python .agents/skills/qdrant-vector-database/scripts/qdrant_ops.py --url http://localhost:6333 --health

# Inspecionar detalhes de uma colecao (HNSW, quantizacao, total de pontos)
python .agents/skills/qdrant-vector-database/scripts/qdrant_ops.py --inspect knowledge_base

# Criar snapshot de backup a quente da colecao
python .agents/skills/qdrant-vector-database/scripts/qdrant_ops.py --snapshot knowledge_base
```

---

## 6. Portão de Verificação (Verification Gate)

1. A coleção deve responder a consultas vetoriais com latência p95 < 25ms para K=10.
2. Campos de filtro utilizados em cláusulas `must` (ex: `tenant_id`, `category`) devem constar como índices ativos de payload via `qdrant_ops.py --inspect`.
3. Coleções com mais de 50.000 pontos devem ter `scalar` quantization habilitada para preservar os limites de memória RAM do container.
