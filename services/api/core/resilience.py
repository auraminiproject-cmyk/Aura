"""Circuit breakers for external HTTP services (Groq, HF, Qdrant)."""

import logging

import pybreaker

logger = logging.getLogger(__name__)

groq_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="groq")
hf_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="huggingface")
qdrant_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, name="qdrant")


def breaker_state(name: str) -> str:
    mapping = {"groq": groq_breaker, "huggingface": hf_breaker, "qdrant": qdrant_breaker}
    br = mapping.get(name)
    if br is None:
        return "unknown"
    return "open" if br.current_state == "open" else "closed"
