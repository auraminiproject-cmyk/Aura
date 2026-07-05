"""Validates body measurements before they hit the Body Analyzer.
Ensures biological realism and prevents absurd input from breaking calculations.
"""

from typing import Any

def validate_measurements(body_profile: dict[str, Any] | None) -> list[str]:
    """Check if the provided body profile has realistic measurements.

    Returns a list of warning strings for anything that looks impossible or missing.
    """
    if not body_profile:
        return []  # Can't validate if missing

    warnings = []
    
    # Standard adult human bounds (in cm)
    BOUNDS = {
        "height": (120, 220),
        "chest": (60, 160),
        "waist": (50, 150),
        "hip": (60, 160),
        "shoulder": (30, 80),
        "inseam": (50, 110),
    }

    # Ensure measurements are valid floats
    parsed_profile = {}
    for key, val in body_profile.items():
        if key.startswith("_"):
            continue  # Ignore metadata like _front_photo_b64
        try:
            parsed_profile[key] = float(val)
        except (ValueError, TypeError):
            warnings.append(f"Measurement '{key}' must be a number.")

    # Check bounds
    for key, (min_val, max_val) in BOUNDS.items():
        if key in parsed_profile:
            val = parsed_profile[key]
            if val < min_val:
                warnings.append(f"{key.capitalize()} ({val} cm) is unusually small. Please verify.")
            elif val > max_val:
                warnings.append(f"{key.capitalize()} ({val} cm) is unusually large. Please verify.")
        else:
            # We don't strictly warn for missing keys here unless we want to enforce it, 
            # but usually it's better to let the Reasoner know what's missing if critical.
            pass

    # Basic proportional checks
    if "chest" in parsed_profile and "waist" in parsed_profile:
        if parsed_profile["waist"] > parsed_profile["chest"] * 1.5:
            warnings.append("Waist seems disproportionately larger than chest. Please verify.")
            
    return warnings
