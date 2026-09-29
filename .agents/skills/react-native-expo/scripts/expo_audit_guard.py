#!/usr/bin/env python3
"""
React Native & Expo Configuration and Hygiene Auditor
Audits Expo mobile projects for:
- Missing bundleIdentifier (iOS) and package (Android) in app.json
- Insecure token storage (AsyncStorage instead of SecureStore)
- Slow FlatList usage in large collections
Zero external dependencies (Python 3 stdlib).
"""

import sys
import json
import re
from pathlib import Path


def audit_app_json(filepath: Path) -> list[dict]:
    findings = []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        expo = data.get("expo", {})

        # iOS bundleIdentifier
        ios = expo.get("ios", {})
        if not ios.get("bundleIdentifier"):
            findings.append({
                "severity": "ERROR",
                "rule": "MISSING_IOS_BUNDLE_ID",
                "message": "app.json lacks 'expo.ios.bundleIdentifier' (e.g. 'com.company.app'). Required for App Store / EAS build."
            })

        # Android package
        android = expo.get("android", {})
        if not android.get("package"):
            findings.append({
                "severity": "ERROR",
                "rule": "MISSING_ANDROID_PACKAGE",
                "message": "app.json lacks 'expo.android.package' (e.g. 'com.company.app'). Required for Google Play / EAS build."
            })

        # Adaptive icon check
        if not android.get("adaptiveIcon"):
            findings.append({
                "severity": "WARNING",
                "rule": "MISSING_ADAPTIVE_ICON",
                "message": "app.json lacks 'expo.android.adaptiveIcon'. App icon may look degraded on newer Android devices."
            })

    except Exception as e:
        findings.append({
            "severity": "ERROR",
            "rule": "INVALID_APP_JSON",
            "message": f"Failed to parse app.json: {e}"
        })

    return findings


def audit_code_files(root: Path) -> list[dict]:
    findings = []
    files = list(root.glob("**/*.tsx")) + list(root.glob("**/*.ts"))

    for f in files:
        # Ignore node_modules
        if "node_modules" in f.parts:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for idx, line in enumerate(lines, start=1):
                # Check for AsyncStorage saving tokens
                if "AsyncStorage.setItem" in line and any(t in line.lower() for t in ("token", "jwt", "secret", "auth")):
                    findings.append({
                        "file": str(f),
                        "line": idx,
                        "severity": "ERROR",
                        "rule": "INSECURE_AUTH_STORAGE",
                        "message": "Auth token stored in AsyncStorage. Use 'expo-secure-store' (iOS Keychain / Android Keystore) for sensitive credentials."
                    })

                # Warn about FlatList in performance-sensitive contexts
                if "from 'react-native'" in line and "FlatList" in line:
                    findings.append({
                        "file": str(f),
                        "line": idx,
                        "severity": "WARNING",
                        "rule": "PREFER_FLASH_LIST",
                        "message": "Standard React Native 'FlatList' imported. For high-performance 60/120 FPS lists, consider '@shopify/flash-list'."
                    })
        except Exception:
            pass

    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    print(f"=== Auditing Expo Mobile App: {target} ===")
    findings = []

    app_json = target / "app.json"
    if app_json.exists():
        findings.extend(audit_app_json(app_json))
    else:
        print("[!] app.json not found in target root.")

    findings.extend(audit_code_files(target))

    total_errors = sum(1 for f in findings if f["severity"] == "ERROR")
    total_warnings = sum(1 for f in findings if f["severity"] == "WARNING")

    for item in findings:
        prefix = f"[{item['severity']}]"
        loc = f" ({item.get('file', '')}:{item.get('line', '')})" if "file" in item else ""
        print(f"  {prefix} [{item['rule']}]{loc}: {item['message']}")

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings.")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
