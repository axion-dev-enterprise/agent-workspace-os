#!/usr/bin/env python3
"""
PDF Print Template & Puppeteer Config Linter
Audits HTML/CSS templates and Puppeteer scripts for:
- CSS Paged Media rules (@page size and margins)
- Page break control (break-inside: avoid on tables and signatures)
- Insecure Puppeteer flags (--disable-web-security, file:// LFI risks)
- Font load synchronization (document.fonts.ready)
Zero external dependencies (Python 3 stdlib).
"""

import sys
import re
from pathlib import Path


def audit_html_template(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")

    # Check for @page
    if "@page" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_AT_PAGE_RULE",
            "message": "Template lacks '@page' CSS rule. PDF page size and print margins may default unpredictably."
        })
    elif "size:" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_PAGE_SIZE",
            "message": "@page rule does not specify 'size: A4' or dimensions."
        })

    # Check for break-inside: avoid on tables
    if "<table" in content and "break-inside: avoid" not in content and "page-break-inside: avoid" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "UNPROTECTED_TABLE_BREAK",
            "message": "HTML contains <table> without 'break-inside: avoid' on rows. Table rows may split awkwardly across pages."
        })

    # Check for signatures
    if any(sig in content.lower() for sig in ("assinatura", "signature", "signee")):
        if "break-inside: avoid" not in content:
            findings.append({
                "severity": "WARNING",
                "rule": "UNPROTECTED_SIGNATURE_BLOCK",
                "message": "Signature block detected without 'break-inside: avoid'. Signatures must not be orphan-separated from text."
            })

    return findings


def audit_puppeteer_script(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")

    # Insecure flags
    if "--disable-web-security" in content:
        findings.append({
            "severity": "ERROR",
            "rule": "INSECURE_DISABLE_WEB_SECURITY",
            "message": "Found '--disable-web-security'. This flag exposes local files (file://) to arbitrary read attacks via HTML."
        })

    # Container safety
    if "--no-sandbox" not in content and "puppeteer" in content.lower():
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_NO_SANDBOX",
            "message": "Missing '--no-sandbox' flag. Headless Chrome may fail to launch in Linux/Docker containers."
        })

    # Font readiness
    if "fonts.ready" not in content and "networkidle0" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "RISK_OF_UNLOADED_FONTS",
            "message": "Script does not wait for 'document.fonts.ready' or 'networkidle0'. PDFs may render with system fallback fonts."
        })

    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files = [target] if target.is_file() else list(target.glob("**/*.*"))

    print(f"=== Auditing {len(files)} file(s) for PDF generation hygiene ===")
    total_errors = 0
    total_warnings = 0

    for f in files:
        findings = []
        if f.suffix in (".html", ".css"):
            findings.extend(audit_html_template(f))
        elif f.suffix in (".ts", ".js", ".py"):
            findings.extend(audit_puppeteer_script(f))

        if findings:
            print(f"\n[FILE] {f.name}")
            for item in findings:
                prefix = f"[{item['severity']}]"
                print(f"  {prefix} [{item['rule']}]: {item['message']}")
                if item["severity"] == "ERROR":
                    total_errors += 1
                else:
                    total_warnings += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across checked files.")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
