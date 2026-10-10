#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paranoid Codebase Bug Hunter Scanner -- AXION Enterprise
Universal, cross-stack static analysis engine for adversarial bug hunting.
Designed to be 100% reusable across any application, backend, frontend, microservice, or database.

Profiles:
- generic: Universal bugs (falsy zeroes, unhandled async errors, float math, memory leaks, enums)
- security: Secret leaks, hardcoded IPs, SQL injection, insecure deserialization/eval
- concurrency: Race conditions, missing row locks, terminal state resurrection, idempotency collisions
- fintech: Solvency checks, balance locks, settlement intervals, currency units
- all: Executes all rule packs (default)

Zero dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IGNORE_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "out",
    ".cache", ".venv", "venv", "__pycache__", "temp", ".idea", ".vscode"
}

RELEVANT_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".sql", ".prisma", ".json", ".go", ".rs", ".java", ".php"
}

# ==============================================================================
# RULE PACKS (Modular & Extensible across any application stack)
# ==============================================================================

RULE_PACKS: Dict[str, List[Dict[str, Any]]] = {
    "generic": [
        {
            "id": "GEN-001",
            "name": "Uncleaned Polling Interval or Timer",
            "severity": "HIGH",
            "category": "Lifecycle & Memory Leak",
            "extensions": [".ts", ".tsx", ".js", ".jsx"],
            "regex": r"setInterval\s*\(\s*(?:async\s*)?\(\s*\)\s*=>",
            "file_missing_pattern": r"clearInterval",
            "description": "setInterval invoked without corresponding clearInterval in the file or cleanup routine, causing leaked timers, memory leaks, and phantom network traffic.",
            "remediation": "Store the interval ID and call clearInterval in component unmount, useEffect teardown, or worker termination."
        },
        {
            "id": "GEN-002",
            "name": "Falsy Zero or Boolean Suppression via Logical OR",
            "severity": "MEDIUM",
            "category": "Nullish & Falsy Trap",
            "extensions": [".ts", ".tsx", ".js", ".jsx"],
            "regex": r"(\w*(?:amount|balance|fee|tax|rate|count|total|price|limit|offset|timeout|retry|retries|delay|score|points|level|index|quantity|stock|priority)\w*)\s*\|\|\s*([0-9]+|\w+)",
            "description": "Logical OR operator (||) used with numeric or countable variable. If the legitimate value is 0, the operator treats it as falsy and applies the fallback, corrupting zero-values.",
            "remediation": "Use nullish coalescing operator (??) instead of logical OR (||) when 0 or false is a valid business value."
        },
        {
            "id": "GEN-003",
            "name": "Case-Sensitive Enum or State Comparison",
            "severity": "HIGH",
            "category": "Enum & Schema Resilience",
            "extensions": [".ts", ".tsx", ".js", ".jsx", ".py"],
            "regex": r"(?:status|state|type|role|phase|mode|priority|interval|action)\s*===\s*['\"]([A-Z_]{3,})['\"]",
            "description": "Strict case-sensitive equality comparison against uppercase string. External APIs, databases, or webhook payloads often deliver lowercase or mixed-case values.",
            "remediation": "Normalize input with .toUpperCase() / .toLowerCase() or utilize case-insensitive enums: status?.toUpperCase() === 'ACTIVE'."
        },
        {
            "id": "GEN-004",
            "name": "Floating Point Precision Hazard in Calculations",
            "severity": "MEDIUM",
            "category": "Precision & Accuracy",
            "extensions": [".ts", ".tsx", ".js", ".jsx", ".py"],
            "regex": r"(?:amount|price|fee|balance|quota|rate|metric)\s*[\*\/]\s*(?:0\.\d+|[0-9]+\.[0-9]+)",
            "description": "Direct floating-point arithmetic on sensitive numbers. IEEE 754 floating-point introduces cumulative precision and rounding artifacts.",
            "remediation": "Operate in integer units (e.g. cents, basis points, micros) or use arbitrary-precision decimal libraries (Decimal, BigInt)."
        },
        {
            "id": "GEN-005",
            "name": "Unhandled Async Function Without Try/Catch Block",
            "severity": "MEDIUM",
            "category": "Reliability & Crash Prevention",
            "extensions": [".ts", ".js"],
            "regex": r"(?:export\s+async\s+function|const\s+\w+\s*=\s*async\s*\([^)]*\)\s*=>\s*\{)(?![\s\S]{1,160}try\s*\{)",
            "description": "Asynchronous route, worker, or controller handler without top-level try/catch block, risking unhandled promise rejections and silent node process terminations.",
            "remediation": "Wrap asynchronous execution in try/catch and dispatch structured errors to global error middleware."
        },
        {
            "id": "GEN-006",
            "name": "Arbitrary Code Execution / Dynamic Eval",
            "severity": "CRITICAL",
            "category": "Code Injection",
            "extensions": [".ts", ".tsx", ".js", ".jsx", ".py"],
            "regex": r"(?:\beval\s*\(|new\s+Function\s*\(|exec\s*\(|subprocess\.Popen\(.*shell\s*=\s*True)",
            "description": "Dynamic string evaluation or shell execution detected. Introduces high-severity remote code execution (RCE) vectors.",
            "remediation": "Replace dynamic code evaluation with structured parsers, AST interpreters, or parameter lists without shell=True."
        }
    ],

    "security": [
        {
            "id": "SEC-001",
            "name": "Hardcoded Server IP Address",
            "severity": "HIGH",
            "category": "Perimeter & Network Exposure",
            "extensions": [".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".go"],
            "regex": r"\b(?!127\.0\.0\.1|0\.0\.0\.0)(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "description": "Hardcoded non-loopback IP address identified in source code. Violates Zero Public Attack Surface and compromises environment portability.",
            "remediation": "Replace hardcoded IPs with internal DNS hostnames routed through Zero Trust tunnels or inject via vault environment variables."
        },
        {
            "id": "SEC-002",
            "name": "Hardcoded Sensitive Credential or Secret",
            "severity": "CRITICAL",
            "category": "Credential Governance",
            "extensions": [".ts", ".tsx", ".js", ".jsx", ".py"],
            "regex": r"(?i)(?:pin|password|secret|api_key|auth_token|access_key)\s*[:=]\s*['\"](?:1234|0000|admin|password|test|secret|root|bearer\s+[a-zA-Z0-9_\-\.]{8,})['\"]",
            "description": "Hardcoded secret, default password, test PIN or bearer token literal detected in source code.",
            "remediation": "Remove secret literal immediately. Inject credentials exclusively from runtime vault (load_vault())."
        },
        {
            "id": "SEC-003",
            "name": "Potential SQL Injection via String Concatenation",
            "severity": "CRITICAL",
            "category": "Data Layer Security",
            "extensions": [".ts", ".js", ".py"],
            "regex": r"(?i)(?:execute|query|rawQuery|\$queryRawUnsafe)\s*\(\s*['\"`].*(?:SELECT|UPDATE|DELETE|INSERT).*(?:\+|(?:\$\{[^\}]+\}))",
            "description": "SQL query built via raw string concatenation or unescaped template interpolation, creating severe SQL injection vulnerabilities.",
            "remediation": "Use parameterized queries, prepared statements, or ORM tagged template literals ($queryRaw`...`)."
        },
        {
            "id": "SEC-004",
            "name": "Permissive Wildcard CORS Configuration",
            "severity": "HIGH",
            "category": "Network & Access Boundaries",
            "extensions": [".ts", ".js", ".py"],
            "regex": r"(?i)(?:Access-Control-Allow-Origin\s*['\"]?\s*:\s*['\"]?\*|origin\s*:\s*['\"]?\*['\"]?)",
            "description": "Permissive wildcard CORS header found. Allows unauthorized third-party origins to execute authenticated cross-origin requests.",
            "remediation": "Restrict origins to verified domain allowlist and never combine wildcard origins with credentials support."
        }
    ],

    "concurrency": [
        {
            "id": "CONC-001",
            "name": "State or Balance Read Without Explicit Lock",
            "severity": "HIGH",
            "category": "Concurrency & Locking",
            "extensions": [".ts", ".js", ".py", ".sql"],
            "regex": r"(?i)(SELECT\s+.*(?:balance|saldo|credit|funds|stock|inventory|seats|quota|available).*\bFROM\s+\w+[^;]*)(?!.*FOR\s+UPDATE)",
            "negative_lookahead": r"FOR\s+UPDATE",
            "description": "Resource balance, stock, or quota read without explicit 'FOR UPDATE' row lock, exposing transactions to double-allocation, double-spending, or race conditions.",
            "remediation": "Enforce explicit row lock ('SELECT ... FOR UPDATE') inside a transaction or use atomic conditional update (WHERE stock >= :amount)."
        },
        {
            "id": "CONC-002",
            "name": "State Machine Terminal State Resurrection",
            "severity": "HIGH",
            "category": "State Machine & Idempotency",
            "extensions": [".ts", ".js", ".py"],
            "regex": r"(?i)(?:update.*status|status\s*=).*(?:PAID|COMPLETED|FAILED|CANCELED|EXPIRED|RESOLVED|ARCHIVED|CLOSED|TERMINATED)",
            "file_missing_pattern": r"(?i)(?:terminal|isTerminalStatus|status\s*in\s*\[|already.*closed|return\s+\{.*ack)",
            "description": "Event handler or worker updates entity status without checking if the record is already in an irreversible terminal state, risking resurrection.",
            "remediation": "Inspect current entity status before mutation. If already in terminal state, acknowledge event and discard further state changes."
        },
        {
            "id": "CONC-003",
            "name": "Idempotency Key or Request ID Reuse Across Cycles",
            "severity": "HIGH",
            "category": "Idempotency & Replay",
            "extensions": [".ts", ".js", ".py"],
            "regex": r"(?:renew|recurring|retry|cycle|repeat).*(?:correlation_id|idempotency_key|tx_id|payment_id)\s*[:=]\s*(?:original|subscription\.id|sub\.id|item\.id)",
            "description": "Recurring cycle or scheduled task recycling the original resource ID as transaction/request idempotency key, causing upstream deduplication failures.",
            "remediation": "Generate a unique composite idempotency key per cycle or execution (e.g. `${entityId}_cycle_${cycleNumber}_${uuid()}`)."
        }
    ],

    "fintech": [
        {
            "id": "FIN-001",
            "name": "Immediate Settlement Without Release Grace Period",
            "severity": "HIGH",
            "category": "Financial Invariants",
            "extensions": [".ts", ".js", ".py"],
            "regex": r"(?i)(?:credit.*available.*balance|settle.*immediate|release.*funds).*(?:card|credit_card)",
            "description": "Credit card transactions credited immediately to available balance without enforcing contractual settlement period (e.g., D+14 or D+30).",
            "remediation": "Credit pending settlement ledger with release date calculated based on payment instrument rules."
        },
        {
            "id": "FIN-002",
            "name": "Potential Currency Unit Mismatch (Float vs Cents)",
            "severity": "HIGH",
            "category": "Financial Invariants",
            "extensions": [".ts", ".tsx", ".js", ".jsx"],
            "regex": r"(?:R\$|\$|EUR)\s*\{?\s*(?:tx|payment|order|item)\.(?:amount|price|value)\s*\}?",
            "file_missing_pattern": r"(?:amountCents|/ 100|\.toFixed)",
            "description": "Direct currency rendering using unnormalized amount property without explicit cent division (/ 100), risking displaying 100x multiplied amounts.",
            "remediation": "Standardize strictly on integer cents (amountCents) and convert via (amountCents / 100).toFixed(2)."
        }
    ]
}

class UniversalCodebaseScanner:
    def __init__(
        self,
        root_dir: Path,
        profile: str = "all",
        target_extensions: Optional[List[str]] = None,
        severity_filter: str = "ALL",
        custom_rules_file: Optional[Path] = None
    ):
        self.root_dir = root_dir.resolve()
        self.profile = profile.lower()
        self.target_extensions = set(target_extensions) if target_extensions else RELEVANT_EXTENSIONS
        self.severity_filter = severity_filter.upper()
        self.custom_rules_file = custom_rules_file
        self.rules: List[Dict[str, Any]] = self._assemble_rules()
        self.findings: List[Dict[str, Any]] = []

    def _assemble_rules(self) -> List[Dict[str, Any]]:
        active_rules: List[Dict[str, Any]] = []

        if self.profile == "all":
            for pack in RULE_PACKS.values():
                active_rules.extend(pack)
        elif self.profile in RULE_PACKS:
            active_rules.extend(RULE_PACKS[self.profile])
        else:
            print(f"Warning: Unknown profile '{self.profile}', defaulting to 'all'.", file=sys.stderr)
            for pack in RULE_PACKS.values():
                active_rules.extend(pack)

        # Load external custom rules if provided
        if self.custom_rules_file and self.custom_rules_file.exists():
            try:
                with open(self.custom_rules_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                    if isinstance(custom, list):
                        active_rules.extend(custom)
                        print(f"[+] Loaded {len(custom)} custom rules from {self.custom_rules_file}")
            except Exception as e:
                print(f"Error loading custom rules: {e}", file=sys.stderr)

        return active_rules

    def should_skip_dir(self, dir_name: str) -> bool:
        return dir_name in IGNORE_DIRS or dir_name.startswith(".")

    def should_scan_file(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.target_extensions

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not self.should_skip_dir(d)]
            for file_name in files:
                file_path = Path(root) / file_name
                if not self.should_scan_file(file_path):
                    continue
                self._scan_single_file(file_path)
        return self.findings

    def _scan_single_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return

        rel_path = file_path.relative_to(self.root_dir).as_posix()
        file_ext = file_path.suffix.lower()

        for rule in self.rules:
            if self.severity_filter != "ALL" and rule.get("severity") != self.severity_filter:
                continue

            if file_ext not in rule.get("extensions", []):
                continue

            # Check file-wide negative patterns if specified
            if "file_missing_pattern" in rule:
                has_trigger = re.search(rule["regex"], content)
                has_mitigation = re.search(rule["file_missing_pattern"], content)
                if has_trigger and not has_mitigation:
                    match = re.search(rule["regex"], content)
                    line_no = content[:match.start()].count("\n") + 1 if match else 1
                    snippet = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                    self.findings.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule.get("severity", "MEDIUM"),
                        "category": rule.get("category", "General"),
                        "file": rel_path,
                        "line": line_no,
                        "snippet": snippet,
                        "description": rule.get("description", ""),
                        "remediation": rule.get("remediation", "")
                    })
                continue

            # Standard line-by-line / block matching
            try:
                for line_idx, line in enumerate(lines, start=1):
                    trimmed = line.strip()
                    if trimmed.startswith("//") or trimmed.startswith("#") or trimmed.startswith("*"):
                        continue

                    match = re.search(rule["regex"], line)
                    if match:
                        if "negative_lookahead" in rule and re.search(rule["negative_lookahead"], line):
                            continue

                        self.findings.append({
                            "rule_id": rule["id"],
                            "name": rule["name"],
                            "severity": rule.get("severity", "MEDIUM"),
                            "category": rule.get("category", "General"),
                            "file": rel_path,
                            "line": line_idx,
                            "snippet": trimmed,
                            "description": rule.get("description", ""),
                            "remediation": rule.get("remediation", "")
                        })
            except Exception:
                continue

def format_console_report(findings: List[Dict[str, Any]], root_path: Path, profile: str) -> str:
    out = []
    out.append("================================================================================")
    out.append("             PARANOID BUG HUNTER -- ADVERSARIAL SCAN REPORT                     ")
    out.append("================================================================================")
    out.append(f"Target Directory: {root_path}")
    out.append(f"Active Profile:   {profile.upper()}")
    out.append(f"Total Findings:   {len(findings)}")
    out.append("--------------------------------------------------------------------------------")

    if not findings:
        out.append("STATUS: CLEAN. No paranoid bug patterns detected under active profile.")
        out.append("================================================================================")
        return "\n".join(out)

    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f.get("severity", "LOW")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    out.append(f"Breakdown: CRITICAL={by_severity['CRITICAL']} | HIGH={by_severity['HIGH']} | MEDIUM={by_severity['MEDIUM']} | LOW={by_severity['LOW']}")
    out.append("================================================================================\n")

    for idx, f in enumerate(findings, start=1):
        out.append(f"[{idx:03d}] [{f['severity']}] {f['rule_id']} - {f['name']}")
        out.append(f"      Location:    {f['file']}:{f['line']}")
        out.append(f"      Category:    {f['category']}")
        out.append(f"      Snippet:     {f['snippet']}")
        out.append(f"      Description: {f['description']}")
        out.append(f"      Fix:         {f['remediation']}")
        out.append("--------------------------------------------------------------------------------")

    return "\n".join(out)

def format_markdown_report(findings: List[Dict[str, Any]], root_path: Path, profile: str) -> str:
    md = []
    md.append("# Paranoid Bug Hunter -- Relatorio de Auditoria Estatica")
    md.append("")
    md.append(f"- **Diretorio Auditado:** `{root_path}`")
    md.append(f"- **Perfil de Regras:** `{profile.upper()}`")
    md.append(f"- **Total de Achados:** {len(findings)}")
    md.append("")
    md.append("## Sumario Executivo")
    md.append("")

    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f.get("severity", "LOW")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    md.append("| Severidade | Quantidade |")
    md.append("| :--- | :--- |")
    md.append(f"| CRITICAL | {by_severity['CRITICAL']} |")
    md.append(f"| HIGH | {by_severity['HIGH']} |")
    md.append(f"| MEDIUM | {by_severity['MEDIUM']} |")
    md.append(f"| LOW | {by_severity['LOW']} |")
    md.append("")
    md.append("## Detalhamento de Achados")
    md.append("")

    if not findings:
        md.append("Nenhuma vulnerabilidade ou anti-padrao detectado no escopo auditado.")
        return "\n".join(md)

    for idx, f in enumerate(findings, start=1):
        md.append(f"### {idx:02d}. [{f['severity']}] {f['rule_id']}: {f['name']}")
        md.append(f"- **Arquivo:** `{f['file']}:{f['line']}`")
        md.append(f"- **Categoria:** {f['category']}")
        md.append(f"- **Trecho:** `{f['snippet']}`")
        md.append(f"- **Impacto Potencial:** {f['description']}")
        md.append(f"- **Acao Recomendada:** {f['remediation']}")
        md.append("")

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(
        description="Paranoid Bug Hunter -- Static Codebase Adversarial Scanner (Universal & Extensible)"
    )
    parser.add_argument(
        "--dir", "-d",
        default=".",
        help="Target directory to scan (default: current directory)"
    )
    parser.add_argument(
        "--profile", "-p",
        default="all",
        choices=["all", "generic", "security", "concurrency", "fintech"],
        help="Rulepack profile to execute (default: all)"
    )
    parser.add_argument(
        "--severity", "-s",
        default="ALL",
        choices=["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        help="Filter findings by severity"
    )
    parser.add_argument(
        "--rules",
        help="Path to external custom JSON rules file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON array of findings"
    )
    parser.add_argument(
        "--report", "-r",
        help="Path to write markdown audit report file"
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 even if issues are found"
    )

    args = parser.parse_args()
    target_dir = Path(args.dir)

    if not target_dir.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    custom_rules_path = Path(args.rules) if args.rules else None

    scanner = UniversalCodebaseScanner(
        root_dir=target_dir,
        profile=args.profile,
        severity_filter=args.severity,
        custom_rules_file=custom_rules_path
    )
    findings = scanner.scan()

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print(format_console_report(findings, target_dir, args.profile))

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(format_markdown_report(findings, target_dir, args.profile))
        print(f"[OK] Markdown report saved to: {report_path}")

    if not args.exit_zero and len(findings) > 0:
        has_critical = any(f.get("severity") in ("CRITICAL", "HIGH") for f in findings)
        sys.exit(2 if has_critical else 1)

    sys.exit(0)

if __name__ == "__main__":
    main()
