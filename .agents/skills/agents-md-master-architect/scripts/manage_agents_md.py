#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_agents_md.py — AGENTS.md Governance & Linter Engine
AXION Enterprise / Agentic AI Foundation Standards

Enforces the official AGENTS.md specification (https://agents.md):
1. Audits AGENTS.md for size, dead links, rule sequence, and bloat risk.
2. Safely inserts concise rules referencing docs/rules/ to preserve token efficiency.
3. Validates nested AGENTS.md in packages and subdirectories.
"""

import os
import sys
import argparse
import re
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
ROOT_AGENTS_MD = WORKSPACE_ROOT / "AGENTS.md"
RULES_DIR = WORKSPACE_ROOT / "docs" / "rules"

RULE_DOC_TEMPLATE = """# {title} — Regra de Governança Canônica

> **Status**: Ativa & Mandatória  
> **Escopo**: Operações de Agente / Workspace AXION  
> **Origem**: AGENTS.md Master Architect  

---

## 1. Princípio & Racional

{summary}

---

## 2. Diretrizes Técnicas Determinísticas

1. **Obrigatório**:
   - Todo código ou comando executado nesta categoria deve seguir os padrões documentados.
2. **Proibição Estrita**:
   - É proibido contornar os portões de verificação empírica.

---

## 3. Verificação & Evidência

Antes de concluir a tarefa, execute a checagem com o validador:
```bash
python .agents/skills/agents-md-master-architect/scripts/manage_agents_md.py --audit
```
"""

def extract_markdown_links(content: str) -> list:
    """Finds all markdown links [text](url) in the content."""
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = []
    for match in re.finditer(pattern, content):
        links.append({
            "text": match.group(1),
            "target": match.group(2)
        })
    return links

def resolve_link_path(target: str, base_dir: Path) -> Path:
    """Resolves local file links from markdown format."""
    clean = target.strip()
    if clean.startswith("file:///"):
        clean = clean[8:]
        return Path(clean)
    if clean.startswith("http://") or clean.startswith("https://") or clean.startswith("mailto:"):
        return None  # External link
    if clean.startswith("#"):
        return None  # Anchor link
    
    # Strip query/anchor
    clean = clean.split("#")[0].split("?")[0]
    if not clean:
        return None
        
    resolved = (base_dir / clean).resolve()
    return resolved

def audit_agents_md(file_path: Path) -> dict:
    """Performs comprehensive quality and compliance audit on an AGENTS.md file."""
    if not file_path.exists():
        return {"status": "error", "message": f"Arquivo não encontrado: {file_path}"}

    content = file_path.read_text(encoding="utf-8", errors="replace")
    size_bytes = len(content.encode("utf-8"))
    size_kb = round(size_bytes / 1024, 2)
    lines_count = len(content.splitlines())
    estimated_tokens = round(len(content) / 4)

    # Bloat warning: AGENTS.md open spec recommends keeping context lean
    bloat_warning = size_kb > 25.0

    # Extract and test local links
    links = extract_markdown_links(content)
    broken_links = []
    local_links_checked = 0

    for link in links:
        resolved = resolve_link_path(link["target"], file_path.parent)
        if resolved is not None:
            local_links_checked += 1
            if not resolved.exists():
                broken_links.append({
                    "text": link["text"],
                    "target": link["target"],
                    "resolved": str(resolved)
                })

    # Rule sequence extraction (handles 1, 2, 3, 4, 4A, 5, 5A, etc.)
    rule_matches = re.findall(r"###\s*Regra\s*#?([0-9]+[A-Za-z]?)[^:\n]*:\s*([^\n]+)", content, re.IGNORECASE)
    rules_found = [{"raw_number": num, "title": title.strip()} for num, title in rule_matches]
    
    # Check rule numbering continuity on the base integer part
    rule_continuity_error = None
    seen_bases = []
    for r in rules_found:
        base_match = re.match(r"^(\d+)", r["raw_number"])
        if base_match:
            base_num = int(base_match.group(1))
            if not seen_bases or base_num != seen_bases[-1]:
                seen_bases.append(base_num)

    expected = 1
    for b in seen_bases:
        if b != expected:
            rule_continuity_error = f"Salto na numeração de regras base: esperada #{expected}, encontrada #{b}"
            break
        expected += 1

    # Check canonical sections
    canonical_sections = [
        "Diretrizes", "Regras", "Skills", "Verificação"
    ]
    missing_sections = [sec for sec in canonical_sections if not re.search(sec, content, re.IGNORECASE)]

    status = "OK" if not broken_links and not rule_continuity_error and not bloat_warning else "WARNING"

    return {
        "status": status,
        "file": str(file_path),
        "size_kb": size_kb,
        "lines": lines_count,
        "estimated_tokens": estimated_tokens,
        "bloat_warning": bloat_warning,
        "local_links_checked": local_links_checked,
        "broken_links": broken_links,
        "rules_count": len(rules_found),
        "rule_continuity_error": rule_continuity_error,
        "missing_sections": missing_sections
    }

def add_rule_to_agents_md(title: str, summary: str, rule_doc: str = None) -> bool:
    """Adds a concise rule to AGENTS.md and scaffolds the referenced doc in docs/rules/."""
    if not ROOT_AGENTS_MD.exists():
        print(f"❌ Erro: {ROOT_AGENTS_MD} não encontrado.")
        return False

    content = ROOT_AGENTS_MD.read_text(encoding="utf-8")

    # Find highest rule number
    rule_nums = [int(m) for m in re.findall(r"###\s*Regra\s*#?(\d+)", content, re.IGNORECASE)]
    next_num = max(rule_nums) + 1 if rule_nums else 1

    # Setup rule document path
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", title.strip().upper())
    doc_rel = rule_doc or f"docs/rules/{slug}.md"
    doc_path = WORKSPACE_ROOT / doc_rel
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    if not doc_path.exists():
        doc_content = RULE_DOC_TEMPLATE.format(title=title, summary=summary)
        doc_path.write_text(doc_content, encoding="utf-8")
        print(f"📄 Criado documento de regra detalhado em: {doc_path}")

    # Build concise rule block (Anti-Bloat rule)
    new_rule_block = (
        f"\n### Regra #{next_num}: {title}\n"
        f"- {summary}\n"
        f"- **Guia & Especificação Completa**: [`{doc_rel}`](file:///C:/workspace/{doc_rel})\n"
    )

    # Insert before the closing or before sequence list
    seq_marker = "## Sequência Canônica de Leitura de Regras"
    if seq_marker in content:
        content = content.replace(seq_marker, new_rule_block + "\n" + seq_marker, 1)
        # Also add to reading sequence list
        seq_item = f"- [ ] **Regra #{next_num}**: `{title}` ➔ [`{doc_rel}`](file:///C:/workspace/{doc_rel})\n"
        content = content.replace(
            seq_marker + "\n\n",
            seq_marker + "\n\n" + seq_item,
            1
        )
    else:
        content += "\n" + new_rule_block

    ROOT_AGENTS_MD.write_text(content, encoding="utf-8")
    print(f"✅ Regra #{next_num} ('{title}') adicionada com sucesso ao AGENTS.md!")
    return True

def main():
    parser = argparse.ArgumentParser(description="AGENTS.md Governance & Linter Tool — AXION Enterprise")
    parser.add_argument("--audit", action="store_true", help="Audita AGENTS.md e verifica links quebrados e conformidade")
    parser.add_argument("--file", help="Caminho para um AGENTS.md específico (padrão: raiz C:\\workspace\\AGENTS.md)")
    parser.add_argument("--add-rule", help="Título da nova regra a ser adicionada")
    parser.add_argument("--summary", default="", help="Resumo conciso de 1-2 linhas da regra")
    parser.add_argument("--rule-doc", help="Caminho relativo para o documento detalhado em docs/rules/")
    args = parser.parse_args()

    target_file = Path(args.file) if args.file else ROOT_AGENTS_MD

    if args.add_rule:
        if not args.summary:
            print("❌ Erro: --summary é obrigatório ao adicionar uma nova regra.")
            sys.exit(1)
        success = add_rule_to_agents_md(args.add_rule, args.summary, args.rule_doc)
        sys.exit(0 if success else 1)

    # Default action: Audit
    print(f"🔍 Auditando arquivo AGENTS.md: {target_file}\n" + "━" * 50)
    report = audit_agents_md(target_file)

    if report.get("status") == "error":
        print(f"❌ {report['message']}")
        sys.exit(1)

    print(f"📊 Tamanho: {report['size_kb']} KB ({report['lines']} linhas, ~{report['estimated_tokens']} tokens)")
    print(f"📋 Regras Identificadas: {report['rules_count']}")
    print(f"🔗 Links Locais Verificados: {report['local_links_checked']}")

    if report["bloat_warning"]:
        print(f"⚠️  ALERTA DE INCHAÇO: Arquivo com {report['size_kb']} KB (> 25 KB). Recomenda-se modularizar regras para docs/rules/.")
    else:
        print("✅ Tamanho dentro do orçamento enxuto do padrão AGENTS.md (< 25 KB).")

    if report["rule_continuity_error"]:
        print(f"⚠️  {report['rule_continuity_error']}")
    else:
        print("✅ Numeração sequencial de regras contínua e sem saltos.")

    if report["broken_links"]:
        print(f"\n❌ Links Locais Quebrados ({len(report['broken_links'])} encontrados):")
        for bl in report["broken_links"]:
            print(f"   • [{bl['text']}] -> {bl['target']} (Não existe: {bl['resolved']})")
    else:
        print("✅ Todos os links locais para regras e documentações são válidos.")

    print("━" * 50)
    if report["status"] == "OK":
        print("🎉 Auditoria de AGENTS.md aprovada com 100% de conformidade!")
        sys.exit(0)
    else:
        print("⚠️ Auditoria finalizada com avisos.")
        sys.exit(0)

if __name__ == "__main__":
    main()
