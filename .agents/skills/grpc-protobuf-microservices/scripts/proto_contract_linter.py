#!/usr/bin/env python3
"""
Protocol Buffers (.proto) Contract Linter & Field Hygiene Auditor
Audits proto files for:
- Duplicate field numbers in messages
- Reserved protobuf field number ranges (19000 - 19999)
- Missing syntax declaration (proto3)
- Missing package namespaces
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path


def audit_proto_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # 1. Syntax check
    if not re.search(r'syntax\s*=\s*"proto3";', content):
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "MISSING_PROTO3_SYNTAX",
            "message": "Missing explicit 'syntax = \"proto3\";' declaration."
        })

    # 2. Package check
    if not re.search(r'package\s+[a-zA-Z0-9_.]+;', content):
        findings.append({
            "line": 1,
            "severity": "ERROR",
            "rule": "MISSING_PACKAGE_NAMESPACE",
            "message": "Proto file lacks a 'package' declaration. Leads to global namespace pollution."
        })

    # 3. Message field numbers analysis
    in_message = False
    current_message = ""
    seen_field_numbers = {}

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        # Detect message start
        msg_match = re.match(r'^message\s+([A-Za-z0-9_]+)', stripped)
        if msg_match:
            in_message = True
            current_message = msg_match.group(1)
            seen_field_numbers[current_message] = set()

        if in_message and stripped.startswith("}"):
            in_message = False
            current_message = ""

        # Field match: type field_name = 1;
        field_match = re.search(r'=\s*(\d+)\s*;', stripped)
        if in_message and field_match and not stripped.startswith("reserved"):
            field_num = int(field_match.group(1))

            # Reserved range check
            if 19000 <= field_num <= 19999:
                findings.append({
                    "line": idx,
                    "severity": "ERROR",
                    "rule": "RESERVED_FIELD_NUMBER",
                    "message": f"Field number {field_num} in message '{current_message}' falls into Protobuf implementation reserved range (19000-19999)."
                })

            # Duplicate check
            if field_num in seen_field_numbers[current_message]:
                findings.append({
                    "line": idx,
                    "severity": "ERROR",
                    "rule": "DUPLICATE_FIELD_NUMBER",
                    "message": f"Duplicate field number {field_num} in message '{current_message}'."
                })
            else:
                seen_field_numbers[current_message].add(field_num)

    return findings


def lint_proto_directory(target: Path) -> int:
    files = [target] if target.is_file() else list(target.glob("**/*.proto"))

    if not files:
        print(f"[!] No .proto files found in {target}")
        return 0

    print(f"=== Auditing {len(files)} Protocol Buffer contract(s) ===")
    total_errors = 0
    total_warnings = 0

    for f in files:
        findings = audit_proto_file(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [Line {item['line']} | {item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1
        else:
            print(f"[OK] {f.name}: Follows Protobuf contract hygiene standards.")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(files)} file(s).")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(lint_proto_directory(target))
