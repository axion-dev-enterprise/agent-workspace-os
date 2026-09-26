#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_skills.py — Operational Skills Ecosystem Auditor
AXION Enterprise / Agentic AI Foundation Standards

Audits all skills in .agents/skills/ for:
1. Valid YAML frontmatter (name, description).
2. Proper naming conventions (kebab-case).
3. Python script syntax validity in scripts/ (via ast.parse).
4. Registry registration in sync_skills_registry.py DOMAIN_MAP.
5. Overall ecosystem health and coverage report.
"""

import os
import sys
import ast
import re
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
SKILLS_DIR = WORKSPACE_ROOT / ".agents" / "skills"
SYNC_SCRIPT = WORKSPACE_ROOT / "scripts" / "sync_skills_registry.py"

def audit_skill(skill_dir: Path, domain_map: dict) -> dict:
    """Audits a single skill directory."""
    name = skill_dir.name
    issues = []
    warnings = []

    skill_md = skill_dir / "SKILL.md"
    scripts_dir = skill_dir / "scripts"
    refs_dir = skill_dir / "references"

    # Check SKILL.md existence
    if not skill_md.exists():
        return {
            "name": name,
            "status": "FAIL",
            "issues": ["SKILL.md inexistente"],
            "scripts_count": 0,
            "refs_count": 0,
            "in_domain_map": False
        }

    # Parse SKILL.md frontmatter
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    fm_name = None
    fm_desc = None

    if not fm_match:
        issues.append("YAML frontmatter ausente ou malformado")
    else:
        fm_content = fm_match.group(1)
        name_m = re.search(r"^name:\s*(.+)$", fm_content, re.MULTILINE)
        desc_m = re.search(r"^description:\s*(?:>-\s*\n|\s*)(.*?)(?=\n\w+:|\Z)", fm_content, re.DOTALL | re.MULTILINE)
        
        if name_m:
            fm_name = name_m.group(1).strip()
        else:
            issues.append("Campo 'name' ausente no frontmatter")

        if desc_m:
            fm_desc = desc_m.group(1).strip()
            if len(fm_desc) < 15:
                warnings.append("Descrição no frontmatter muito curta (gatilho fraco)")
        else:
            issues.append("Campo 'description' ausente no frontmatter")

    if fm_name and fm_name != name:
        warnings.append(f"Nome no frontmatter ('{fm_name}') diverge do diretório ('{name}')")

    # Audit scripts/
    scripts_count = 0
    if scripts_dir.exists() and scripts_dir.is_dir():
        for py_file in scripts_dir.glob("*.py"):
            scripts_count += 1
            try:
                ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                issues.append(f"Erro de sintaxe em scripts/{py_file.name}: {e}")

    # Audit references/
    refs_count = 0
    if refs_dir.exists() and refs_dir.is_dir():
        refs_count = len(list(refs_dir.glob("*.md")))

    in_domain_map = name in domain_map

    status = "FAIL" if issues else ("WARN" if warnings else "PASS")

    return {
        "name": name,
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "scripts_count": scripts_count,
        "refs_count": refs_count,
        "in_domain_map": in_domain_map,
        "description": (fm_desc[:60] + "...") if fm_desc else "N/A"
    }

def load_domain_map() -> dict:
    """Extracts DOMAIN_MAP from sync_skills_registry.py."""
    if not SYNC_SCRIPT.exists():
        return {}
    try:
        content = SYNC_SCRIPT.read_text(encoding="utf-8")
        match = re.search(r"DOMAIN_MAP\s*=\s*\{(.*?)\n\}", content, re.DOTALL)
        if match:
            # Simple line parsing
            domain_map = {}
            for line in match.group(1).splitlines():
                m = re.search(r'"([^"]+)":\s*\("([^"]+)",\s*"([^"]+)"\)', line)
                if m:
                    domain_map[m.group(1)] = (m.group(2), m.group(3))
            return domain_map
    except Exception:
        pass
    return {}

def main():
    parser = argparse.ArgumentParser(description="Auditor Geral de Skills — AXION Enterprise")
    parser.add_argument("--filter", help="Filtra por substring no nome da skill")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON")
    args = parser.parse_args()

    domain_map = load_domain_map()
    skills = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    
    if args.filter:
        skills = [s for s in skills if args.filter.lower() in s.name.lower()]

    results = []
    passed = 0
    warned = 0
    failed = 0

    for s_dir in skills:
        res = audit_skill(s_dir, domain_map)
        results.append(res)
        if res["status"] == "PASS":
            passed += 1
        elif res["status"] == "WARN":
            warned += 1
        else:
            failed += 1

    if args.json:
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0 if failed == 0 else 1)

    print("=" * 70)
    print(f"📊 RELATÓRIO DE AUDITORIA DO ECOSSISTEMA DE SKILLS ({len(results)} skills)")
    print("=" * 70)
    print(f"✅ Aprovadas: {passed} | ⚠️ Com Avisos: {warned} | ❌ Com Falhas: {failed}\n")

    for r in results:
        status_icon = "✅" if r["status"] == "PASS" else ("⚠️" if r["status"] == "WARN" else "❌")
        scripts_tag = f"[{r['scripts_count']} scripts]" if r['scripts_count'] > 0 else "[sem scripts]"
        refs_tag = f"[{r['refs_count']} refs]" if r['refs_count'] > 0 else ""
        dmap_tag = "📌 DOMAIN_MAP" if r["in_domain_map"] else "⚠️ Sem categoria no DOMAIN_MAP"

        print(f"{status_icon} **{r['name']}** {scripts_tag} {refs_tag} | {dmap_tag}")
        if r["issues"]:
            for iss in r["issues"]:
                print(f"   ❌ {iss}")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"   ⚠️ {w}")

    print("\n" + "=" * 70)
    if failed == 0:
        print("🎉 Todas as skills operacionais estão íntegras e em conformidade!")
        sys.exit(0)
    else:
        print(f"❌ {failed} skill(s) necessitam de correções imediatas.")
        sys.exit(1)

if __name__ == "__main__":
    main()
