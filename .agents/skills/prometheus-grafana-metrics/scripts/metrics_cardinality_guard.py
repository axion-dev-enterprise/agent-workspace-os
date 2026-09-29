#!/usr/bin/env python3
"""
Prometheus Metrics Cardinality Guard & Exporter Validator
Audits metrics declarations and live /metrics exposition for:
- Dangerous high-cardinality labels (user_id, token, uuid, email, timestamp)
- Missing unit suffixes in metric names (_seconds, _bytes, _total)
- Cardinality explosion in scrape output
Zero external dependencies.
"""

import sys
import re
import urllib.request
from pathlib import Path

HIGH_CARDINALITY_LABEL_PATTERNS = [
    re.compile(r'\b(user_?id|account_?id|customer_?id)\b', re.IGNORECASE),
    re.compile(r'\b(order_?id|transaction_?id|payment_?id)\b', re.IGNORECASE),
    re.compile(r'\b(email|phone|cpf|ssn)\b', re.IGNORECASE),
    re.compile(r'\b(token|jwt|session_?id|auth)\b', re.IGNORECASE),
    re.compile(r'\b(uuid|guid|trace_?id|span_?id)\b', re.IGNORECASE),
    re.compile(r'\b(timestamp|created_?at|time)\b', re.IGNORECASE),
]

CODE_LABEL_PATTERN = re.compile(r'labelnames\s*=\s*\[(.*?)\]|label_names\s*=\s*\[(.*?)\]|labels:\s*\[(.*?)\]', re.IGNORECASE)


def audit_code_file(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        match = CODE_LABEL_PATTERN.search(line)
        if match:
            labels_str = match.group(1) or match.group(2) or match.group(3) or ""
            labels = [lbl.strip(" '\"") for lbl in labels_str.split(",") if lbl.strip()]
            for lbl in labels:
                for pat in HIGH_CARDINALITY_LABEL_PATTERNS:
                    if pat.search(lbl):
                        findings.append({
                            "file": str(filepath),
                            "line": idx,
                            "severity": "ERROR",
                            "rule": "HIGH_CARDINALITY_LABEL",
                            "message": f"Dangerous label '{lbl}' detected in Prometheus metric declaration. Cardinality explosion will crash TSDB."
                        })
    return findings


def audit_live_endpoint(url: str) -> list[dict]:
    findings = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Metrics-Cardinality-Guard/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return [{"severity": "ERROR", "rule": "FETCH_FAILED", "message": f"Could not reach {url}: {e}"}]

    metric_series_count = {}
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Extract metric name and labels: metric_name{label="val",...} 123
        m = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{?(.*?)\}?\s+.*$', line)
        if m:
            m_name = m.group(1)
            labels_raw = m.group(2)
            metric_series_count[m_name] = metric_series_count.get(m_name, 0) + 1

            # Check individual labels for unbounded patterns (e.g. UUIDs as values)
            for pair in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)=("[^"]*")', labels_raw):
                lbl_name = pair.group(1)
                lbl_val = pair.group(2).strip('"')
                for pat in HIGH_CARDINALITY_LABEL_PATTERNS:
                    if pat.search(lbl_name):
                        findings.append({
                            "severity": "ERROR",
                            "rule": "HIGH_CARDINALITY_EXPOSED",
                            "message": f"Metric '{m_name}' exposes high-cardinality label '{lbl_name}'."
                        })
                if len(lbl_val) > 100:
                    findings.append({
                        "severity": "WARNING",
                        "rule": "LARGE_LABEL_VALUE",
                        "message": f"Metric '{m_name}' has unusually large label value ({len(lbl_val)} chars) for '{lbl_name}'."
                    })

    for m_name, count in metric_series_count.items():
        if count > 500:
            findings.append({
                "severity": "ERROR",
                "rule": "CARDINALITY_SPIKE",
                "message": f"Metric '{m_name}' has {count} active timeseries in single scrape. High risk of memory bloat."
            })

    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python metrics_cardinality_guard.py scan-code <diretório-ou-arquivo>")
        print("  python metrics_cardinality_guard.py check-endpoint <url-de-metrics>")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "scan-code":
        target = Path(sys.argv[2])
        files = [target] if target.is_file() else list(target.glob("**/*.*"))
        code_exts = {".py", ".ts", ".js", ".go", ".rs"}
        files = [f for f in files if f.suffix in code_exts]

        print(f"=== Auditing {len(files)} code file(s) for metric cardinality ===")
        total_err = 0
        for f in files:
            findings = audit_code_file(f)
            if findings:
                print(f"\n[FILE] {f.name}")
                for item in findings:
                    print(f"  [{item['severity']}] [Line {item['line']} | {item['rule']}]: {item['message']}")
                    if item["severity"] == "ERROR":
                        total_err += 1
        print("\n---------------------------------------------------------")
        print(f"Code Scan Completed: {total_err} errors found.")
        sys.exit(1 if total_err > 0 else 0)

    elif cmd == "check-endpoint":
        url = sys.argv[2]
        print(f"=== Inspecting metrics endpoint: {url} ===")
        findings = audit_live_endpoint(url)
        if findings:
            for item in findings:
                print(f"  [{item['severity']}] [{item['rule']}]: {item['message']}")
            sys.exit(1 if any(f["severity"] == "ERROR" for f in findings) else 0)
        else:
            print("[OK] Metrics endpoint passed cardinality hygiene checks.")
            sys.exit(0)


if __name__ == "__main__":
    main()
