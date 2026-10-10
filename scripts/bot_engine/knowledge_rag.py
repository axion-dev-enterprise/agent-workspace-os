#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Ultra-Low-Latency In-Memory Knowledge RAG Engine
======================================================
Motor RAG local-first de altíssimo desempenho (< 3ms) baseado em SQLite FTS5 (BM25).
Indexa de forma determinística os documentos canônicos em `docs/knowledge/` por seções
hierárquicas, oferecendo busca lexical probabilística com zero chamadas externas de rede,
hot-reload em tempo real e compatibilidade com o Prompt Caching da OpenRouter.
"""

import os
import re
import time
import sqlite3
import threading
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional

WORKSPACE_ROOT = Path(r"C:\workspace")
KNOWLEDGE_DIR = WORKSPACE_ROOT / "docs" / "knowledge"

# Mapeamento de categorias de documentos
VERTICAL_MAPPING = {
    "commercial_playbook.md": "commercial",
    "technical_architecture.md": "technical",
    "support_operations_faq.md": "operations",
    "identity_governance.md": "governance",
    "rag_architecture_spec.md": "technical",
    "README.md": "index"
}

# Palavras de parada e saudações comuns para o Intent Gate (retorno em < 0.05ms)
GREETINGS_AND_TRIVIAL = {
    "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "e ai", "e aí",
    "opa", "fala", "blz", "beleza", "tudo bem", "tudo bom", "como vai",
    "ok", "okay", "certo", "perfeito", "entendido", "sim", "nao", "não",
    "valeu", "obrigado", "obrigada", "vlw", "obgd", "tchau", "ate mais",
    "até mais", "show", "combinado", "/start", "/help", "teste", "ping"
}


def normalize_text_for_search(text: str) -> str:
    """Remove caracteres especiais, pontuação FTS e normaliza espaços."""
    if not text:
        return ""
    # Remove diacríticos para compatibilidade adicional
    normalized = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in normalized if not unicodedata.combining(c))
    # Limpa caracteres que quebram sintaxe do SQLite FTS5 (como ", *, (, ), :, ^)
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


class KnowledgeRAGEngine:
    """Motor RAG em memória com SQLite FTS5 e particionamento hierárquico."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KnowledgeRAGEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, knowledge_dir: Optional[Path] = None):
        if self._initialized:
            return

        self.knowledge_dir = knowledge_dir or KNOWLEDGE_DIR
        self._db_lock = threading.Lock()
        self._file_mtimes: Dict[str, float] = {}
        self.total_chunks = 0
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._init_fts_schema()
        self.reload_index(force=True)
        self._initialized = True

    def _init_fts_schema(self):
        """Cria a tabela virtual FTS5 em memória com suporte a tokenizador unicode61."""
        with self._db_lock:
            cur = self._conn.cursor()
            cur.execute("DROP TABLE IF EXISTS knowledge_fts")
            cur.execute("""
                CREATE VIRTUAL TABLE knowledge_fts USING fts5(
                    doc_id UNINDEXED,
                    doc_name UNINDEXED,
                    vertical UNINDEXED,
                    section_title,
                    section_path,
                    content,
                    tags,
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
            self._conn.commit()

    def _parse_markdown_sections(self, file_path: Path) -> List[Dict[str, Any]]:
        """Particiona um documento Markdown respeitando os cabeçalhos ## e ###."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        doc_name = file_path.name
        vertical = VERTICAL_MAPPING.get(doc_name, "general")

        lines = text.splitlines()
        chunks = []

        current_h1 = doc_name
        current_h2 = ""
        current_h3 = ""
        current_content_lines = []

        def save_chunk():
            nonlocal current_content_lines, current_h2, current_h3
            content = "\n".join(current_content_lines).strip()
            if content and len(content) > 30:  # Ignora seções quase vazias
                # Constrói o caminho semântico da seção
                path_parts = [doc_name]
                if current_h1 and current_h1 != doc_name:
                    path_parts.append(current_h1)
                if current_h2:
                    path_parts.append(current_h2)
                if current_h3:
                    path_parts.append(current_h3)

                section_path = " > ".join(path_parts)
                section_title = current_h3 or current_h2 or current_h1

                # Extrai tags automáticas a partir dos títulos
                tags = " ".join([doc_name, current_h1, current_h2, current_h3, vertical])
                tags = normalize_text_for_search(tags)

                chunks.append({
                    "doc_id": f"{doc_name}:{len(chunks)}",
                    "doc_name": doc_name,
                    "vertical": vertical,
                    "section_title": section_title,
                    "section_path": section_path,
                    "content": content,
                    "tags": tags
                })
            current_content_lines = []

        for line in lines:
            if line.startswith("# "):
                save_chunk()
                current_h1 = line[2:].strip()
                current_h2 = ""
                current_h3 = ""
            elif line.startswith("## "):
                save_chunk()
                current_h2 = line[3:].strip()
                current_h3 = ""
            elif line.startswith("### "):
                save_chunk()
                current_h3 = line[4:].strip()
            else:
                current_content_lines.append(line)

        save_chunk()
        return chunks

    def reload_index(self, force: bool = False) -> int:
        """Carrega e indexa todos os arquivos em docs/knowledge se houver alterações ou se force=True."""
        if not self.knowledge_dir.exists():
            return 0

        current_files = list(self.knowledge_dir.glob("*.md"))
        needs_reload = force

        if not needs_reload:
            for f in current_files:
                mtime = f.stat().st_mtime
                if self._file_mtimes.get(f.name) != mtime:
                    needs_reload = True
                    break

        if not needs_reload and self._file_mtimes:
            return self.total_chunks  # Nenhum arquivo alterado

        total_chunks = 0
        with self._db_lock:
            cur = self._conn.cursor()
            cur.execute("DELETE FROM knowledge_fts")

            for f in current_files:
                try:
                    chunks = self._parse_markdown_sections(f)
                    for c in chunks:
                        cur.execute("""
                            INSERT INTO knowledge_fts (
                                doc_id, doc_name, vertical, section_title, section_path, content, tags
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            c["doc_id"], c["doc_name"], c["vertical"],
                            c["section_title"], c["section_path"], c["content"], c["tags"]
                        ))
                    self._file_mtimes[f.name] = f.stat().st_mtime
                    total_chunks += len(chunks)
                except Exception as e:
                    print(f"[RAG Engine] Erro ao indexar {f.name}: {e}")

            self._conn.commit()

        self.total_chunks = total_chunks
        return total_chunks

    def is_retrieval_candidate(self, text: str) -> bool:
        """
        Intent-Gated Filter (< 0.05ms):
        Retorna False se o texto for saudação trivial, confirmação ou sem intenção factual.
        """
        if not text:
            return False

        stripped = text.strip()
        # Comandos iniciados por / (ex: /start, /help, /brain) são tratados localmente pelo bot
        if stripped.startswith("/"):
            return False

        # Remove pontuação para tratar pontuações como 'bom dia!', 'tudo bem?' e 'valeu!'
        cleaned = re.sub(r'[^\w\s]', '', text).strip().lower()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Saudações e confirmações curtas exatas
        if cleaned in GREETINGS_AND_TRIVIAL or cleaned in {"start", "help", "menu", "status"}:
            return False

        # Verifica se é uma frase muito curta composta apenas por termos triviais
        words = cleaned.split()
        if len(words) <= 2 and all(w in GREETINGS_AND_TRIVIAL or len(w) <= 2 for w in words):
            return False

        # Se tiver mais de 2 palavras ou contiver termos factuais, é candidato a RAG
        return True

    def search(self, query: str, limit: int = 2, vertical: str = "all") -> List[Dict[str, Any]]:
        """
        Executa a busca FTS5 com ranqueamento BM25 em memória (< 3ms).
        """
        start_ts = time.perf_counter()
        self.reload_index()  # Verifica mtime (< 0.01ms se inalterado)

        norm_query = normalize_text_for_search(query)
        if not norm_query:
            return []

        tokens = norm_query.split()
        if not tokens:
            return []

        # Constrói query FTS5 flexível: busca termos exatos ou tokens individuais
        fts_query_parts = []
        for t in tokens:
            if len(t) >= 2:
                fts_query_parts.append(f'"{t}"*')

        if not fts_query_parts:
            return []

        match_clause = " OR ".join(fts_query_parts)

        # Monta SQL com pesos BM25 calibrados:
        # section_title (peso 5.0), section_path (peso 3.0), content (peso 1.0), tags (peso 4.0)
        sql = """
            SELECT doc_name, section_title, section_path, content, vertical,
                   bm25(knowledge_fts, 5.0, 3.0, 1.0, 4.0) as rank
            FROM knowledge_fts
            WHERE knowledge_fts MATCH ?
        """
        params = [match_clause]

        if vertical != "all":
            sql += " AND vertical = ?"
            params.append(vertical)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        results = []
        with self._db_lock:
            cur = self._conn.cursor()
            try:
                cur.execute(sql, params)
                rows = cur.fetchall()
                for r in rows:
                    results.append({
                        "doc_name": r[0],
                        "section_title": r[1],
                        "section_path": r[2],
                        "content": r[3],
                        "vertical": r[4],
                        "bm25_score": abs(float(r[5])),
                        "elapsed_ms": (time.perf_counter() - start_ts) * 1000.0
                    })
            except Exception as e:
                # Fallback para busca por LIKE caso haja caractere atípico
                cur.execute("""
                    SELECT doc_name, section_title, section_path, content, vertical
                    FROM knowledge_fts
                    WHERE content LIKE ? OR section_title LIKE ?
                    LIMIT ?
                """, (f"%{tokens[0]}%", f"%{tokens[0]}%", limit))
                for r in cur.fetchall():
                    results.append({
                        "doc_name": r[0],
                        "section_title": r[1],
                        "section_path": r[2],
                        "content": r[3],
                        "vertical": r[4],
                        "bm25_score": 10.0,
                        "elapsed_ms": (time.perf_counter() - start_ts) * 1000.0
                    })

        return results

    def format_retrieved_context(self, results: List[Dict[str, Any]]) -> str:
        """Formata os snippets em bloco seguro pronto para injeção no prompt."""
        if not results:
            return ""

        chunks_text = []
        for idx, res in enumerate(results, start=1):
            chunks_text.append(
                f"[FONTE CANÔNICA #{idx}: {res['section_path']}]\n"
                f"{res['content']}"
            )

        joined = "\n\n".join(chunks_text)
        return (
            "<base_conhecimento_canonica>\n"
            f"{joined}\n"
            "</base_conhecimento_canonica>"
        )


# Instância global singleton
_GLOBAL_ENGINE = None

def get_rag_engine() -> KnowledgeRAGEngine:
    """Retorna o singleton do motor RAG."""
    global _GLOBAL_ENGINE
    if _GLOBAL_ENGINE is None:
        _GLOBAL_ENGINE = KnowledgeRAGEngine()
    return _GLOBAL_ENGINE


def search_knowledge_base(query: str, limit: int = 2, vertical: str = "all") -> List[Dict[str, Any]]:
    """Função utilitária para busca na base canônica."""
    engine = get_rag_engine()
    return engine.search(query, limit=limit, vertical=vertical)


def get_context_for_message(message: str, limit: int = 2) -> Optional[str]:
    """
    Avalia a mensagem pelo Intent Gate e, se aplicável, retorna o bloco
    formatado com os trechos canônicos em menos de 3ms.
    """
    engine = get_rag_engine()
    if not engine.is_retrieval_candidate(message):
        return None

    results = engine.search(message, limit=limit)
    if not results:
        return None

    return engine.format_retrieved_context(results)


def benchmark_rag(queries: Optional[List[str]] = None) -> Dict[str, Any]:
    """Executa benchmark de latência com consultas reais."""
    engine = get_rag_engine()
    test_queries = queries or [
        "quanto custa criar um site sob demanda",
        "qual o valor da mensalidade do whatsapp",
        "como funciona o teste gratis de 30 dias",
        "o que e o axion pay e checkout transparente",
        "quem e o ceo e autoridade da axion",
        "quais as portas e servicos no pm2",
        "como evitar banimento no whatsapp e regras de opt in",
        "vocês fazem gestao de trafego pago e pixel capi"
    ]

    latencies = []
    reports = []

    for q in test_queries:
        t0 = time.perf_counter()
        res = engine.search(q, limit=2)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        latencies.append(elapsed_ms)
        reports.append({
            "query": q,
            "hits": len(res),
            "top_section": res[0]["section_path"] if res else "Nenhum",
            "elapsed_ms": round(elapsed_ms, 2)
        })

    avg_ms = sum(latencies) / len(latencies)
    max_ms = max(latencies)
    min_ms = min(latencies)

    return {
        "total_queries": len(test_queries),
        "avg_latency_ms": round(avg_ms, 3),
        "min_latency_ms": round(min_ms, 3),
        "max_latency_ms": round(max_ms, 3),
        "queries_report": reports
    }


if __name__ == "__main__":
    print("=== TESTE & BENCHMARK DO MOTOR RAG AXION ===")
    t_start = time.perf_counter()
    eng = get_rag_engine()
    indexed_chunks = eng.total_chunks
    t_load = (time.perf_counter() - t_start) * 1000.0
    print(f"[*] Chunks indexados em SQLite FTS5: {indexed_chunks} (Carga inicial: {t_load:.2f}ms)")

    # Teste do Intent Gate
    print("\n[*] Teste do Intent Gate:")
    greetings = ["oi", "bom dia", "ok", "valeu", "quanto custa um site?", "como funciona o trial?"]
    for g in greetings:
        cand = eng.is_retrieval_candidate(g)
        print(f"  - '{g}' -> Candidato RAG: {cand}")

    # Benchmark de Latência
    print("\n[*] Executando Benchmark de Latencia com Consultas Reais:")
    bench = benchmark_rag()
    print(f"  - Latencia Media: {bench['avg_latency_ms']} ms")
    print(f"  - Latencia Minima: {bench['min_latency_ms']} ms")
    print(f"  - Latencia Maxima: {bench['max_latency_ms']} ms")
    print("\nDetalhe das Consultas:")
    for rep in bench["queries_report"]:
        print(f"  [{rep['elapsed_ms']}ms] '{rep['query']}'")
        safe_top = rep['top_section'].encode('ascii', errors='replace').decode('ascii')
        print(f"    -> Top Hit: {safe_top}")
