#!/usr/bin/env python3
"""
GraphQL Schema & Apollo Federation Linter
Audits GraphQL SDL (.graphql / .gql) files for:
- Missing @key directives on federated entities
- Unbounded lists without pagination arguments
- Deprecated fields lacking explanatory reasons
- Dangerous root-level schema queries
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path


def audit_graphql_schema(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    in_type_block = False
    current_type_name = ""
    is_federated = "@key" in content or "@shareable" in content or "extend schema" in content

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect type definitions
        type_match = re.match(r'^(type|interface)\s+([A-Za-z0-9_]+)(.*)$', stripped)
        if type_match:
            kind, name, rest = type_match.groups()
            current_type_name = name
            in_type_block = True

            # If this is a federated schema, check if custom object types define a @key
            if is_federated and kind == "type" and name not in ("Query", "Mutation", "Subscription"):
                if "@key" not in rest and "@shareable" not in rest:
                    findings.append({
                        "file": str(filepath),
                        "line": idx,
                        "severity": "WARNING",
                        "rule": "FEDERATED_KEY_MISSING",
                        "message": f"Type '{name}' in federated subgraph does not specify an entity '@key' directive."
                    })

        if stripped.endswith("}"):
            in_type_block = False
            current_type_name = ""

        # Check for unbounded lists in fields: fieldName: [TypeName] without (first: Int, after: String)
        if in_type_block and ":" in stripped and current_type_name in ("Query", "Mutation"):
            if re.search(r':\s*\[[A-Za-z0-9_!]+\]', stripped) and "(" not in stripped:
                findings.append({
                    "file": str(filepath),
                    "line": idx,
                    "severity": "WARNING",
                    "rule": "UNBOUNDED_LIST_QUERY",
                    "message": f"Root query '{stripped.split(':')[0].strip()}' returns a list without pagination arguments (limit/offset or cursor)."
                })

        # Check for bare @deprecated without reason
        if "@deprecated" in stripped and not re.search(r'@deprecated\s*\(\s*reason\s*:', stripped):
            findings.append({
                "file": str(filepath),
                "line": idx,
                "severity": "WARNING",
                "rule": "BARE_DEPRECATED_DIRECTIVE",
                "message": f"Line {idx}: '@deprecated' directive should provide an explicit 'reason'."
            })

    return findings


def lint_schemas(target: Path) -> int:
    files = [target] if target.is_file() else list(target.glob("**/*.graphql")) + list(target.glob("**/*.gql"))

    if not files:
        print(f"[!] No .graphql or .gql files found in {target}")
        return 0

    print(f"=== Auditing {len(files)} GraphQL Schema(s) ===")
    total_errors = 0
    total_warnings = 0

    for f in files:
        findings = audit_graphql_schema(f)
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
            print(f"[OK] {f.name}: Follows GraphQL schema hygiene standards.")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(files)} file(s).")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(lint_schemas(target))
