"""Body reconstruction — VLM body analysis → HF pose → measurement extraction → parametric mesh.

Production pipeline:
  Tier 0: VLM (Groq Vision) analyzes body photo → extracts build type + proportions → 88% confidence
  Tier 1: HF DETR bounding box → body width ratio → 75% confidence
  Tier 2: Image dimension heuristic → 65% confidence
"""

import base64
import json
import logging
import math
import re
import struct
from dataclasses import dataclass
from io import BytesIO

import httpx

from PIL import Image

from services.api.core.config import get_settings
from services.api.core.resilience import groq_breaker, hf_breaker

logger = logging.getLogger(__name__)

# Anthropometric ratio tables (relative to height)
# Source: standard anthropometric proportions used in garment construction
ANTHROPOMETRIC_RATIOS = {
    "shoulder_width": 0.259,   # shoulder breadth / height
    "chest": 0.527,            # chest circumference / height
    "waist": 0.432,            # waist circumference / height
    "hip": 0.542,              # hip circumference / height
    "inseam": 0.470,           # inseam length / height
    "arm_length": 0.330,       # arm length (shoulder to wrist) / height
    "torso_length": 0.300,     # torso length / height
    "neck": 0.214,             # neck circumference / height
}

# Build-type multipliers for adjusting base ratios
BUILD_ADJUSTMENTS = {
    "slim": {
        "shoulder_width": 0.94, "chest": 0.90, "waist": 0.85,
        "hip": 0.90, "neck": 0.92, "inseam": 1.02, "arm_length": 1.0, "torso_length": 1.0,
    },
    "average": {
        "shoulder_width": 1.0, "chest": 1.0, "waist": 1.0,
        "hip": 1.0, "neck": 1.0, "inseam": 1.0, "arm_length": 1.0, "torso_length": 1.0,
    },
    "athletic": {
        "shoulder_width": 1.08, "chest": 1.06, "waist": 0.92,
        "hip": 0.97, "neck": 1.04, "inseam": 1.0, "arm_length": 1.01, "torso_length": 1.0,
    },
    "broad": {
        "shoulder_width": 1.10, "chest": 1.12, "waist": 1.10,
        "hip": 1.08, "neck": 1.06, "inseam": 0.98, "arm_length": 0.99, "torso_length": 1.0,
    },
    "plus": {
        "shoulder_width": 1.06, "chest": 1.18, "waist": 1.22,
        "hip": 1.16, "neck": 1.10, "inseam": 0.97, "arm_length": 0.98, "torso_length": 1.0,
    },
    "hourglass": {
        "shoulder_width": 1.02, "chest": 1.06, "waist": 0.88,
        "hip": 1.08, "neck": 0.98, "inseam": 1.0, "arm_length": 1.0, "torso_length": 1.0,
    },
    "pear": {
        "shoulder_width": 0.95, "chest": 0.96, "waist": 0.98,
        "hip": 1.12, "neck": 0.96, "inseam": 0.99, "arm_length": 1.0, "torso_length": 1.0,
    },
}

VLM_BODY_PROMPT = """You are a professional body measurement estimator for a fashion tailoring app.

Analyze this full-body photo carefully. You MUST respond with ONLY this exact JSON format, no other text:

{
  "build_type": "<one of: slim, average, athletic, broad, plus, hourglass, pear>",
  "shoulder_ratio": <float 0.85-1.15, how wide shoulders appear relative to average>,
  "chest_ratio": <float 0.85-1.20, chest size relative to average>,
  "waist_ratio": <float 0.80-1.25, waist size relative to average>,
  "hip_ratio": <float 0.85-1.20, hip size relative to average>,
  "limb_length": "<one of: short, average, long>",
  "neck_thickness": "<one of: thin, average, thick>",
  "torso_proportion": "<one of: short_torso, average, long_torso>",
  "gender_presentation": "<one of: masculine, feminine, neutral>",
  "estimated_weight_kg": <int, rough estimate>,
  "notes": "<brief 1-line observation about body proportions>"
}

Rules:
- Be precise. These ratios drive real garment cutting measurements.
- shoulder_ratio 1.0 = average person. 1.10 = noticeably broad shoulders.
- waist_ratio 1.0 = average. 0.85 = very slim waist. 1.20 = larger waist.
- Look at actual visible proportions, not assumptions.
- If the photo doesn't show a full body, estimate conservatively and note it."""


@dataclass
class BodyReconstructionResult:
    glb_base64: str
    smplx_params: dict
    confidence: float
    measurements: dict


async def reconstruct_body(
    front_image: bytes,
    side_image: bytes | None = None,
    *,
    height_cm: float | None = None,
) -> BodyReconstructionResult:
    """Body reconstruction pipeline: validate → analyze → estimate measurements → mesh.

    Tier 0: VLM (Groq Vision) for precise body shape analysis → 88% confidence.
    Tier 1: HF DETR bounding box → body width ratio → 75% confidence.
    Tier 2: Image dimension heuristic → 65% confidence.

    Args:
        front_image: Front photo bytes.
        side_image: Optional side photo bytes.
        height_cm: User-provided height in cm. If None, estimated from image.
    """
    for label, img_bytes in (("front", front_image), ("side", side_image or front_image)):
        _validate_image(img_bytes, label)

    settings = get_settings()
    measurements = None
    confidence = 0.5

    # Tier 0: VLM body analysis (Groq Vision — most precise)
    if settings.groq_api_key and groq_breaker.current_state != "open":
        try:
            measurements, confidence = await _vlm_body_analysis(
                front_image, settings, height_cm=height_cm,
            )
            logger.info("VLM body analysis succeeded, confidence=%.2f", confidence)
        except Exception as exc:
            logger.warning("VLM body analysis failed: %s", exc)

    # Tier 1: HF Inference API for body pose estimation
    if not measurements:
        if settings.huggingface_api_key and hf_breaker.current_state != "open":
            try:
                measurements, confidence = await _hf_body_analysis(
                    front_image, settings, height_cm=height_cm,
                )
            except Exception as exc:
                logger.warning("HF body analysis failed: %s", exc)

    # Tier 2: Image-based heuristic estimation
    if not measurements:
        measurements, confidence = _image_heuristic_measurements(
            front_image, height_cm=height_cm,
        )

    # Build SMPL-X params from measurements
    smplx = _measurements_to_smplx(measurements)

    # Generate parametric body mesh from measurements
    glb_bytes = _parametric_glb_from_measurements(measurements)

    return BodyReconstructionResult(
        glb_base64=base64.b64encode(glb_bytes).decode("ascii"),
        smplx_params=smplx,
        confidence=confidence,
        measurements=measurements,
    )


# ── Tier 0: VLM Body Analysis ───────────────────────────────────────────────


async def _vlm_body_analysis(
    image_bytes: bytes,
    settings,
    *,
    height_cm: float | None = None,
) -> tuple[dict, float]:
    """Use Groq Vision (llama-3.2-90b-vision) to analyze body proportions."""
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    messages = [
        {"role": "system", "content": "You are a precise body measurement estimation system."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": VLM_BODY_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.vlm_primary_model,
                "messages": messages,
                "temperature": 0.1,  # Low temp for precision
                "max_tokens": 512,
            },
        )
        if resp.status_code == 429:
            groq_breaker.fail()
            raise RuntimeError("Groq rate limited")
        resp.raise_for_status()
        data = resp.json()
        groq_breaker.success()

    text = data["choices"][0]["message"]["content"].strip()
    logger.info("VLM body response: %s", text[:300])

    # Parse JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON found in VLM response")

    body_info = json.loads(json_match.group())

    # Extract ratios from VLM analysis
    build_type = body_info.get("build_type", "average").lower()
    if build_type not in BUILD_ADJUSTMENTS:
        build_type = "average"

    # Get build-type base adjustments
    build_adj = BUILD_ADJUSTMENTS[build_type]

    # Override with VLM-specific ratios where provided
    shoulder_r = body_info.get("shoulder_ratio", build_adj["shoulder_width"])
    chest_r = body_info.get("chest_ratio", build_adj["chest"])
    waist_r = body_info.get("waist_ratio", build_adj["waist"])
    hip_r = body_info.get("hip_ratio", build_adj["hip"])

    # Clamp ratios to reasonable ranges
    shoulder_r = max(0.82, min(1.20, float(shoulder_r)))
    chest_r = max(0.82, min(1.25, float(chest_r)))
    waist_r = max(0.78, min(1.30, float(waist_r)))
    hip_r = max(0.82, min(1.25, float(hip_r)))

    # Limb length adjustment
    limb_adj = {"short": 0.96, "average": 1.0, "long": 1.04}
    limb_factor = limb_adj.get(body_info.get("limb_length", "average"), 1.0)

    # Neck thickness
    neck_adj = {"thin": 0.90, "average": 1.0, "thick": 1.10}
    neck_factor = neck_adj.get(body_info.get("neck_thickness", "average"), 1.0)

    # Torso proportion
    torso_adj = {"short_torso": 0.94, "average": 1.0, "long_torso": 1.06}
    torso_factor = torso_adj.get(body_info.get("torso_proportion", "average"), 1.0)

    # Gender-based base adjustments
    gender = body_info.get("gender_presentation", "neutral")
    if gender == "feminine":
        # Women tend to have wider hips, narrower shoulders
        shoulder_r *= 0.97
        hip_r *= 1.03
    elif gender == "masculine":
        # Men tend to have wider shoulders, narrower hips
        shoulder_r *= 1.03
        hip_r *= 0.97

    base_height = height_cm or 165.0

    measurements = {
        "height_cm": round(base_height),
        "shoulder_cm": round(base_height * ANTHROPOMETRIC_RATIOS["shoulder_width"] * shoulder_r, 1),
        "chest_cm": round(base_height * ANTHROPOMETRIC_RATIOS["chest"] * chest_r, 1),
        "waist_cm": round(base_height * ANTHROPOMETRIC_RATIOS["waist"] * waist_r, 1),
        "hip_cm": round(base_height * ANTHROPOMETRIC_RATIOS["hip"] * hip_r, 1),
        "inseam_cm": round(base_height * ANTHROPOMETRIC_RATIOS["inseam"] * limb_factor, 1),
        "arm_length_cm": round(base_height * ANTHROPOMETRIC_RATIOS["arm_length"] * limb_factor, 1),
        "torso_length_cm": round(base_height * ANTHROPOMETRIC_RATIOS["torso_length"] * torso_factor, 1),
        "neck_cm": round(base_height * ANTHROPOMETRIC_RATIOS["neck"] * neck_factor, 1),
    }

    # Confidence: 0.88 with height, 0.78 without
    conf = 0.88 if height_cm else 0.78

    # Add VLM metadata to measurements for downstream use
    measurements["_vlm_build_type"] = build_type
    measurements["_vlm_notes"] = body_info.get("notes", "")

    return measurements, conf


# ── Tier 1: HF Body Analysis ────────────────────────────────────────────────


def _derive_measurements_from_height(
    height_cm: float,
    *,
    body_width_ratio: float = 1.0,
) -> dict:
    """Derive full body measurements from height using anthropometric ratios.

    Args:
        height_cm: User's height in cm.
        body_width_ratio: Multiplier for width-based measurements (1.0 = average build).
            >1.0 = broader, <1.0 = slimmer. Derived from image analysis when available.
    """
    return {
        "height_cm": round(height_cm),
        "shoulder_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["shoulder_width"] * body_width_ratio, 1),
        "chest_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["chest"] * body_width_ratio, 1),
        "waist_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["waist"] * body_width_ratio, 1),
        "hip_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["hip"] * body_width_ratio, 1),
        "inseam_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["inseam"], 1),
        "arm_length_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["arm_length"], 1),
        "torso_length_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["torso_length"], 1),
        "neck_cm": round(height_cm * ANTHROPOMETRIC_RATIOS["neck"] * body_width_ratio, 1),
    }


async def _hf_body_analysis(
    image_bytes: bytes,
    settings,
    *,
    height_cm: float | None = None,
) -> tuple[dict, float]:
    """Use HF Inference API for object/body detection to estimate proportions."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Use a body detection / pose estimation model
        resp = await client.post(
            "https://api-inference.huggingface.co/models/facebook/detr-resnet-50",
            headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            content=image_bytes,
        )
        if resp.status_code == 503:
            hf_breaker.fail()
            raise RuntimeError("HF model loading")
        if resp.status_code != 200:
            raise RuntimeError(f"HF returned {resp.status_code}")

        hf_breaker.success()
        detections = resp.json()

        # Find person detection for body bounding box
        person_box = None
        for det in detections:
            if det.get("label", "").lower() == "person" and det.get("score", 0) > 0.5:
                person_box = det.get("box", {})
                break

        if person_box:
            # Derive body width ratio from bounding box proportions
            img = Image.open(BytesIO(image_bytes))
            img_w, img_h = img.size
            box_h = person_box.get("ymax", img_h) - person_box.get("ymin", 0)
            box_w = person_box.get("xmax", img_w) - person_box.get("xmin", 0)

            # Estimate height from image if not provided
            if not height_cm:
                ratio = box_h / img_h if img_h > 0 else 0.8
                if ratio > 0.7:  # full body visible
                    height_cm = 155 + (ratio * 20)
                else:
                    height_cm = 165  # default

            # Body width ratio: compare detected box width/height to average
            # Average person box w/h ratio is ~0.25
            actual_wh = box_w / box_h if box_h > 0 else 0.25
            body_width_ratio = actual_wh / 0.25
            body_width_ratio = max(0.85, min(1.20, body_width_ratio))  # clamp

            measurements = _derive_measurements_from_height(
                height_cm, body_width_ratio=body_width_ratio,
            )
            return measurements, 0.75

    # Fallback within HF: basic image analysis
    return _image_heuristic_measurements(image_bytes, height_cm=height_cm)


def _image_heuristic_measurements(
    image_bytes: bytes,
    *,
    height_cm: float | None = None,
) -> tuple[dict, float]:
    """Estimate body measurements from image dimensions and aspect ratio."""
    try:
        img = Image.open(BytesIO(image_bytes))
        w, h = img.size
        aspect = h / w if w > 0 else 1.5

        # Estimate body width ratio from aspect ratio
        if aspect > 2.0:  # tall/narrow framing → likely slimmer
            body_width_ratio = 0.92
        elif aspect > 1.3:  # standard portrait
            body_width_ratio = 1.0
        else:  # wide/landscape
            body_width_ratio = 1.08

        base_height = height_cm or 165
        measurements = _derive_measurements_from_height(
            base_height, body_width_ratio=body_width_ratio,
        )
        confidence = 0.65 if height_cm else 0.45
        return measurements, confidence
    except Exception:
        base_height = height_cm or 165
        return _derive_measurements_from_height(base_height), 0.3


def _measurements_to_smplx(measurements: dict) -> dict:
    """Convert body measurements to SMPL-X shape parameters (betas).

    SMPL-X betas[0] correlates with height, betas[1] with BMI/weight.
    """
    height = measurements.get("height_cm", 165)
    chest = measurements.get("chest_cm", 88)
    waist = measurements.get("waist_cm", 72)

    # Normalize to SMPL-X beta scale (-2 to 2)
    beta_height = (height - 165) / 15  # 165cm = neutral
    beta_weight = (chest + waist - 160) / 40  # 160 combined = neutral

    betas = [round(beta_height, 3), round(beta_weight, 3)] + [0.0] * 8

    return {
        "betas": betas,
        "body_pose": [0.0] * 63,
        "global_orient": [0.0, 0.0, 0.0],
        "gender": "neutral",
    }


def _validate_image(data: bytes, label: str) -> None:
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        w, h = img.size
        if w < 256 or h < 256:
            raise ValueError(f"{label} image too small")
        if max(w, h) / min(w, h) > 2.5:
            raise ValueError(f"{label} aspect ratio out of range")
    except Exception as exc:
        raise ValueError(f"Invalid {label} image") from exc


# ── Parametric GLB mesh generation ──────────────────────────────────────────

def _parametric_glb_from_measurements(measurements: dict) -> bytes:
    """Generate a low-poly parametric body mesh (GLB) shaped by measurements.

    Creates a simplified human body shape using ellipsoid cross-sections
    at key measurement points, connected into a triangulated mesh.
    """
    height = measurements.get("height_cm", 165) / 100.0  # convert to meters
    shoulder = measurements.get("shoulder_cm", 42) / 100.0
    chest_circ = measurements.get("chest_cm", 88) / 100.0
    waist_circ = measurements.get("waist_cm", 72) / 100.0
    hip_circ = measurements.get("hip_cm", 90) / 100.0
    inseam = measurements.get("inseam_cm", 78) / 100.0

    # Convert circumferences to radii (C = 2*pi*r)
    chest_r = chest_circ / (2 * math.pi)
    waist_r = waist_circ / (2 * math.pi)
    hip_r = hip_circ / (2 * math.pi)
    shoulder_r = shoulder / 2

    # Body cross-sections from bottom to top (y-coordinate, x-radius, z-radius)
    # y=0 is ground, y=height is top of head
    sections = [
        (0.0, 0.04, 0.04),                         # feet
        (inseam * 0.2, 0.05, 0.05),                 # ankle
        (inseam * 0.5, 0.06, 0.06),                 # mid-calf
        (inseam * 0.75, 0.07, 0.07),                # knee
        (inseam * 0.95, hip_r * 0.7, hip_r * 0.6),  # upper thigh
        (inseam, hip_r, hip_r * 0.8),               # crotch/hip
        (height * 0.55, waist_r, waist_r * 0.7),    # waist
        (height * 0.65, chest_r, chest_r * 0.75),   # chest
        (height * 0.72, shoulder_r, chest_r * 0.5),  # shoulders
        (height * 0.78, shoulder_r * 0.3, 0.06),    # neck base
        (height * 0.82, 0.07, 0.08),                # neck
        (height * 0.88, 0.09, 0.10),                # head mid
        (height * 0.95, 0.08, 0.09),                # head top
        (height, 0.03, 0.03),                        # crown
    ]

    segments = 12  # vertices per ring
    vertices = []
    normals = []

    for y, rx, rz in sections:
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = rx * math.cos(angle)
            z = rz * math.sin(angle)
            vertices.extend([x, y, z])
            # Approximate normal (outward from center axis)
            nx = math.cos(angle)
            nz = math.sin(angle)
            normals.extend([nx, 0.0, nz])

    # Triangulate: connect adjacent rings
    indices = []
    num_sections = len(sections)
    for s in range(num_sections - 1):
        for i in range(segments):
            curr = s * segments + i
            next_i = s * segments + (i + 1) % segments
            above = (s + 1) * segments + i
            above_next = (s + 1) * segments + (i + 1) % segments

            indices.extend([curr, above, next_i])
            indices.extend([next_i, above, above_next])

    return _build_glb(vertices, normals, indices)


def _build_glb(vertices: list[float], normals: list[float], indices: list[int]) -> bytes:
    """Build a valid GLB (glTF 2.0 binary) file from vertex/normal/index data."""
    import struct as st

    # Pack binary data
    vert_bytes = st.pack(f"<{len(vertices)}f", *vertices)
    norm_bytes = st.pack(f"<{len(normals)}f", *normals)
    idx_bytes = st.pack(f"<{len(indices)}H", *indices)  # unsigned short

    # Pad to 4-byte alignment
    def _pad4(data: bytes) -> bytes:
        pad = (4 - len(data) % 4) % 4
        return data + b"\x00" * pad

    vert_bytes = _pad4(vert_bytes)
    norm_bytes = _pad4(norm_bytes)
    idx_bytes = _pad4(idx_bytes)

    bin_data = idx_bytes + vert_bytes + norm_bytes

    num_vertices = len(vertices) // 3
    num_indices = len(indices)

    # Compute bounding box for positions
    min_pos = [float("inf")] * 3
    max_pos = [float("-inf")] * 3
    for i in range(num_vertices):
        for j in range(3):
            v = vertices[i * 3 + j]
            min_pos[j] = min(min_pos[j], v)
            max_pos[j] = max(max_pos[j], v)

    gltf = {
        "asset": {"version": "2.0", "generator": "aura-fashion-ai"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "body"}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 1, "NORMAL": 2},
                "indices": 0,
                "mode": 4,  # TRIANGLES
            }],
            "name": "body_mesh",
        }],
        "accessors": [
            {  # 0: indices
                "bufferView": 0,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": num_indices,
                "type": "SCALAR",
                "max": [num_indices - 1],
                "min": [0],
            },
            {  # 1: positions
                "bufferView": 1,
                "componentType": 5126,  # FLOAT
                "count": num_vertices,
                "type": "VEC3",
                "max": max_pos,
                "min": min_pos,
            },
            {  # 2: normals
                "bufferView": 2,
                "componentType": 5126,
                "count": num_vertices,
                "type": "VEC3",
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(idx_bytes), "target": 34963},
            {"buffer": 0, "byteOffset": len(idx_bytes), "byteLength": len(vert_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(idx_bytes) + len(vert_bytes), "byteLength": len(norm_bytes), "target": 34962},
        ],
        "buffers": [{"byteLength": len(bin_data)}],
    }

    json_str = json.dumps(gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b" " * json_pad

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_data)

    # GLB header
    header = st.pack("<III", 0x46546C67, 2, total_length)
    # JSON chunk header
    json_hdr = st.pack("<II", len(json_bytes), 0x4E4F534A)
    # BIN chunk header
    bin_hdr = st.pack("<II", len(bin_data), 0x004E4942)

    return header + json_hdr + json_bytes + bin_hdr + bin_data
