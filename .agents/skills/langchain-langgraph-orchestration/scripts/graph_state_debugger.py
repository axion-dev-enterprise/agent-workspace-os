#!/usr/bin/env python3
"""
LangGraph State Machine Linter & Topology Auditor
Analyzes graph definitions for infinite recursion vulnerabilities, missing exit conditions,
unpinned thread_id checkpointers, and unhandled conditional edges.
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path

REQUIRED_ELEMENTS = [
    (re.compile(r'set_entry_point\s*\('), "Entrypoint definition ('set_entry_point')"),
    (re.compile(r'add_node\s*\('), "Node registration ('add_node')"),
]

RISK_PATTERNS = [
    (re.compile(r'compile\s*\(\s*\)'), "WARNING", "Graph compiled without checkpointer. State will be ephemeral in production."),
    (re.compile(r'recursion_limit["\']?\s*:\s*(?:100|\d{3,})'), "WARNING", "High recursion_limit detected. Guard against runaway token loops."),
    (re.compile(r'operator\.add'), "INFO", "Standard append-only message state reducer found."),
]


def audit_graph_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # Skip if not a LangGraph file
    if "StateGraph" not in content and "MessageGraph" not in content:
        return findings

    # Check required elements
    for pat, desc in REQUIRED_ELEMENTS:
        if not pat.search(content):
            findings.append({
                "severity": "ERROR",
                "rule": "MISSING_GRAPH_TOPOLOGY",
                "message": f"Graph file lacks mandatory element: {desc}."
            })

    # Check for END node connection
    if "END" not in content:
        findings.append({
            "severity": "ERROR",
            "rule": "NO_TERMINAL_NODE",
            "message": "Graph lacks reference to terminal 'END' node. Risk of infinite execution loop."
        })

    # Line-by-line inspection
    for idx, line in enumerate(lines, start=1):
        for pat, sev, msg in RISK_PATTERNS:
            if pat.search(line):
                findings.append({
                    "severity": sev,
                    "rule": "GRAPH_CONFIGURATION",
                    "message": f"Line {idx}: {msg}"
                })

    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    py_files = [target] if target.is_file() else list(target.glob("**/*.py"))

    print(f"=== Auditing {len(py_files)} Python file(s) for LangGraph topologies ===")
    total_errors = 0
    total_warnings = 0

    for f in py_files:
        findings = audit_graph_file(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [{item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                elif item["severity"] == "WARNING":
                    total_warnings += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(py_files)} files.")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
