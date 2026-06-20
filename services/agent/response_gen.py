"""Culturally warm multilingual responses with optional style profile injection."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.agent.llm import complete
from services.agent.schemas import AgentState
from services.api.core.models import StyleProfile


async def load_style_context(db: AsyncSession, user_id: str) -> str:
    result = await db.execute(select(StyleProfile).where(StyleProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        return ""
    tags = profile.liked_tags or []
    vec = profile.preference_vector or []
    return f"User likes: {tags}. Preference strength: {vec[:3] if vec else 'neutral'}."


async def synthesize_with_profile(
    state: AgentState,
    *,
    style_context: str = "",
    history: list[dict[str, Any]] | None = None,
) -> str:
    lang_hint = {"te": "Telugu code-mixed", "hi": "Hindi", "en": "English"}.get(state.language, "Telugu")
    system = (
        f"Expert Indian fashion stylist. Respond in {lang_hint}. Warm, practical, under 120 words. "
        f"{style_context}"
    )

    # Build history context for multi-turn conversation
    history_text = ""
    if history:
        recent = history[-6:]  # Last 3 exchanges (6 messages)
        history_lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            history_lines.append(f"{role}: {content}")
        history_text = "Conversation so far:\n" + "\n".join(history_lines) + "\n\n"

    prompt = (
        f"{history_text}"
        f"Message: {state.message}\nIntent: {state.intent}\nParams: {state.params.model_dump_json()}\n"
        "Include next step (e.g. upload photos)."
    )
    try:
        return await complete(prompt, system=system, temperature=0.5)
    except Exception:
        return (
            f"{state.params.occasion or 'Outfit'} ki red/gold ethnic wear suggest chestanu. "
            "Avatar kosam photos upload cheyandi."
        )
