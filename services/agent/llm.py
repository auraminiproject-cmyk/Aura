"""Triple-mode LLM completion: LiteLLM Proxy → Groq Direct → Ollama → Offline.

In Docker/local dev the LiteLLM proxy (http://localhost:4000) handles routing and
fallback automatically.  In production on Render (no LiteLLM sidecar) we fall
through: Groq direct → Ollama → offline heuristic.
"""

import logging
from typing import Any

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)


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
                logger.info("LLM response via LiteLLM proxy")
                return result
            except Exception as exc:
                logger.warning("LiteLLM proxy unavailable: %s — falling through", exc)

        # Tier 2 — Groq Direct (production primary)
        if settings.groq_api_key and chosen.startswith("groq/"):
            try:
                groq_model = chosen.replace("groq/", "")
                logger.info("Calling Groq with model=%s, key=%s...", groq_model, settings.groq_api_key[:10])
                result = await _groq_complete(messages, model=groq_model, temperature=temperature)
                trace.set_output(result[:500])
                logger.info("LLM response via Groq direct (%s)", groq_model)
                return result
            except Exception as exc:
                logger.error("Groq direct failed: %s", exc, exc_info=True)
        else:
            logger.warning("Groq skipped: key_set=%s, model=%s", bool(settings.groq_api_key), chosen)

        # Tier 3 — Ollama (local fallback)
        try:
            result = await _ollama_complete(prompt, system=system, temperature=temperature)
            trace.set_output(result[:500])
            logger.info("LLM response via Ollama")
            return result
        except Exception as exc:
            logger.warning("Ollama unavailable: %s", exc)

        # Tier 4 — Offline heuristic
        logger.warning("All LLM providers failed — using offline fallback")
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
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={"model": model, "messages": messages, "temperature": temperature},
        )
        if resp.status_code != 200:
            logger.error("Groq HTTP %d: %s", resp.status_code, resp.text[:300])
            resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _ollama_complete(prompt: str, *, system: str | None, temperature: float) -> str:
    settings = get_settings()
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    model_name = settings.llm_fallback_model.replace("ollama/", "llama3.2")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": model_name, "prompt": full_prompt, "stream": False, "options": {"temperature": temperature}},
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()

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
