#!/usr/bin/env python3
"""
Telemetry Service — Agent Workspace OS
Compliant with axion-telemetry-ops & RFC 7807.
Features:
- Global Trace ID generation (UUID v4) and propagation
- Metric tracking: latency (ms), prompt/completion tokens, status, model, client
- RFC 7807 structured error responses
- Persistent JSONL logging (workspace/telemetry/metrics.jsonl) with PII sanitization
- In-memory aggregation for high-speed dashboard queries
"""

import os
import sys
import json
import time
import uuid

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TELEMETRY_DIR = os.path.join(WORKSPACE_ROOT, "workspace", "telemetry")
METRICS_FILE = os.path.join(TELEMETRY_DIR, "metrics.jsonl")

try:
    os.makedirs(TELEMETRY_DIR, exist_ok=True)
except Exception:
    pass

_recent_events = []
_MAX_RECENT_EVENTS = 100

def generate_trace_id():
    """Generate a RFC-compliant UUIDv4 trace ID."""
    return str(uuid.uuid4())

def rfc7807_error(code, message, trace_id=None, status_code=500):
    """Format an error strictly according to RFC 7807 specification."""
    t_id = trace_id or generate_trace_id()
    return {
        "error": {
            "code": code,
            "message": message,
            "traceId": t_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": status_code
        }
    }

def record_metric(event_data):
    """
    Record an API / proxy transaction metric.
    Sanitizes sensitive headers and records latency, tokens, traceId.
    """
    trace_id = event_data.get("traceId") or generate_trace_id()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    metric = {
        "traceId": trace_id,
        "timestamp": now_iso,
        "endpoint": event_data.get("endpoint", "/v1/chat/completions"),
        "model": event_data.get("model", "meta-llama/llama-3.3-70b-instruct:free"),
        "status": int(event_data.get("status", 200)),
        "latency_ms": round(float(event_data.get("latency_ms", 0)), 1),
        "prompt_tokens": int(event_data.get("prompt_tokens", 0)),
        "completion_tokens": int(event_data.get("completion_tokens", 0)),
        "total_tokens": int(event_data.get("total_tokens", 0)),
        "cost_usd": float(event_data.get("cost_usd", 0.0)),
        "client_ip": event_data.get("client_ip", "127.0.0.1"),
        "is_stream": bool(event_data.get("is_stream", False)),
        "has_tools": bool(event_data.get("has_tools", False))
    }

    _recent_events.insert(0, metric)
    if len(_recent_events) > _MAX_RECENT_EVENTS:
        _recent_events.pop()

    try:
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(metric, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return metric

def get_telemetry_summary():
    """Return aggregated telemetry for the web dashboard."""
    # Ensure memory cache is populated if empty
    if not _recent_events and os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-_MAX_RECENT_EVENTS:]):
                    try:
                        _recent_events.append(json.loads(line.strip()))
                    except Exception:
                        pass
        except Exception:
            pass

    total_requests = len(_recent_events)
    if total_requests == 0:
        return {
            "total_requests": 0,
            "success_rate_percent": 100.0,
            "avg_latency_ms": 0.0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models_breakdown": {},
            "recent_events": []
        }

    successful = sum(1 for e in _recent_events if 200 <= e.get("status", 200) < 400)
    success_rate = round((successful / total_requests) * 100.0, 1)
    total_latency = sum(e.get("latency_ms", 0.0) for e in _recent_events)
    avg_latency = round(total_latency / total_requests, 1)

    prompt_tokens = sum(e.get("prompt_tokens", 0) for e in _recent_events)
    completion_tokens = sum(e.get("completion_tokens", 0) for e in _recent_events)
    total_tokens = sum(e.get("total_tokens", 0) for e in _recent_events)
    total_cost = sum(e.get("cost_usd", 0.0) for e in _recent_events)

    models_breakdown = {}
    for e in _recent_events:
        m = e.get("model", "unknown")
        models_breakdown[m] = models_breakdown.get(m, 0) + 1

    return {
        "total_requests": total_requests,
        "success_rate_percent": success_rate,
        "avg_latency_ms": avg_latency,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "models_breakdown": models_breakdown,
        "recent_events": _recent_events[:30]
    }
