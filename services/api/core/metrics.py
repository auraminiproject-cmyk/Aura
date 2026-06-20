"""Prometheus metrics for AURA Fashion AI.

Exposes custom metrics at /metrics endpoint via prometheus_client.
Grafana dashboard queries these via Prometheus scrape.
"""

import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest

    # ── HTTP Metrics ─────────────────────────────────────────────────────
    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "handler", "status"],
    )
    HTTP_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration",
        ["method", "handler"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # ── Chat Metrics ─────────────────────────────────────────────────────
    CHAT_MESSAGES = Counter(
        "fashion_ai_chat_messages_total",
        "Total chat messages by intent",
        ["intent", "language"],
    )

    # ── LLM Metrics ──────────────────────────────────────────────────────
    LLM_DURATION = Histogram(
        "fashion_ai_llm_duration_seconds",
        "LLM call duration by provider",
        ["provider"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )
    LLM_ERRORS = Counter(
        "fashion_ai_llm_errors_total",
        "LLM errors by provider",
        ["provider"],
    )

    # ── Search Metrics ───────────────────────────────────────────────────
    SEARCH_DURATION = Histogram(
        "fashion_ai_search_duration_seconds",
        "Product search duration",
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    )

    # ── WebSocket Metrics ────────────────────────────────────────────────
    WS_CONNECTIONS = Gauge(
        "fashion_ai_websocket_connections_active",
        "Active WebSocket connections",
    )

    # ── Circuit Breaker Metrics ──────────────────────────────────────────
    CB_STATE = Gauge(
        "fashion_ai_circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=open)",
        ["provider"],
    )

    _ENABLED = True

except ImportError:
    _ENABLED = False
    logger.debug("prometheus_client not installed — metrics disabled")


def metrics_response() -> bytes:
    """Generate Prometheus metrics response."""
    if _ENABLED:
        return generate_latest()
    return b""


def track_request(method: str, handler: str, status: int, duration: float) -> None:
    """Track an HTTP request."""
    if _ENABLED:
        HTTP_REQUESTS.labels(method=method, handler=handler, status=str(status)).inc()
        HTTP_DURATION.labels(method=method, handler=handler).observe(duration)


def track_chat(intent: str, language: str) -> None:
    """Track a chat message."""
    if _ENABLED:
        CHAT_MESSAGES.labels(intent=intent, language=language).inc()


def track_llm(provider: str, duration: float, error: bool = False) -> None:
    """Track an LLM call."""
    if _ENABLED:
        LLM_DURATION.labels(provider=provider).observe(duration)
        if error:
            LLM_ERRORS.labels(provider=provider).inc()


def track_search(duration: float) -> None:
    """Track a product search."""
    if _ENABLED:
        SEARCH_DURATION.observe(duration)


def track_ws_connect() -> None:
    if _ENABLED:
        WS_CONNECTIONS.inc()


def track_ws_disconnect() -> None:
    if _ENABLED:
        WS_CONNECTIONS.dec()


def update_circuit_breaker(provider: str, is_open: bool) -> None:
    if _ENABLED:
        CB_STATE.labels(provider=provider).set(1 if is_open else 0)
