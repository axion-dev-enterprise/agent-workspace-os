#!/usr/bin/env python3
"""
OpenAI-Compatible Proxy — Agent Workspace OS
Translates standard OpenAI API requests (/v1/chat/completions, /v1/models)
to OpenRouter with zero-cost tool-calling models, streaming SSE support,
and automated RFC 7807 telemetry instrumentation.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
try:
    from telemetry_service import generate_trace_id, record_metric, rfc7807_error
except ImportError:
    from .telemetry_service import generate_trace_id, record_metric, rfc7807_error

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
DEFAULT_MODEL = "cohere/north-mini-code:free"
FALLBACK_FREE_MODELS = [
    "cohere/north-mini-code:free",
    "openrouter/auto"
]

MODEL_ALIASES = {
    "default": DEFAULT_MODEL,
    "gpt-4o-mini": DEFAULT_MODEL,
    "gpt-4o": DEFAULT_MODEL,
    "gpt-3.5-turbo": DEFAULT_MODEL,
    "claude-3-haiku": DEFAULT_MODEL
}

def resolve_openrouter_key(client_auth_header=None):
    """
    Resolve OpenRouter API Key with hierarchy:
    1. Direct client authorization header (if valid and not a local placeholder)
    2. workspace.config.json (ai.openrouter_api_key)
    3. .env file in WORKSPACE_ROOT
    4. Development Vault keys
    """
    if client_auth_header and client_auth_header.startswith("Bearer "):
        token = client_auth_header.split(" ", 1)[1].strip()
        if token.startswith("sk-or-") or (len(token) > 20 and not token.startswith("sk-os-")):
            return token

    # 2. Check workspace.config.json
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                key = cfg.get("ai", {}).get("openrouter_api_key") or cfg.get("openrouter_api_key")
                if key:
                    return key
        except Exception:
            pass

    # 3. Check local .env
    env_path = os.path.join(WORKSPACE_ROOT, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'')
        except Exception:
            pass

    # 4. Check Vault paths
    vault_paths = [
        "D:/WORKSPACE/SECURE/VAULT/tokens/llm/openrouter.env",
        "D:/WORKSPACE/SECURE/VAULT/tokens/openrouter/openrouter.env",
        "D:/WORKSPACE/SECURE/VAULT/sensix/openrouter.env"
    ]
    for vp in vault_paths:
        if os.path.exists(vp):
            try:
                with open(vp, "r", encoding="utf-8") as f:
                    for line in f:
                        trimmed = line.strip()
                        if trimmed.startswith("OPENROUTER_API_KEY=") or trimmed.startswith("OPENROUTER_KEY="):
                            return trimmed.split("=", 1)[1].strip().strip('"\'')
            except Exception:
                pass

    return ""

def get_models_list():
    """Return list of models matching OpenAI specification."""
    models_data = [
        {
            "id": DEFAULT_MODEL,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openrouter-free",
            "permission": [],
            "root": DEFAULT_MODEL,
            "parent": None,
            "features": {"tool_calls": True, "streaming": True, "cost": "0.00"}
        },
        {
            "id": "google/gemini-2.0-flash-exp:free",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "google",
            "permission": [],
            "features": {"tool_calls": True, "streaming": True, "cost": "0.00"}
        },
        {
            "id": "openrouter/auto",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openrouter",
            "permission": [],
            "features": {"tool_calls": True, "streaming": True, "cost": "auto"}
        },
        {
            "id": "gpt-4o-mini",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openai-alias",
            "permission": [],
            "features": {"tool_calls": True, "alias_for": DEFAULT_MODEL}
        }
    ]
    return {"object": "list", "data": models_data}

def handle_chat_completions(req_body, req_headers, client_ip="127.0.0.1", sse_writer=None):
    """
    Handle /v1/chat/completions forwarding to OpenRouter.
    Supports streaming SSE (if sse_writer provided and stream=True).
    Tracks RFC 7807 telemetry and latency.
    """
    start_time = time.time()
    trace_id = None
    for k, v in req_headers.items():
        if k.lower() == "x-trace-id":
            trace_id = v
            break
    if not trace_id:
        trace_id = generate_trace_id()

    # Model resolution
    raw_model = req_body.get("model", DEFAULT_MODEL)
    target_model = MODEL_ALIASES.get(raw_model, raw_model)
    if not target_model or target_model in ("", "default"):
        target_model = DEFAULT_MODEL

    req_body["model"] = target_model
    is_stream = bool(req_body.get("stream", False))
    has_tools = bool(req_body.get("tools"))

    # Resolve OpenRouter Key
    auth_header = req_headers.get("Authorization") or req_headers.get("authorization")
    api_key = resolve_openrouter_key(auth_header)

    if not api_key:
        err_res = rfc7807_error(
            code="AUTHENTICATION_CONFIG_MISSING",
            message="Chave do OpenRouter não configurada. Defina no painel /setup ou no arquivo workspace.config.json.",
            trace_id=trace_id,
            status_code=401
        )
        record_metric({
            "traceId": trace_id, "endpoint": "/v1/chat/completions",
            "model": target_model, "status": 401, "latency_ms": (time.time() - start_time) * 1000,
            "client_ip": client_ip, "is_stream": is_stream, "has_tools": has_tools
        })
        return {"status": 401, "headers": {"X-Trace-ID": trace_id, "Content-Type": "application/json"}, "body": json.dumps(err_res).encode("utf-8")}

    upstream_url = "https://openrouter.ai/api/v1/chat/completions"
    upstream_payload = json.dumps(req_body).encode("utf-8")

    upstream_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://axionenterprise.cloud",
        "X-Title": "Agent Workspace OS",
        "X-Trace-ID": trace_id
    }

    upstream_req = urllib.request.Request(upstream_url, data=upstream_payload, headers=upstream_headers, method="POST")

    if is_stream and sse_writer is not None:
        # ── Streaming Mode (SSE) ──
        try:
            with urllib.request.urlopen(upstream_req, timeout=60) as resp:
                prompt_tokens_est = len(json.dumps(req_body.get("messages", []))) // 4
                completion_chunks = 0
                for line in resp:
                    sse_writer(line)
                    completion_chunks += 1

            latency_ms = (time.time() - start_time) * 1000
            record_metric({
                "traceId": trace_id,
                "endpoint": "/v1/chat/completions",
                "model": target_model,
                "status": 200,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens_est,
                "completion_tokens": max(1, completion_chunks),
                "total_tokens": prompt_tokens_est + max(1, completion_chunks),
                "client_ip": client_ip,
                "is_stream": True,
                "has_tools": has_tools
            })
            return {"streaming_completed": True, "traceId": trace_id}

        except urllib.error.HTTPError as he:
            err_content = he.read().decode("utf-8", errors="replace")
            err_res = rfc7807_error(code="OPENROUTER_UPSTREAM_ERROR", message=err_content, trace_id=trace_id, status_code=he.code)
            record_metric({"traceId": trace_id, "endpoint": "/v1/chat/completions", "model": target_model, "status": he.code, "latency_ms": (time.time() - start_time) * 1000, "client_ip": client_ip})
            return {"status": he.code, "headers": {"X-Trace-ID": trace_id, "Content-Type": "application/json"}, "body": json.dumps(err_res).encode("utf-8")}
        except Exception as e:
            err_res = rfc7807_error(code="PROXY_STREAM_EXCEPTION", message=str(e), trace_id=trace_id, status_code=502)
            return {"status": 502, "headers": {"X-Trace-ID": trace_id, "Content-Type": "application/json"}, "body": json.dumps(err_res).encode("utf-8")}

    else:
        # ── Non-Streaming Mode ──
        try:
            with urllib.request.urlopen(upstream_req, timeout=45) as resp:
                raw_resp = resp.read()
                latency_ms = (time.time() - start_time) * 1000
                parsed_resp = json.loads(raw_resp.decode("utf-8"))

                usage = parsed_resp.get("usage", {})
                p_tok = usage.get("prompt_tokens", 0)
                c_tok = usage.get("completion_tokens", 0)
                t_tok = usage.get("total_tokens", p_tok + c_tok)

                record_metric({
                    "traceId": trace_id,
                    "endpoint": "/v1/chat/completions",
                    "model": target_model,
                    "status": 200,
                    "latency_ms": latency_ms,
                    "prompt_tokens": p_tok,
                    "completion_tokens": c_tok,
                    "total_tokens": t_tok,
                    "client_ip": client_ip,
                    "is_stream": False,
                    "has_tools": has_tools
                })

                return {
                    "status": 200,
                    "headers": {
                        "Content-Type": "application/json; charset=utf-8",
                        "X-Trace-ID": trace_id
                    },
                    "body": raw_resp
                }

        except urllib.error.HTTPError as he:
            latency_ms = (time.time() - start_time) * 1000
            err_content = he.read().decode("utf-8", errors="replace")
            err_res = rfc7807_error(code="OPENROUTER_UPSTREAM_ERROR", message=err_content, trace_id=trace_id, status_code=he.code)
            record_metric({
                "traceId": trace_id, "endpoint": "/v1/chat/completions", "model": target_model,
                "status": he.code, "latency_ms": latency_ms, "client_ip": client_ip
            })
            return {
                "status": he.code,
                "headers": {"Content-Type": "application/json; charset=utf-8", "X-Trace-ID": trace_id},
                "body": json.dumps(err_res).encode("utf-8")
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            err_res = rfc7807_error(code="PROXY_EXECUTION_EXCEPTION", message=str(e), trace_id=trace_id, status_code=502)
            record_metric({
                "traceId": trace_id, "endpoint": "/v1/chat/completions", "model": target_model,
                "status": 502, "latency_ms": latency_ms, "client_ip": client_ip
            })
            return {
                "status": 502,
                "headers": {"Content-Type": "application/json; charset=utf-8", "X-Trace-ID": trace_id},
                "body": json.dumps(err_res).encode("utf-8")
            }
