#!/usr/bin/env python3
"""
Web Vitals & Performance Linter
Audits HTML, TSX, JSX, and CSS files for Core Web Vitals anti-patterns:
- Cumulative Layout Shift (CLS): <img> without explicit dimensions or aspect-ratio
- Largest Contentful Paint (LCP): Hero image with loading="lazy" or missing priority
- Interaction to Next Paint (INP): Massive barrel imports (import * from ...)
- Font display shifts (FOUT/FOIT)
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path

IMG_WITHOUT_DIM_PATTERN = re.compile(r'<img\b(?![^>]*\b(width|height|aspect-ratio)\b)[^>]*>', re.IGNORECASE)
HERO_LAZY_PATTERN = re.compile(r'<img\b[^>]*\b(hero|banner|cover|main)\b[^>]*\bloading=["\']lazy["\']', re.IGNORECASE)
WILDCARD_IMPORT_PATTERN = re.compile(r'import\s+\*\s+as\s+[a-zA-Z_]\w*\s+from\s+[\'"](lucide-react|@heroicons|lodash|moment)[\'"]')


def audit_markup_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for idx, line in enumerate(lines, start=1):
        # 1. CLS Check: Images without explicit width/height
        if "<img" in line and IMG_WITHOUT_DIM_PATTERN.search(line):
            findings.append({
                "line": idx,
                "severity": "WARNING",
                "rule": "CLS_MISSING_IMG_DIMENSIONS",
                "message": f"<img> tag lacks explicit width, height or aspect-ratio. Causes layout shift during load."
            })

        # 2. LCP Check: Hero images lazy-loaded
        if HERO_LAZY_PATTERN.search(line):
            findings.append({
                "line": idx,
                "severity": "ERROR",
                "rule": "LCP_HERO_LAZY_LOADED",
                "message": "Hero/banner image is configured with loading='lazy'. Critical LCP asset must load eagerly."
            })

        # 3. Bundle bloat check: Wildcard imports
        wildcard_match = WILDCARD_IMPORT_PATTERN.search(line)
        if wildcard_match:
            findings.append({
                "line": idx,
                "severity": "WARNING",
                "rule": "BUNDLE_WILDCARD_IMPORT",
                "message": f"Wildcard import from '{wildcard_match.group(1)}' ruins tree-shaking. Import specific named members."
            })

    # 4. CSS font-display check
    if filepath.suffix == ".css":
        if "@font-face" in content and "font-display:" not in content:
            findings.append({
                "line": 1,
                "severity": "WARNING",
                "rule": "CLS_FONT_DISPLAY_MISSING",
                "message": "@font-face block lacks 'font-display: swap' or 'optional'. May cause Flash of Invisible Text (FOIT)."
            })

    return findings


def lint_tree(target: Path) -> int:
    extensions = {".html", ".tsx", ".jsx", ".vue", ".css"}
    files = [target] if target.is_file() else [f for f in target.glob("**/*.*") if f.suffix in extensions]

    if not files:
        print(f"[!] No frontend markup/style files found in {target}")
        return 0

    print(f"=== Auditing {len(files)} file(s) for Web Vitals & Performance ===")
    total_errors = 0
    total_warnings = 0

    for f in files:
        if "node_modules" in f.parts or ".next" in f.parts:
            continue
        findings = audit_markup_file(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [Line {item['line']} | {item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across checked files.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(lint_tree(target))
