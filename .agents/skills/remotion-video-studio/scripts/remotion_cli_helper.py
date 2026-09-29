#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remotion CLI Helper -- AXION Enterprise
Inspects, previews, and renders Remotion programmatic videos.
Runs on Python 3 standard library.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

def check_node():
    try:
        res = subprocess.run(["node", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def inspect_project(project_dir: Path):
    pkg_file = project_dir / "package.json"
    if not pkg_file.exists():
        print(f"Error: No package.json found in {project_dir}", file=sys.stderr)
        return False
    try:
        pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        remotion_version = deps.get("remotion", "Not installed")
        print(f"Project: {pkg.get('name', 'unnamed')}")
        print(f"Remotion Version: {remotion_version}")
        return True
    except Exception as e:
        print(f"Error reading package.json: {e}", file=sys.stderr)
        return False

def run_command(cmd, cwd):
    print(f"[CMD] {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd).returncode

def main():
    parser = argparse.ArgumentParser(description="Remotion Video Studio CLI Helper")
    parser.add_argument("--dir", "-d", default=".", help="Remotion project directory")
    parser.add_argument("--info", action="store_true", help="Inspect Remotion project info")
    parser.add_argument("--studio", action="store_true", help="Launch Remotion Studio")
    parser.add_argument("--render", help="Composition ID to render")
    parser.add_argument("--out", "-o", default="out.mp4", help="Output file path")
    parser.add_argument("--frames", help="Frame range (e.g. 0-60)")

    args = parser.parse_args()
    proj = Path(args.dir).resolve()

    node_v = check_node()
    if not node_v:
        print("Error: Node.js is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)

    if args.info:
        inspect_project(proj)
        sys.exit(0)

    if args.studio:
        code = run_command(["npx", "remotion", "preview"], cwd=proj)
        sys.exit(code)

    if args.render:
        cmd = ["npx", "remotion", "render", args.render, args.out]
        if args.frames:
            cmd.extend(["--frames", args.frames] )
        code = run_command(cmd, cwd=proj)
        sys.exit(code)

    parser.print_help()

if __name__ == "__main__":
    main()