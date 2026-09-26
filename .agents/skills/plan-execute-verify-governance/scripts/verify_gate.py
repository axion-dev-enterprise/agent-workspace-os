#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_gate.py — Evidence-First Verification Gate & Receipt Generator
Zero-dependency, Python 3 stdlib only.
Enforces the Iron Law of Engineering:
"NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"

Executes verification commands, checks exit codes, validates output assertions,
and issues a cryptographic evidence receipt (SHA-256) for audit trails.
"""

import sys
import os
import subprocess
import hashlib
import json
import time
import re
import argparse
from datetime import datetime, timezone

def run_verification(command: str, expect_pattern: str = None, timeout: int = 120, cwd: str = ".") -> dict:
    start_time = time.time()
    iso_start = datetime.now(timezone.utc).isoformat()
    
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        duration = round(time.time() - start_time, 3)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 3)
        return {
            "verified": False,
            "status": "TIMEOUT",
            "command": command,
            "duration_sec": duration,
            "error": f"Command timed out after {timeout} seconds."
        }
    except Exception as e:
        duration = round(time.time() - start_time, 3)
        return {
            "verified": False,
            "status": "EXECUTION_ERROR",
            "command": command,
            "duration_sec": duration,
            "error": str(e)
        }

    # Evaluate assertions
    pattern_matched = True
    pattern_msg = ""
    if expect_pattern:
        if re.search(expect_pattern, stdout + "\n" + stderr, re.MULTILINE):
            pattern_matched = True
            pattern_msg = f"Output matched required pattern: '{expect_pattern}'"
        else:
            pattern_matched = False
            pattern_msg = f"Output DID NOT match required pattern: '{expect_pattern}'"

    is_verified = (exit_code == 0) and pattern_matched
    
    # Generate cryptographic hash receipt of execution
    raw_payload = f"{command}:{exit_code}:{iso_start}:{duration}:{stdout[:500]}"
    receipt_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:16]

    receipt = {
        "verified": is_verified,
        "receipt_id": f"VR-{receipt_hash.upper()}",
        "timestamp": iso_start,
        "command": command,
        "exit_code": exit_code,
        "duration_sec": duration,
        "pattern_check": pattern_msg if expect_pattern else "N/A",
        "stdout_preview": stdout[-500:].strip() if stdout else "",
        "stderr_preview": stderr[-500:].strip() if stderr else ""
    }
    
    return receipt

def main():
    parser = argparse.ArgumentParser(description="Evidence-First Verification Gate")
    parser.add_argument("command", help="Verification command to execute (e.g., 'pytest tests/' or 'npm test')")
    parser.add_argument("--expect", "-e", help="Regex pattern that MUST exist in stdout/stderr")
    parser.add_argument("--timeout", "-t", type=int, default=120, help="Timeout in seconds (default: 120)")
    parser.add_argument("--cwd", default=".", help="Working directory for command")
    parser.add_argument("--json", action="store_true", help="Output raw JSON receipt")
    
    args = parser.parse_args()
    
    receipt = run_verification(args.command, expect_pattern=args.expect, timeout=args.timeout, cwd=args.cwd)
    
    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        status_symbol = "[VERIFIED ✓]" if receipt["verified"] else "[FAILED ✗]"
        print(f"\n{'='*60}")
        print(f"VERIFICATION GATE RECEIPT: {receipt.get('receipt_id', 'ERR')}")
        print(f"Status:   {status_symbol}")
        print(f"Command:  {receipt['command']}")
        print(f"Exit:     {receipt.get('exit_code', -1)} (Duration: {receipt.get('duration_sec', 0)}s)")
        if args.expect:
            print(f"Pattern:  {receipt['pattern_check']}")
        print(f"{'='*60}")
        if receipt.get("stdout_preview"):
            print("Output Preview:\n" + receipt["stdout_preview"])
        if receipt.get("stderr_preview"):
            print("Errors/Stderr Preview:\n" + receipt["stderr_preview"])
            
    sys.exit(0 if receipt["verified"] else 1)

if __name__ == "__main__":
    main()
