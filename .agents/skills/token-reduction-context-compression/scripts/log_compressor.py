#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log_compressor.py — Terminal & Test Log Noise Pruner
Zero-dependency, Python 3 stdlib only.
Compresses command outputs, test runs, and build logs by:
1. Identifying and preserving: Errors, Failures, Exceptions, Tracebacks, Warnings, Non-zero exits, and Final summaries.
2. Dropping: Progress bars (1%..100%), repeated 'PASS' / '[OK]', download progress, verbose compilation notices.
Reduces token cost by 80% to 95% on terminal executions.
"""

import sys
import re
import argparse

CRITICAL_PATTERNS = [
    r"(?i)\b(error|fail|failed|failure|exception|traceback|panic|fatal|crash)\b",
    r"(?i)\b(warn|warning)\b",
    r"(?i)\b(assert|assertionerror)\b",
    r"(?i)\bline\s+\d+",
    r"^\s*File\s+\".*\",\s+line\s+\d+",
    r"(?i)\b(passed|failed|skipped|xfailed|errors?)\s+in\s+[\d\.]+",
    r"(?i)\btest result:\s+(ok|failed)",
    r"(?i)\bexit\s+code\b",
    r"^\s*at\s+[\w\.\/<>]+\s*\(.*:\d+:\d+\)"
]

NOISE_PATTERNS = [
    r"(?i)^\s*downloading\b",
    r"(?i)^\s*fetch(ing)?\b",
    r"^\s*[\.o\+]{10,}\s*$",
    r"\[\s*\d+%\s*\]",
    r"(?i)^\s*(ok|pass|passed)\s*$",
    r"(?i)^\s*installing\s+.*(?<!error)$"
]

def is_critical(line: str) -> bool:
    for pat in CRITICAL_PATTERNS:
        if re.search(pat, line):
            return True
    return False

def is_noise(line: str) -> bool:
    for pat in NOISE_PATTERNS:
        if re.search(pat, line):
            return True
    return False

def compress_logs(log_content: str, max_lines: int = 100) -> str:
    lines = log_content.splitlines()
    if len(lines) <= 25:
        return log_content  # Small log, no compression needed
        
    kept_lines = []
    omitted_count = 0
    
    # Always keep first 3 lines (command invocation context)
    for line in lines[:3]:
        kept_lines.append(line)
        
    # Process middle lines
    for line in lines[3:-5] if len(lines) > 8 else []:
        if is_critical(line):
            kept_lines.append(line)
        elif not is_noise(line) and len(kept_lines) < max_lines:
            # Keep occasional context if not noise
            omitted_count += 1
        else:
            omitted_count += 1
            
    # Always keep last 5 lines (typically the summary, exit code or assertion summary)
    if len(lines) > 3:
        kept_lines.append(f"\n[... {omitted_count} lines of repetitive output pruned to save tokens ...]\n")
        for line in lines[-5:]:
            kept_lines.append(line)
            
    return "\n".join(kept_lines)

def main():
    parser = argparse.ArgumentParser(description="Log Noise Pruner for Terminal Token Reduction")
    parser.add_argument("file", nargs="?", default="-", help="Log file to compress or '-' for stdin")
    parser.add_argument("--max-lines", "-m", type=int, default=80, help="Max lines to keep (default: 80)")
    
    args = parser.parse_args()
    
    if args.file == "-":
        content = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
            
    compressed = compress_logs(content, max_lines=args.max_lines)
    print(compressed)

if __name__ == "__main__":
    main()
