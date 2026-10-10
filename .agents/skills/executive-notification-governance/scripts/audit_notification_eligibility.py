#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executive Notification & Noise Audit Tool -- AXION Enterprise
Standalone script enforcing Rule #24:
- Evaluates task eligibility against anti-scratch rules
- Simulates RAM hysteresis and deadband state transitions
- Verifies deliverable evidence extraction
Zero external dependencies: 100% Python 3 standard library.
"""

import sys
import os
import re
from pathlib import Path

def is_executive_task_eligible(task_id: str, log_bytes: int, log_content: str, duration_secs: float = 0.0) -> bool:
    """Evaluates if a task should trigger an executive notification to the CEO."""
    # 1. Ephemeral scratch tasks rejection
    if re.search(r"task-\d+", task_id) or "antigravity_" in task_id:
        has_business_milestone = any(m in log_content.lower() for m in [
            "[executive_delivery]", "deploy_success", "liberado_ok", "produção", "release_completed"
        ])
        if not has_business_milestone:
            return False

    # 2. Minimum content requirement
    if log_bytes < 150 and not any(tag in log_content.lower() for tag in ["[executive_delivery]", "deploy_success"]):
        return False

    # 3. Deliverables or meaningful evidence requirement
    evidence_patterns = [
        r"https?://[^\s<>\"']+",
        r"localhost:\d+",
        r"porta\s+\d+",
        r"commit\s+[a-f0-9]{7,40}",
        r"bateria de testes",
        r"finalizado com sucesso"
    ]
    has_evidence = any(re.search(pat, log_content, re.IGNORECASE) for pat in evidence_patterns)
    return has_evidence or duration_secs >= 15.0

def simulate_ram_hysteresis(readings: list) -> list:
    """Simulates alert states across a sequence of RAM percentage readings.
    Thresholds:
      >= 96.0 -> CRITICAL
      >= 92.0 -> WARNING
      <= 80.0 -> OK (NORMALIZED)
      80.1 .. 91.9 -> DEADBAND (hold previous state)
    """
    state = "OK"
    events = []
    for pct in readings:
        prev_state = state
        if pct >= 96.0:
            state = "CRITICAL"
        elif pct >= 92.0:
            if state != "CRITICAL":
                state = "WARNING"
        elif pct <= 80.0:
            state = "OK"
        # In deadband (80 < pct < 92), state remains unchanged
        if state != prev_state:
            events.append((pct, f"{prev_state} -> {state}"))
    return events

def run_self_audit():
    print("=== AXION Executive Notification & Noise Audit ===")
    
    # Test 1: Ephemeral scratch rejection
    scratch_ok = not is_executive_task_eligible("antigravity_task-1234", 232, "Processo finalizado (log: 232 bytes)")
    print(f"[*] Ephemeral scratch rejected: {'PASS' if scratch_ok else 'FAIL'}")

    # Test 2: Executive delivery acceptance
    exec_ok = is_executive_task_eligible(
        "task-prod-deploy", 850,
        "[executive_delivery] Deploy efetuado com sucesso na URL https://gramaticalizando.example.com"
    )
    print(f"[*] Real milestone accepted: {'PASS' if exec_ok else 'FAIL'}")

    # Test 3: RAM Hysteresis deadband
    sim_readings = [78.0, 85.0, 89.0, 93.0, 91.0, 88.0, 90.0, 79.0]
    events = simulate_ram_hysteresis(sim_readings)
    # Expected transitions:
    # 78.0: OK
    # 85, 89: in deadband -> still OK
    # 93.0: OK -> WARNING
    # 91, 88, 90: in deadband -> still WARNING (no flapping!)
    # 79.0: WARNING -> OK
    deadband_ok = len(events) == 2 and events[0][1] == "OK -> WARNING" and events[1][1] == "WARNING -> OK"
    print(f"[*] RAM deadband (anti-flapping): {'PASS' if deadband_ok else 'FAIL'}")

    all_passed = scratch_ok and exec_ok and deadband_ok
    print(f"\nFinal Audit Verdict: {'ALL PASS' if all_passed else 'FAILURES DETECTED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_self_audit())
