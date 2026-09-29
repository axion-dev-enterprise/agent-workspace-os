#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whitelabel Security Validator — AXION Enterprise
Scans repository files for private/proprietary AXION identifiers to prevent accidental leaks.
Used in CI/CD, pre-push git hooks, and release export workflows.
"""

import os
import sys
import re
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Sensitive string patterns that must NEVER appear in whitelabel branch
FORBIDDEN_PATTERNS = [
    r"axion" + r"enterprise\.cloud",
    r"axion" + r"enterprise777@gmail\.com",
    r"iago@" + r"axionenterprise\.cloud",
    r"axion" + r"-vps",
    r"axion" + r"-dell-latitude-3420",
    r"axion" + r"-enterprise-srv",
    r"100\.95\." + r"86\.83",
    r"100\.73\." + r"36\.87",
    r"100\.86\." + r"136\.29",
    r"cfat_[A-Za-z0-9_-]{35,}",
    r"a79a584696834139a2b70ec306f5705c",
]

# Sensitive file names that must NEVER exist in whitelabel branch
FORBIDDEN_FILES = [
    "docs/BACKUP_RETENTION_REPORT.md",
    "docs/GOOGLE_WORKSPACE_INVENTORY.md",
    "docs/HEALTH_STATUS.md",
    "docs/HYBRID_ARCHITECTURE_UNIFICATION_PLAN.md",
    "docs/MASTER_INFRASTRUCTURE_MAP.md",
    "docs/PRODUCTION_DEPLOYMENT_REPORT.md",
    "docs/SCHEDULED_TASKS_AND_SKILLS_STUDY.md",
    "docs/SSL_DOMAIN_STATUS.md",
    "docs/SUBDOMAINS.md",
    "docs/TAILNET_AND_VERCEL_INFRASTRUCTURE.md",
    "docs/ZERO_TRUST_PORT_AUDIT.md",
    "scripts/inspect_vercel_projects.py",
    "scripts/probe_tailnet_nodes.py",
    "scripts/production_deploy_test.py",
    "apps/axion-pay",
    "workspace/google_workspace_inventory.json",
    "workspace/health_telemetry.json",
    "workspace/master_infrastructure_map.json",
    "workspace/ssl_telemetry.json",
    "workspace/vercel_stack_analysis.json",
    "workspace/zero_trust_audit.json",
]

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "memory",
    "temp",
    "tmp",
    ".gemini",
    ".vercel",
    ".wrangler",
    "__pycache__",
    ".venv",
    "venv",
    "axion-pay",
    "bot_engine",
}

EXCLUDED_FILES = {
    "validate_whitelabel.py",
    "export_whitelabel_release.py",
    "package-lock.json",
    "workspace.config.json",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".ico", ".svg", ".zip", ".tar", ".gz", ".lock", ".bin", ".woff", ".woff2", ".ttf"
}

def is_tracked_by_git(repo_root: Path, rel_path: str) -> bool:
    try:
        res = subprocess.run(["git", "ls-files", rel_path], cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
        return bool(res.stdout.strip())
    except Exception:
        return (repo_root / rel_path).exists()

def scan_repository(repo_root: Path) -> list:
    violations = []
    
    # 1. Check for forbidden file tracking in Git
    for forbidden_file in FORBIDDEN_FILES:
        if is_tracked_by_git(repo_root, forbidden_file):
            violations.append({
                "type": "FORBIDDEN_FILE",
                "file": forbidden_file,
                "message": f"Proprietary file/path '{forbidden_file}' is tracked in Git."
            })
            
    # 2. Check tracked file contents for forbidden string patterns
    compiled_patterns = [(pat, re.compile(pat, re.IGNORECASE)) for pat in FORBIDDEN_PATTERNS]
    
    try:
        res = subprocess.run(["git", "ls-files"], cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
        tracked_files = res.stdout.splitlines() if res.returncode == 0 else []
    except Exception:
        tracked_files = []

    for rel_str in tracked_files:
        rel_str = rel_str.strip().replace("\\", "/")
        if not rel_str:
            continue
        file_name = Path(rel_str).name
        if file_name in EXCLUDED_FILES or rel_str in EXCLUDED_FILES or any(rel_str.endswith(f"/{ef}") for ef in EXCLUDED_FILES):
            continue
        ext = os.path.splitext(file_name)[1].lower()
        if ext in BINARY_EXTENSIONS:
            continue

        full_path = repo_root / rel_str
        if not full_path.is_file():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            for raw_pat, comp_pat in compiled_patterns:
                matches = list(comp_pat.finditer(content))
                if matches:
                    lines = content.splitlines()
                    for m in matches:
                        line_no = content[:m.start()].count("\n") + 1
                        line_text = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                        violations.append({
                            "type": "FORBIDDEN_STRING",
                            "file": rel_str,
                            "line": line_no,
                            "pattern": raw_pat,
                            "snippet": line_text[:100]
                        })
        except Exception as e:
            violations.append({
                "type": "READ_ERROR",
                "file": rel_str,
                "message": str(e)
            })
                
    return violations

def main():
    repo_root = Path(__file__).resolve().parent.parent
    violations = scan_repository(repo_root)
    
    if violations:
        print("=" * 70)
        print(f"[VIOLATION] WHITELABEL VIOLATIONS DETECTED: {len(violations)} issues found")
        print("=" * 70)
        file_violations = [v for v in violations if v["type"] == "FORBIDDEN_FILE"]
        string_violations = [v for v in violations if v["type"] == "FORBIDDEN_STRING"]
        
        if file_violations:
            print(f"\n--- Proprietary Files ({len(file_violations)}) ---")
            for v in file_violations[:10]:
                print(f"  [FILE LEAK] {v['file']}")
            if len(file_violations) > 10:
                print(f"  ... and {len(file_violations) - 10} more files")
                
        if string_violations:
            print(f"\n--- String Leaks ({len(string_violations)}) ---")
            for v in string_violations[:15]:
                print(f"  [STRING LEAK] {v['file']}:{v['line']} -> {v['pattern']} in: \"{v['snippet']}\"")
            if len(string_violations) > 15:
                print(f"  ... and {len(string_violations) - 15} more occurrences")
                
        print("=" * 70)
        sys.exit(1)
    else:
        print("[OK] Whitelabel Validation PASSED: 0 proprietary leaks detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
