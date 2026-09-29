#!/usr/bin/env python3
"""
Prompt Injection & Jailbreak Heuristic Scanner
Scans untrusted inputs and prompt templates for prompt injection patterns,
system instruction override attempts, and delimiter escape sequences.
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path

INJECTION_SIGNATURES = [
    (re.compile(r'(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules)\b'), "DIRECT_OVERRIDE", "Attempts to override prior system instructions"),
    (re.compile(r'(?i)\bdisregard\s+(all\s+)?(previous|prior)\s+(rules|prompts|guidelines)\b'), "DIRECT_OVERRIDE", "Attempts to disregard system rules"),
    (re.compile(r'(?i)\byou\s+are\s+now\s+(unrestricted|in\s+DAN\s+mode|an\s+evil\s+AI|jailbroken)\b'), "ROLE_REVERSAL", "Attempts persona jailbreak or role escalation"),
    (re.compile(r'(?i)\bprint\s+(your\s+)?(system\s+prompt|initial\s+instructions|system\s+instructions)\b'), "EXFILTRATION_PROMPT", "Attempts to extract system prompt"),
    (re.compile(r'(?i)\brepeat\s+everything\s+(above|from\s+the\s+beginning)\b'), "EXFILTRATION_PROMPT", "Attempts verbatim context dump"),
    (re.compile(r'(?i)</(user_input|untrusted_data|document_payload)>\s*(?:new\s+task|instruction|system)'), "DELIMITER_ESCAPE", "Attempts to break out of data encapsulation tags"),
]


def audit_text_for_injections(text: str) -> list[dict]:
    findings = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        for pattern, tag, desc in INJECTION_SIGNATURES:
            if pattern.search(line):
                findings.append({
                    "line": idx,
                    "rule": tag,
                    "description": desc,
                    "snippet": line.strip()[:80]
                })

    return findings


def audit_prompt_template_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")

    # Check if raw variables are interpolated without XML/Markdown delimiters
    raw_interpolations = re.findall(r'f["\'].*?\{([a-zA-Z_][a-zA-Z0-9_]*)\}.*?["\']', content)
    for var in raw_interpolations:
        if any(untrusted in var.lower() for untrusted in ("input", "query", "user", "doc", "payload")):
            # Check if surrounded by tags
            tag_pattern = rf'<[\w\-]+>\s*\{{{var}\}}\s*</[\w\-]+>'
            if not re.search(tag_pattern, content):
                findings.append({
                    "line": 0,
                    "rule": "UNTAGGED_INTERPOLATION",
                    "description": f"Variable '{{{var}}}' appears to be interpolated directly without encapsulating XML tags.",
                    "snippet": f"{{{var}}}"
                })

    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python prompt_injection_scanner.py scan-input <arquivo-de-texto-ou-prompt>")
        print("  python prompt_injection_scanner.py scan-code <arquivo.py>")
        sys.exit(0)

    cmd = sys.argv[1]
    target = Path(sys.argv[2])

    if cmd == "scan-input":
        text = target.read_text(encoding="utf-8", errors="ignore")
        findings = audit_text_for_injections(text)
        print(f"=== Injection Scan: {target.name} ===")
        if findings:
            for f in findings:
                print(f"[FAIL] [Line {f['line']} | {f['rule']}]: {f['description']}")
                print(f"       Snippet: '{f['snippet']}'")
            sys.exit(1)
        else:
            print("[OK] No prompt injection signatures found in input.")
            sys.exit(0)

    elif cmd == "scan-code":
        findings = audit_prompt_template_file(target)
        print(f"=== Code Template Hygiene: {target.name} ===")
        if findings:
            for f in findings:
                print(f"[WARN] [{f['rule']}]: {f['description']}")
            sys.exit(0)
        else:
            print("[OK] Prompt construction follows tag encapsulation patterns.")
            sys.exit(0)


if __name__ == "__main__":
    main()
