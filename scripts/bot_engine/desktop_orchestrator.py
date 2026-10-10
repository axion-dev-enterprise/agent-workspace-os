#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Agents Orchestrator & Quota-Aware Dispatcher -- AXION Enterprise
Orchestrates incoming tasks to the optimal desktop agent CLI (OpenAI Codex,
Google Antigravity, or OpenCode) based on task specialization, neural model tier,
rate limits, usage quotas, process load, and automatic failover.

Part of Rule #25 (Desktop Agents Maestro & Quota-Aware Dispatch Guard).
"""

import os
import sys
import json
import time
import re
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

MEMORY_DIR = WORKSPACE_ROOT / "memory" / "desktop_agents"
QUOTA_STATUS_FILE = MEMORY_DIR / "quota_status.json"
DISPATCH_HISTORY_FILE = MEMORY_DIR / "dispatch_history.jsonl"

_ORCHESTRATOR_LOCK = threading.Lock()

# Agents Catalog & Specifications
AGENT_SPECS = {
    "codex": {
        "name": "OpenAI Codex CLI",
        "cli_command": "codex",
        "model": "OpenAI o1 / GPT-4o / Codex-Alpha",
        "provider": "openai",
        "tier": "premium",
        "description": "Especialista em síntese e edição de código, refatoração profunda, testes automatizados, revisão e correção cirúrgica de bugs.",
        "strengths": ["coding", "refactoring", "bugfix", "unit_tests", "code_review", "diffs", "typescript", "python"],
        "cooldown_on_rate_limit_secs": 900,  # 15 minutes
        "cooldown_on_quota_depleted_secs": 7200,  # 2 hours
        "max_concurrent_processes": 3
    },
    "antigravity": {
        "name": "Google Antigravity CLI",
        "cli_command": "agy",
        "model": "Google Gemini 2.0 / 1.5 Pro/Flash",
        "provider": "google",
        "tier": "enterprise",
        "description": "Especialista em arquitetura de workspace, governança de regras, skills, orquestração multi-etapas, infraestrutura, RAG e MCP.",
        "strengths": ["architecture", "skills", "governance", "multi_agent", "workflow", "mcp", "infrastructure", "planning"],
        "cooldown_on_rate_limit_secs": 900,
        "cooldown_on_quota_depleted_secs": 7200,
        "max_concurrent_processes": 5
    },
    "opencode": {
        "name": "OpenCode CLI",
        "cli_command": "opencode",
        "model": "opencode/mimo-v2.6-flash-free",
        "provider": "opencode_community",
        "tier": "free_tier",
        "description": "Especialista em execução rápida e econômica, scripts ágeis, inspeções pontuais, varreduras leves e fallback de alta disponibilidade.",
        "strengths": ["fast_scripts", "lightweight", "scans", "format", "conversions", "zero_cost", "fallback"],
        "cooldown_on_rate_limit_secs": 300,
        "cooldown_on_quota_depleted_secs": 1800,
        "max_concurrent_processes": 4
    }
}

# Semantic Keywords for Affinity Scoring
AFFINITY_KEYWORDS = {
    "codex": [
        "código", "programar", "refatorar", "refactor", "bug", "corrigir", "função", "classe",
        "teste", "pytest", "unit", "tdd", "lint", "eslint", "typescript", "javascript",
        "python", "backend", "frontend", "api", "endpoint", "review", "git diff", "commit",
        "erro", "exception", "traceback", "sintaxe", "compilar", "build"
    ],
    "antigravity": [
        "arquitetura", "governança", "regra", "skill", "workflow", "mcp", "planejamento",
        "multi-agente", "subagente", "pesquisa", "docs", "documentação", "infraestrutura",
        "cloudflare", "tailscale", "docker", "vps", "banco", "migração", "database",
        "sre", "sentinela", "auditoria", "rag", "knowledge"
    ],
    "opencode": [
        "rápido", "rapido", "simples", "script", "converter", "formatar", "listar", "scan",
        "varrer", "leve", "grátis", "gratis", "free", "econômico", "baixo custo",
        "inspeção rápida", "limpeza", "extrair dados"
    ]
}

# Quota and Rate Limit Error Patterns
RATE_LIMIT_PATTERNS = [
    r"\b429\b",
    r"too many requests",
    r"rate limit",
    r"rate-limit",
    r"tpm limit",
    r"rpm limit",
    r"requests per minute",
    r"tokens per minute"
]

QUOTA_DEPLETED_PATTERNS = [
    r"quota exceeded",
    r"insufficient_quota",
    r"exceeded your current quota",
    r"credit balance is too low",
    r"billing hard limit",
    r"resource exhausted",
    r"out of credits",
    r"payment required"
]


def ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_quota_ledger() -> Dict[str, Any]:
    """Loads current quota and health statuses of all 3 desktop agents."""
    ensure_memory_dir()
    if QUOTA_STATUS_FILE.exists():
        try:
            data = json.loads(QUOTA_STATUS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # Default initial state
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    default_ledger = {
        "date": today,
        "agents": {
            "codex": {
                "status": "ready",
                "rate_limited_until": 0,
                "quota_exceeded_until": 0,
                "consecutive_failures": 0,
                "invocations_today": 0,
                "successful_today": 0,
                "failed_today": 0,
                "last_invoked_at": None,
                "last_error": None
            },
            "antigravity": {
                "status": "ready",
                "rate_limited_until": 0,
                "quota_exceeded_until": 0,
                "consecutive_failures": 0,
                "invocations_today": 0,
                "successful_today": 0,
                "failed_today": 0,
                "last_invoked_at": None,
                "last_error": None
            },
            "opencode": {
                "status": "ready",
                "rate_limited_until": 0,
                "quota_exceeded_until": 0,
                "consecutive_failures": 0,
                "invocations_today": 0,
                "successful_today": 0,
                "failed_today": 0,
                "last_invoked_at": None,
                "last_error": None
            }
        }
    }
    return default_ledger


def save_quota_ledger(ledger: Dict[str, Any]):
    """Persists updated quota and health ledger safely."""
    ensure_memory_dir()
    try:
        QUOTA_STATUS_FILE.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[desktop_orchestrator] Aviso ao salvar quota ledger: {e}")


def update_agent_execution_feedback(agent: str, success: bool, output: str = "", error: str = ""):
    """Updates ledger based on execution outcome, detecting rate limits or depleted quotas."""
    with _ORCHESTRATOR_LOCK:
        ledger = load_quota_ledger()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if ledger.get("date") != today:
            ledger["date"] = today
            for a in ledger.get("agents", {}).values():
                a["invocations_today"] = 0
                a["successful_today"] = 0
                a["failed_today"] = 0

        agent_data = ledger.setdefault("agents", {}).setdefault(agent, {
            "status": "ready",
            "rate_limited_until": 0,
            "quota_exceeded_until": 0,
            "consecutive_failures": 0,
            "invocations_today": 0,
            "successful_today": 0,
            "failed_today": 0,
            "last_invoked_at": None,
            "last_error": None
        })

        now = time.time()
        agent_data["invocations_today"] += 1
        agent_data["last_invoked_at"] = datetime.datetime.now().isoformat()

        combined_text = (output + " " + (error or "")).lower()

        is_rate_limited = any(re.search(pat, combined_text) for pat in RATE_LIMIT_PATTERNS)
        is_quota_depleted = any(re.search(pat, combined_text) for pat in QUOTA_DEPLETED_PATTERNS)

        if success:
            agent_data["successful_today"] += 1
            agent_data["consecutive_failures"] = 0
            agent_data["status"] = "ready"
            agent_data["last_error"] = None
        else:
            agent_data["failed_today"] += 1
            agent_data["consecutive_failures"] += 1
            agent_data["last_error"] = (error or output[:150]).strip()

            spec = AGENT_SPECS.get(agent, {})
            if is_quota_depleted:
                cooldown = spec.get("cooldown_on_quota_depleted_secs", 7200)
                agent_data["quota_exceeded_until"] = now + cooldown
                agent_data["status"] = "quota_depleted"
                print(f"[desktop_orchestrator] 🚨 Agente '{agent}' atingiu limite de quota! Cooldown até +{cooldown}s")
            elif is_rate_limited:
                cooldown = spec.get("cooldown_on_rate_limit_secs", 900)
                agent_data["rate_limited_until"] = now + cooldown
                agent_data["status"] = "rate_limited"
                print(f"[desktop_orchestrator] ⚠️ Agente '{agent}' recebeu Rate Limit (429)! Cooldown até +{cooldown}s")
            elif agent_data["consecutive_failures"] >= 3:
                agent_data["status"] = "degraded"
            else:
                agent_data["status"] = "ready"

        save_quota_ledger(ledger)


def get_agent_operational_state(agent: str) -> Dict[str, Any]:
    """Evaluates whether an agent is ready, rate-limited, quota-depleted, or degraded."""
    ledger = load_quota_ledger()
    agent_data = ledger.get("agents", {}).get(agent, {})
    now = time.time()

    rl_until = agent_data.get("rate_limited_until", 0)
    qd_until = agent_data.get("quota_exceeded_until", 0)

    if qd_until > now:
        return {
            "available": False,
            "status": "quota_depleted",
            "reason": f"Quota esgotada. Retomada em {int(qd_until - now)}s.",
            "remaining_seconds": int(qd_until - now)
        }

    if rl_until > now:
        return {
            "available": False,
            "status": "rate_limited",
            "reason": f"Rate limit ativo (429). Retomada em {int(rl_until - now)}s.",
            "remaining_seconds": int(rl_until - now)
        }

    if agent_data.get("consecutive_failures", 0) >= 3:
        return {
            "available": True,
            "status": "degraded",
            "reason": f"Agente com {agent_data.get('consecutive_failures')} falhas consecutivas recentes.",
            "remaining_seconds": 0
        }

    return {
        "available": True,
        "status": "ready",
        "reason": "Agente operacional e disponível.",
        "remaining_seconds": 0
    }


def score_agent_for_task(agent: str, prompt: str, cli_status: Dict[str, Any]) -> float:
    """Computes suitability score for an agent on a specific task."""
    score = 50.0  # Base score
    lower_prompt = prompt.lower()

    # 1. Availability check (Hard filter)
    op_state = get_agent_operational_state(agent)
    if not op_state["available"]:
        return -999.0

    cli_info = cli_status.get("clis", {}).get(agent, {})
    if not cli_info.get("ready"):
        return -999.0

    # 2. Semantic Affinity Scoring
    keywords = AFFINITY_KEYWORDS.get(agent, [])
    matches = sum(1 for kw in keywords if kw in lower_prompt)
    score += matches * 15.0

    # 3. Model & Tier adjustments
    spec = AGENT_SPECS.get(agent, {})
    tier = spec.get("tier")
    if tier == "premium" and any(k in lower_prompt for k in ["complexo", "difícil", "arquitetura", "refatorar", "otimizar"]):
        score += 20.0
    if tier == "free_tier" and any(k in lower_prompt for k in ["rápido", "rapido", "simples", "leve", "econômico", "free"]):
        score += 25.0

    # 4. Concurrency Penalty
    running = cli_info.get("running_processes", 0)
    max_proc = spec.get("max_concurrent_processes", 3)
    if running >= max_proc:
        score -= 30.0
    elif running > 0:
        score -= (running * 5.0)

    # 5. Degraded penalty
    if op_state["status"] == "degraded":
        score -= 25.0

    return score


def select_optimal_desktop_agent(
    task_description: str,
    preferred_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Selects the optimal desktop agent CLI and establishes a fallback chain.
    """
    try:
        from . import tool_executor
    except ImportError:
        from bot_engine import tool_executor
    cli_status = tool_executor.get_desktop_clis_status()

    # Normalize preferred agent
    pref = (preferred_agent or "").strip().lower()
    if pref in ["agy", "antigravity"]:
        pref = "antigravity"
    elif pref in ["codex", "openai"]:
        pref = "codex"
    elif pref in ["opencode"]:
        pref = "opencode"
    else:
        pref = None

    scores = {}
    for agent in ["codex", "antigravity", "opencode"]:
        scores[agent] = score_agent_for_task(agent, task_description, cli_status)

    # If preferred agent was requested and is available, prioritize it
    if pref and scores.get(pref, -999) > -500:
        selected = pref
        selection_reason = f"Agente preferencial '{pref}' solicitado explicitamente e operacional."
    else:
        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = ranked[0][0]
        top_score = ranked[0][1]
        if top_score <= -500:
            # All agents unavailable or blocked! Fallback to openCode if installed
            selected = "opencode"
            selection_reason = "Todos os agentes primários sob cooldown/restrição de quota; fallback de emergência para OpenCode."
        else:
            selection_reason = (
                f"Seleção autônoma baseada em afinidade semântica (score: {top_score:.1f}), "
                f"disponibilidade de quota e modelo neural ideal."
            )

    # Determine fallback chain (other agents sorted by score)
    fallbacks = [a for a, s in sorted(scores.items(), key=lambda x: x[1], reverse=True) if a != selected and s > -500]
    if not fallbacks:
        # Guarantee at least opencode as ultimate fallback if not already primary
        fallbacks = [a for a in ["opencode", "antigravity", "codex"] if a != selected]

    return {
        "selected_agent": selected,
        "selected_spec": AGENT_SPECS.get(selected),
        "selection_reason": selection_reason,
        "scores": scores,
        "fallback_chain": fallbacks,
        "cli_status": cli_status.get("clis", {}).get(selected, {})
    }


def dispatch_task_to_desktop_agent(
    task_description: str,
    preferred_agent: Optional[str] = None,
    timeout: int = 180,
    on_step_callback = None
) -> Dict[str, Any]:
    """
    Main orchestration function: dispatches a task to the chosen desktop agent CLI.
    If execution fails due to rate-limit, quota exhaustion, or error, automatically
    fails over to the next eligible agent in the fallback chain.
    """
    try:
        from . import tool_executor
        from . import desktop_watcher
    except ImportError:
        from bot_engine import tool_executor, desktop_watcher

    t_start = time.time()
    plan = select_optimal_desktop_agent(task_description, preferred_agent=preferred_agent)
    primary_agent = plan["selected_agent"]
    fallbacks = plan["fallback_chain"]

    execution_chain = [primary_agent] + fallbacks
    attempt_history = []
    final_result = None

    for attempt_idx, current_agent in enumerate(execution_chain, 1):
        if on_step_callback:
            spec = AGENT_SPECS.get(current_agent, {})
            on_step_callback(
                attempt_idx,
                "dispatch",
                f"Delegando tarefa para {spec.get('name')} (Modelo: {spec.get('model')})..."
            )

        print(f"[desktop_orchestrator] Executando tentativa {attempt_idx} com agente: {current_agent}")
        agent_spec = AGENT_SPECS.get(current_agent, {})

        # Execute using the respective tool_executor wrapper
        if current_agent == "codex":
            res = tool_executor.run_codex_cli(prompt=task_description, subcommand="exec", timeout=timeout)
        elif current_agent == "antigravity":
            res = tool_executor.run_antigravity_cli(prompt=task_description, subcommand="print", timeout=timeout)
        else:
            res = tool_executor.run_opencode_cli(prompt=task_description, subcommand="run", timeout=timeout)

        success = bool(res.get("success"))
        output = res.get("output", "")
        error = res.get("error", "")

        # Update quota ledger with execution outcome
        update_agent_execution_feedback(current_agent, success=success, output=output, error=error)

        attempt_info = {
            "attempt": attempt_idx,
            "agent": current_agent,
            "agent_name": agent_spec.get("name"),
            "model": agent_spec.get("model"),
            "success": success,
            "elapsed_seconds": res.get("elapsed_seconds", 0.0),
            "output_length": len(output)
        }
        attempt_history.append(attempt_info)

        if success and len(output.strip()) > 30:
            final_result = {
                "success": True,
                "agent_used": current_agent,
                "agent_name": agent_spec.get("name"),
                "model_used": agent_spec.get("model"),
                "output": output,
                "task": task_description,
                "selection_reason": plan["selection_reason"],
                "total_elapsed_seconds": round(time.time() - t_start, 2),
                "failover_occurred": attempt_idx > 1,
                "attempt_history": attempt_history,
                "cmd_executed": res.get("cmd_executed")
            }
            break
        else:
            print(f"[desktop_orchestrator] Falha na tentativa com '{current_agent}'. Verificando failover...")
            if on_step_callback and attempt_idx < len(execution_chain):
                next_agent = execution_chain[attempt_idx]
                on_step_callback(
                    attempt_idx + 1,
                    "failover",
                    f"Falha/restrição em {current_agent}. Acionando fallback automático para {next_agent}..."
                )

    if not final_result:
        # All attempts failed
        last_attempt = attempt_history[-1] if attempt_history else {}
        final_result = {
            "success": False,
            "agent_used": last_attempt.get("agent", primary_agent),
            "output": output or "Não foi possível concluir a execução em nenhum dos agentes desktop disponíveis.",
            "error": error or "Todas as tentativas da cadeia de fallback falharam.",
            "task": task_description,
            "total_elapsed_seconds": round(time.time() - t_start, 2),
            "failover_occurred": True,
            "attempt_history": attempt_history
        }

    # Record in history JSONL
    try:
        ensure_memory_dir()
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "task": task_description[:200],
            "agent_selected": primary_agent,
            "agent_used": final_result.get("agent_used"),
            "success": final_result.get("success"),
            "duration": final_result.get("total_elapsed_seconds"),
            "failover": final_result.get("failover_occurred")
        }
        with open(DISPATCH_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[desktop_orchestrator] Erro ao gravar histórico: {e}")

    # Register in Desktop Watcher for executive delivery
    if final_result.get("success"):
        try:
            task_id = f"orchestrated_{final_result['agent_used']}_{int(time.time())}"
            title = f"Tarefa Orquestrada [{final_result['agent_name']}]: {task_description[:50]}"
            desktop_watcher.record_desktop_task_completion(
                agent=final_result["agent_name"].split()[0],
                task_id=task_id,
                title=title,
                status="completed",
                result=final_result["output"][-300:] or "Tarefa orquestrada finalizada com sucesso."
            )
        except Exception as w_err:
            print(f"[desktop_orchestrator] Erro ao notificar watcher: {w_err}")

    return final_result


def get_orchestrator_dashboard() -> Dict[str, Any]:
    """Generates an executive dashboard of desktop agents quotas, status, and health."""
    try:
        from . import tool_executor
    except ImportError:
        from bot_engine import tool_executor
    cli_status = tool_executor.get_desktop_clis_status()
    ledger = load_quota_ledger()

    summary_items = []
    for agent, spec in AGENT_SPECS.items():
        op = get_agent_operational_state(agent)
        ag_data = ledger.get("agents", {}).get(agent, {})
        cli_info = cli_status.get("clis", {}).get(agent, {})

        icon = "🟢" if op["status"] == "ready" and cli_info.get("ready") else ("🟡" if op["status"] in ["degraded", "rate_limited"] else "🔴")
        summary_items.append({
            "agent": agent,
            "name": spec["name"],
            "model": spec["model"],
            "tier": spec["tier"],
            "status": op["status"],
            "ready": cli_info.get("ready", False),
            "version": cli_info.get("version"),
            "running_processes": cli_info.get("running_processes", 0),
            "invocations_today": ag_data.get("invocations_today", 0),
            "successful_today": ag_data.get("successful_today", 0),
            "failed_today": ag_data.get("failed_today", 0),
            "cooldown_remaining": op["remaining_seconds"]
        })

    return {
        "success": True,
        "date": ledger.get("date"),
        "agents": summary_items,
        "total_invocations_today": sum(item["invocations_today"] for item in summary_items)
    }


if __name__ == "__main__":
    print("=== AXION Desktop Agents Orchestrator Self-Test ===")
    dash = get_orchestrator_dashboard()
    print(json.dumps(dash, indent=2, ensure_ascii=False))
