#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AXION Error Handling, Global Catchers & Resilience Engine
Provides sys/threading excepthooks, circuit breakers, safe decorators,
and exponential backoff retry mechanisms for production resilience.
"""

import sys
import time
import random
import functools
import threading
import urllib.error
from typing import Callable, Any

try:
    from bot_engine import telemetry
except ImportError:
    import telemetry

_GLOBAL_CATCHERS_INSTALLED = False
_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Global Process & Thread Exception Catchers
# ---------------------------------------------------------------------------

def install_global_catchers(service_name: str, broadcast_fn: Callable = None) -> None:
    """
    Installs sys.excepthook and threading.excepthook to intercept ALL uncaught exceptions
    across main and background threads, recording them in telemetry and triggering alerts.
    """
    global _GLOBAL_CATCHERS_INSTALLED
    with _LOCK:
        if _GLOBAL_CATCHERS_INSTALLED:
            return
        _GLOBAL_CATCHERS_INSTALLED = True

    def _sys_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_record = telemetry.record_error(
            service=service_name,
            error_type=exc_type.__name__,
            message=str(exc_value),
            exc_info=(exc_type, exc_value, exc_traceback),
            context={"thread": "main", "service": service_name},
            severity="CRITICAL"
        )

        if broadcast_fn:
            try:
                alert_text = (
                    f"💥 <b>FALHA NÃO TRATADA [{service_name}]</b>\n"
                    f"Tipo: <code>{exc_type.__name__}</code>\n"
                    f"Mensagem: <code>{str(exc_value)[:200]}</code>\n"
                    "O evento foi registrado na telemetria persistente."
                )
                broadcast_fn(alert_text, severity="CRITICAL")
            except Exception as be:
                print(f"[ErrorHandler] Falha ao enviar broadcast de alerta: {be}")

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def _threading_excepthook(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return

        thread_name = args.thread.name if args.thread else "unnamed_thread"
        telemetry.record_error(
            service=service_name,
            error_type=args.exc_type.__name__,
            message=str(args.exc_value),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            context={"thread": thread_name, "service": service_name},
            severity="ERROR"
        )
        print(f"[ErrorHandler][ThreadException][{thread_name}] {args.exc_type.__name__}: {args.exc_value}")

    sys.excepthook = _sys_excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _threading_excepthook

    print(f"[ErrorHandler] Global exception catchers instalados com sucesso para [{service_name}].")


# ---------------------------------------------------------------------------
# Safe Catch Decorator
# ---------------------------------------------------------------------------

def safe_catch(service: str = "general", fallback_return: Any = None, alert_on_fail: bool = False, broadcast_fn: Callable = None):
    """
    Decorator to wrap functions in a resilient try/except block, logging any exception
    to telemetry and returning fallback_return instead of crashing the calling thread.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_record = telemetry.record_error(
                    service=service,
                    error_type=type(e).__name__,
                    message=str(e),
                    exc_info=e,
                    context={"function": func.__name__, "args_count": len(args)},
                    severity="CRITICAL" if alert_on_fail else "ERROR"
                )
                if alert_on_fail and broadcast_fn:
                    try:
                        broadcast_fn(
                            f"⚠️ <b>Erro capturado em {func.__name__} [{service}]:</b>\n<code>{str(e)[:200]}</code>",
                            severity="WARNING"
                        )
                    except Exception:
                        pass
                return fallback_return
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Circuit Breaker Pattern
# ---------------------------------------------------------------------------

class CircuitBreakerOpenException(Exception):
    """Raised when a call is attempted while the circuit breaker is OPEN"""
    pass


class CircuitBreaker:
    """
    In-memory Circuit Breaker to prevent cascading failures to fragile external APIs.
    Transitions: CLOSED -> (N failures) -> OPEN -> (recovery_timeout) -> HALF-OPEN -> CLOSED
    """
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 20.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_failure_time >= self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    print(f"[CircuitBreaker][{self.name}] Estado transitou para HALF-OPEN (testando recuperação)")
                    return True
                return False
            return True

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                print(f"[CircuitBreaker][{self.name}] Serviço recuperado! Estado restaurado para CLOSED.")

    def record_failure(self, error: Exception):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state in ("CLOSED", "HALF-OPEN") and self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                telemetry.record_circuit_breaker_trip(
                    self.name,
                    f"Atingido limite de {self.failure_threshold} falhas consecutivas ({type(error).__name__}: {str(error)[:100]})"
                )
                print(f"[CircuitBreaker][{self.name}] Disparado! Estado alterado para OPEN ({self.recovery_timeout}s de cooldown).")

    def call(self, func: Callable, *args, **kwargs):
        if not self.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuito '{self.name}' está ABERTO temporariamente devido a falhas consecutivas. Aguarde recuperação."
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise


# Pre-configured circuit breakers for core services
OPENROUTER_CIRCUIT = CircuitBreaker("openrouter_api", failure_threshold=4, recovery_timeout=25.0)
TELEGRAM_CIRCUIT = CircuitBreaker("telegram_api", failure_threshold=6, recovery_timeout=15.0)


# ---------------------------------------------------------------------------
# Exponential Backoff Retry Runner
# ---------------------------------------------------------------------------

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    service_name: str = "network",
    circuit: CircuitBreaker = None
) -> Any:
    """
    Executes a callable with automatic retries, exponential backoff, jitter,
    and HTTP 429 Retry-After header awareness.
    """
    delay = initial_delay
    last_exc = None

    for attempt in range(max_retries + 1):
        if circuit and not circuit.can_execute():
            raise CircuitBreakerOpenException(f"Circuito '{circuit.name}' está ABERTO.")

        try:
            res = func()
            if circuit:
                circuit.record_success()
            return res
        except Exception as e:
            last_exc = e
            if circuit:
                circuit.record_failure(e)

            # Check if this exception is non-retryable
            is_non_retryable = False
            retry_after_delay = None

            if isinstance(e, urllib.error.HTTPError):
                status_code = e.code
                # 429 Too Many Requests
                if status_code == 429:
                    header_val = e.headers.get("Retry-After")
                    if header_val and header_val.isdigit():
                        retry_after_delay = float(header_val)
                    else:
                        retry_after_delay = delay * 2
                # Non-retryable client errors (400, 401, 403, 404, 422)
                elif status_code in (400, 401, 403, 404, 422):
                    is_non_retryable = True

            if is_non_retryable or attempt >= max_retries:
                telemetry.record_error(
                    service=service_name,
                    error_type=type(e).__name__,
                    message=f"Tentativas esgotadas ({attempt}/{max_retries}): {e}",
                    exc_info=e,
                    context={"attempts": attempt, "service": service_name}
                )
                raise e

            sleep_time = retry_after_delay if retry_after_delay is not None else delay
            if jitter and retry_after_delay is None:
                sleep_time += random.uniform(0.1, 0.5)

            print(f"[Retry][{service_name}] Tentativa {attempt + 1}/{max_retries} falhou ({type(e).__name__}: {str(e)[:80]}). Aguardando {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor

    raise last_exc
