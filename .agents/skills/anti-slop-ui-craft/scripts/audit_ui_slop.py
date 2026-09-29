#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canonical AI Slop UI Auditor -- AXION Enterprise
Scans frontend codebases (React, Vite, Next.js, HTML) for known AI UI/UX anti-patterns:
- Radioactive text gradients and glowing blur-3xl blobs
- Prohibited copywriting buzzwords ("Supercharge", "Unleash", etc.)
- Sparkles icon abuse
- Clickable div syndrome (a11y failure)
- Obsolete 100vh viewport units
- Native alert/confirm dialog invocations

Zero external dependencies: Uses Python standard library only.
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure Windows terminal prints UTF-8 safely
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SLOP_PATTERNS = [
    # 1. Radioactive Text Gradients
    (
        r"bg-clip-text\s+text-transparent\s+bg-gradient-to-[a-z]+",
        "GRADIENT_TEXT",
        "CRITICAL",
        "Text gradient detected (bg-clip-text text-transparent). Use solid high-contrast typography.",
    ),
    # 2. Aurora Blobs
    (
        r"blur-(?:2xl|3xl)[^>]*rounded-full",
        "AURORA_BLOB",
        "WARNING",
        "Decorative blurred background blob detected. Use intentional directional lighting or clean surfaces.",
    ),
    # 3. Clickable Div (WCAG failure)
    (
        r"<div\b[^>]*\bonClick\s*=",
        "CLICKABLE_DIV",
        "CRITICAL",
        "Clickable <div> detected. Replace with semantic <button type=\"button\"> or <a href> for a11y.",
    ),
    # 4. Obsolete 100vh instead of 100dvh
    (
        r"(?:h-screen|h-\[100vh\]|min-h-\[100vh\])",
        "OBSOLETE_VIEWPORT_VH",
        "WARNING",
        "Fixed 100vh viewport unit detected. Use min-h-[100dvh] to prevent mobile address bar layout shifts.",
    ),
    # 5. Native browser dialogs
    (
        r"\b(?:window\.)?(?:alert|confirm|prompt)\s*\(",
        "NATIVE_DIALOG",
        "CRITICAL",
        "Native dialog (alert/confirm/prompt) detected. Use custom accessible modal/toast components.",
    ),
    # 6. Sparkles / Star emoji abuse
    (
        r"(?:✨|<Sparkles\b)",
        "SPARKLES_ABUSE",
        "WARNING",
        "Sparkles icon (✨) detected as modern indicator. Use precise technical vector icons.",
    ),
]

COPY_BUZZWORDS = [
    (r"\bSupercharge\s+your\b", "Supercharge your", "Use concrete action verb (e.g., 'Gerencie', 'Aprenda', 'Acelere')."),
    (r"\bUnleash\s+the\s+power\b", "Unleash the power", "State factual product value in 5 words."),
    (r"\bSeamlessly\s+integrate\b", "Seamlessly integrate", "Specify actual integrations directly."),
    (r"\bAll-in-one\s+platform\b", "All-in-one platform", "State specific niche and actual capabilities."),
    (r"\bElevate\s+your\b", "Elevate your", "Use measurable metrics or direct outcomes."),
]

VALID_EXTENSIONS = {".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro"}
IGNORE_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".vercel", "temp"}


def audit_file(filepath: Path) -> List[Dict[str, Any]]:
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [{"line": 0, "code": "READ_ERROR", "severity": "ERROR", "message": str(e)}]

    lines = content.splitlines()

    for line_idx, line in enumerate(lines, start=1):
        # 1. Structural Slop Patterns
        for pattern, code, severity, message in SLOP_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "line": line_idx,
                    "code": code,
                    "severity": severity,
                    "message": message,
                    "snippet": line.strip()[:100],
                })

        # 2. Copy Buzzwords
        for pattern, phrase, suggestion in COPY_BUZZWORDS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "line": line_idx,
                    "code": "AI_COPY_BUZZWORD",
                    "severity": "WARNING",
                    "message": f"Banned AI buzzword detected: '{phrase}'. Suggestion: {suggestion}",
                    "snippet": line.strip()[:100],
                })

    return issues


def scan_directory(target_path: Path) -> Tuple[int, int, Dict[str, List[Dict[str, Any]]]]:
    total_files = 0
    total_violations = 0
    results: Dict[str, List[Dict[str, Any]]] = {}

    if target_path.is_file():
        files = [target_path]
    else:
        files = [
            p for p in target_path.rglob("*")
            if p.is_file()
            and p.suffix in VALID_EXTENSIONS
            and not any(ignored in p.parts for ignored in IGNORE_DIRS)
        ]

    for file in files:
        total_files += 1
        issues = audit_file(file)
        if issues:
            total_violations += len(issues)
            results[str(file)] = issues

    return total_files, total_violations, results


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    if not target.exists():
        print(f"[!] Target path does not exist: {target}")
        sys.exit(1)

    print(f"[*] Starting AI Slop UI Audit on: {target.resolve()}")
    total_files, total_violations, results = scan_directory(target)

    critical_count = 0
    warning_count = 0

    for file_path, issues in results.items():
        print(f"\n[FILE] {file_path}")
        for issue in issues:
            sev = issue["severity"]
            if sev == "CRITICAL":
                critical_count += 1
                color_prefix = "[CRITICAL]"
            else:
                warning_count += 1
                color_prefix = "[WARNING ]"

            print(f"  Line {issue['line']:4d} | {color_prefix} {issue['code']}: {issue['message']}")
            print(f"             Snippet: {issue['snippet']}")

    print("\n" + "=" * 60)
    print(f"Audit Summary: {total_files} files scanned | {total_violations} issues found ({critical_count} critical, {warning_count} warnings)")
    print("=" * 60)

    if critical_count > 0:
        print("[FAIL] Critical AI Slop / WCAG violations found! Remediate before deployment.")
        sys.exit(1)
    elif warning_count > 0:
        print("[PASS WITH WARNINGS] No critical errors, but aesthetic cliches should be addressed.")
        sys.exit(0)
    else:
        print("[CLEAN] 100% Free of AI Slop cliches. Human craftsmanship validated.")
        sys.exit(0)


if __name__ == "__main__":
    main()
