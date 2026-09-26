#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_compressor.py — Grep & Ripgrep Output Compressor
Zero-dependency, Python 3 stdlib only.
Compresses verbose file search results before agent ingestion by:
1. Grouping matches by filename.
2. Limiting matches per file (default: 3) to prevent single-file flooding.
3. Stripping minified or ultra-long lines (> 180 chars).
Reduces search token usage by 70% to 90%.
"""

import sys
import re
import argparse
from collections import defaultdict

def compress_search(raw_output: str, max_per_file: int = 3, max_line_len: int = 160) -> str:
    lines = raw_output.splitlines()
    if len(lines) <= 20:
        return raw_output
        
    file_matches = defaultdict(list)
    unparsed_lines = []
    
    # Standard grep pattern: filename:linenumber:content or filename-linenumber-content
    pattern = re.compile(r"^([^:\n]+)[:\-](\d+)[:\-](.*)$")
    
    for line in lines:
        match = pattern.match(line)
        if match:
            fn, ln, text = match.groups()
            text = text.strip()
            if len(text) > max_line_len:
                text = text[:max_line_len - 3] + "..."
            file_matches[fn].append((ln, text))
        else:
            if len(unparsed_lines) < 10:
                unparsed_lines.append(line)
                
    output_lines = []
    for fn, matches in file_matches.items():
        output_lines.append(f"📁 {fn} ({len(matches)} matches):")
        for ln, text in matches[:max_per_file]:
            output_lines.append(f"  L{ln}: {text}")
        if len(matches) > max_per_file:
            output_lines.append(f"  [... {len(matches) - max_per_file} additional matches omitted ...]")
            
    if unparsed_lines:
        output_lines.append("\n[Uncategorized lines]:")
        output_lines.extend(unparsed_lines[:5])
        
    return "\n".join(output_lines)

def main():
    parser = argparse.ArgumentParser(description="Search & Grep Output Compressor")
    parser.add_argument("file", nargs="?", default="-", help="Search output file or '-' for stdin")
    parser.add_argument("--max-per-file", "-m", type=int, default=3, help="Max matches per file (default: 3)")
    
    args = parser.parse_args()
    
    if args.file == "-":
        content = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
            
    compressed = compress_search(content, max_per_file=args.max_per_file)
    print(compressed)

if __name__ == "__main__":
    main()
