#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Execution Watcher — Autonomous Agent Observability & Scoring Engine
Monitors every agent execution, scores it, persists to disk, and provides
real-time reporting and anomaly detection.
"""

import os
import sys
import json
import time
import datetime
import re
import threading
import uuid
import pathlib
import html

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_WATCHER_DIR = pathlib.Path(r"C:\workspace\memory\watcher")
_EXECUTIONS_FILE = _WATCHER_DIR / "executions.jsonl"
_STATS_FILE = _WATCHER_DIR / "watcher_stats.json"
_ANOMALIES_FILE = _WATCHER_DIR / "anomalies.jsonl"

_LOCK = threading.Lock()

# Score weights
_WEIGHTS = {
    "goal_completion": 0.35,
    "tool_efficiency": 0.25,
    "speed": 0.15,
    "response_quality": 0.15,
    "reliability": 0.10,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    """Create watcher directory and empty files if they don't exist."""
    _WATCHER_DIR.mkdir(parents=True, exist_ok=True)
    for fpath in (_EXECUTIONS_FILE, _ANOMALIES_FILE):
        if not fpath.exists():
            fpath.touch()
    if not _STATS_FILE.exists():
        _write_stats(_default_stats())


def _default_stats() -> dict:
    return {
        "total_executions": 0,
        "total_anomalies": 0,
        "avg_score_all": 0.0,
        "avg_score_last100": 0.0,
        "by_grade": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        "last_daemon_check_anomalies": None,
        "last_daemon_summary": None,
    }


def _read_stats() -> dict:
    try:
        with open(_STATS_FILE, "r", encoding="utf-8", errors="replace") as fh:
            return json.load(fh)
    except Exception:
        return _default_stats()


def _write_stats(stats: dict) -> None:
    with open(_STATS_FILE, "w", encoding="utf-8", errors="replace") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)


def _append_jsonl(filepath: pathlib.Path, record: dict) -> None:
    with open(filepath, "a", encoding="utf-8", errors="replace") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(filepath: pathlib.Path) -> list:
    lines = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return lines


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _score_goal_completion(record: dict) -> int:
    """Score 0-10: Was the goal achieved?"""
    terminated_by = record.get("terminated_by", "")
    final_answer = record.get("_final_answer", "")
    if terminated_by == "goal_achieved":
        return 10
    if terminated_by == "completed" and final_answer:
        return 8
    if "error" in str(terminated_by).lower() or not final_answer:
        return 0
    return 6


def _score_tool_efficiency(record: dict) -> int:
    """Score 0-10: Did the agent use tools appropriately?"""
    tools_used = record.get("tools_used", [])
    steps = record.get("steps", record.get("step_count", 0))
    terminated_by = record.get("terminated_by", "")
    goal_achieved = terminated_by in ("goal_achieved", "completed")
    had_tools = bool(tools_used)
    has_error = "error" in str(terminated_by).lower()
    final_answer = record.get("_final_answer", "")

    if not had_tools and has_error:
        return 0
    if not had_tools:
        # Conversational or direct responses that answered successfully without tools
        if goal_achieved and final_answer:
            return 8
        return 5
    if had_tools and goal_achieved and steps <= 3:
        return 10
    if had_tools and goal_achieved and steps <= 6:
        return 8
    if had_tools and goal_achieved:
        return 7
    if had_tools:
        return 5
    return 3



def _score_speed(record: dict) -> int:
    """Score 0-10: How fast was the execution?"""
    duration = record.get("duration_seconds", record.get("elapsed_seconds", None))
    if duration is None:
        # Try to derive from timestamps
        start = record.get("started_at") or record.get("start_time")
        end = record.get("ended_at") or record.get("end_time")
        if start and end:
            try:
                fmt = "%Y-%m-%dT%H:%M:%S"
                t0 = datetime.datetime.fromisoformat(str(start)[:19])
                t1 = datetime.datetime.fromisoformat(str(end)[:19])
                duration = (t1 - t0).total_seconds()
            except Exception:
                duration = None

    if duration is None:
        return 5  # Unknown — neutral score

    if duration < 5:
        return 10
    if duration < 15:
        return 8
    if duration < 30:
        return 6
    if duration < 60:
        return 4
    if duration < 120:
        return 2
    return 0


def _score_response_quality(record: dict) -> int:
    """Score 0-10: Quality of final answer."""
    final_answer = record.get("_final_answer", "")
    tools_used = record.get("tools_used", [])
    had_tools = bool(tools_used)

    if not final_answer or len(final_answer.strip()) == 0:
        return 0

    length = len(final_answer.strip())

    if length > 200 and had_tools:
        return 10
    if length > 200:
        return 8
    if 100 <= length <= 200:
        return 7
    if length > 0:
        return 5
    return 0


def _score_reliability(record: dict) -> int:
    """Score 0-10: Any errors or anomalies?"""
    terminated_by = str(record.get("terminated_by", ""))
    errors = record.get("errors", [])
    fallback_model = record.get("fallback_model_used", False)
    tool_failures = record.get("tool_failures", [])

    if "crash" in terminated_by.lower() or "error" in terminated_by.lower():
        return 0
    if tool_failures:
        return 4
    if fallback_model:
        return 7
    if errors:
        return 4
    return 10


def _compute_scores(record: dict, final_answer: str) -> dict:
    """Compute all dimension scores and weighted total."""
    # Inject final_answer temporarily for scoring helpers
    record["_final_answer"] = final_answer

    scores = {
        "goal_completion": _score_goal_completion(record),
        "tool_efficiency": _score_tool_efficiency(record),
        "speed": _score_speed(record),
        "response_quality": _score_response_quality(record),
        "reliability": _score_reliability(record),
    }

    total = sum(scores[dim] * weight for dim, weight in _WEIGHTS.items())
    total = round(total, 2)

    return scores, total


def _grade(total_score: float) -> str:
    """Return letter grade from numeric score."""
    if total_score >= 9.0:
        return "A"
    if total_score >= 7.0:
        return "B"
    if total_score >= 5.0:
        return "C"
    if total_score >= 3.0:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# Stats update
# ---------------------------------------------------------------------------

def _update_stats(stats: dict, total_score: float, grade: str, is_anomaly: bool) -> dict:
    """Return updated stats dict (does not write to disk)."""
    n = stats.get("total_executions", 0)
    prev_avg = stats.get("avg_score_all", 0.0)

    stats["total_executions"] = n + 1
    # Incremental mean
    stats["avg_score_all"] = round((prev_avg * n + total_score) / (n + 1), 4)

    if is_anomaly:
        stats["total_anomalies"] = stats.get("total_anomalies", 0) + 1

    by_grade = stats.get("by_grade", {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0})
    by_grade[grade] = by_grade.get(grade, 0) + 1
    stats["by_grade"] = by_grade

    return stats


def _recompute_last100_avg() -> float:
    """Read last 100 executions and compute their average score."""
    all_execs = _read_jsonl(_EXECUTIONS_FILE)
    last100 = all_execs[-100:]
    if not last100:
        return 0.0
    scores = [e.get("total_score", 0.0) for e in last100 if "total_score" in e]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_execution(execution_record: dict, final_answer: str = "") -> dict:
    """
    Called after each agent turn. Computes score, persists to disk, returns
    the fully scored record. Thread-safe.

    Parameters
    ----------
    execution_record : dict
        Raw execution metadata (must contain at minimum 'terminated_by').
    final_answer : str
        The agent's final textual response.

    Returns
    -------
    dict
        Scored record with all original fields plus: scores, total_score,
        grade, anomaly, watcher_id, watcher_ts.
    """
    _ensure_dirs()

    with _LOCK:
        # Deep copy to avoid mutating caller's dict
        record = dict(execution_record)
        record["_final_answer"] = final_answer

        scores, total_score = _compute_scores(record, final_answer)
        grade = _grade(total_score)

        terminated_by = str(record.get("terminated_by", ""))
        is_anomaly = grade == "F" or "error" in terminated_by.lower()

        watcher_id = str(uuid.uuid4())[:8]
        watcher_ts = datetime.datetime.now().isoformat(timespec="seconds")

        scored_record = {
            **{k: v for k, v in record.items() if k != "_final_answer"},
            "final_answer": final_answer,
            "scores": scores,
            "total_score": total_score,
            "grade": grade,
            "anomaly": is_anomaly,
            "watcher_id": watcher_id,
            "watcher_ts": watcher_ts,
        }

        # Persist execution
        _append_jsonl(_EXECUTIONS_FILE, scored_record)

        # Persist anomaly
        if is_anomaly:
            _append_jsonl(_ANOMALIES_FILE, scored_record)
            print(
                f"[WATCHER ⚠️] ANOMALY detected — watcher_id={watcher_id} "
                f"grade={grade} score={total_score} terminated_by={terminated_by}",
                file=sys.stderr,
            )

        # Update rolling stats
        stats = _read_stats()
        stats = _update_stats(stats, total_score, grade, is_anomaly)
        # Recompute last-100 average every 10 executions to avoid constant I/O
        if stats["total_executions"] % 10 == 0:
            stats["avg_score_last100"] = _recompute_last100_avg()
        _write_stats(stats)

    return scored_record


def get_recent_executions(limit: int = 20) -> list:
    """
    Returns the last `limit` executions (most recent first).

    Parameters
    ----------
    limit : int
        Number of records to return.

    Returns
    -------
    list[dict]
    """
    _ensure_dirs()
    all_execs = _read_jsonl(_EXECUTIONS_FILE)
    return list(reversed(all_execs[-limit:]))


def get_stats() -> dict:
    """
    Returns current watcher_stats.json content or safe defaults.

    Returns
    -------
    dict
    """
    _ensure_dirs()
    return _read_stats()


def format_execution_report(scored_record: dict) -> str:
    """
    Formats a single execution as Telegram HTML for reporting.

    Parameters
    ----------
    scored_record : dict
        A scored record as returned by record_execution().

    Returns
    -------
    str
        HTML-formatted string suitable for Telegram.
    """
    wid = scored_record.get("watcher_id", "????????")
    ts = scored_record.get("watcher_ts", "")
    grade = scored_record.get("grade", "?")
    total = scored_record.get("total_score", 0.0)
    scores = scored_record.get("scores", {})
    terminated_by = scored_record.get("terminated_by", "unknown")
    tools_used = scored_record.get("tools_used", [])
    steps = scored_record.get("steps", scored_record.get("step_count", "?"))
    duration = scored_record.get("duration_seconds", scored_record.get("elapsed_seconds", "?"))
    final_answer = scored_record.get("final_answer", "")
    anomaly = scored_record.get("anomaly", False)

    # Shorten timestamp to HH:MM:SS
    ts_short = ts[11:19] if len(ts) >= 19 else ts

    # Grade emoji
    grade_emoji = {"A": "🏆", "B": "✅", "C": "🟡", "D": "🔶", "F": "❌"}.get(grade, "❓")

    # Tools list
    tools_str = ", ".join(str(t) for t in tools_used) if tools_used else "none"

    # Goal snippet (first 60 chars of final answer or goal field)
    goal = scored_record.get("goal") or scored_record.get("prompt") or final_answer
    goal_snippet = str(goal)[:60].replace("<", "&lt;").replace(">", "&gt;")
    if len(str(goal)) > 60:
        goal_snippet += "…"

    # Duration formatting
    if isinstance(duration, (int, float)):
        dur_str = f"{duration:.1f}s"
    else:
        dur_str = str(duration)

    anomaly_tag = " ⚠️ <b>ANOMALY</b>" if anomaly else ""

    lines = [
        f"<b>[{wid}]</b> {ts_short} | Score: <b>{total}/10 [{grade}]</b> {grade_emoji}{anomaly_tag}",
        f"Goal: {goal_snippet}",
        f"Ferramentas: {tools_str}",
        f"Tempo: {dur_str} | Passos: {steps} | Encerrado: {terminated_by}",
        "Dimensões:",
        f"  • Goal: {scores.get('goal_completion', '?')} | Tools: {scores.get('tool_efficiency', '?')} "
        f"| Speed: {scores.get('speed', '?')} | Quality: {scores.get('response_quality', '?')} "
        f"| Reliability: {scores.get('reliability', '?')}",
    ]
    return "\n".join(lines)


def get_dashboard_html(limit: int = 10) -> str:
    """
    Returns a full Telegram HTML dashboard of the last `limit` executions.

    Parameters
    ----------
    limit : int
        Number of recent executions to show.

    Returns
    -------
    str
        HTML-formatted dashboard string.
    """
    _ensure_dirs()
    stats = _read_stats()
    recent = get_recent_executions(limit=limit)

    avg_last100 = stats.get("avg_score_last100", stats.get("avg_score_all", 0.0))
    avg_grade = _grade(avg_last100)
    total_execs = stats.get("total_executions", 0)
    total_anomalies = stats.get("total_anomalies", 0)

    sep = "━" * 25

    header = (
        f"📊 <b>WATCHER — Painel de Execuções</b>\n"
        f"{sep}\n"
        f"📈 Score Médio (últimas 100): <b>{avg_last100}/10 [{avg_grade}]</b>\n"
        f"✅ Total Executado: <b>{total_execs}</b> | ❌ Anomalias: <b>{total_anomalies}</b>\n"
        f"{sep}"
    )

    blocks = [header]

    if not recent:
        blocks.append("Nenhuma execução registrada ainda.")
    else:
        for rec in recent:
            wid = rec.get("watcher_id", "????????")
            ts = rec.get("watcher_ts", "")
            ts_short = ts[11:16] if len(ts) >= 16 else ts  # HH:MM
            grade = rec.get("grade", "?")
            total = rec.get("total_score", 0.0)
            tools_used = rec.get("tools_used", [])
            steps = rec.get("steps", rec.get("step_count", "?"))
            duration = rec.get("duration_seconds", rec.get("elapsed_seconds", "?"))
            terminated_by = rec.get("terminated_by", "")
            goal = rec.get("goal") or rec.get("prompt") or rec.get("final_answer", "")
            goal_snippet = str(goal)[:50].replace("<", "&lt;").replace(">", "&gt;")
            if len(str(goal)) > 50:
                goal_snippet += "…"

            # Tools with status
            if tools_used:
                terminated_ok = terminated_by == "goal_achieved"
                status_icon = "✅" if terminated_ok else "⚠️"
                tools_str = " → ".join(str(t) for t in tools_used) + f" → {status_icon}"
            else:
                tools_str = "none"

            if isinstance(duration, (int, float)):
                dur_str = f"{duration:.1f}s"
            else:
                dur_str = str(duration)

            grade_emoji = {"A": "🏆", "B": "✅", "C": "🟡", "D": "🔶", "F": "❌"}.get(grade, "❓")

            block_lines = [
                f"<b>[{wid}]</b> {ts_short} | Score: <b>{total} [{grade}]</b> {grade_emoji}",
                f"Goal: {goal_snippet}",
                f"Ferramentas: {tools_str}",
                f"Tempo: {dur_str} | Passos: {steps}",
                "━" * 23,
            ]
            blocks.append("\n".join(block_lines))

    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# Daemon thread
# ---------------------------------------------------------------------------

def _daemon_loop(broadcast_fn=None) -> None:
    """
    Internal daemon loop. Runs indefinitely in a background thread.
    - Every 5 minutes: checks for new F-grade anomalies → broadcasts alert.
    - Every 30 minutes: computes & logs a summary stats update.
    """
    CHECK_INTERVAL_SECONDS = 300      # 5 minutes
    SUMMARY_INTERVAL_SECONDS = 1800   # 30 minutes

    last_anomaly_check = time.monotonic()
    last_summary = time.monotonic()
    # Track how many anomalies existed at last check
    last_known_anomaly_count = None

    while True:
        try:
            time.sleep(30)  # Poll every 30s; actual actions gate on intervals
            now = time.monotonic()

            # --- Anomaly check (every 5 min) ---
            if now - last_anomaly_check >= CHECK_INTERVAL_SECONDS:
                last_anomaly_check = now
                _ensure_dirs()
                stats = _read_stats()
                current_anomalies = stats.get("total_anomalies", 0)

                if last_known_anomaly_count is None:
                    last_known_anomaly_count = current_anomalies
                elif current_anomalies > last_known_anomaly_count:
                    new_count = current_anomalies - last_known_anomaly_count
                    last_known_anomaly_count = current_anomalies

                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    latest_anomalies = _read_jsonl(_ANOMALIES_FILE)[-new_count:] if _ANOMALIES_FILE.exists() else []
                    details_lines = []
                    for anom in latest_anomalies[-2:]:
                        g_snippet = str(anom.get("goal") or anom.get("prompt") or "Execução")[:60]
                        term = str(anom.get("terminated_by") or anom.get("error") or "falha")[:80]
                        wid = anom.get("watcher_id", "anom")
                        details_lines.append(f"• <code>[{wid}]</code> <b>{html.escape(g_snippet)}</b>\n  Causa: <code>{html.escape(term)}</code>")
                    
                    details_str = "\n".join(details_lines) if details_lines else f"• {new_count} anomalia(s) registrada(s)."
                    alert_msg = (
                        f"⚠️ <b>[AXION WATCHER] Anomalia Detectada</b> — {ts}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"{details_str}\n\n"
                        f"• <b>Total Histórico:</b> <code>{current_anomalies}</code>\n"
                        f"• <b>Status Operacional:</b> Agente auto-recuperado via fallback.\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━"
                    )

                    # Update last check timestamp in stats
                    with _LOCK:
                        stats["last_daemon_check_anomalies"] = datetime.datetime.now().isoformat(timespec="seconds")
                        _write_stats(stats)

                    if callable(broadcast_fn):
                        try:
                            broadcast_fn(alert_msg)
                        except Exception as broadcast_err:
                            print(
                                f"[WATCHER] broadcast_fn error: {broadcast_err}",
                                file=sys.stderr,
                            )
                    else:
                        print(f"[WATCHER ALERT]\n{alert_msg}", file=sys.stderr)
                else:
                    last_known_anomaly_count = current_anomalies
                    with _LOCK:
                        stats["last_daemon_check_anomalies"] = datetime.datetime.now().isoformat(timespec="seconds")
                        _write_stats(stats)

            # --- Summary (every 30 min) ---
            if now - last_summary >= SUMMARY_INTERVAL_SECONDS:
                last_summary = now
                _ensure_dirs()
                with _LOCK:
                    stats = _read_stats()
                    avg_last100 = _recompute_last100_avg()
                    stats["avg_score_last100"] = avg_last100
                    stats["last_daemon_summary"] = datetime.datetime.now().isoformat(timespec="seconds")
                    _write_stats(stats)

                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                summary_msg = (
                    f"[WATCHER SUMMARY — {ts}] "
                    f"Total: {stats.get('total_executions', 0)} | "
                    f"Avg(last100): {avg_last100}/10 [{_grade(avg_last100)}] | "
                    f"Anomalias: {stats.get('total_anomalies', 0)} | "
                    f"By grade: {stats.get('by_grade', {})}"
                )
                print(summary_msg, file=sys.stderr)

        except Exception as loop_err:
            print(f"[WATCHER DAEMON ERROR] {loop_err}", file=sys.stderr)
            time.sleep(60)  # Back off on unexpected errors


def start_watcher_daemon(broadcast_fn=None) -> threading.Thread:
    """
    Starts the background watcher daemon thread.

    The daemon:
    - Every 5 minutes: checks for new F-grade anomalies and calls broadcast_fn
      with an alert message if any are found.
    - Every 30 minutes: recomputes and persists rolling stats.

    Parameters
    ----------
    broadcast_fn : callable, optional
        A function that accepts a single str argument (the alert message).
        If None, alerts are printed to stderr.

    Returns
    -------
    threading.Thread
        The daemon thread (already started).
    """
    _ensure_dirs()
    t = threading.Thread(
        target=_daemon_loop,
        args=(broadcast_fn,),
        name="axion-watcher-daemon",
        daemon=True,
    )
    t.start()
    print("[WATCHER] Daemon started.", file=sys.stderr)
    return t


# ---------------------------------------------------------------------------
# Module self-test (run directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running watcher self-test…")

    sample = {
        "terminated_by": "goal_achieved",
        "tools_used": ["vercel_deploy"],
        "steps": 3,
        "duration_seconds": 23.4,
        "goal": "Faça um site para Alice com deploy na Vercel",
        "errors": [],
        "tool_failures": [],
        "fallback_model_used": False,
    }

    result = record_execution(sample, final_answer="Site criado com sucesso! Deploy feito em https://alice.vercel.app")
    print(f"Scored: {result['total_score']}/10 [{result['grade']}]")
    print(format_execution_report(result))
    print()
    print(get_dashboard_html(limit=5))
    print()
    print("Stats:", json.dumps(get_stats(), indent=2, ensure_ascii=False))
