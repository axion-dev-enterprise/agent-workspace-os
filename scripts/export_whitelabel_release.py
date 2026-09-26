#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whitelabel Release Exporter — AXION Enterprise
Synchronizes changes from internal branch ('axion') to public distribution branch ('main').
Performs deterministic redaction, domain sanitization, topology exclusion, and validation.
"""

import os
import sys
import subprocess
import shutil
import re
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")

REPLACEMENTS = [
    ("axionenterprise.cloud", "example.com"),
    ("iago@axionenterprise.cloud", "admin@example.com"),
    ("axionenterprise777@gmail.com", "developer@example.com"),
    ("axion-vps", "vps-node-01"),
    ("axion-dell-latitude-3420", "workstation-node-01"),
    ("axion-enterprise-srv", "srv-node-01"),
    ("100.95.86.83", "100.64.0.1"),
    ("100.73.36.87", "100.64.0.2"),
    ("100.86.136.29", "100.64.0.3"),
    ("a79a584696834139a2b70ec306f5705c", "your_cloudflare_account_id"),
    ("axion777", "your-team-slug"),
]

# Files that should be purged from main branch
INTERNAL_FILES = [
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
    "scripts/telegram_assistant_bot.py",
    "workspace/google_workspace_inventory.json",
    "workspace/health_telemetry.json",
    "workspace/master_infrastructure_map.json",
    "workspace/ssl_telemetry.json",
    "workspace/vercel_stack_analysis.json",
    "workspace/zero_trust_audit.json",
]

def run_git(args: list) -> str:
    res = subprocess.run(["git"] + args, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: git {' '.join(args)}\nError: {res.stderr.strip()}")
    return res.stdout.strip()

def sanitize_file(file_path: Path):
    if not file_path.is_file():
        return
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return
    
    modified = False
    new_content = re.sub(r"cfat_[A-Za-z0-9_-]{30,}", "cfat_YOUR_CLOUDFLARE_API_TOKEN", content)
    if new_content != content:
        content = new_content
        modified = True
        
    for target, repl in REPLACEMENTS:
        if target in content:
            content = content.replace(target, repl)
            modified = True
            
    if modified:
        file_path.write_text(content, encoding="utf-8")

def export_whitelabel(commit_message: str = None, push_remote: bool = False):
    print("=" * 70)
    print("=== AXION Whitelabel Release Exporter ===")
    print("=" * 70)
    
    # 1. Verify current branch
    current_branch = run_git(["branch", "--show-current"])
    if current_branch != "axion":
        print(f"[ERROR] Must be on branch 'axion' to run export (currently on '{current_branch}')")
        sys.exit(1)
        
    # Check working tree
    status = run_git(["status", "--porcelain"])
    if status:
        print("[ERROR] Working tree has uncommitted changes. Please commit or stash them first.")
        print(status)
        sys.exit(1)
        
    print(f"[*] Current branch is '{current_branch}' with clean worktree.")
    
    # 2. Get list of files modified or added compared to main
    diff_files = run_git(["diff", "--name-only", "main...axion"]).splitlines()
    print(f"[*] Found {len(diff_files)} changed files between main and axion.")
    
    # 3. Checkout branch main
    print("[*] Switching to branch 'main'...")
    run_git(["checkout", "main"])
    
    try:
        # 4. For files in diff_files: if not internal, checkout from axion and sanitize
        copied_count = 0
        for rel_file in diff_files:
            if not rel_file.strip():
                continue
            if rel_file in INTERNAL_FILES:
                continue
            if rel_file.startswith("memory/") or rel_file.startswith("temp/"):
                continue
                
            # Checkout file from axion branch
            run_git(["checkout", "axion", "--", rel_file])
            file_path = WORKSPACE_ROOT / rel_file
            if file_path.exists():
                if rel_file not in ["scripts/validate_whitelabel.py", "scripts/export_whitelabel_release.py"]:
                    sanitize_file(file_path)
                copied_count += 1
                
        print(f"[*] Synchronized and sanitized {copied_count} files onto 'main'.")
        
        # 5. Global sanitization sweep across all text files on 'main'
        EXCLUDED_SWEEP_DIRS = {".git", "node_modules", "memory", "temp", "tmp", ".gemini", ".vercel", ".wrangler"}
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_SWEEP_DIRS]
            for f in files:
                full_f = Path(root) / f
                rel_f = str(full_f.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                if rel_f in ["scripts/validate_whitelabel.py", "scripts/export_whitelabel_release.py"]:
                    continue
                if full_f.suffix.lower() in [".md", ".json", ".py", ".ts", ".js", ".html", ".css", ".txt", ".yml", ".yaml"]:
                    sanitize_file(full_f)
                    
        # 6. Ensure all internal files are strictly removed on main
        purged = 0
        for int_file in INTERNAL_FILES:
            target = WORKSPACE_ROOT / int_file
            if target.exists():
                target.unlink()
                try:
                    run_git(["rm", "--cached", "-f", int_file])
                except Exception:
                    pass
                purged += 1
        if purged > 0:
            print(f"[*] Purged {purged} internal proprietary files from 'main'.")
            
        # 6. Re-run registry synchronizer on main
        subprocess.run([sys.executable, "scripts/sync_skills_registry.py"], cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        # Sanitize any registry or docs updated by synchronizer
        for check_doc in ["docs/SKILLS_REGISTRY.md", "AGENTS.md", "workspace/inventory.json"]:
            p = WORKSPACE_ROOT / check_doc
            if p.exists():
                sanitize_file(p)
                
        # 7. Run validation
        val_res = subprocess.run([sys.executable, "scripts/validate_whitelabel.py"], cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if val_res.returncode != 0:
            print("[FAIL] Whitelabel validation failed on branch 'main'!")
            print(val_res.stdout)
            print("[*] Aborting and switching back to 'axion'...")
            run_git(["reset", "--hard", "HEAD"])
            run_git(["checkout", "axion"])
            sys.exit(1)
            
        print("[OK] Whitelabel validation PASSED: 0 leaks on 'main'.")
        
        # 8. Check status on main
        main_status = run_git(["status", "--porcelain"])
        if not main_status:
            print("[*] No changes detected on 'main' compared to upstream.")
        else:
            msg = commit_message or "[antigravity][whitelabel] chore: sync latest updates to public whitelabel distribution"
            run_git(["add", "-A"])
            run_git(["commit", "-m", msg])
            print(f"[OK] Committed to 'main': {msg}")
            
            if push_remote:
                print("[*] Pushing 'main' to origin/main...")
                run_git(["push", "origin", "main"])
                print("[OK] Successfully pushed 'main' to origin/main!")
                
    finally:
        # Always return to axion branch
        print("[*] Switching back to enterprise branch 'axion'...")
        run_git(["checkout", "axion"])
        print("=== Whitelabel sync completed successfully! ===")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    push = "--push" in sys.argv
    export_whitelabel(commit_message=msg, push_remote=push)
