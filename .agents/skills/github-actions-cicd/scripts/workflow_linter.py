#!/usr/bin/env python3
"""
GitHub Actions Workflow Security & Hygiene Linter
Audits workflow YAML files for:
- Missing or excessive permissions (principle of least privilege)
- Pinned commit SHA vs unpinned/mutable branch tags
- Expression injection vulnerabilities (e.g. in run steps)
- Dangerous triggers (pull_request_target misuse)
- Missing concurrency cancel-in-progress on PR pipelines
Zero external dependencies (Python 3 stdlib only).
"""

import sys
import re
from pathlib import Path

MUTABLE_REF_PATTERN = re.compile(r'uses:\s*([\w\-]+/[\w\-]+)@(main|master|latest|v\d+)\b')
EXPR_INJECTION_PATTERN = re.compile(r'run:.*?\$\{\{\s*github\.event\.(issue|pull_request|comment|head_commit)')


def audit_workflow(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # 1. Check permissions block
    if "permissions:" not in content:
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "MISSING_EXPLICIT_PERMISSIONS",
            "message": "Workflow does not declare top-level 'permissions:'. Defaults may grant excessive write access."
        })
    elif "permissions: write-all" in content or "write-all" in content:
        findings.append({
            "line": 1,
            "severity": "ERROR",
            "rule": "EXCESSIVE_PERMISSIONS",
            "message": "Workflow grants 'write-all' permissions. Restrict to specific scopes (e.g. contents: read)."
        })

    # 2. Check for dangerous triggers
    if "pull_request_target" in content:
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "DANGEROUS_TRIGGER_PULL_REQUEST_TARGET",
            "message": "'pull_request_target' runs with write permissions and repository secrets. Ensure untrusted code is not checked out."
        })

    # 3. Check for concurrency on PR workflows
    if "pull_request:" in content and "concurrency:" not in content:
        findings.append({
            "line": 1,
            "severity": "WARNING",
            "rule": "MISSING_CONCURRENCY_CANCEL",
            "message": "Pull request workflow lacks 'concurrency' with 'cancel-in-progress: true' to avoid redundant CI runs."
        })

    # 4. Line by line inspections: Action pinning and script injection
    for idx, line in enumerate(lines, start=1):
        # Expression injection in bash run steps
        if EXPR_INJECTION_PATTERN.search(line):
            findings.append({
                "line": idx,
                "severity": "ERROR",
                "rule": "EXPRESSION_INJECTION_RISK",
                "message": f"Direct interpolation of untrusted github.event in 'run:' command. Pass via intermediate env variable: '{line.strip()[:60]}...'"
            })

        # Mutable action refs
        match = MUTABLE_REF_PATTERN.search(line)
        if match:
            action_name = match.group(1)
            ref = match.group(2)
            findings.append({
                "line": idx,
                "severity": "WARNING",
                "rule": "MUTABLE_ACTION_REFERENCE",
                "message": f"Action '{action_name}' is pinned to mutable tag '@{ref}'. Pin to full commit SHA for supply-chain integrity."
            })

    return findings


def lint_workflows(target_dir: Path) -> int:
    workflow_files = []
    if target_dir.is_file():
        workflow_files.append(target_dir)
    else:
        for ext in ("*.yml", "*.yaml"):
            workflow_files.extend(target_dir.glob(f"**/{ext}"))

    if not workflow_files:
        print(f"[!] No workflow YAML files found in {target_dir}")
        return 0

    print(f"=== Auditing {len(workflow_files)} GitHub Actions workflow(s) ===")
    total_errors = 0
    total_warnings = 0

    for f in workflow_files:
        findings = audit_workflow(f)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = "[FAIL]" if item["severity"] == "ERROR" else "[WARN]"
                print(f"  {prefix} [Line {item['line']} | {item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1
        else:
            print(f"[OK] {f.name}: Follows CI/CD security hygiene standards.")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(workflow_files)} files.")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".github/workflows")
    sys.exit(lint_workflows(target))
