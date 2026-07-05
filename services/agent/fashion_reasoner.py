"""Chain-of-thought fashion reasoning agent — Groq 70b with explicit <think> blocks.

This is the core intelligence module. It receives pre-computed body analysis +
RAG knowledge and produces a reasoned, personalized fashion recommendation
using the same step-by-step <think> process the finetuning was designed to teach.

The key insight: instead of teaching the model to reason via training data,
we INJECT the reasoning framework + domain knowledge via system prompt,
achieving equivalent quality without the 3-day finetuning process.
"""

import json
import logging
import re
from typing import Any

from services.agent.llm import complete
from services.api.core.config import get_settings

logger = logging.getLogger(__name__)


REASONING_SYSTEM_PROMPT = """You are AURA, an elite AI fashion reasoning engine with 25+ years of expertise.

═══ YOUR REASONING PROCESS (MANDATORY — FOLLOW EXACTLY) ═══

You MUST think step-by-step before giving advice. Wrap your analysis in <think>...</think> tags.

<think>
STEP 1 — BODY GEOMETRY ANALYSIS:
Analyze the client's exact measurements. What body type? What WHR tells us about
silhouette choices? What proportional tricks will flatter this specific frame?

STEP 2 — SKIN & COLOR SCIENCE:
What undertone? Which colors create vibrant contrast vs which muddy the skin?
Use wavelength/reflection science, not generic advice.

STEP 3 — CLIMATE & FABRIC SELECTION:
What's the weather? Which fabric has the right breathability, drape, and weight?
Use fiber physics: porosity, moisture transport, thermal conductivity.

STEP 4 — BUDGET OPTIMIZATION:
What price tier? Where to shop for best value? Cost-per-wear calculation.

STEP 5 — CULTURAL & OCCASION ALIGNMENT:
What are the cultural expectations? What's appropriate and what's not?
Regional traditions, religious norms, occasion dress codes.

STEP 6 — SYNTHESIS:
What outfit satisfies ALL constraints simultaneously? Why is this the OPTIMAL
choice for THIS specific person? What makes it unique to them?
</think>

Then give the actual recommendation — warm, specific, actionable.

═══ HARD RULES ═══
- Every recommendation MUST reference the client's actual measurements
- Name SPECIFIC fabrics (not "silk" → "Kanjeevaram silk" or "Banarasi brocade")
- Include price estimates in INR where possible
- If constraints conflict, explain the trade-off and your reasoning
- KEEP SPOKEN REPLIES CONCISE (3-5 sentences after thinking) — this will be TTS'd
- NEVER give generic advice — every word must be unique to THIS client

═══ LANGUAGE MIRRORING ═══
{language_instruction}

═══ EXPERT KNOWLEDGE (use this as ground truth) ═══
{knowledge_context}

═══ CLIENT PROFILE ═══
{body_analysis}
"""


async def reason(
    *,
    user_message: str,
    body_analysis_text: str = "",
    knowledge_context: str = "",
    conversation_history: list[dict[str, str]] | None = None,
    detected_language: str | None = None,
    wants_finalize: bool = False,
) -> tuple[str, str]:
    """Run the fashion reasoning agent.

    Args:
        user_message: What the user said.
        body_analysis_text: Pre-formatted body analysis from body_analyzer.
        knowledge_context: Pre-formatted RAG knowledge from fashion_rag.
        conversation_history: Previous messages in this session.
        detected_language: Auto-detected language (te/hi/en).
        wants_finalize: Whether the user wants to finalize the outfit.

    Returns:
        Tuple of (full_reasoning_reply, stripped_reply_for_tts).
        full_reasoning includes <think> blocks; stripped has them removed.
    """
    settings = get_settings()

    # Language instruction
    lang_names = {"te": "Telugu", "hi": "Hindi", "en": "English"}
    lang_name = lang_names.get(detected_language or "en", detected_language or "English")
    language_instruction = (
        f"The client is speaking in {lang_name}. Reply in {lang_name} "
        f"(with natural code-mixing if appropriate). "
        f"Match their emotional energy and conversational style."
    )

    # Build system prompt with injected knowledge
    system = REASONING_SYSTEM_PROMPT.format(
        language_instruction=language_instruction,
        knowledge_context=knowledge_context or "(No specific knowledge retrieved — reason from your training.)",
        body_analysis=body_analysis_text or "(No body measurements available yet — ask the client to upload photos for avatar analysis.)",
    )

    if wants_finalize:
        system += (
            "\n\n═══ FINALIZATION MODE ═══\n"
            "The client wants to FINALIZE. After your <think> reasoning, output the final "
            "outfit spec as a JSON block wrapped in ```json ... ``` with these exact keys:\n"
            "{\n"
            '  "garment_type": "...",\n'
            '  "fabric": "specific fabric name",\n'
            '  "color": "specific color",\n'
            '  "silhouette": "...",\n'
            '  "style_notes": "...",\n'
            '  "occasion": "...",\n'
            '  "budget_inr": 0\n'
            "}\n"
        )

    # Build messages
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]

    # Add conversation history (last 10 turns)
    if conversation_history:
        for msg in conversation_history[-10:]:
            messages.append(msg)

    # Add current message
    messages.append({"role": "user", "content": user_message})

    # Call LLM — use the primary reasoning model
    model = getattr(settings, "fashion_reasoning_model", settings.llm_stylist_model)
    try:
        full_reply = await complete(
            user_message,
            model=model,
            messages=messages,
            temperature=0.6,
        )
    except Exception as exc:
        logger.error("Fashion reasoner LLM failed: %s", exc)
        full_reply = (
            "Let me think about the best outfit for you... "
            "Could you tell me more about the occasion and your preferences?"
        )

    # Strip <think> blocks for TTS (voice) output
    stripped = strip_think_blocks(full_reply)

    return full_reply, stripped


def strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks from LLM output for TTS."""
    # Remove think blocks (including multiline)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Clean up extra whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def extract_think_block(text: str) -> str | None:
    """Extract the <think> reasoning block if present."""
    match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def format_body_analysis_for_llm(analysis_dict: dict[str, Any]) -> str:
    """Format body analyzer output into a readable context block for the LLM."""
    if not analysis_dict:
        return "(No body measurements available)"

    lines = [
        f"Body type: {analysis_dict.get('body_type', 'unknown')}",
        f"Waist-hip ratio: {analysis_dict.get('whr', 'N/A')}",
        f"Shoulder-hip ratio: {analysis_dict.get('shr', 'N/A')}",
        f"Height category: {analysis_dict.get('height_category', 'N/A')}",
        f"Frame size: {analysis_dict.get('frame_size', 'N/A')}",
        f"Vertical proportion: {analysis_dict.get('vertical_proportion', 'N/A')}",
        f"Pattern scale: {analysis_dict.get('pattern_scale', 'N/A')}",
    ]

    notes = analysis_dict.get("proportional_notes", [])
    if notes:
        lines.append("Proportional analysis:")
        for note in notes:
            lines.append(f"  • {note}")

    sil_recs = analysis_dict.get("silhouette_recs", [])
    if sil_recs:
        lines.append("Recommended silhouettes:")
        for rec in sil_recs:
            lines.append(f"  ✓ {rec}")

    sil_avoid = analysis_dict.get("silhouette_avoid", [])
    if sil_avoid:
        lines.append("Avoid:")
        for av in sil_avoid:
            lines.append(f"  ✗ {av}")

    neck_recs = analysis_dict.get("neckline_recs", [])
    if neck_recs:
        lines.append("Necklines:")
        for nr in neck_recs:
            lines.append(f"  → {nr}")

    return "\n".join(lines)
