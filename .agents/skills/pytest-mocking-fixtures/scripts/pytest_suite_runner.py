#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest Suite Runner & Coverage Gate -- AXION Enterprise
Executes pytest with strict coverage thresholds, short tracebacks,
and clean formatted terminal output.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_pytest(target_dir: Path, cov_package: str = None, min_coverage: int = 80, fast: bool = False, verbose: bool = False):
    cmd = [sys.executable, "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    cmd.extend(["--tb=short", "-ra"])

    if fast:
        cmd.extend(["-n", "auto"])

    if cov_package:
        cmd.extend([
            f"--cov={cov_package}",
            "--cov-report=term-missing",
            f"--cov-fail-under={min_coverage}"
        ])

    print(f"[*] Executing Pytest in {target_dir}...")
    print(f"[*] Command: {' '.join(cmd)}\n")

    res = subprocess.run(cmd, cwd=target_dir)
    return res.returncode

def main():
    parser = argparse.ArgumentParser(description="Pytest Suite Runner & Coverage Gate")
    parser.add_argument("--dir", "-d", default=".", help="Directory to run pytest in")
    parser.add_argument("--cov", "-c", help="Package name to measure coverage for (e.g. motion_engine)")
    parser.add_argument("--min-cov", type=int, default=80, help="Minimum coverage percentage (default: 80)")
    parser.add_argument("--fast", action="store_true", help="Run tests in parallel via pytest-xdist")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose test execution output")

    args = parser.parse_args()
    target = Path(args.dir).resolve()

    if not target.exists():
        print(f"Error: Target directory {target} does not exist.", file=sys.stderr)
        sys.exit(1)

    code = run_pytest(target, cov_package=args.cov, min_coverage=args.min_cov, fast=args.fast, verbose=args.verbose)

    print("\n--------------------------------------------------------------------------------")
    if code == 0:
        print("[PASS] All tests passed and coverage criteria met!")
    else:
        print(f"[FAIL] Pytest suite failed with return code {code}.")
    print("================================================================================")
    sys.exit(code)

if __name__ == "__main__":
    main()
