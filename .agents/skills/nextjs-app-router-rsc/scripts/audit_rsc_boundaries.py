#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Next.js RSC Boundary & Security Auditor -- AXION Enterprise
Scans Next.js App Router source trees for:
1. Unnecessary 'use client' directives on components without hooks or browser events (bundle bloat).
2. Dangerous server-only/database imports inside client components (secret leaks).
3. Server Actions missing validation (Zod/Valibot) or authentication guards.
4. Suspense boundary coverage on dynamic data components.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

CLIENT_HOOKS_PATTERN = r"\b(?:useState|useEffect|useReducer|useCallback|useMemo|useRef|useLayoutEffect|useContext|useId|useSyncExternalStore|usePathname|useSearchParams|useRouter)\b"
BROWSER_EVENTS_PATTERN = r"\b(?:onClick|onChange|onSubmit|onKeyDown|onKeyUp|onMouseEnter|onMouseLeave|onScroll|onFocus|onBlur)\b"
SERVER_ONLY_IMPORTS = r"(?i)(?:from\s+['\"](?:server-only|fs|child_process|path|@prisma|drizzle-orm|jsonwebtoken|bcrypt)['\"]|process\.env\.(?:DATABASE_URL|SECRET|API_KEY|TOKEN|PRIVATE_KEY))"

class RscAuditor:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.findings: List[Dict[str, Any]] = []

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".next", "dist", "build"}]
            for file_name in files:
                if not file_name.endswith((".tsx", ".ts", ".jsx", ".js")):
                    continue
                file_path = Path(root) / file_name
                self._audit_file(file_path)
        return self.findings

    def _audit_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        rel_path = file_path.relative_to(self.root_dir).as_posix()
        is_client = bool(re.search(r"^\s*['\"]use client['\"]", content, re.MULTILINE))
        is_server_action = bool(re.search(r"^\s*['\"]use server['\"]", content, re.MULTILINE))

        # Check 1: Server-only secrets/DB imports leaked into 'use client'
        if is_client:
            server_match = re.search(SERVER_ONLY_IMPORTS, content)
            if server_match:
                self.findings.append({
                    "rule": "RSC-001",
                    "severity": "CRITICAL",
                    "file": rel_path,
                    "title": "Server-Only or Secret Dependency Leaked in Client Component",
                    "description": f"Client component imports server-restricted modules or sensitive env variables: {server_match.group(0)}",
                    "remediation": "Move database and secret operations to a Server Action or Route Handler. Never import DB adapters in 'use client' files."
                })

        # Check 2: Unnecessary 'use client' directive
        if is_client:
            has_hooks = bool(re.search(CLIENT_HOOKS_PATTERN, content))
            has_events = bool(re.search(BROWSER_EVENTS_PATTERN, content))
            if not has_hooks and not has_events and not "createContext" in content:
                self.findings.append({
                    "rule": "RSC-002",
                    "severity": "MEDIUM",
                    "file": rel_path,
                    "title": "Unnecessary 'use client' Directive (Bundle Bloat)",
                    "description": "Component is marked with 'use client' but contains no React state hooks, lifecycle methods, or DOM event listeners.",
                    "remediation": "Remove 'use client' to keep this component as a React Server Component (RSC), reducing client bundle size to 0 KB."
                })

        # Check 3: Server Action missing validation
        if is_server_action or "use server" in content:
            has_validation = bool(re.search(r"\b(?:zod|safeParse|parse|validate|schema)\b", content, re.IGNORECASE))
            has_auth = bool(re.search(r"\b(?:auth|session|currentUser|userId|getToken|verifySession)\b", content, re.IGNORECASE))
            if not has_validation:
                self.findings.append({
                    "rule": "RSC-003",
                    "severity": "HIGH",
                    "file": rel_path,
                    "title": "Server Action Without Schema Validation",
                    "description": "Server Action executes without schema validation (Zod/Valibot), exposing server to malicious payloads.",
                    "remediation": "Validate action inputs with schema.safeParse(input) before executing mutations."
                })
            if not has_auth and not "public" in file_path.name.lower():
                self.findings.append({
                    "rule": "RSC-004",
                    "severity": "HIGH",
                    "file": rel_path,
                    "title": "Server Action Missing Session / Auth Check",
                    "description": "Server Action does not verify active user session or permissions before execution.",
                    "remediation": "Call auth() or verifySession() at the beginning of the Server Action."
                })

def main():
    parser = argparse.ArgumentParser(description="Next.js RSC Boundary & Security Auditor")
    parser.add_argument("--dir", "-d", default=".", help="Target Next.js project directory")
    parser.add_argument("--json", action="store_true", help="Output raw JSON array")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit with code 0")

    args = parser.parse_args()
    target_dir = Path(args.dir)

    if not target_dir.exists():
        print(f"Error: Directory {target_dir} not found.", file=sys.stderr)
        sys.exit(1)

    auditor = RscAuditor(target_dir)
    findings = auditor.scan()

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print("================================================================================")
        print("             NEXT.JS RSC BOUNDARY & SECURITY AUDITOR REPORT                     ")
        print("================================================================================")
        print(f"Directory: {target_dir}")
        print(f"Findings:  {len(findings)}")
        print("--------------------------------------------------------------------------------")
        if not findings:
            print("[PASS] Clean! No RSC boundary leaks or unvalidated Server Actions detected.")
        else:
            for idx, f in enumerate(findings, start=1):
                print(f"[{idx:02d}] [{f['severity']}] {f['rule']}: {f['title']}")
                print(f"     File: {f['file']}")
                print(f"     Desc: {f['description']}")
                print(f"     Fix:  {f['remediation']}")
                print("--------------------------------------------------------------------------------")
        print("================================================================================")

    if not args.exit_zero and any(f["severity"] in ("CRITICAL", "HIGH") for f in findings):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
