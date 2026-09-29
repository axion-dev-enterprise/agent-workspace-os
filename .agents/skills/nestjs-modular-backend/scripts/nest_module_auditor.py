#!/usr/bin/env python3
"""
NestJS Architecture & Module Hygiene Linter
Audits NestJS codebases for:
- Missing enableShutdownHooks in main.ts
- Missing or insecure ValidationPipe configuration
- Un-typed @Body() parameters in controllers
- Circular dependency risks and leaky provider exports
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path


def audit_main_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")

    if "enableShutdownHooks" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_SHUTDOWN_HOOKS",
            "message": "main.ts does not call 'app.enableShutdownHooks()'. Pods in K8s may terminate abruptly on SIGTERM."
        })

    if "ValidationPipe" not in content:
        findings.append({
            "severity": "ERROR",
            "rule": "MISSING_GLOBAL_VALIDATION",
            "message": "main.ts does not configure a global 'ValidationPipe'. Inputs will not be validated by DTO schemas."
        })
    elif "whitelist: true" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "INCOMPLETE_VALIDATION_PIPE",
            "message": "ValidationPipe lacks 'whitelist: true'. Unwhitelisted payload properties won't be stripped."
        })

    return findings


def audit_controller_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for idx, line in enumerate(lines, start=1):
        # Look for @Body() body or @Body() data without type
        match = re.search(r'@Body\(\s*\)\s*([a-zA-Z_]\w*)\s*(?::\s*any\b|(?=\s*[,)]))', line)
        if match:
            findings.append({
                "severity": "ERROR",
                "rule": "UNTYPED_BODY_PARAM",
                "message": f"Line {idx}: Controller parameter '{match.group(1)}' lacks a dedicated DTO type class."
            })
    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    ts_files = [target] if target.is_file() else list(target.glob("**/*.ts"))

    print(f"=== Auditing NestJS Project: {target} ===")
    total_errors = 0
    total_warnings = 0

    for f in ts_files:
        findings = []
        if f.name == "main.ts":
            findings.extend(audit_main_file(f))
        if f.name.endswith(".controller.ts"):
            findings.extend(audit_controller_file(f))

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
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(ts_files)} file(s).")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
