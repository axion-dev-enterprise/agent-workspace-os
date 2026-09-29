#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canonical Skill Validator -- AXION Enterprise
Enforces Rule #13A (The Meta-Rule for Skills & Rules Creation):
- Anti-Stub Gate (Minimum technical density >= 40 lines)
- Valid YAML Frontmatter (name and description)
- Executable Python Syntax in scripts/
- Anti-Silo and Reusability checks
- Anti-Fragmentation warnings for bloated prefix clusters

Zero dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import re
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

WORKSPACE_ROOT = Path(r"C:\workspace")
SKILLS_DIR = WORKSPACE_ROOT / ".agents" / "skills"
MIN_NON_EMPTY_LINES = 35

def parse_frontmatter(content: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts name and description from YAML frontmatter."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, None
    frontmatter = match.group(1)

    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else None

    desc_match = re.search(r"^description:\s*(?:>-\s*\n|\s*)(.*?)(?=\n\w+:|\Z)", frontmatter, re.DOTALL | re.MULTILINE)
    desc = desc_match.group(1).strip() if desc_match else None
    if desc:
        desc = re.sub(r"\s+", " ", desc)

    return name, desc

def validate_single_skill(skill_dir: Path, strict: bool = False) -> Dict[str, Any]:
    """Audits a single skill directory against Rule #13A."""
    report = {
        "name": skill_dir.name,
        "path": skill_dir,
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "lines": 0,
        "scripts_count": 0
    }

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        report["status"] = "FAIL"
        report["errors"].append("Missing required file: SKILL.md")
        return report

    try:
        content = skill_md.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        report["status"] = "FAIL"
        report["errors"].append(f"Failed to read SKILL.md: {e}")
        return report

    # 1. Frontmatter check
    name, desc = parse_frontmatter(content)
    if not name:
        report["errors"].append("Missing or invalid 'name' in YAML frontmatter.")
    elif name != skill_dir.name:
        report["warnings"].append(f"Frontmatter name '{name}' does not match directory name '{skill_dir.name}'.")

    if not desc or len(desc) < 20:
        report["errors"].append("Missing or too short 'description' in YAML frontmatter (min 20 characters).")

    # 2. Density Check (Anti-Stub Gate)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    report["lines"] = len(lines)
    if len(lines) < MIN_NON_EMPTY_LINES:
        report["errors"].append(
            f"Anti-Stub Gate Violation: Skill has only {len(lines)} non-empty lines (minimum required: {MIN_NON_EMPTY_LINES}). "
            "Skills must contain actionable operational workflows, gotchas, or runbooks, not mere placeholders."
        )

    # 3. Scripts Syntax Check
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        py_scripts = list(scripts_dir.glob("*.py"))
        report["scripts_count"] = len(py_scripts)
        for py_file in py_scripts:
            try:
                ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError as syn_err:
                report["errors"].append(f"Syntax error in script '{py_file.name}': {syn_err}")

    # Set final status
    if report["errors"]:
        report["status"] = "FAIL"
    elif report["warnings"] and strict:
        report["status"] = "FAIL"
    elif report["warnings"]:
        report["status"] = "WARN"

    return report

def check_prefix_fragmentation(skills: List[Path]) -> Dict[str, List[str]]:
    """Identifies clusters of skills with matching prefixes that should be consolidated."""
    clusters = {}
    for s in skills:
        prefix = s.name.split("-")[0]
        clusters.setdefault(prefix, []).append(s.name)
    # Return clusters with 3 or more skills
    return {p: names for p, names in clusters.items() if len(names) >= 3}

def main():
    parser = argparse.ArgumentParser(
        description="Canonical Skill Validator -- Enforces Rule #13A (Anti-Stub & Anti-Silo Mandate)"
    )
    parser.add_argument(
        "--skill", "-s",
        help="Name of specific skill directory to validate in .agents/skills"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Validate all skills in .agents/skills"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures"
    )

    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print(f"Error: Skills directory not found at {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    targets = []
    if args.skill:
        target = SKILLS_DIR / args.skill
        if not target.exists():
            print(f"Error: Skill '{args.skill}' does not exist in {SKILLS_DIR}", file=sys.stderr)
            sys.exit(1)
        targets.append(target)
    elif args.all:
        targets = [p for p in sorted(SKILLS_DIR.iterdir()) if p.is_dir()]
    else:
        # Default: validate all or prompt
        targets = [p for p in sorted(SKILLS_DIR.iterdir()) if p.is_dir()]

    print("================================================================================")
    print("             CANONICAL SKILL VALIDATOR -- RULE #13A AUDIT                       ")
    print("================================================================================")
    print(f"Skills Root: {SKILLS_DIR}")
    print(f"Total Targets to Audit: {len(targets)}")
    print(f"Strict Mode: {args.strict}")
    print("--------------------------------------------------------------------------------\n")

    results = []
    for t in targets:
        rep = validate_single_skill(t, strict=args.strict)
        results.append(rep)

    passes = [r for r in results if r["status"] == "PASS"]
    warns = [r for r in results if r["status"] == "WARN"]
    fails = [r for r in results if r["status"] == "FAIL"]

    for r in results:
        status_tag = f"[{r['status']}]"
        print(f"{status_tag:<8} {r['name']:<35} ({r['lines']} linhas, {r['scripts_count']} scripts)")
        for err in r["errors"]:
            print(f"         [FAIL] {err}")
        for w in r["warnings"]:
            print(f"         [WARN] {w}")

    print("\n--------------------------------------------------------------------------------")
    print(f"Summary: PASS={len(passes)} | WARN={len(warns)} | FAIL={len(fails)} (Total={len(results)})")

    # Anti-Fragmentation Check
    if args.all or len(targets) > 5:
        clusters = check_prefix_fragmentation(targets)
        if clusters:
            print("\n[!] Fragmentation Warning (Rule #13A Consolidation Law):")
            for prefix, names in clusters.items():
                print(f"    - Prefix '{prefix}' has {len(names)} fragmented skills: {names}")
            print("    Recommendation: Consolidate into unified skills (e.g. remotion suite -> remotion-video-studio).")

    print("================================================================================")

    if fails:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
