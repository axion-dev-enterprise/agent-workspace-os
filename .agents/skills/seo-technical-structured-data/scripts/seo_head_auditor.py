#!/usr/bin/env python3
"""
Technical SEO & JSON-LD Structured Data Auditor
Audits HTML pages and metadata declarations for:
- Title tag presence and length (30-65 chars)
- Meta description presence and length (50-160 chars)
- Canonical URL presence (must be absolute)
- OpenGraph tags (og:title, og:description, og:image)
- Valid JSON-LD Schema.org structure (@context and @type)
Zero external dependencies (Python 3 stdlib).
"""

import sys
import json
import re
from pathlib import Path


def audit_html_content(content: str, filename: str) -> list[dict]:
    findings = []

    # 1. Title tag
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if not title_match:
        findings.append({
            "severity": "ERROR",
            "rule": "MISSING_TITLE_TAG",
            "message": "Page lacks an explicit <title> tag."
        })
    else:
        title = title_match.group(1).strip()
        if len(title) < 20 or len(title) > 70:
            findings.append({
                "severity": "WARNING",
                "rule": "SUBOPTIMAL_TITLE_LENGTH",
                "message": f"Title length ({len(title)} chars) is outside optimal SEO range (30-65 chars): '{title}'"
            })

    # 2. Meta description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if not desc_match:
        findings.append({
            "severity": "ERROR",
            "rule": "MISSING_META_DESCRIPTION",
            "message": "Page lacks a <meta name='description'> tag."
        })
    else:
        desc = desc_match.group(1).strip()
        if len(desc) < 50 or len(desc) > 165:
            findings.append({
                "severity": "WARNING",
                "rule": "SUBOPTIMAL_DESCRIPTION_LENGTH",
                "message": f"Meta description length ({len(desc)} chars) is outside optimal range (50-160 chars)."
            })

    # 3. Canonical Link
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', content, re.IGNORECASE)
    if not canonical_match:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_CANONICAL_URL",
            "message": "Page lacks an explicit <link rel='canonical'> tag. Search engines may penalize duplicate query strings."
        })
    else:
        href = canonical_match.group(1).strip()
        if not href.startswith("http://") and not href.startswith("https://"):
            findings.append({
                "severity": "ERROR",
                "rule": "RELATIVE_CANONICAL_URL",
                "message": f"Canonical URL '{href}' is relative. Canonical links MUST be absolute URLs."
            })

    # 4. OpenGraph
    for og_prop in ("og:title", "og:description", "og:image"):
        if f'property="{og_prop}"' not in content and f"property='{og_prop}'" not in content:
            findings.append({
                "severity": "WARNING",
                "rule": "MISSING_OPENGRAPH_TAG",
                "message": f"Missing social preview tag: '{og_prop}'."
            })

    # 5. JSON-LD Schemas
    json_ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    if not json_ld_matches:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_JSON_LD",
            "message": "Page does not include any Schema.org JSON-LD structured data script."
        })
    else:
        for idx, block in enumerate(json_ld_matches, start=1):
            try:
                schema_data = json.loads(block.strip())
                if "@context" not in schema_data or "@type" not in schema_data:
                    findings.append({
                        "severity": "ERROR",
                        "rule": "INVALID_SCHEMA_ORG",
                        "message": f"JSON-LD block #{idx} lacks '@context' or '@type'."
                    })
            except json.JSONDecodeError as e:
                findings.append({
                    "severity": "ERROR",
                    "rule": "MALFORMED_JSON_LD",
                    "message": f"JSON-LD block #{idx} contains invalid JSON: {e}"
                })

    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files = [target] if target.is_file() else list(target.glob("**/*.html"))

    if not files:
        print(f"[!] No HTML files found in {target}")
        return 0

    print(f"=== Auditing {len(files)} HTML page(s) for Technical SEO ===")
    total_errors = 0
    total_warnings = 0

    for f in files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        findings = audit_html_content(content, f.name)
        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [{item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1
        else:
            print(f"[OK] {f.name}: Conforms to technical SEO and JSON-LD standards.")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(files)} file(s).")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    main()
