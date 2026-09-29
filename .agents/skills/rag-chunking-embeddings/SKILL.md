---
name: rag-chunking-embeddings
description: >-
  Operational engineering skill for advanced Retrieval-Augmented Generation (RAG), hierarchical chunking, hybrid search (dense + BM25), Reciprocal Rank Fusion (RRF), and cross-encoder re-ranking.
---

# Advanced RAG & Retrieval Pipelines Skill

Guia operacional para arquitetura de sistemas de busca semântica, divisão inteligente de documentos, fusão híbrida de resultados e mitigação de alucinações em fluxos com LLMs.

---

## 1. Estratégias de Chunking Semântico

Evite divisões cegas por contagem de caracteres arbitrária que fragmentem tabelas, códigos ou pensamentos no meio de sentenças.

### 1.1 Hierarchical Markdown Chunking
Preserve os títulos e a hierarquia dos cabeçalhos como metadados injetados no início de cada chunk:
```markdown
[Documento: manual_pagamentos.md > Seção: Estornos > Subseção: Prazos e Taxas]
Os estornos de transações Pix ocorrem em até 2 horas úteis caso comprovada fraude...
```

### 1.2 Regras de Ouro de Chunking
- **Tamanho Canônico**: 400 a 800 tokens (aproximadamente 1200 a 2400 caracteres) para manter especificidade contextual.
- **Overlap Conectivo**: 10% a 15% de sobreposição entre blocos consecutivos para assegurar continuidade semântica entre limites de parágrafo.
- **Proteção de Fences de Código**: Nunca quebre um bloco ```...``` no meio. Se o código for maior que o chunk, divida por funções ou módulos.

---

## 2. Busca Híbrida: Dense + Sparse (BM25)

Embeddings densos são excelentes para sinônimos e conceitos, mas falham com códigos exatos de SKU, erros técnicos (`ERR_CONNECTION_REFUSED`) ou números de protocolo.

### 2.1 Reciprocal Rank Fusion (RRF)
Combine os dois rankings normalizando a posição relativa:
\[
RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}
\]
Onde \(k \approx 60\) e \(r_m(d)\) é o índice ordinal do documento no ranking \(m\).

```python
def rrf_score(dense_rank: int, sparse_rank: int, k: int = 60) -> float:
    score = 0.0
    if dense_rank > 0:
        score += 1.0 / (k + dense_rank)
    if sparse_rank > 0:
        score += 1.0 / (k + sparse_rank)
    return score
```

---

## 3. Re-Ranking com Cross-Encoders

Envie os top 20 a 30 candidatos retornados da busca híbrida para um modelo Cross-Encoder (ex: `cohere/rerank-v3` ou `bge-reranker-large`):
- Avalia simultaneamente o par `(Pergunta, Chunk)` gerando atenção cruzada completa.
- Elimina falsos positivos com alta similaridade de cosseno mas sem resposta direta à questão.
- Reduz a janela enviada ao LLM final para apenas os top 3 a 5 chunks, economizando tokens e latência.

---

## 4. Grounding e Prompt Bounding (Anti-Alucinação)

Isole o contexto recuperado com delimitadores inequívocos e proíba suposições externas:

```markdown
Você é um assistente técnico restrito. Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE nas fontes fornecidas dentro de <context_sources>.
Se a informação não estiver presente ou for ambígua, responda explicitamente: "Informação não encontrada na base de conhecimento."

<context_sources>
{retrieved_chunks}
</context_sources>
```

---

## 5. Ferramental Integrado

Utilize o utilitário Python embutido para avaliar estratégias de chunking em arquivos Markdown ou simular fusões RRF:
```powershell
# Avaliar particionamento semântico
python .agents/skills/rag-chunking-embeddings/scripts/chunking_evaluator.py chunk docs/API_REFERENCE.md 1200 150

# Testar fusão de ranqueamento híbrido
python .agents/skills/rag-chunking-embeddings/scripts/chunking_evaluator.py demo-rrf
```
