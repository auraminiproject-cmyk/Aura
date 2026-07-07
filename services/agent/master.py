import json
import re
from typing import Any

from services.agent.llm import complete
from services.agent.schemas import AgentState, DesignParams

INTENT_KEYWORDS = {
    # Check specific intents FIRST (before broad design_request)
    "product_search": ["buy", "shop", "price", "myntra", "ajio", "amazon", "nalli", "manyavar", "కొను", "कीमत", "खरीद", "sale"],
    "tailoring": ["stitch", "tailor", "fabric", "yard", "measurement", "సెల్వి", "सिलाई", "दर्जी"],
    "wardrobe": ["wardrobe", "closet", "saved", "collection", "capsule"],
    "greeting": ["hello", "hi", "namaste", "నమస్కారం", "hey", "नमस्ते"],
    # Broad design intent checked LAST among specific intents
    "design_request": ["wedding", "saree", "lehenga", "outfit", "dress", "wear", "kurta", "sherwani", "పెళ్ళి", "అమ్మాయి", "शादी", "लहंगा"],
}


def classify_intent(message: str) -> str:
    lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for k in keywords:
            # Short keywords (<=3 chars) need word boundary matching
            if len(k) <= 3:
                if re.search(rf"\b{re.escape(k)}\b", lower):
                    return intent
            else:
                if k in lower:
                    return intent
    return "general"


def extract_params_heuristic(message: str) -> DesignParams:
    params = DesignParams()
    budget_match = re.search(r"(\d{3,6})\s*(inr|rupees|rs|₹)?", message, re.I)
    if budget_match:
        params.budget_inr = float(budget_match.group(1))
    for occasion in ("wedding", "festival", "office", "party", "casual", "temple"):
        if occasion in message.lower():
            params.occasion = occasion
            break
    colors = re.findall(r"\b(red|gold|blue|green|black|white|pink|maroon)\b", message, re.I)
    params.colors = [c.lower() for c in colors]
    if "hyderabad" in message.lower() or "telugu" in message.lower():
        params.cultural_context = "Hyderabad, Telugu"
    return params


async def extract_params_llm(message: str, language: str, gender: str = "neutral", history: list[dict[str, Any]] = None) -> DesignParams:
    history_str = ""
    if history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]]) + "\n\n"

    system = (
        "Extract fashion design parameters as JSON with keys: "
        "occasion, budget_inr, colors (array), body_type, cultural_context, garment_types (array). "
        f"The client's gender is '{gender}'. "
        "Review the conversation history and the latest message to determine the FINAL agreed upon outfit. "
        "If the latest message is a generic confirmation (like 'finalize' or 'yes'), extract the parameters from the history. "
        "If the user asks for a general outfit without naming a specific clothing item, you MUST infer 1-2 appropriate specific garment types. "
        "NEVER just return ['outfit'] or an empty array if an outfit is requested. "
        "Return ONLY valid JSON."
    )
    try:
        raw = await complete(f"{history_str}Latest Message ({language}): {message}", system=system, temperature=0.1)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            return DesignParams(**{k: v for k, v in data.items() if v is not None})
    except (json.JSONDecodeError, ValueError):
        pass
    return extract_params_heuristic(message)


async def synthesize_response(state: AgentState) -> str:
    lang_hint = {"te": "Telugu (code-mixed with English)", "hi": "Hindi", "en": "English"}.get(
        state.language, "Telugu"
    )
    system = (
        f"You are a warm expert Indian fashion stylist. Respond in {lang_hint}. "
        "Be culturally accurate, practical, and concise (under 120 words)."
    )
    user_prompt = (
        f"User message: {state.message}\n"
        f"Intent: {state.intent}\n"
        f"Extracted params: {state.params.model_dump_json()}\n"
        "Give outfit advice and next steps (e.g. upload photos for avatar)."
    )
    try:
        return await complete(user_prompt, system=system, temperature=0.5)
    except Exception:
        return (
            f"{state.params.occasion or 'Your'} look ki red/gold ethnic wear chala baguntundi. "
            f"Budget ~{int(state.params.budget_inr or 5000)} INR. "
            "Avatar kosam front+side photos upload cheyandi."
        )



