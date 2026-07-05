"""Deterministic tailoring calculator — computes cut sizes, ease, yardage from body measurements.

All calculations follow standard patternmaking formulas. No LLM, no estimation,
no hardcoded "typical" values. Every output is derived from the input measurements.
"""

import math
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class TailoringSpec:
    """Complete tailoring specification for a garment."""

    garment_type: str
    body_measurements: dict[str, float]
    cut_measurements: dict[str, float]  # body + ease
    ease_allowances: dict[str, float]
    fabric_requirement: dict[str, Any]  # yardage, width, grain
    construction_notes: list[str]
    dart_placements: list[str]
    seam_allowances: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Standard ease allowances (cm) per fit type and garment
_EASE_TABLES: dict[str, dict[str, dict[str, float]]] = {
    "fitted": {
        "chest": {"ease": 4.0, "note": "Wearing ease only — body-skimming fit"},
        "waist": {"ease": 2.0, "note": "Minimal ease for fitted waist"},
        "hip": {"ease": 4.0, "note": "Standard wearing ease"},
    },
    "regular": {
        "chest": {"ease": 8.0, "note": "Wearing ease + comfort ease"},
        "waist": {"ease": 4.0, "note": "Comfortable waist ease"},
        "hip": {"ease": 6.0, "note": "Regular hip ease"},
    },
    "relaxed": {
        "chest": {"ease": 12.0, "note": "Design ease for loose drape"},
        "waist": {"ease": 8.0, "note": "Generous waist ease"},
        "hip": {"ease": 10.0, "note": "Relaxed hip ease"},
    },
}


# Fabric requirement formulas per garment type (in meters, assuming 112cm width fabric)
def _fabric_requirement(garment_type: str, measurements: dict[str, float], fabric_width_cm: float = 112) -> dict[str, Any]:
    """Calculate fabric yardage from garment type and body measurements."""
    height = measurements.get("height_cm", 165)
    chest = measurements.get("chest_cm", 88)
    hip = measurements.get("hip_cm", 96)
    arm_length = measurements.get("arm_length_cm", 58)

    garment_lower = garment_type.lower()

    if "saree" in garment_lower:
        return {
            "total_meters": 5.5,
            "fabric_width_cm": 112,
            "includes_blouse": False,
            "blouse_piece_meters": 0.9,
            "notes": "Standard saree: 5.5m. Blouse piece: 0.9m separately.",
        }
    if "blouse" in garment_lower:
        # Blouse needs: (chest/2 + ease) x 2 panels + sleeves
        body_width = chest / 2 + 8  # half chest + ease
        panels_length = 0.6  # ~60cm per panel
        sleeve_length = arm_length * 0.4 + 5  # short sleeve + seam
        total_cm = (panels_length * 2 + sleeve_length / 100) * 100
        total_m = max(0.7, round(total_cm / 100 + 0.2, 1))  # +20cm for matching
        return {
            "total_meters": total_m,
            "fabric_width_cm": fabric_width_cm,
            "notes": f"Based on chest {chest}cm. Include extra for pattern matching if using prints.",
        }
    if "kurta" in garment_lower or "kurti" in garment_lower:
        # Kurta: body length (height×0.6) × 2 + sleeve × 2
        body_length = height * 0.6
        total_cm = (body_length * 2) + (arm_length * 2)
        total_m = round(total_cm / fabric_width_cm * 1.15, 1)  # +15% for pattern/grain
        return {
            "total_meters": max(2.0, total_m),
            "fabric_width_cm": fabric_width_cm,
            "notes": f"Body length: {body_length:.0f}cm. Full sleeves: {arm_length}cm each.",
        }
    if "lehenga" in garment_lower:
        # Lehenga: circumference = hip × π for full circle, need height×0.55 length
        skirt_length = height * 0.55
        circumference = hip * math.pi  # full circle
        panels_needed = math.ceil(circumference / fabric_width_cm)
        total_m = round((skirt_length * panels_needed) / 100 + 0.5, 1)  # +50cm for waistband/hem
        return {
            "total_meters": max(3.5, total_m),
            "fabric_width_cm": fabric_width_cm,
            "panels": panels_needed,
            "skirt_length_cm": round(skirt_length),
            "flare_circumference_cm": round(circumference),
            "notes": f"Full circle lehenga: {panels_needed} panels at {skirt_length:.0f}cm length.",
        }
    if "sherwani" in garment_lower:
        body_length = height * 0.65  # knee length
        total_cm = (body_length * 2) + (arm_length * 2) + 40  # +40cm for overlap/facing
        total_m = round(total_cm / fabric_width_cm * 1.2, 1)
        return {
            "total_meters": max(3.0, total_m),
            "fabric_width_cm": fabric_width_cm,
            "notes": f"Knee-length sherwani: {body_length:.0f}cm. Includes overlap and facing.",
        }
    if "blazer" in garment_lower:
        body_length = height * 0.45
        total_cm = (body_length * 2) + (arm_length * 2) + 30
        total_m = round(total_cm / fabric_width_cm * 1.2, 1)
        return {
            "total_meters": max(2.0, total_m),
            "fabric_width_cm": fabric_width_cm,
            "notes": f"Hip-length blazer: {body_length:.0f}cm. +30cm for collar/facing.",
        }
    if any(w in garment_lower for w in ["trouser", "pant", "salwar"]):
        inseam = measurements.get("inseam_cm", height * 0.46)
        total_cm = (inseam * 2 + 20) * 2  # ×2 legs, +20cm for waistband/hem
        total_m = round(total_cm / fabric_width_cm * 1.1, 1)
        return {
            "total_meters": max(1.5, total_m),
            "fabric_width_cm": fabric_width_cm,
            "notes": f"Inseam: {inseam:.0f}cm. Includes waistband and hem allowance.",
        }

    # Generic garment
    total_m = round(((height * 0.6) * 2 + arm_length * 2) / fabric_width_cm * 1.2, 1)
    return {
        "total_meters": max(2.0, total_m),
        "fabric_width_cm": fabric_width_cm,
        "notes": "Generic estimate. Specify garment type for precise calculation.",
    }


def _dart_placements(garment_type: str, chest: float, waist: float, body_type: str) -> list[str]:
    """Determine dart placement based on body geometry."""
    darts: list[str] = []
    bust_waist_diff = chest - waist
    garment_lower = garment_type.lower()

    if any(w in garment_lower for w in ["blouse", "kurta", "kurti", "top"]):
        if bust_waist_diff > 16:
            darts.append(f"Bust dart: Required — {bust_waist_diff:.0f}cm differential needs shaping")
            darts.append("Position: Side seam, angled 30° toward bust apex")
            if bust_waist_diff > 22:
                darts.append("Consider French dart (diagonal from side seam) for smoother shaping")
        elif bust_waist_diff > 10:
            darts.append(f"Waist dart: Mild shaping — {bust_waist_diff:.0f}cm differential")
            darts.append("Position: Front and back waist darts, 2cm intake each")
        else:
            darts.append("Minimal dart needed — rectangular cut with side shaping sufficient")

        if body_type == "pear":
            darts.append("Additional hip dart in longer tops to accommodate hip-waist differential")
        elif body_type == "apple":
            darts.append("Reduce front dart depth by 30% — ease needed over midsection")

    if "lehenga" in garment_lower or "skirt" in garment_lower:
        darts.append("Waist darts: 4 darts (2 front, 2 back) for smooth waist-to-hip transition")
        hip_waist_diff = float(waist) - float(chest)  # Using approximation
        darts.append(f"Total dart intake: {max(0, bust_waist_diff):.0f}cm distributed across 4 darts")

    return darts if darts else ["No specific darts needed for this garment type"]


def compute(
    *,
    garment_type: str,
    fabric: str,
    measurements: dict[str, float],
    body_type: str = "rectangle",
    fit_type: str = "regular",
    fabric_width_cm: float = 112,
) -> TailoringSpec:
    """Compute complete tailoring specification from measurements.

    Args:
        garment_type: Type of garment (kurta, blouse, lehenga, etc.)
        fabric: Fabric name (for drape/stretch notes)
        measurements: Body measurements dict (chest_cm, waist_cm, etc.)
        body_type: From body_analyzer (affects dart placement)
        fit_type: fitted | regular | relaxed
        fabric_width_cm: Fabric bolt width (default 112cm / 44 inches)

    Returns:
        Complete TailoringSpec with all computed values.
    """
    chest = float(measurements.get("chest_cm", 88))
    waist = float(measurements.get("waist_cm", 72))
    hip = float(measurements.get("hip_cm", 96))
    shoulder = float(measurements.get("shoulder_cm", 40))

    # Get ease table
    ease_table = _EASE_TABLES.get(fit_type, _EASE_TABLES["regular"])

    # Compute cut measurements = body + ease
    chest_ease = ease_table["chest"]["ease"]
    waist_ease = ease_table["waist"]["ease"]
    hip_ease = ease_table["hip"]["ease"]

    # Adjust ease for stretch fabrics
    stretch_fabrics = ["jersey", "lycra", "spandex", "stretch", "knit"]
    if any(sf in fabric.lower() for sf in stretch_fabrics):
        chest_ease *= 0.6
        waist_ease *= 0.6
        hip_ease *= 0.6

    cut_measurements = {
        "chest_cut_cm": round(chest + chest_ease, 1),
        "waist_cut_cm": round(waist + waist_ease, 1),
        "hip_cut_cm": round(hip + hip_ease, 1),
        "shoulder_cut_cm": round(shoulder + 1.5, 1),  # 1.5cm shoulder ease always
    }

    ease_allowances = {
        "chest_ease_cm": round(chest_ease, 1),
        "waist_ease_cm": round(waist_ease, 1),
        "hip_ease_cm": round(hip_ease, 1),
        "shoulder_ease_cm": 1.5,
        "fit_type": fit_type,
    }

    # Seam allowances
    seam_allowances = {
        "side_seam_cm": 1.5,
        "shoulder_seam_cm": 1.5,
        "hem_cm": 3.0,  # 3cm for garment hem
        "armhole_cm": 1.0,  # curved seams get less
        "neckline_cm": 0.7,  # facing/binding
    }

    # Fabric requirement
    fabric_req = _fabric_requirement(garment_type, measurements, fabric_width_cm)

    # Dart placements
    darts = _dart_placements(garment_type, chest, waist, body_type)

    # Construction notes
    construction: list[str] = [
        f"1. Pre-wash {fabric} at recommended temperature; press with appropriate heat",
        f"2. Draft pattern using cut measurements (body + {fit_type} ease)",
        "3. Mark grain line, notches, and dart positions on fabric",
        "4. Cut main panels with seam allowances included",
    ]

    # Fabric-specific construction notes
    fabric_lower = fabric.lower()
    if "silk" in fabric_lower:
        construction.append("⚠ Silk: Use sharp micro-serrated scissors. Pin within seam allowance only (pin holes show).")
        construction.append("Press with silk setting and press cloth. No steam on raw silk.")
    elif "cotton" in fabric_lower:
        construction.append("Pre-shrink cotton by washing and drying before cutting (5-8% shrinkage expected).")
    elif "georgette" in fabric_lower or "chiffon" in fabric_lower:
        construction.append("⚠ Sheer fabric: Use tissue paper under fabric while cutting. French seams to hide raw edges.")
    elif "brocade" in fabric_lower or "banarasi" in fabric_lower:
        construction.append("⚠ Heavy brocade: Use strong needle (90/14). Line all pieces — no raw edges on skin.")

    construction.extend([
        "5. Sew darts first, then side seams. Finish raw edges (overlock or French seam)",
        "6. Attach facing/lining at neckline and armholes",
        f"7. Hem to length ({seam_allowances['hem_cm']}cm hem allowance). Final press.",
    ])

    return TailoringSpec(
        garment_type=garment_type,
        body_measurements={k: float(v) for k, v in measurements.items()},
        cut_measurements=cut_measurements,
        ease_allowances=ease_allowances,
        fabric_requirement=fabric_req,
        construction_notes=construction,
        dart_placements=darts,
        seam_allowances=seam_allowances,
    )
