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
    r"5511988045139",
    r"551151041784",
    r"36735559962762",
    r"8573157037",
    r"8994207035:AAHqnAplG1WbGfmCLaqpIlTc9muYEAPLFWs",
    r"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",
    r"Iago\s+Barreto",
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
    "docs/ISABELA_AUDIO_TRANSCRIPTIONS_2026-10-06.md",
    "docs/ISABELA_COURSES_REVIEW_2026-10-06.md",
    "docs/ISABELA_E2E_INITIAL_RESULTS_2026-10-07.md",
    "docs/ISABELA_INFRA_INSPECTION_2026-10-07.md",
    "docs/ISABELA_LOCAL_ARCHITECTURE_2026-10-07.md",
    "docs/ISABELA_MASTER_PLAN_2026-10-07.md",
    "docs/ISABELA_NEXT_AGENT_HANDOFF_2026-10-06.md",
    "docs/PARANOID_BUG_AUDIT.md",
    "docs/knowledge",
    ".agents/skills/axion-payments-engine",
    "scripts/inspect_vercel_projects.py",
    "scripts/probe_tailnet_nodes.py",
    "scripts/production_deploy_test.py",
    "scripts/test_ceo_features_battery.py",
    "scripts/test_battery_runner.py",
    "scripts/test_flow_stage2_validation.py",
    "scripts/inspect_chats.py",
    "ecosystem.dev.js",
    "apps/axion-pay",
    "apps/axion-client-apps",
    "apps/isabela-platform",
    "apps/spapharma-tracking-app",
    "services/axion-flow",
    "services/axion-auth-center-core",
    "services/spapharma-oauth-bridge",
    "services/agent-email/otp_client.py",
    "references",
    "reports",
    "vault/ai/isabela-clients",
    "vault/cloud/isabela-clients",
    "vault/cloud/spaceship-vps",
    "vault/payments",
    "vault/security",
    "workspace/google_workspace_inventory.json",
    "workspace/health_telemetry.json",
    "workspace/master_infrastructure_map.json",
    "workspace/ssl_telemetry.json",
    "workspace/vercel_stack_analysis.json",
    "workspace/zero_trust_audit.json",
    "workspace/whatsapp_team.json",
    "workspace/whatsapp_leads.json",
]

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "memory",
    "memory_dev",
    "temp",
    "tmp",
    ".gemini",
    ".vercel",
    ".wrangler",
    "__pycache__",
    ".venv",
    "venv",
    "axion-pay",
    "auth_info_baileys",
    "auth_info",
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
            
    # 2. Check file contents for forbidden string patterns
    compiled_patterns = [(pat, re.compile(pat, re.IGNORECASE)) for pat in FORBIDDEN_PATTERNS]
    
    # Prefer Git-tracked files to prevent false positives from untracked/ignored workspace directories
    tracked_files = []
    try:
        git_res = subprocess.run(["git", "ls-files"], cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if git_res.returncode == 0:
            tracked_files = [f.strip() for f in git_res.stdout.splitlines() if f.strip()]
    except Exception:
        pass

    if tracked_files:
        candidate_paths = [repo_root / f for f in tracked_files]
    else:
        candidate_paths = []
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                candidate_paths.append(Path(root) / file)

    for full_path in candidate_paths:
        if not full_path.is_file():
            continue
        rel_str = str(full_path.relative_to(repo_root)).replace("\\", "/")
        if any(part in EXCLUDED_DIRS for part in rel_str.split("/")):
            continue
        if full_path.name in EXCLUDED_FILES or rel_str in EXCLUDED_FILES or any(rel_str.endswith(f"/{ef}") for ef in EXCLUDED_FILES):
            continue
        ext = os.path.splitext(full_path.name)[1].lower()
        if ext in BINARY_EXTENSIONS:
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
