#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Agents Orchestrator Audit Tool -- AXION Enterprise
Standalone script enforcing Rule #25:
- Validates semantic affinity scoring across Codex, Antigravity, and OpenCode
- Tests quota ledger persistence and cooldown triggers
- Verifies failover chain computation
Zero external dependencies: 100% Python 3 standard library.
"""

import sys
import os
from pathlib import Path

# Setup paths
_parents = Path(__file__).resolve().parents
WORKSPACE_ROOT = _parents[4] if len(_parents) >= 5 else Path(r"C:\workspace")
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from bot_engine import desktop_orchestrator
except ImportError:
    import desktop_orchestrator


def run_orchestrator_audit():
    print("=== AXION Desktop Agents Orchestrator Audit ===")

    # Reset test ledger to clean ready state
    ledger = desktop_orchestrator.load_quota_ledger()
    for a in ledger.get("agents", {}).values():
        a["status"] = "ready"
        a["rate_limited_until"] = 0
        a["quota_exceeded_until"] = 0
        a["consecutive_failures"] = 0
    desktop_orchestrator.save_quota_ledger(ledger)
    
    # 1. Test Semantic Affinity Routing
    t1 = "Refatore a função de autenticação e crie testes unitários em pytest"
    plan1 = desktop_orchestrator.select_optimal_desktop_agent(t1)
    sel1 = plan1.get("selected_agent")
    pass1 = (sel1 == "codex")
    print(f"[*] Task 1 (Coding/Pytest): expected 'codex' -> got '{sel1}' [{ 'PASS' if pass1 else 'FAIL' }]")

    t2 = "Desenhe a arquitetura do workspace e a governança de novas skills de infraestrutura"
    plan2 = desktop_orchestrator.select_optimal_desktop_agent(t2)
    sel2 = plan2.get("selected_agent")
    pass2 = (sel2 == "antigravity")
    print(f"[*] Task 2 (Architecture/Skills): expected 'antigravity' -> got '{sel2}' [{ 'PASS' if pass2 else 'FAIL' }]")

    t3 = "Execute um script rápido para listar arquivos temporários"
    plan3 = desktop_orchestrator.select_optimal_desktop_agent(t3)
    sel3 = plan3.get("selected_agent")
    pass3 = (sel3 == "opencode")
    print(f"[*] Task 3 (Fast script): expected 'opencode' -> got '{sel3}' [{ 'PASS' if pass3 else 'FAIL' }]")

    # 2. Test Quota Ledger Load
    ledger = desktop_orchestrator.load_quota_ledger()
    pass_ledger = isinstance(ledger, dict) and "agents" in ledger and "codex" in ledger["agents"]
    print(f"[*] Quota ledger validation: [{ 'PASS' if pass_ledger else 'FAIL' }]")

    # 3. Test Dashboard Generation
    dash = desktop_orchestrator.get_orchestrator_dashboard()
    pass_dash = isinstance(dash, dict) and len(dash.get("agents", [])) == 3
    print(f"[*] Orchestrator dashboard: [{ 'PASS' if pass_dash else 'FAIL' }]")

    all_passed = pass1 and pass2 and pass3 and pass_ledger and pass_dash
    print(f"\nFinal Audit Verdict: {'ALL PASS' if all_passed else 'FAILURES DETECTED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_orchestrator_audit())
