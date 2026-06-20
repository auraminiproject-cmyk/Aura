"""Langfuse LLM observability — trace all LLM/VLM calls for debugging and cost tracking.

Langfuse Cloud free tier: 50K observations/month.
Falls back silently to no-op when Langfuse is unavailable.
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

_langfuse = None
_initialized = False


def _init_langfuse():
    """Lazy-init Langfuse client from env vars."""
    global _langfuse, _initialized
    if _initialized:
        return _langfuse
    _initialized = True
    try:
        from langfuse import Langfuse

        _langfuse = Langfuse()
        logger.info("Langfuse initialized (project: %s)", _langfuse.base_url)
    except ImportError:
        logger.debug("Langfuse SDK not installed — observability disabled")
    except Exception as exc:
        logger.warning("Langfuse init failed: %s — observability disabled", exc)
    return _langfuse


class LLMTrace:
    """Context manager for tracing LLM calls."""

    def __init__(self, name: str, *, model: str = "", metadata: dict | None = None):
        self.name = name
        self.model = model
        self.metadata = metadata or {}
        self._trace = None
        self._generation = None
        self._start = 0.0

    def __enter__(self):
        self._start = time.time()
        client = _init_langfuse()
        if client:
            try:
                self._trace = client.trace(
                    name=self.name,
                    metadata=self.metadata,
                )
                self._generation = self._trace.generation(
                    name=f"{self.name}_generation",
                    model=self.model,
                    metadata=self.metadata,
                )
            except Exception as exc:
                logger.debug("Langfuse trace start failed: %s", exc)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self._start) * 1000
        if self._generation:
            try:
                self._generation.end(
                    metadata={
                        "duration_ms": round(duration_ms, 1),
                        "error": str(exc_val) if exc_val else None,
                        **self.metadata,
                    }
                )
            except Exception:
                pass
        if self._trace:
            try:
                self._trace.update(
                    metadata={"duration_ms": round(duration_ms, 1)},
                )
            except Exception:
                pass
        return False  # don't suppress exceptions

    def set_input(self, input_data: Any):
        if self._generation:
            try:
                self._generation.update(input=input_data)
            except Exception:
                pass

    def set_output(self, output_data: Any):
        if self._generation:
            try:
                self._generation.update(output=output_data)
            except Exception:
                pass

    def set_usage(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0):
        if self._generation:
            try:
                self._generation.update(
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens or (input_tokens + output_tokens),
                    }
                )
            except Exception:
                pass


def trace_llm(name: str = "llm_call", *, model: str = ""):
    """Decorator for tracing LLM function calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with LLMTrace(name, model=model) as trace:
                if args:
                    trace.set_input(str(args[0])[:500])
                result = await func(*args, **kwargs)
                if isinstance(result, str):
                    trace.set_output(result[:500])
                return result
        return wrapper
    return decorator


def flush():
    """Flush pending Langfuse events (call on shutdown)."""
    if _langfuse:
        try:
            _langfuse.flush()
        except Exception:
            pass
