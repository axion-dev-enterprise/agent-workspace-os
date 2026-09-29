#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright E2E Test Suite Runner & Reporter -- AXION Enterprise
Executes Playwright tests with standardized flags, trace collection on failure,
and clean console output parsing.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

def find_playwright_config(target_dir: Path) -> Path:
    candidates = [
        target_dir / "playwright.config.ts",
        target_dir / "playwright.config.js",
        target_dir / "e2e" / "playwright.config.ts"
    ]
    for c in candidates:
        if c.exists():
            return c
    return target_dir / "playwright.config.ts"

def run_playwright(target_dir: Path, browser: str = "chromium", grep: str = None, headed: bool = False, update_snapshots: bool = False):
    cmd = ["npx", "playwright", "test"]

    if browser:
        cmd.extend(["--project", browser])
    if grep:
        cmd.extend(["--grep", grep])
    if headed:
        cmd.append("--headed")
    if update_snapshots:
        cmd.append("--update-snapshots")

    cmd.extend(["--reporter", "list,json"])

    print(f"[*] Executing Playwright E2E Test Suite in {target_dir}...")
    print(f"[*] Command: {' '.join(cmd)}")

    env = os.environ.copy()
    env["CI"] = "1"

    res = subprocess.run(cmd, cwd=target_dir, env=env)
    return res.returncode

def main():
    parser = argparse.ArgumentParser(description="Playwright E2E Suite Runner")
    parser.add_argument("--dir", "-d", default=".", help="Project directory containing tests")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit", "all"], default="chromium")
    parser.add_argument("--grep", "-g", help="Run tests matching tag or pattern (e.g. @smoke, @critical)")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed visible mode")
    parser.add_argument("--update-snapshots", action="store_true", help="Update visual comparison snapshots")

    args = parser.parse_args()
    target = Path(args.dir).resolve()

    if not target.exists():
        print(f"Error: Directory {target} not found.", file=sys.stderr)
        sys.exit(1)

    browser = None if args.browser == "all" else args.browser
    code = run_playwright(target, browser=browser, grep=args.grep, headed=args.headed, update_snapshots=args.update_snapshots)

    print("\n--------------------------------------------------------------------------------")
    if code == 0:
        print("[PASS] All Playwright E2E tests completed successfully.")
    else:
        print(f"[FAIL] Playwright suite failed with exit code {code}. Check traces in test-results/.")
    print("================================================================================")
    sys.exit(code)

if __name__ == "__main__":
    main()
