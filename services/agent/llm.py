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
            groq_model = chosen.replace("groq/", "")
            try:
                logger.info("Calling Groq with model=%s", groq_model)
                result = await _groq_complete(messages, model=groq_model, temperature=temperature)
                trace.set_output(result[:500])
                logger.info("LLM response via Groq direct (%s)", groq_model)
                return result
            except Exception as exc:
                logger.warning("Groq %s failed: %s", groq_model, exc)
                # On 429 rate limit, try smaller model before giving up
                if "429" in str(exc) and groq_model != "llama-3.1-8b-instant":
                    try:
                        logger.info("Groq 429 — falling back to llama-3.1-8b-instant")
                        result = await _groq_complete(messages, model="llama-3.1-8b-instant", temperature=temperature)
                        trace.set_output(result[:500])
                        logger.info("LLM response via Groq fallback (8b-instant)")
                        return result
                    except Exception as exc2:
                        logger.warning("Groq 8b-instant also failed: %s", exc2)
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
    """Graceful degradation when no LLM providers are reachable.

    Gender-neutral, contextually varied, non-repetitive.
    """
    import random
    lower = prompt.lower()

    # Detect gender hints
    is_male = any(w in lower for w in (
        "shirt", "kurta", "sherwani", "suit", "blazer", "men", "man", "male",
        "boys", "guy", "groom", "dulha", "పురుషుల", "ladka",
    ))
    is_female = any(w in lower for w in (
        "saree", "lehenga", "dress", "gown", "women", "woman", "female",
        "girls", "bride", "dulhan", "స్త్రీల", "ladki", "anarkali",
    ))

    # Wedding/occasion detection
    if any(w in lower for w in ("wedding", "పెళ్ళి", "vivah", "शादी", "marriage", "reception")):
        if is_male or not is_female:
            options = [
                "Wedding look ki — classic sherwani in rich jewel tones suggest chestanu! "
                "Navy blue or maroon silk sherwani with golden embroidery, churidar, and mojari — "
                "regal and masculine.",
                "Groom/wedding guest look: Silk kurta-pajama set or bandhgala suit "
                "in deep colors. Premium fabric options ₹5000-15000 range lo available.",
            ]
        else:
            options = [
                "Wedding ki gorgeous options: Kanjeevaram silk saree or designer lehenga — "
                "color and fabric body type ki match chestanu!",
                "Bridal/wedding guest look: Rich silk in traditional colors — "
                "red, maroon, or emerald green with zari work.",
            ]
        return random.choice(options)

    # Casual/general detection
    if any(w in lower for w in ("casual", "daily", "office", "work", "college")):
        if is_male or not is_female:
            return ("Smart casual look: well-fitted chinos with a crisp cotton shirt, "
                    "or a kurta with jeans for a fusion vibe. Clean silhouette matters!")
        return ("Everyday chic: A-line kurti with palazzo pants, or a midi dress — "
                "comfortable yet stylish. Cotton or rayon works great.")

    # Greeting
    if any(w in lower for w in ("hello", "hi", "namaste", "నమస్కారం", "hey", "hola")):
        greetings = [
            "Hello! I'm AURA, your fashion stylist. Tell me — what occasion are you dressing for?",
            "Namaste! What kind of outfit are you looking for? Wedding, party, casual, or office?",
            "Hey! Ready to design something amazing. What's the occasion?",
        ]
        return random.choice(greetings)

    # Finalize/confirm
    if any(w in lower for w in ("finalize", "confirm", "done", "perfect", "yes")):
        return ("Great choice! Let me finalize your outfit specification. "
                "I'll generate the design with your exact measurements.")

    # Generic — but VARIED, not the same question every time
    generic = [
        "I'd love to help with that! Tell me the occasion and I'll suggest specific fabrics and styles.",
        "Great taste! Let me recommend something that suits your body type perfectly. What's your budget range?",
        "Interesting! I'm thinking about colors and fabrics that would work beautifully. Formal or casual vibe?",
        "Let me design something unique for you. Indoor or outdoor event?",
    ]
    return random.choice(generic)
