---
name: rag-chunking-embeddings
description: >-
  Operational skill for advanced Retrieval-Augmented Generation (RAG), semantic document chunking, hybrid search (dense + sparse), and cross-encoder re-ranking.
---

# Advanced RAG & Retrieval Pipelines Skill

Skill operacional para construção de sistemas de recuperação de conhecimento com alta precisão e baixa alucinação.

## 1. Diretrizes de Sucesso em RAG
1. **Chunking Inteligente**: Não dividir por tamanho fixo cego. Respeite parágrafos, cabeçalhos Markdown e funções de código com sobreposição (*overlap*) de 10-20%.
2. **Busca Híbrida**: Combinar busca por palavras-chave exatas (BM25) com busca vetorial densa (Embeddings) para cobrir termos técnicos e siglas.
3. **Re-Ranking**: Aplicar um modelo de re-ranking (Cohere Rerank ou Cross-Encoder) nos top 20 resultados para enviar apenas os top 5 mais relevantes para o prompt final.
