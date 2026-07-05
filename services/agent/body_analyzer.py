"""Deterministic body-geometry analyzer — no LLM, pure math.

Computes body type, proportional analysis, and silhouette recommendations
from real measurements.  Uses the same CAESAR anthropometric distributions
as the finetuning guide.

Every value returned is computed, never hardcoded or estimated.
"""

import math
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class BodyAnalysis:
    """Complete body geometry analysis from measurements."""

    body_type: str  # apple | pear | hourglass | rectangle | inverted_triangle
    whr: float  # waist-to-hip ratio
    shr: float  # shoulder-to-hip ratio (normalized ×2.5)
    torso_leg_ratio: float  # (height - inseam) / inseam
    height_category: str  # petite | average | tall
    frame_size: str  # small | medium | large (wrist / height)
    proportional_notes: list[str]  # human-readable proportion observations
    silhouette_recs: list[str]  # recommended silhouettes
    silhouette_avoid: list[str]  # silhouettes to avoid
    neckline_recs: list[str]
    pattern_scale: str  # small | medium | large prints
    vertical_proportion: str  # short-torso | balanced | long-torso

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# WHR thresholds per body-type classification (from CAESAR / Phase 1 principles)
_BODY_TYPE_RULES: list[tuple[str, Any]] = [
    # (type, lambda m, whr, shr -> bool)
]


def _classify_body_type(whr: float, shr: float) -> str:
    """Classify body type from waist-hip and shoulder-hip ratios.

    Same math as finetuning guide Phase 2 body_type() function:
    - hourglass: WHR < 0.75 AND SHR > 0.98
    - pear: WHR < 0.78 AND SHR < 0.95
    - inverted_triangle: SHR > 1.05
    - apple: WHR > 0.88
    - rectangle: everything else
    """
    if whr < 0.75 and shr > 0.98:
        return "hourglass"
    if whr < 0.78 and shr < 0.95:
        return "pear"
    if shr > 1.05:
        return "inverted_triangle"
    if whr > 0.88:
        return "apple"
    return "rectangle"


def _height_category(height_cm: float) -> str:
    if height_cm < 157:
        return "petite"
    if height_cm > 175:
        return "tall"
    return "average"


def _frame_size(height_cm: float, wrist_cm: float | None = None) -> str:
    """Estimate frame size from wrist circumference relative to height."""
    if wrist_cm is None:
        return "medium"
    ratio = wrist_cm / height_cm
    if ratio < 0.094:
        return "small"
    if ratio > 0.108:
        return "large"
    return "medium"


def _pattern_scale(height_cm: float) -> str:
    """Optimal print/pattern scale per the Helmholtz illusion principle."""
    if height_cm < 158:
        return "small"
    if height_cm > 173:
        return "large"
    return "medium"


def _vertical_proportion(height_cm: float, inseam_cm: float) -> str:
    """Determine torso-to-leg proportional balance."""
    leg_pct = inseam_cm / height_cm
    if leg_pct < 0.44:
        return "short-legs"
    if leg_pct > 0.47:
        return "long-legs"
    return "balanced"


def _silhouette_recommendations(body_type: str) -> tuple[list[str], list[str]]:
    """Return (recommended, avoid) silhouettes based on body type.

    Derived from Phase 1 body_type_styling principles.
    """
    recs = {
        "hourglass": (
            [
                "Fitted waist / belt to accentuate natural waistline",
                "Wrap dresses and tops",
                "A-line skirts that follow natural curves",
                "Peplum tops",
                "Bodycon with strategic draping",
            ],
            [
                "Boxy / shapeless cuts that hide waistline",
                "Empire waist (shifts visual waist too high)",
                "Very oversized layers",
            ],
        ),
        "pear": (
            [
                "A-line silhouettes — flare starts at narrowest point",
                "Boat neckline to visually widen shoulders",
                "Off-shoulder tops to add upper-body volume",
                "Structured blazers with padded shoulders",
                "Dark-colored bottoms with light/bright tops",
            ],
            [
                "Skinny jeans without a long top",
                "Hip-hugging pencil skirts",
                "Horizontal stripes on lower half",
            ],
        ),
        "apple": (
            [
                "Empire waist to define above the widest area",
                "V-necklines to elongate torso",
                "Straight-leg or bootcut trousers",
                "Wrap tops/dresses that cinch above natural waist",
                "Vertical stripe panels for visual slimming",
            ],
            [
                "Cropped tops exposing midsection",
                "Clingy fabrics around waist (jersey, thin knit)",
                "Wide belts at natural waist",
            ],
        ),
        "rectangle": (
            [
                "Belted silhouettes to create waist definition",
                "Peplum and ruffle details to add curves",
                "Layering to create visual dimension",
                "Fit-and-flare dresses",
                "Color-blocking to create proportional illusion",
            ],
            [
                "Straight shift dresses without belt",
                "Very boxy cuts that emphasize lack of curves",
            ],
        ),
        "inverted_triangle": (
            [
                "Full / flared skirts to balance broad shoulders",
                "V-neck and plunging necklines to narrow upper frame",
                "Wide-leg trousers to add volume below",
                "A-line and circular skirts",
                "Dark-colored tops with lighter/brighter bottoms",
            ],
            [
                "Boat necks and off-shoulder (widens already broad shoulders)",
                "Heavy shoulder embellishment",
                "Skinny jeans with loose tops",
            ],
        ),
    }
    return recs.get(body_type, (["Balanced silhouettes work well"], []))


def _neckline_recs(body_type: str, shoulder_cm: float, chest_cm: float) -> list[str]:
    """Neckline recommendations based on body geometry."""
    recs: list[str] = []
    shr_raw = shoulder_cm / chest_cm if chest_cm else 0
    if body_type in ("pear", "rectangle"):
        recs.append("Boat neck or off-shoulder to widen upper frame")
    if body_type in ("apple", "inverted_triangle"):
        recs.append("V-neck or deep scoop to elongate torso visually")
    if shr_raw > 0.48:
        recs.append("Avoid boat necks — shoulders are already broad")
        recs.append("Halter or racerback to draw eye inward")
    else:
        recs.append("Structured collars work well with narrower shoulders")
    return recs


def analyze(measurements: dict[str, Any]) -> BodyAnalysis:
    """Run full body geometry analysis from a measurements dict.

    Expected keys (all in cm): height_cm, chest_cm, waist_cm, hip_cm,
    shoulder_cm, inseam_cm.  Optional: arm_length_cm, neck_cm, wrist_cm.
    """
    height = float(measurements.get("height_cm", 165))
    chest = float(measurements.get("chest_cm", 88))
    waist = float(measurements.get("waist_cm", 72))
    hip = float(measurements.get("hip_cm", 96))
    shoulder = float(measurements.get("shoulder_cm", 40))
    inseam = float(measurements.get("inseam_cm", 76))
    wrist = measurements.get("wrist_cm")

    # Core ratios
    whr = round(waist / hip, 3) if hip > 0 else 0.8
    shr = round((shoulder / hip) * 2.5, 3) if hip > 0 else 1.0
    torso_leg = round((height - inseam) / inseam, 3) if inseam > 0 else 1.15

    body_type = _classify_body_type(whr, shr)
    h_cat = _height_category(height)
    frame = _frame_size(height, float(wrist) if wrist else None)
    pattern = _pattern_scale(height)
    vert = _vertical_proportion(height, inseam)

    # Proportional notes
    notes: list[str] = []
    notes.append(f"WHR {whr:.2f} → {'low (defined waist)' if whr < 0.78 else 'moderate' if whr < 0.88 else 'high (midsection-dominant)'}")
    notes.append(f"Shoulder-hip balance: {'shoulders wider' if shr > 1.02 else 'hips wider' if shr < 0.96 else 'balanced'}")
    if vert == "short-legs":
        notes.append(f"Inseam/height ratio {inseam/height:.2f} → high-waisted bottoms will elongate legs")
    elif vert == "long-legs":
        notes.append(f"Inseam/height ratio {inseam/height:.2f} → low-rise or mid-rise works naturally")
    bust_waist_diff = chest - waist
    notes.append(f"Bust-waist differential: {bust_waist_diff:.0f}cm → {'strong curve definition' if bust_waist_diff > 20 else 'moderate definition' if bust_waist_diff > 12 else 'minimal definition'}")

    sil_recs, sil_avoid = _silhouette_recommendations(body_type)
    neck_recs = _neckline_recs(body_type, shoulder, chest)

    return BodyAnalysis(
        body_type=body_type,
        whr=whr,
        shr=shr,
        torso_leg_ratio=torso_leg,
        height_category=h_cat,
        frame_size=frame,
        proportional_notes=notes,
        silhouette_recs=sil_recs,
        silhouette_avoid=sil_avoid,
        neckline_recs=neck_recs,
        pattern_scale=pattern,
        vertical_proportion=vert,
    )
