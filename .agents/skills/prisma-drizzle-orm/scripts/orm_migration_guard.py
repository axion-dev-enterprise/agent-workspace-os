#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORM Migration & Zero-Downtime SQL Auditor -- AXION Enterprise
Scans Prisma and Drizzle SQL migration files for destructive operations,
table-locking locks, and zero-downtime violations before production deployment.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

DANGEROUS_PATTERNS = [
    {
        "id": "MIG-001",
        "severity": "CRITICAL",
        "name": "Destructive DROP Operation",
        "regex": r"(?i)\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b",
        "description": "Dropping a table or schema in production causes permanent data loss.",
        "remediation": "Deprecate the table in code first. Archive data before executing destructive drop via planned maintenance."
    },
    {
        "id": "MIG-002",
        "severity": "CRITICAL",
        "name": "Destructive DROP COLUMN Operation",
        "regex": r"(?i)\bALTER\s+TABLE\s+.*\bDROP\s+COLUMN\b",
        "description": "Dropping a column immediately breaks running application versions that still select this field (violates Expand/Contract pattern).",
        "remediation": "Phase 1: Remove all references in code. Phase 2: Deploy code. Phase 3: Drop column in a subsequent migration."
    },
    {
        "id": "MIG-003",
        "severity": "HIGH",
        "name": "Table-Locking NOT NULL Addition without DEFAULT",
        "regex": r"(?i)\bALTER\s+TABLE\s+.*\bADD\s+COLUMN\s+.*\bNOT\s+NULL\b(?!\s+DEFAULT)",
        "description": "Adding a NOT NULL column without a DEFAULT value requires a full table rewrite and acquires an ACCESS EXCLUSIVE lock on Postgres.",
        "remediation": "Add column as NULLable first or provide a DEFAULT value so Postgres can add it via metadata rewrite instantly."
    },
    {
        "id": "MIG-004",
        "severity": "HIGH",
        "name": "Index Creation Without CONCURRENTLY",
        "regex": r"(?i)\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY\b)",
        "description": "Creating an index without CONCURRENTLY locks the table against writes until the index build is complete.",
        "remediation": "Use 'CREATE INDEX CONCURRENTLY' in PostgreSQL to build the index without blocking incoming transactions."
    },
    {
        "id": "MIG-005",
        "severity": "MEDIUM",
        "name": "Column Rename (Zero-Downtime Hazard)",
        "regex": r"(?i)\bALTER\s+TABLE\s+.*\bRENAME\s+COLUMN\b",
        "description": "Renaming a column breaks running instances immediately. Use the Expand/Contract pattern with a new column and dual-write.",
        "remediation": "Add new column, sync data, migrate code to new column, then deprecate old column."
    }
]

class MigrationAuditor:
    def __init__(self, migration_dir: Path):
        self.migration_dir = migration_dir.resolve()
        self.findings: List[Dict[str, Any]] = []

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        for root, dirs, files in os.walk(self.migration_dir):
            for file_name in files:
                if not file_name.endswith((".sql", ".prisma", ".ts", ".js")):
                    continue
                file_path = Path(root) / file_name
                self._audit_file(file_path)
        return self.findings

    def _audit_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
        except Exception:
            return

        rel_path = file_path.relative_to(self.migration_dir).as_posix()

        for rule in DANGEROUS_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if clean_line.startswith("--") or clean_line.startswith("//") or clean_line.startswith("/*"):
                    continue
                match = re.search(rule["regex"], clean_line)
                if match:
                    self.findings.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "file": rel_path,
                        "line": idx,
                        "snippet": clean_line,
                        "description": rule["description"],
                        "remediation": rule["remediation"]
                    })

def main():
    parser = argparse.ArgumentParser(description="ORM Migration & Zero-Downtime SQL Auditor")
    parser.add_argument("--dir", "-d", default=".", help="Directory containing migration files (prisma/migrations or drizzle)")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit with code 0")

    args = parser.parse_args()
    target_dir = Path(args.dir)

    if not target_dir.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    auditor = MigrationAuditor(target_dir)
    findings = auditor.scan()

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print("================================================================================")
        print("             ORM MIGRATION & ZERO-DOWNTIME AUDITOR REPORT                       ")
        print("================================================================================")
        print(f"Target Directory: {target_dir}")
        print(f"Findings:         {len(findings)}")
        print("--------------------------------------------------------------------------------")
        if not findings:
            print("[PASS] Clean! No destructive or table-locking migration operations detected.")
        else:
            for idx, f in enumerate(findings, start=1):
                print(f"[{idx:02d}] [{f['severity']}] {f['rule_id']}: {f['name']}")
                print(f"     File:    {f['file']}:{f['line']}")
                print(f"     Snippet: {f['snippet']}")
                print(f"     Risk:    {f['description']}")
                print(f"     Fix:     {f['remediation']}")
                print("--------------------------------------------------------------------------------")
        print("================================================================================")

    if not args.exit_zero and any(f["severity"] in ("CRITICAL", "HIGH") for f in findings):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
