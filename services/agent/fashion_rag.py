"""Enhanced fashion knowledge RAG — retrieves domain expertise from the knowledge base.

Pulls structured fashion knowledge relevant to the current query: body type styling,
color theory for skin tone, fabric recommendations for climate, cultural/occasion
rules, budget tier advice.  Also includes a comprehensive embedded fashion
principles corpus distilled from the finetuning guide's 200+ principle categories.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge" / "fashion_knowledge_base.json"

# ═══════════════════════════════════════════════════════════════════════════
# EMBEDDED FASHION PRINCIPLES — distilled from the finetuning guide Phase 1
# These serve as in-context expert knowledge when the KB file is thin
# ═══════════════════════════════════════════════════════════════════════════

BODY_TYPE_PRINCIPLES: dict[str, dict[str, Any]] = {
    "hourglass": {
        "geometry": "WHR < 0.75, balanced shoulder-hip ratio. Natural waist is the narrowest point.",
        "principle": "Accentuate the defined waist. The hourglass already has visual balance — fitted waist garments enhance this.",
        "best_fabrics": ["jersey", "stretch cotton", "silk charmeuse", "georgette"],
        "best_garments": ["wrap dress", "belted kurti", "fitted blouse", "lehenga with defined waist"],
        "saree_draping": "Nivi drape with pallu over shoulder to show waistline. Avoid heavy pleating that hides waist.",
        "avoid": ["boxy cuts", "empire waist", "oversized layers", "drop-waist"],
    },
    "pear": {
        "geometry": "WHR < 0.78, shoulders narrower than hips. Lower body carries more visual weight.",
        "principle": "Widen upper body to balance narrower shoulders. A-line silhouettes create visual equilibrium by flaring from the narrowest point.",
        "best_fabrics": ["structured cotton", "taffeta", "organza (for tops)", "flowy georgette (bottoms)"],
        "best_garments": ["A-line kurta", "boat-neck blouse", "off-shoulder top", "structured blazer", "flared lehenga"],
        "saree_draping": "Keep pallu broad across shoulder to add width. Choose contrast blouse in lighter shade.",
        "avoid": ["clingy fabric on hips", "pencil skirt without long top", "skinny jeans", "horizontal stripes on bottom"],
    },
    "apple": {
        "geometry": "WHR > 0.88, midsection carries most volume. Shoulders and hips may be balanced.",
        "principle": "Draw attention away from midsection. V-necks elongate torso; empire waist defines above the widest point.",
        "best_fabrics": ["flowing fabrics that skim (not cling)", "cotton lawn", "chiffon", "soft crepe"],
        "best_garments": ["empire kurta", "V-neck blouse", "straight-leg trousers", "anarkali", "A-line tunic"],
        "saree_draping": "Pre-stitched or seedha pallu drape. Avoid tight tucking at waist.",
        "avoid": ["wide belts at waist", "clingy jersey tops", "cropped tops", "tucked-in shirts"],
    },
    "rectangle": {
        "geometry": "WHR 0.78-0.88, minimal waist definition. Shoulders and hips roughly equal.",
        "principle": "Create waist illusion through cut, belting, or color-blocking. Peplum/ruffle details add curve definition.",
        "best_fabrics": ["structured fabrics with body", "denim", "brocade", "thick cotton"],
        "best_garments": ["peplum top", "belted dress", "fit-and-flare", "layered outfits", "ruffle details"],
        "saree_draping": "Drape with a thin belt or brooch at waist. Choose printed sarees that create visual breaks.",
        "avoid": ["shapeless shifts", "straight column dresses", "very boxy blazers"],
    },
    "inverted_triangle": {
        "geometry": "SHR > 1.05, broad shoulders relative to hips. Upper body visually dominant.",
        "principle": "Add volume below to balance broad shoulders. Full/flared skirts and wide-leg trousers create proportion.",
        "best_fabrics": ["fluid drape fabrics for tops", "full-body fabrics for skirts", "silk", "chiffon"],
        "best_garments": ["V-neck top", "full skirt", "wide-leg palazzo", "A-line lehenga", "raglan sleeve"],
        "saree_draping": "Nivi drape without pallu pin — let it fall naturally. Avoid heavy shoulder embellishment.",
        "avoid": ["boat necks", "puff sleeves", "heavy shoulder pads", "halter tops"],
    },
}

COLOR_SCIENCE: dict[str, dict[str, Any]] = {
    "very_fair_cool": {
        "best": ["jewel tones (sapphire, emerald, ruby)", "navy", "burgundy", "dusty rose", "silver metallics"],
        "avoid": ["mustard", "orange", "warm brown", "camel"],
        "principle": "Cool undertones reflect cool-wavelength light. Jewel tones create vibrant contrast without washing out pale skin.",
    },
    "fair_warm": {
        "best": ["coral", "peach", "warm red", "olive green", "gold metallics", "teal"],
        "avoid": ["icy pastels", "neon pink", "stark white"],
        "principle": "Warm skin reflects warm wavelengths. Earth tones and warm hues harmonize with golden undertones.",
    },
    "medium_warm": {
        "best": ["mustard", "terracotta", "emerald", "warm red", "gold", "burnt orange"],
        "avoid": ["pastel lavender", "icy blue", "silver"],
        "principle": "Medium warmth can carry saturated warm colors without being overwhelmed. Earthy tones complement olive/golden undertones.",
    },
    "medium_cool": {
        "best": ["royal blue", "purple", "teal", "charcoal", "silver", "berry"],
        "avoid": ["orange", "mustard", "rust"],
        "principle": "Cool medium tones pair with blue-based colors. Silver jewelry over gold.",
    },
    "dusky_warm": {
        "best": ["jewel tones (emerald, deep teal, ruby)", "gold", "burnt orange", "mustard", "bright coral"],
        "avoid": ["pastels (wash out)", "dull browns", "grey"],
        "principle": "High contrast between dusky skin and jewel tones creates visual pop. Bright saturated colors look stunning. Gold jewelry enhances warm undertone.",
    },
    "dusky_cool": {
        "best": ["royal blue", "magenta", "deep purple", "silver", "icy white"],
        "avoid": ["olive", "warm brown", "mustard"],
        "principle": "Cool-toned deep skin radiates with blue-purple spectrum. Silver/platinum metals complement cool undertones.",
    },
    "dark_warm": {
        "best": ["bright yellow", "electric blue", "hot pink", "gold", "emerald", "white"],
        "avoid": ["dull dark colors (navy, dark brown)", "maroon"],
        "principle": "Deep warm skin is enhanced by high-contrast bright colors. Avoid dark-on-dark which reduces vibrance. White and gold create stunning contrast.",
    },
    "dark_cool": {
        "best": ["cobalt blue", "fuchsia", "bright white", "silver", "citrus yellow"],
        "avoid": ["earthy tones", "muted olive", "rust"],
        "principle": "Deep cool skin shines with high-saturation cool-leaning brights. Contrast is key.",
    },
}

FABRIC_CLIMATE: dict[str, dict[str, Any]] = {
    "hot_humid": {
        "best": ["cotton lawn", "linen", "cotton mul", "khadi", "chanderi (cotton-silk)"],
        "avoid": ["polyester", "silk (water stains)", "velvet", "heavy brocade"],
        "principle": "High humidity demands hollow-fiber fabrics (linen absorbs 20% body weight in moisture). Porosity enables evaporative cooling.",
    },
    "hot_dry": {
        "best": ["cotton voile", "lightweight silk", "rayon", "bamboo fabric"],
        "avoid": ["heavy denim", "wool", "thick synthetics"],
        "principle": "Dry heat needs breathable coverage. Loose weaves allow airflow; silk regulates temperature.",
    },
    "mild": {
        "best": ["cotton", "light wool", "silk", "georgette", "crepe"],
        "avoid": ["heavy wool", "thick fleece"],
        "principle": "Mild climates offer maximum fabric freedom. Layer-ready fabrics work best.",
    },
    "cold": {
        "best": ["wool", "pashmina", "heavy silk", "velvet", "tweed", "Kanjeevaram silk"],
        "avoid": ["thin cotton", "chiffon", "net"],
        "principle": "Cold weather needs insulating fibers. Wool traps air in crimped fibers; silk has low thermal conductivity.",
    },
    "monsoon": {
        "best": ["synthetic-cotton blend", "quick-dry fabrics", "dark-colored cottons"],
        "avoid": ["pure silk (water spots)", "suede", "leather", "heavy embroidery"],
        "principle": "Rain demands quick-dry, water-resistant properties. Dark colors hide rain splashes.",
    },
}

CULTURAL_OCCASION: dict[str, dict[str, Any]] = {
    "hindu_wedding": {
        "colors": ["red (auspicious, North India)", "gold", "maroon", "green (South India)"],
        "avoid_colors": ["black", "white (mourning)"],
        "garments": ["Kanjeevaram saree (Tamil)", "Banarasi (UP)", "Paithani (Maharashtra)", "Pochampally (Telangana)", "lehenga choli"],
        "notes": "Red symbolizes prosperity and fertility in North Indian weddings. South Indian brides often wear gold-bordered silk in green/red.",
    },
    "muslim_event": {
        "colors": ["green (sacred)", "white", "royal blue", "gold"],
        "avoid_colors": ["saffron (Hindu connotation in some contexts)"],
        "garments": ["sharara set", "gharara", "salwar kameez", "abaya with embroidery"],
        "notes": "Modest dressing preferred — full sleeves, covered neckline. Jewelry often includes kundan or polki.",
    },
    "christian_event": {
        "colors": ["white (bridal)", "pastels", "ivory", "deep jewel tones"],
        "garments": ["gown", "saree with modern drape", "Indo-Western fusion"],
        "notes": "Western-style gowns common. Kerala Christian brides wear white/cream saree with gold.",
    },
    "sikh_event": {
        "colors": ["red", "hot pink", "royal blue", "gold"],
        "garments": ["lehenga", "sharara", "salwar suit with phulkari dupatta"],
        "notes": "Phulkari embroidery from Punjab is signature. Bright, vibrant colors preferred.",
    },
    "formal_corporate": {
        "colors": ["navy", "charcoal", "white", "subtle pastels"],
        "garments": ["blazer + trousers", "pencil skirt + blouse", "formal kurta (men)", "saree with minimal embellishment"],
        "notes": "Power dressing: fitted silhouettes signal confidence. Monochrome or 2-color palette max.",
    },
    "casual": {
        "colors": ["any"],
        "garments": ["kurti + jeans", "t-shirt + chinos", "maxi dress", "cotton saree"],
        "notes": "Comfort-first but intentional. Well-fitted basics over oversized fast fashion.",
    },
    "festival": {
        "colors": ["bright, saturated colors", "gold accents"],
        "garments": ["ethnic wear", "Indo-Western fusion", "heavily embellished pieces"],
        "notes": "Festivals celebrate color. Heavy embroidery and statement jewelry appropriate.",
    },
}


@lru_cache(maxsize=1)
def _load_knowledge() -> dict:
    """Load fashion knowledge base from JSON file (cached)."""
    if KNOWLEDGE_PATH.is_file():
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Failed to load knowledge base: %s", exc)
    return {}


def retrieve(
    *,
    body_type: str | None = None,
    skin_tone: str | None = None,
    climate: str | None = None,
    occasion: str | None = None,
    culture: str | None = None,
    budget_inr: float | None = None,
    garment_keywords: list[str] | None = None,
    user_message: str = "",
) -> dict[str, Any]:
    """Retrieve all relevant fashion knowledge for the given context.

    Returns a structured dict with knowledge blocks ready for LLM injection.
    """
    kb = _load_knowledge()
    result: dict[str, Any] = {}

    # 1. Body type styling knowledge
    if body_type:
        bt_key = body_type.lower().replace(" ", "_").replace("-", "_")
        embedded = BODY_TYPE_PRINCIPLES.get(bt_key)
        kb_bt = kb.get("body_type_guide", {}).get(bt_key, {})
        if embedded:
            result["body_type_knowledge"] = {
                **embedded,
                **({"kb_extra": kb_bt} if kb_bt else {}),
            }

    # 2. Color science for skin tone
    if skin_tone:
        tone_key = skin_tone.lower().replace(" ", "_").replace("-", "_")
        # Try exact match first, then partial
        color_info = COLOR_SCIENCE.get(tone_key)
        if not color_info:
            for k, v in COLOR_SCIENCE.items():
                if any(part in tone_key for part in k.split("_")):
                    color_info = v
                    break
        if color_info:
            result["color_science"] = color_info

        # Also pull from KB
        kb_color = kb.get("color_theory", {}).get("skin_tone_guide", {})
        for tone_label in ["fair", "wheatish", "dusky", "dark"]:
            if tone_label in (skin_tone or "").lower():
                kb_tone = kb_color.get(tone_label, {})
                if kb_tone:
                    result.setdefault("color_science", {})["kb_extra"] = kb_tone
                break

    # 3. Fabric for climate
    if climate:
        climate_key = climate.lower().replace(" ", "_")
        # Map city climates to categories
        city_climate_map = {
            "chennai": "hot_humid", "mumbai": "hot_humid", "kolkata": "hot_humid",
            "kochi": "hot_humid", "singapore": "hot_humid",
            "delhi": "hot_dry", "jaipur": "hot_dry", "hyderabad": "hot_dry",
            "dubai": "hot_dry",
            "bangalore": "mild", "pune": "mild",
            "shimla": "cold", "london": "cold",
            "monsoon": "monsoon",
        }
        for city, cat in city_climate_map.items():
            if city in climate_key:
                result["fabric_climate"] = FABRIC_CLIMATE.get(cat, {})
                result["fabric_climate"]["detected_climate"] = cat
                break
        if "fabric_climate" not in result:
            for cat, info in FABRIC_CLIMATE.items():
                if cat in climate_key:
                    result["fabric_climate"] = {**info, "detected_climate": cat}
                    break

    # 4. Cultural / occasion knowledge
    occasion_key = (occasion or "").lower()
    culture_key = (culture or "").lower()
    msg_lower = user_message.lower()

    for occ_name, occ_info in CULTURAL_OCCASION.items():
        if any(part in occasion_key or part in msg_lower for part in occ_name.split("_")):
            result["cultural_occasion"] = {**occ_info, "matched_occasion": occ_name}
            break

    # 5. Budget tier
    if budget_inr:
        budget = float(budget_inr)
        kb_tiers = kb.get("budget_tiers", {})
        tier_ranges = [
            ("ultra_budget", 0, 2000),
            ("budget", 2000, 5000),
            ("mid_range", 5000, 10000),
            ("premium", 10000, 25000),
            ("luxury", 25000, 100000),
        ]
        for tier_name, lo, hi in tier_ranges:
            if lo <= budget < hi:
                result["budget_tier"] = {
                    "tier": tier_name,
                    "range_inr": f"₹{lo:,}-{hi:,}",
                    "advice": _budget_advice(tier_name),
                    **(kb_tiers.get(tier_name, {})),
                }
                break

    # 6. Garment-specific knowledge from KB
    if garment_keywords:
        kb_tailoring = kb.get("tailoring_guide", {})
        for kw in garment_keywords:
            kw_lower = kw.lower()
            for garment_key, info in kb_tailoring.items():
                if kw_lower in garment_key:
                    result.setdefault("garment_knowledge", []).append(
                        {**info, "garment": garment_key}
                    )
                    break

    # 7. Regional fashion from KB
    kb_regional = kb.get("regional_fashion", {})
    region_hints = {
        "tamil": "south_india", "telugu": "south_india", "south": "south_india",
        "kanjeevaram": "south_india", "pochampally": "south_india",
        "north": "north_india", "banarasi": "north_india", "lucknow": "north_india",
        "bengali": "eastern_india", "kolkata": "eastern_india",
        "gujarati": "western_india", "rajasthani": "western_india",
    }
    combined = f"{msg_lower} {occasion_key} {climate or ''}"
    for hint, region in region_hints.items():
        if hint in combined:
            reg_info = kb_regional.get(region, {})
            if reg_info:
                result["regional_fashion"] = {**reg_info, "region": region}
            break

    return result


def _budget_advice(tier: str) -> str:
    """Tier-specific shopping and value advice."""
    advice = {
        "ultra_budget": "Focus on 1-2 key pieces. Shop end-of-season sales. Cotton basics stretch budget furthest.",
        "budget": "Invest in one quality ethnic piece + style with existing basics. Street markets for accessories.",
        "mid_range": "Good range for quality ethnic wear. Branded options available. Invest in fabric quality over embellishment.",
        "premium": "Custom tailoring viable. Designer labels accessible. Focus on timeless pieces with high cost-per-wear.",
        "luxury": "Full custom couture possible. Choose signature handloom textiles. Investment pieces that last decades.",
    }
    return advice.get(tier, "")


def format_for_llm(knowledge: dict[str, Any]) -> str:
    """Format retrieved knowledge into a structured context block for LLM injection."""
    if not knowledge:
        return ""

    sections: list[str] = []

    if "body_type_knowledge" in knowledge:
        bt = knowledge["body_type_knowledge"]
        sections.append(
            f"BODY TYPE STYLING:\n"
            f"  Geometry: {bt.get('geometry', '')}\n"
            f"  Principle: {bt.get('principle', '')}\n"
            f"  Best fabrics: {', '.join(bt.get('best_fabrics', []))}\n"
            f"  Best garments: {', '.join(bt.get('best_garments', []))}\n"
            f"  Saree tip: {bt.get('saree_draping', '')}\n"
            f"  Avoid: {', '.join(bt.get('avoid', []))}"
        )

    if "color_science" in knowledge:
        cs = knowledge["color_science"]
        sections.append(
            f"COLOR SCIENCE:\n"
            f"  Best colors: {', '.join(cs.get('best', []))}\n"
            f"  Avoid colors: {', '.join(cs.get('avoid', []))}\n"
            f"  Principle: {cs.get('principle', '')}"
        )

    if "fabric_climate" in knowledge:
        fc = knowledge["fabric_climate"]
        sections.append(
            f"FABRIC FOR CLIMATE ({fc.get('detected_climate', 'unknown')}):\n"
            f"  Best: {', '.join(fc.get('best', []))}\n"
            f"  Avoid: {', '.join(fc.get('avoid', []))}\n"
            f"  Why: {fc.get('principle', '')}"
        )

    if "cultural_occasion" in knowledge:
        co = knowledge["cultural_occasion"]
        sections.append(
            f"CULTURAL/OCCASION ({co.get('matched_occasion', '')}):\n"
            f"  Colors: {', '.join(co.get('colors', []))}\n"
            f"  Avoid colors: {', '.join(co.get('avoid_colors', []))}\n"
            f"  Garments: {', '.join(co.get('garments', []))}\n"
            f"  Notes: {co.get('notes', '')}"
        )

    if "budget_tier" in knowledge:
        bt = knowledge["budget_tier"]
        sections.append(
            f"BUDGET ({bt.get('tier', '')}, {bt.get('range_inr', '')}):\n"
            f"  {bt.get('advice', '')}"
        )

    if "regional_fashion" in knowledge:
        rf = knowledge["regional_fashion"]
        sections.append(
            f"REGIONAL ({rf.get('region', '')}):\n"
            f"  Signature: {rf.get('signature_garments', '')}\n"
            f"  Jewelry: {rf.get('jewelry', '')}"
        )

    if not sections:
        return ""

    return "\n\n═══ FASHION EXPERT KNOWLEDGE (retrieved, factual) ═══\n" + "\n\n".join(sections) + "\n═══════════════════════════════════════════════════\n"
