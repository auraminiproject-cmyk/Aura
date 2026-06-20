"""End-to-end fashion session: agent → outfits → products → tailoring fallback."""

import base64
import logging
from typing import Any

from services.agent.master import run_fashion_agent
from services.agent.tailor_guide import generate_tailoring_guide
from services.retrieval.product_match import match_products
from services.vision.generate_outfit import generate_outfits

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.72


async def run_design_session(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    language: str = "te",
    num_variants: int = 4,
) -> dict[str, Any]:
    agent = await run_fashion_agent(message, history=history, language=language)
    brief = message if agent["intent"] == "design_request" else f"{message} — {agent['reply'][:200]}"

    outfit_result = await generate_outfits(design_brief=brief, num_variants=num_variants)
    variants = [v.__dict__ for v in outfit_result.variants]

    products = await match_products(
        outfit_description=brief,
        max_price_inr=agent.get("params", {}).get("budget_inr"),
        limit=5,
        threshold=SIMILARITY_THRESHOLD,
    )

    tailoring_pdf_b64: str | None = None
    if len(products) < 2:
        params = agent.get("params") or {}
        garments = params.get("garment_types") if isinstance(params, dict) else None
        garment_type = "lehenga"
        if isinstance(garments, list) and garments:
            garment_type = str(garments[0])
        measurements = {"chest_cm": 88, "waist_cm": 72, "hip_cm": 96}
        pdf = await generate_tailoring_guide(
            garment_type=garment_type,
            fabric="silk",
            measurements=measurements,
            occasion=params.get("occasion"),
        )
        tailoring_pdf_b64 = base64.b64encode(pdf).decode("ascii")

    return {
        "agent": agent,
        "outfits": {
            "variants": variants,
            "preview_ready_ms": outfit_result.preview_ready_ms,
            "full_ready_ms": outfit_result.full_ready_ms,
        },
        "products": products,
        "tailoring_pdf_base64": tailoring_pdf_b64,
        "needs_tailoring": tailoring_pdf_b64 is not None,
    }
