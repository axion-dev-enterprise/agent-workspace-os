#!/usr/bin/env python3
"""
Kubernetes Manifest Security & Hygiene Linter
Audits Kubernetes YAML manifests for production anti-patterns, missing resource bounds,
security contexts, probes, and image tag discipline. Zero external dependencies.
"""

import sys
import os
import re
from pathlib import Path

# Checks to perform on pod specs
RULES = {
    "MISSING_RESOURCES": "Container must specify both resources.requests and resources.limits",
    "MISSING_READINESS": "Long-running pod must define a readinessProbe",
    "MISSING_LIVENESS": "Long-running pod must define a livenessProbe",
    "ROOT_USER_ALLOWED": "SecurityContext should enforce runAsNonRoot: true",
    "WRITABLE_ROOT_FS": "SecurityContext should enforce readOnlyRootFilesystem: true",
    "PRIVILEGE_ESCALATION": "allowPrivilegeEscalation should be explicitly false",
    "LATEST_IMAGE_TAG": "Image uses ':latest' or no tag, violating immutable deployment policy",
    "MISSING_HEALTH_CHECK_PATH": "HTTP probes should use dedicated health/readiness endpoints",
}


def audit_yaml_content(content: str, filepath: str) -> list[dict]:
    findings = []
    lines = content.splitlines()

    # Detect if this is a workload with pods (Deployment, StatefulSet, DaemonSet, Pod)
    is_workload = bool(re.search(r'kind:\s*(Deployment|StatefulSet|DaemonSet|Job|Pod)', content, re.IGNORECASE))
    if not is_workload:
        return findings

    has_requests = "requests:" in content
    has_limits = "limits:" in content
    if not (has_requests and has_limits):
        findings.append({
            "rule": "MISSING_RESOURCES",
            "severity": "ERROR",
            "message": "Missing 'requests' or 'limits' in resource specifications.",
            "file": filepath
        })

    # Probes
    has_readiness = "readinessProbe:" in content
    has_liveness = "livenessProbe:" in content
    if not has_readiness:
        findings.append({
            "rule": "MISSING_READINESS",
            "severity": "WARNING",
            "message": "Missing readinessProbe. Traffic may route to unready containers.",
            "file": filepath
        })
    if not has_liveness:
        findings.append({
            "rule": "MISSING_LIVENESS",
            "severity": "WARNING",
            "message": "Missing livenessProbe. Unresponsive deadlocks won't trigger restart.",
            "file": filepath
        })

    # Security Context
    has_run_as_non_root = bool(re.search(r'runAsNonRoot:\s*true', content))
    if not has_run_as_non_root:
        findings.append({
            "rule": "ROOT_USER_ALLOWED",
            "severity": "ERROR",
            "message": "Missing 'runAsNonRoot: true' in securityContext.",
            "file": filepath
        })

    has_readonly_root = bool(re.search(r'readOnlyRootFilesystem:\s*true', content))
    if not has_readonly_root:
        findings.append({
            "rule": "WRITABLE_ROOT_FS",
            "severity": "WARNING",
            "message": "Missing 'readOnlyRootFilesystem: true' in container securityContext.",
            "file": filepath
        })

    has_priv_esc = bool(re.search(r'allowPrivilegeEscalation:\s*false', content))
    if not has_priv_esc:
        findings.append({
            "rule": "PRIVILEGE_ESCALATION",
            "severity": "WARNING",
            "message": "allowPrivilegeEscalation should be explicitly set to false.",
            "file": filepath
        })

    # Image tags
    image_matches = re.findall(r'image:\s*([^\s"\']+)', content)
    for img in image_matches:
        if img.endswith(":latest") or ":" not in img.split("/")[-1]:
            findings.append({
                "rule": "LATEST_IMAGE_TAG",
                "severity": "ERROR",
                "message": f"Image '{img}' is untagged or pinned to ':latest'. Use explicit sha256 or semver.",
                "file": filepath
            })

    return findings


def lint_path(target_path: Path) -> int:
    files_to_check = []
    if target_path.is_file():
        files_to_check.append(target_path)
    elif target_path.is_dir():
        for ext in ("*.yaml", "*.yml"):
            files_to_check.extend(target_path.glob(f"**/{ext}"))

    if not files_to_check:
        print(f"[!] No YAML manifests found in {target_path}")
        return 0

    total_errors = 0
    total_warnings = 0

    print(f"=== Auditing {len(files_to_check)} Kubernetes manifest(s) ===")
    for f in files_to_check:
        try:
            content = f.read_text(encoding="utf-8")
            findings = audit_yaml_content(content, str(f))
            if findings:
                print(f"\n[FILE] {f.name}")
                for finding in findings:
                    prefix = "[FAIL]" if finding["severity"] == "ERROR" else "[WARN]"
                    if finding["severity"] == "ERROR":
                        total_errors += 1
                    else:
                        total_warnings += 1
                    print(f"  {prefix} [{finding['rule']}]: {finding['message']}")
            else:
                print(f"[OK] {f.name}: Conforms to production guardrails.")
        except Exception as e:
            print(f"[ERROR] Failed to read {f}: {e}")
            total_errors += 1

    print("\n---------------------------------------------------------")
    print(f"Audit Summary: {total_errors} errors, {total_warnings} warnings across {len(files_to_check)} file(s).")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(lint_path(target))
