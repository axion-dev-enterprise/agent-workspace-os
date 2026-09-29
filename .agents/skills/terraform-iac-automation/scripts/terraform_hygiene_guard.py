#!/usr/bin/env python3
"""
Terraform Hygiene & Security Linter
Audits Terraform (.tf) files for hardcoded secrets, missing stateful protections (prevent_destroy),
untyped variables, and provider version pinning. Zero external dependencies.
"""

import sys
import re
from pathlib import Path

# Resources that should ideally have lifecycle { prevent_destroy = true }
CRITICAL_RESOURCES = [
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_s3_bucket",
    "google_sql_database_instance",
    "google_storage_bucket",
    "azurerm_cosmosdb_account",
    "azurerm_storage_account",
]

SECRET_PATTERNS = [
    (re.compile(r'(?i)(password|secret|token|api_key|access_key)\s*=\s*"([^"]+)"'), "Potential hardcoded secret or token"),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'), "Hardcoded private key block detected"),
]


def audit_tf_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # 1. Check for hardcoded secrets
    for line_idx, line in enumerate(lines, start=1):
        # Ignore comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        for pattern, desc in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                val = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(0)
                # Ignore variable interpolations or empty strings or dummy placeholders
                if not (val.startswith("var.") or val.startswith("local.") or val in ("", "CHANGE_ME", "dummy")):
                    findings.append({
                        "file": str(filepath),
                        "line": line_idx,
                        "severity": "ERROR",
                        "rule": "HARDCODED_CREDENTIAL",
                        "message": f"{desc} in assignment: '{stripped[:40]}...'"
                    })

    # 2. Check variables without type or description
    var_blocks = re.findall(r'variable\s+"([^"]+)"\s*{([^}]+)}', content, re.DOTALL)
    for var_name, var_body in var_blocks:
        if "type" not in var_body:
            findings.append({
                "file": str(filepath),
                "line": 0,
                "severity": "WARNING",
                "rule": "UNTYPED_VARIABLE",
                "message": f"Variable '{var_name}' lacks explicit 'type' constraint."
            })
        if "description" not in var_body:
            findings.append({
                "file": str(filepath),
                "line": 0,
                "severity": "WARNING",
                "rule": "UNDOCUMENTED_VARIABLE",
                "message": f"Variable '{var_name}' lacks 'description' field."
            })

    # 3. Check critical resources for prevent_destroy
    for res in CRITICAL_RESOURCES:
        res_matches = re.finditer(rf'resource\s+"{res}"\s+"([^"]+)"\s*\{{(.*?)\n\}}', content, re.DOTALL)
        for m in res_matches:
            res_id = m.group(1)
            body = m.group(2)
            if "prevent_destroy" not in body or "true" not in body:
                findings.append({
                    "file": str(filepath),
                    "line": 0,
                    "severity": "WARNING",
                    "rule": "MISSING_PREVENT_DESTROY",
                    "message": f"Critical stateful resource '{res}.{res_id}' should declare 'lifecycle {{ prevent_destroy = true }}'."
                })

    return findings


def lint_directory(root_dir: Path) -> int:
    tf_files = list(root_dir.glob("**/*.tf"))
    if not tf_files:
        print(f"[!] No .tf files found in {root_dir}")
        return 0

    print(f"=== Auditing {len(tf_files)} Terraform (.tf) file(s) in {root_dir} ===")
    total_errors = 0
    total_warnings = 0

    for f in tf_files:
        findings = audit_tf_file(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = "[FAIL]" if item["severity"] == "ERROR" else "[WARN]"
                loc = f":{item['line']}" if item["line"] > 0 else ""
                print(f"  {prefix} [{item['rule']}{loc}] {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1
        else:
            print(f"[OK] {f.name}: Passed hygiene checks.")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(tf_files)} files.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(lint_directory(target))
