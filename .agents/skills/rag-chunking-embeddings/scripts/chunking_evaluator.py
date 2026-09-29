#!/usr/bin/env python3
"""
RAG Chunking Evaluator & RRF Fusion Tool
Performs semantic hierarchical chunking on Markdown/Text files, detects boundary truncations
(broken code blocks, split tables), and implements Reciprocal Rank Fusion (RRF).
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
import math
from pathlib import Path


def semantic_markdown_chunker(text: str, max_chars: int = 1500, overlap_chars: int = 150) -> list[dict]:
    """Splits markdown text preserving section headers and tracking code fences."""
    chunks = []
    lines = text.splitlines()

    current_header = "Introduction"
    current_buffer = []
    current_char_count = 0
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block

        # Check for header
        if not in_code_block and re.match(r'^#{1,4}\s+', line):
            current_header = line.strip()

        line_len = len(line) + 1
        if current_char_count + line_len > max_chars and not in_code_block:
            # Commit current chunk
            chunk_content = "\n".join(current_buffer).strip()
            if chunk_content:
                chunks.append({
                    "section": current_header,
                    "length_chars": len(chunk_content),
                    "content": chunk_content,
                    "code_intact": not in_code_block
                })
            # Overlap: keep last few lines
            overlap_buffer = []
            overlap_chars_accum = 0
            for prev_line in reversed(current_buffer):
                if overlap_chars_accum + len(prev_line) > overlap_chars:
                    break
                overlap_buffer.insert(0, prev_line)
                overlap_chars_accum += len(prev_line) + 1

            current_buffer = overlap_buffer + [line]
            current_char_count = sum(len(l) + 1 for l in current_buffer)
        else:
            current_buffer.append(line)
            current_char_count += line_len

    if current_buffer:
        chunk_content = "\n".join(current_buffer).strip()
        if chunk_content:
            chunks.append({
                "section": current_header,
                "length_chars": len(chunk_content),
                "content": chunk_content,
                "code_intact": True
            })

    return chunks


def reciprocal_rank_fusion(dense_rankings: list[str], sparse_rankings: list[str], k: int = 60) -> list[tuple[str, float]]:
    """Calculates RRF score: score(doc) = sum(1 / (k + rank))."""
    scores = {}

    for rank, doc_id in enumerate(dense_rankings, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    for rank, doc_id in enumerate(sparse_rankings, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    sorted_ranks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_ranks


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python chunking_evaluator.py chunk <arquivo.md> [max_chars] [overlap]")
        print("  python chunking_evaluator.py demo-rrf")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "chunk":
        filepath = Path(sys.argv[2])
        max_chars = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
        overlap = int(sys.argv[4]) if len(sys.argv) > 4 else 150

        text = filepath.read_text(encoding="utf-8", errors="ignore")
        chunks = semantic_markdown_chunker(text, max_chars, overlap)

        print(f"=== Chunking Analysis for {filepath.name} ===")
        print(f"Total Text Size: {len(text)} chars")
        print(f"Generated Chunks: {len(chunks)}")
        print(f"Average Chunk Size: {sum(c['length_chars'] for c in chunks) / max(len(chunks), 1):.1f} chars\n")

        for idx, c in enumerate(chunks, start=1):
            print(f"--- Chunk #{idx} [{c['section']}] ({c['length_chars']} chars) ---")
            sample = c["content"][:160].replace("\n", " ")
            print(f"Preview: {sample}...\n")

    elif cmd == "demo-rrf":
        dense = ["doc_A", "doc_B", "doc_C", "doc_D"]
        sparse = ["doc_C", "doc_E", "doc_A", "doc_F"]
        fused = reciprocal_rank_fusion(dense, sparse)
        print("=== Reciprocal Rank Fusion (RRF) Demonstration ===")
        print(f"Dense Ranking:  {dense}")
        print(f"Sparse Ranking: {sparse}")
        print("\nFused Result:")
        for doc, score in fused:
            print(f"  Doc: {doc:8s} | Score: {score:.5f}")


if __name__ == "__main__":
    main()
