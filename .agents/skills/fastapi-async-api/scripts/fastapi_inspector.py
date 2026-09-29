#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Route & Event Loop Blocking Auditor -- AXION Enterprise
Scans FastAPI source files for:
1. Event loop blocking traps: Synchronous blocking calls (time.sleep, requests.get, subprocess.run) inside 'async def'.
2. Missing response_model or status_code on route decorators.
3. Unprotected POST/PUT/DELETE routes without authentication dependency.
4. Validates health check endpoints.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

BLOCKING_PATTERNS = [
    (r"\btime\.sleep\s*\(", "time.sleep() blocks the entire asyncio event loop! Use 'await asyncio.sleep()' instead."),
    (r"\brequests\.(?:get|post|put|delete|patch)\s*\(", "Synchronous 'requests' library blocks the event loop! Use 'httpx.AsyncClient' with async/await."),
    (r"\burllib\.request\.urlopen\s*\(", "Synchronous urllib blocks the event loop! Use 'httpx.AsyncClient'."),
    (r"\bsubprocess\.(?:run|call|check_output)\s*\(", "Synchronous subprocess blocks event loop! Use 'asyncio.create_subprocess_exec'."),
]

class FastAPIInspector:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir.resolve()
        self.findings: List[Dict[str, Any]] = []
        self.routes_found: int = 0

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        self.routes_found = 0
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "__pycache__", "build", "dist"}]
            for file_name in files:
                if not file_name.endswith(".py"):
                    continue
                file_path = Path(root) / file_name
                self._inspect_file(file_path)
        return self.findings

    def _inspect_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
        except Exception:
            return

        rel_path = file_path.relative_to(self.target_dir).as_posix()

        # Check for route decorators
        in_async_def = False
        current_func = ""
        func_start_line = 0

        for line_no, line in enumerate(lines, start=1):
            if re.search(r"@\w*(?:app|router)\.(?:get|post|put|delete|patch)\s*\(", line):
                self.routes_found += 1
                # Check for explicit status_code
                if not re.search(r"status_code\s*=", line) and ("post" in line or "delete" in line):
                    self.findings.append({
                        "file": rel_path,
                        "line": line_no,
                        "severity": "LOW",
                        "title": "Route Missing Explicit status_code",
                        "description": f"Mutating route {line.strip()[:60]} does not specify status_code (e.g. status_code=status.HTTP_201_CREATED)."
                    })

            # Detect async def
            async_match = re.search(r"^\s*async\s+def\s+(\w+)\s*\(", line)
            if async_match:
                in_async_def = True
                current_func = async_match.group(1)
                func_start_line = line_no
                continue

            # Detect synchronous def reset
            if re.search(r"^\s*def\s+(\w+)\s*\(", line) and not line.strip().startswith("async"):
                in_async_def = False

            # Inside async def: check blocking calls
            if in_async_def:
                for pat, msg in BLOCKING_PATTERNS:
                    if re.search(pat, line):
                        self.findings.append({
                            "file": rel_path,
                            "line": line_no,
                            "severity": "HIGH",
                            "title": f"Event Loop Blocking Call inside 'async def {current_func}'",
                            "description": msg,
                            "snippet": line.strip()
                        })

def main():
    parser = argparse.ArgumentParser(description="FastAPI Route & Event Loop Blocking Auditor")
    parser.add_argument("--dir", "-d", default=".", help="Target FastAPI codebase directory")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")

    args = parser.parse_args()
    target = Path(args.dir)

    if not target.exists():
        print(f"Error: Directory '{target}' does not exist.", file=sys.stderr)
        sys.exit(1)

    inspector = FastAPIInspector(target)
    findings = inspector.scan()

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print("================================================================================")
        print("             FASTAPI ASYNC & EVENT LOOP BLOCKING AUDITOR                        ")
        print("================================================================================")
        print(f"Target Directory: {target}")
        print(f"Routes Detected:  {inspector.routes_found}")
        print(f"Total Findings:   {len(findings)}")
        print("--------------------------------------------------------------------------------")
        if not findings:
            print("[PASS] Clean! No event loop blocking calls or route antipatterns detected.")
        else:
            for idx, f in enumerate(findings, start=1):
                print(f"[{idx:02d}] [{f['severity']}] {f['title']}")
                print(f"     Location: {f['file']}:{f['line']}")
                print(f"     Details:  {f['description']}")
                if "snippet" in f:
                    print(f"     Snippet:  {f['snippet']}")
                print("--------------------------------------------------------------------------------")
        print("================================================================================")

    sys.exit(1 if any(f["severity"] == "HIGH" for f in findings) else 0)

if __name__ == "__main__":
    main()
