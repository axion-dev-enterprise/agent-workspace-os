#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Telemetry & Observability Engine
Collects structured operational events, system metrics, tool runtimes,
API latencies, and persistent error diagnostics across the AXION platform.
"""

import os
import sys
import json
import time
import datetime
import traceback
import threading
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Paths
WORKSPACE_ROOT = Path("C:/workspace")
TELEMETRY_DIR = WORKSPACE_ROOT / "memory" / "telemetry"
EVENTS_FILE = TELEMETRY_DIR / "events.jsonl"
ERRORS_FILE = TELEMETRY_DIR / "errors.jsonl"
STATS_FILE = TELEMETRY_DIR / "telemetry_stats.json"

_LOCK = threading.Lock()
_STARTUP_TIME = time.time()

# ---------------------------------------------------------------------------
# Internal Storage & Initialization
# ---------------------------------------------------------------------------

def _ensure_dirs():
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    if not EVENTS_FILE.exists():
        EVENTS_FILE.touch()
    if not ERRORS_FILE.exists():
        ERRORS_FILE.touch()
    if not STATS_FILE.exists():
        _write_stats(_default_stats())


def _default_stats() -> dict:
    return {
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "requests": {"total": 0, "success": 0, "error": 0},
        "llm": {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "retries": 0,
            "total_latency_ms": 0,
            "avg_latency_ms": 0.0
        },
        "tools": {
            "total_executed": 0,
            "total_success": 0,
            "total_failed": 0,
            "by_tool": {},
            "failures_by_tool": {}
        },
        "errors": {
            "total_recorded": 0,
            "by_severity": {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
            "by_service": {}
        },
        "circuit_breaker": {
            "trips": 0,
            "last_trip": None
        }
    }


def _read_stats() -> dict:
    try:
        if STATS_FILE.exists():
            with open(STATS_FILE, "r", encoding="utf-8", errors="replace") as f:
                return json.load(f)
    except Exception:
        pass
    return _default_stats()


def _write_stats(stats: dict) -> None:
    try:
        with open(STATS_FILE, "w", encoding="utf-8", errors="replace") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Telemetry] Falha ao persistir stats: {e}")


def _append_jsonl(filepath: Path, data: dict) -> None:
    try:
        with open(filepath, "a", encoding="utf-8", errors="replace") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Telemetry] Falha ao gravar em {filepath.name}: {e}")


# ---------------------------------------------------------------------------
# Public Ingestion API
# ---------------------------------------------------------------------------

def record_event(category: str, name: str, data: dict = None, severity: str = "INFO") -> dict:
    """Records an operational event in events.jsonl"""
    _ensure_dirs()
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "category": category,
        "name": name,
        "severity": severity.upper(),
        "data": data or {}
    }
    with _LOCK:
        _append_jsonl(EVENTS_FILE, event)
    return event


def record_error(
    service: str,
    error_type: str,
    message: str,
    exc_info=None,
    context: dict = None,
    severity: str = "ERROR"
) -> dict:
    """
    Persists structured error diagnostics with stack trace to errors.jsonl
    and increments telemetry counters.
    """
    _ensure_dirs()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sev = severity.upper()

    tb_str = ""
    if exc_info:
        if isinstance(exc_info, BaseException):
            tb_str = "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
        elif isinstance(exc_info, tuple) and len(exc_info) == 3:
            tb_str = "".join(traceback.format_exception(*exc_info))
        else:
            tb_str = traceback.format_exc()
    elif sys.exc_info()[0] is not None:
        tb_str = traceback.format_exc()

    error_record = {
        "timestamp": now_iso,
        "service": service,
        "error_type": error_type,
        "message": str(message)[:1000],
        "traceback": tb_str.strip()[:3000] if tb_str else None,
        "context": context or {},
        "severity": sev
    }

    with _LOCK:
        _append_jsonl(ERRORS_FILE, error_record)

        stats = _read_stats()
        stats["errors"]["total_recorded"] += 1
        stats["errors"]["by_severity"][sev] = stats["errors"]["by_severity"].get(sev, 0) + 1
        stats["errors"]["by_service"][service] = stats["errors"]["by_service"].get(service, 0) + 1
        _write_stats(stats)

    print(f"[{now_iso}][Telemetry][{sev}][{service}] {error_type}: {message[:120]}")
    return error_record


def record_request_metric(success: bool) -> None:
    """Records top-level chat request outcome"""
    _ensure_dirs()
    with _LOCK:
        stats = _read_stats()
        stats["requests"]["total"] += 1
        if success:
            stats["requests"]["success"] += 1
        else:
            stats["requests"]["error"] += 1
        _write_stats(stats)


def record_llm_metric(model: str, duration_ms: int, success: bool, retries: int = 0, error: str = None) -> None:
    """Records LLM query latency and reliability metrics"""
    _ensure_dirs()
    with _LOCK:
        stats = _read_stats()
        llm = stats["llm"]
        llm["total_calls"] += 1
        llm["retries"] += retries
        if success:
            llm["success_calls"] += 1
            llm["total_latency_ms"] += duration_ms
            llm["avg_latency_ms"] = round(llm["total_latency_ms"] / max(1, llm["success_calls"]), 1)
        else:
            llm["error_calls"] += 1
        _write_stats(stats)

    record_event("llm", "api_call", {
        "model": model,
        "duration_ms": duration_ms,
        "success": success,
        "retries": retries,
        "error": error
    }, severity="INFO" if success else "WARNING")


def record_tool_metric(tool_name: str, duration_ms: int, success: bool, error: str = None) -> None:
    """Records tool execution stats and per-tool failure tallies"""
    _ensure_dirs()
    with _LOCK:
        stats = _read_stats()
        t = stats["tools"]
        t["total_executed"] += 1
        t["by_tool"][tool_name] = t["by_tool"].get(tool_name, 0) + 1

        if success:
            t["total_success"] += 1
        else:
            t["total_failed"] += 1
            t["failures_by_tool"][tool_name] = t["failures_by_tool"].get(tool_name, 0) + 1

        _write_stats(stats)

    record_event("tool", "tool_executed", {
        "tool": tool_name,
        "duration_ms": duration_ms,
        "success": success,
        "error": error
    }, severity="INFO" if success else "WARNING")


def record_circuit_breaker_trip(name: str, reason: str) -> None:
    """Logs a circuit breaker trip event"""
    _ensure_dirs()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _LOCK:
        stats = _read_stats()
        stats["circuit_breaker"]["trips"] += 1
        stats["circuit_breaker"]["last_trip"] = {"name": name, "reason": reason, "timestamp": now_iso}
        _write_stats(stats)

    record_error("circuit_breaker", "CircuitBreakerOpen", f"Circuit '{name}' opened: {reason}", severity="WARNING")


# ---------------------------------------------------------------------------
# Telemetry Retrieval & Reporting
# ---------------------------------------------------------------------------

def get_recent_errors(limit: int = 15) -> list[dict]:
    """Returns the most recent N recorded errors (newest first)"""
    _ensure_dirs()
    lines = []
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return list(reversed(lines[-limit:]))


def get_telemetry_summary() -> dict:
    """Returns consolidated telemetry health and metrics snapshot"""
    _ensure_dirs()
    with _LOCK:
        stats = _read_stats()

    uptime = time.time() - _STARTUP_TIME
    req = stats.get("requests", {})
    total_req = req.get("total", 0)
    success_req = req.get("success", 0)
    req_success_rate = round((success_req / total_req * 100), 1) if total_req > 0 else 100.0

    tools = stats.get("tools", {})
    total_tools = tools.get("total_executed", 0)
    failed_tools = tools.get("total_failed", 0)
    tool_failure_rate = round((failed_tools / total_tools * 100), 1) if total_tools > 0 else 0.0

    llm = stats.get("llm", {})
    total_llm = llm.get("total_calls", 0)
    err_llm = llm.get("error_calls", 0)
    llm_error_rate = round((err_llm / total_llm * 100), 1) if total_llm > 0 else 0.0

    return {
        "status": "HEALTHY" if req_success_rate >= 90.0 and tool_failure_rate <= 15.0 else "DEGRADED",
        "uptime_seconds": round(uptime, 1),
        "requests": {
            "total": total_req,
            "success": success_req,
            "error": req.get("error", 0),
            "success_rate_pct": req_success_rate
        },
        "llm": {
            "total_calls": total_llm,
            "avg_latency_ms": llm.get("avg_latency_ms", 0.0),
            "retries": llm.get("retries", 0),
            "error_rate_pct": llm_error_rate
        },
        "tools": {
            "total_executed": total_tools,
            "total_failed": failed_tools,
            "failure_rate_pct": tool_failure_rate,
            "top_tools": sorted(tools.get("by_tool", {}).items(), key=lambda x: x[1], reverse=True)[:5],
            "top_failing_tools": sorted(tools.get("failures_by_tool", {}).items(), key=lambda x: x[1], reverse=True)[:5]
        },
        "errors": stats.get("errors", {}),
        "circuit_breaker": stats.get("circuit_breaker", {})
    }


def format_telemetry_html() -> str:
    """Formats telemetry metrics as an executive Telegram HTML message"""
    summary = get_telemetry_summary()
    st = summary["status"]
    icon = "🟢" if st == "HEALTHY" else "🟡"

    req = summary["requests"]
    llm = summary["llm"]
    tools = summary["tools"]
    errs = summary["errors"]

    recent_errs = get_recent_errors(limit=3)

    lines = [
        f"{icon} <b>TELEMETRIA & SAÚDE OPERACIONAL — AXION</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"⏱ <b>Uptime:</b> <code>{summary['uptime_seconds']:.0f}s</code> | <b>Estado:</b> <code>{st}</code>",
        f"📥 <b>Requisições:</b> {req['total']} (Sucesso: <b>{req['success_rate_pct']}%</b>)",
        f"🧠 <b>IA / Mimo:</b> {llm['total_calls']} chamadas | Latência média: <code>{llm['avg_latency_ms']:.0f}ms</code>",
        f"⚡ <b>Ferramentas:</b> {tools['total_executed']} execuções (Falhas: <b>{tools['failure_rate_pct']}%</b>)",
        f"🚨 <b>Erros Totais Registrados:</b> {errs.get('total_recorded', 0)}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    if tools.get("top_tools"):
        top_str = ", ".join(f"<code>{k}</code> ({v})" for k, v in tools["top_tools"][:3])
        lines.append(f"🏆 <b>Top Tools:</b> {top_str}")

    if tools.get("top_failing_tools"):
        fail_str = ", ".join(f"<code>{k}</code> ({v})" for k, v in tools["top_failing_tools"][:3])
        lines.append(f"⚠️ <b>Ferramentas c/ Falhas:</b> {fail_str}")

    if recent_errs:
        lines.append("\n🔍 <b>Últimos Erros Registrados:</b>")
        for e in recent_errs:
            t = e.get("timestamp", "")[11:19]
            svc = e.get("service", "core")
            msg = e.get("message", "")[:60]
            lines.append(f"• [<code>{t}</code>] [<b>{svc}</b>] <i>{msg}</i>")
    else:
        lines.append("\n✅ <i>Nenhum erro recente no ledger operacional.</i>")

    return "\n".join(lines)
