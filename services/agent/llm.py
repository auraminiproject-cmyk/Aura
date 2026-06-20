"""Triple-mode LLM completion: LiteLLM Proxy → Groq Direct → Ollama → Offline.

In Docker/local dev the LiteLLM proxy (http://localhost:4000) handles routing and
fallback automatically.  In production on Render (no LiteLLM sidecar) we fall
through: Groq direct → Ollama → offline heuristic.
"""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.api.core.config import get_settings
from services.api.core.resilience import groq_breaker

logger = logging.getLogger(__name__)


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
async def complete(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.4,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """Route an LLM completion through the triple-mode chain.

    Args:
        prompt: User prompt (ignored if *messages* is provided).
        system: Optional system prompt.
        model: Model identifier (e.g. ``groq/llama-3.3-70b-versatile``).
        temperature: Sampling temperature.
        messages: Pre-built OpenAI-format message list.  When supplied,
                  *prompt* and *system* are ignored.
    """
    settings = get_settings()
    chosen = model or settings.llm_fast_model

    if messages is None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

    # Langfuse observability (no-op if not configured)
    from services.api.core.langfuse_client import LLMTrace

    with LLMTrace("llm_complete", model=chosen) as trace:
        trace.set_input(prompt[:500] if prompt else str(messages)[:500])

        # Tier 1 — LiteLLM Proxy (local Docker only)
        if settings.litellm_proxy_url and settings.app_env != "production":
            try:
                result = await _litellm_complete(messages, model=chosen, temperature=temperature)
                trace.set_output(result[:500])
                return result
            except Exception as exc:
                logger.warning("LiteLLM proxy unavailable: %s — falling through", exc)

        # Tier 2 — Groq Direct (production primary)
        if settings.groq_api_key and chosen.startswith("groq/"):
            try:
                result = await _groq_complete(
                    messages, model=chosen.replace("groq/", ""), temperature=temperature,
                )
                trace.set_output(result[:500])
                return result
            except Exception:
                pass  # already logged inside _groq_complete

        # Tier 3 — Ollama (local fallback)
        try:
            result = await _ollama_complete(prompt, system=system, temperature=temperature)
            trace.set_output(result[:500])
            return result
        except Exception:
            pass

        # Tier 4 — Offline heuristic
        result = _offline_fallback(prompt)
        trace.set_output(result[:500])
        return result


async def _litellm_complete(
    messages: list[dict[str, str]], *, model: str, temperature: float,
) -> str:
    """Call the LiteLLM OpenAI-compatible proxy."""
    settings = get_settings()
    proxy_url = settings.litellm_proxy_url.rstrip("/")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{proxy_url}/chat/completions",
            headers={"Authorization": "Bearer sk-fashion-ai-local"},
            json={"model": model, "messages": messages, "temperature": temperature},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _groq_complete(
    messages: list[dict[str, str]], *, model: str, temperature: float,
) -> str:
    settings = get_settings()

    if groq_breaker.current_state == "open":
        raise RuntimeError("Groq circuit breaker open")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": model, "messages": messages, "temperature": temperature},
            )
            if resp.status_code == 429:
                groq_breaker.fail()
                logger.warning("Groq rate limited (429)")
                raise RuntimeError("Groq rate limited")
            resp.raise_for_status()
            data = resp.json()
            groq_breaker.success()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        groq_breaker.fail()
        logger.warning("Groq error (circuit may open): %s", exc)
        raise


async def _ollama_complete(prompt: str, *, system: str | None, temperature: float) -> str:
    settings = get_settings()
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    model_name = settings.llm_fallback_model.replace("ollama/", "llama3.2")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": model_name, "prompt": full_prompt, "stream": False, "options": {"temperature": temperature}},
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except httpx.HTTPError as exc:
        logger.warning("Ollama unavailable: %s", exc)

    raise RuntimeError("Ollama unavailable")


def _offline_fallback(prompt: str) -> str:
    """Graceful degradation when no LLM providers are reachable."""
    lower = prompt.lower()
    if any(w in lower for w in ("wedding", "పెళ్ళి", "vivah", "शादी")):
        return (
            "Meeku wedding ki perfect ethnic look suggest chestanu! "
            "Red/gold lehenga or silk saree body type ki flattering ga untundi. "
            "Budget 5000 INR kinda best options chupistha — photo upload cheyandi avatar kosam."
        )
    if any(w in lower for w in ("hello", "hi", "namaste", "నమస్కారం")):
        return "Namaste! Nenu mee personal fashion stylist. Emi occasion ki dress kavali cheppandi."
    return (
        "Meeru cheppina style brief batti outfit design chestanu. "
        "Occasion, budget, and preferred colors cheppandi — Telugu, Hindi, or English lo."
    )
