#!/usr/bin/env python3
"""
Sentry PII Sanitization Guard & Config Inspector
Verifies Sentry configurations and scrubs sensitive PII (tokens, passwords, cards, bearer tokens)
from error payloads before dispatch. Zero external dependencies.
"""

import sys
import json
import re
from pathlib import Path

SENSITIVE_KEYS = {
    "password", "secret", "token", "access_token", "refresh_token",
    "authorization", "api_key", "cookie", "set-cookie", "credit_card",
    "cvv", "ssn", "private_key"
}

BEARER_PATTERN = re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE)
JWT_PATTERN = re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+')


def scrub_dict(data: dict) -> dict:
    """Recursively scrub sensitive keys and token patterns from a dictionary."""
    scrubbed = {}
    for key, value in data.items():
        k_lower = key.lower().replace("-", "_")
        if any(s in k_lower for s in SENSITIVE_KEYS):
            scrubbed[key] = "[FILTERED_PII]"
        elif isinstance(value, dict):
            scrubbed[key] = scrub_dict(value)
        elif isinstance(value, list):
            scrubbed[key] = [scrub_dict(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, str):
            val_clean = BEARER_PATTERN.sub("Bearer [FILTERED]", value)
            val_clean = JWT_PATTERN.sub("[FILTERED_JWT]", val_clean)
            scrubbed[key] = val_clean
        else:
            scrubbed[key] = value
    return scrubbed


def audit_sentry_config(filepath: Path) -> list[dict]:
    findings = []
    content = filepath.read_text(encoding="utf-8", errors="ignore")

    # Check for sendDefaultPii: true
    if re.search(r'sendDefaultPii\s*:\s*true', content):
        findings.append({
            "severity": "ERROR",
            "rule": "DEFAULT_PII_ENABLED",
            "message": "sendDefaultPii is set to true. This may leak user IP and system user IDs."
        })

    # Check for missing beforeSend hook
    if "beforeSend" not in content and "before_send" not in content:
        findings.append({
            "severity": "WARNING",
            "rule": "MISSING_BEFORE_SEND",
            "message": "No 'beforeSend' or 'before_send' hook defined. Payload data won't be scrubbed for PII."
        })

    # Check for hardcoded raw auth tokens in DSN or options
    if re.search(r'https://[a-f0-9]{32}:([a-f0-9]{32})@', content):
        findings.append({
            "severity": "ERROR",
            "rule": "SECRET_KEY_IN_DSN",
            "message": "Deprecated legacy DSN contains secret key. Use modern public DSN format (https://<key>@<host>/<id>)."
        })

    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sentry_pii_guard.py check-config <caminho-do-arquivo-de-config>")
        print("  python sentry_pii_guard.py test-payload <caminho-do-json-de-evento>")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "check-config":
        cfg_path = Path(sys.argv[2])
        findings = audit_sentry_config(cfg_path)
        if findings:
            print(f"=== Sentry Configuration Audit: {cfg_path.name} ===")
            for f in findings:
                prefix = "[FAIL]" if f["severity"] == "ERROR" else "[WARN]"
                print(f"{prefix} [{f['rule']}]: {f['message']}")
            sys.exit(1 if any(f["severity"] == "ERROR" for f in findings) else 0)
        else:
            print(f"[OK] Sentry configuration in {cfg_path.name} passes security checks.")
            sys.exit(0)

    elif cmd == "test-payload":
        event_path = Path(sys.argv[2])
        raw_data = json.loads(event_path.read_text(encoding="utf-8"))
        scrubbed = scrub_dict(raw_data)
        print("=== Scrubbed Sentry Event Payload ===")
        print(json.dumps(scrubbed, indent=2))
        sys.exit(0)
    else:
        print(f"[!] Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
