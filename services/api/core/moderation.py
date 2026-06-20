"""Lightweight content moderation — no paid API, no card."""

import re

BLOCKED_TEXT_PATTERNS = [
    r"\b(nude|nsfw|explicit|porn)\b",
    r"\b(kill|bomb|terror)\b",
]

BLOCKED_IMAGE_HINTS = {b"\xff\xd8\xff\xe0", b"\x89PNG\r\n\x1a\n"}  # valid jpeg/png headers only check


def moderate_text(text: str) -> tuple[bool, str | None]:
    lower = text.lower()
    for pattern in BLOCKED_TEXT_PATTERNS:
        if re.search(pattern, lower, re.I):
            return False, "Message blocked by content policy"
    if len(text) > 4000:
        return False, "Message too long"
    return True, None


def moderate_image_bytes(data: bytes) -> tuple[bool, str | None]:
    if len(data) > 10 * 1024 * 1024:
        return False, "Image too large"
    if len(data) < 100:
        return False, "Invalid image"
    is_jpeg = data[:3] == b"\xff\xd8\xff"
    is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
    is_webp = data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        return False, "Unsupported or invalid image format"
    return True, None
