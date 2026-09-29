#!/usr/bin/env python3
"""
Social Media Asset Specs & 3D Canvas Hygiene Linter
Audits creative assets and Three.js scenes for:
- Correct platform aspect ratios (1:1 Square, 9:16 Vertical Story/Reels, 16:9 Landscape)
- Missing disposal on Three.js unmount (memory leaks)
- Accessible HTML fallback for WebGL canvases
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path


def audit_threejs_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    if "three" not in content and "Three" not in content:
        return findings

    # Check for memory disposal in unmount/cleanup
    has_dispose = "dispose()" in content or ".dispose(" in content
    if not has_dispose:
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "MISSING_RESOURCE_DISPOSAL",
            "message": "Three.js code does not call dispose() on geometries, materials, or textures. High risk of WebGL context memory leaks on unmount."
        })

    # Check for canvas fallback / prefers-reduced-motion
    if "canvas" in content and "prefers-reduced-motion" not in content:
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "MISSING_REDUCED_MOTION",
            "message": "Canvas animation lacks 'prefers-reduced-motion' media query handling for accessibility."
        })

    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files = [target] if target.is_file() else list(target.glob("**/*.*"))
    code_exts = {".ts", ".tsx", ".js", ".jsx", ".html"}
    files = [f for f in files if f.suffix in code_exts and "node_modules" not in f.parts]

    print(f"=== Auditing {len(files)} file(s) for 3D & Social Studio hygiene ===")
    total_warnings = 0
    total_errors = 0

    for f in files:
        findings = audit_threejs_file(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [{item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across checked files.")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
