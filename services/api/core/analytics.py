"""PostHog product analytics — event tracking for user behavior insights.

Tracks: chat messages, design sessions, product clicks, avatar captures, wardrobe actions.
Falls back to logging when PostHog is not configured.

Requires: POSTHOG_API_KEY and POSTHOG_HOST env vars.
Free tier: 1M events/month.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_posthog = None
_initialized = False


def _init_posthog():
    """Lazy-init PostHog client."""
    global _posthog, _initialized
    if _initialized:
        return _posthog
    _initialized = True
    try:
        import posthog

        from services.api.core.config import get_settings

        settings = get_settings()
        api_key = getattr(settings, "posthog_api_key", "")
        host = getattr(settings, "posthog_host", "https://app.posthog.com")
        if api_key:
            posthog.api_key = api_key
            posthog.host = host
            posthog.disabled = False
            _posthog = posthog
            logger.info("PostHog initialized (host: %s)", host)
        else:
            logger.debug("PostHog not configured — analytics disabled")
    except ImportError:
        logger.debug("PostHog SDK not installed — analytics disabled")
    except Exception as exc:
        logger.warning("PostHog init failed: %s", exc)
    return _posthog


# ── Event Names ──────────────────────────────────────────────────────────────


class Events:
    # Chat
    CHAT_MESSAGE_SENT = "chat_message_sent"
    CHAT_VOICE_INPUT = "chat_voice_input"
    CHAT_SESSION_START = "chat_session_start"

    # Design
    DESIGN_SESSION_START = "design_session_start"
    DESIGN_OUTFIT_GENERATED = "design_outfit_generated"
    DESIGN_TRYON_STARTED = "design_tryon_started"
    DESIGN_SAVED_TO_WARDROBE = "design_saved_to_wardrobe"

    # Products
    PRODUCT_SEARCH = "product_search"
    PRODUCT_CLICKED = "product_clicked"
    PRODUCT_AFFILIATE_CLICK = "product_affiliate_click"

    # Avatar
    AVATAR_PHOTO_CAPTURED = "avatar_photo_captured"
    AVATAR_BODY_ANALYZED = "avatar_body_analyzed"
    AVATAR_3D_VIEWED = "avatar_3d_viewed"

    # VLM
    VLM_IMAGE_ANALYZED = "vlm_image_analyzed"
    VLM_OUTFIT_EVALUATED = "vlm_outfit_evaluated"

    # Auth
    USER_REGISTERED = "user_registered"
    USER_LOGGED_IN = "user_logged_in"

    # Wardrobe
    WARDROBE_ITEM_ADDED = "wardrobe_item_added"
    WARDROBE_ITEM_REMOVED = "wardrobe_item_removed"

    # System
    APP_OPENED = "app_opened"
    LANGUAGE_CHANGED = "language_changed"
    ERROR_OCCURRED = "error_occurred"


# ── Tracking Functions ───────────────────────────────────────────────────────


def track(
    user_id: str,
    event: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """Track a user event."""
    props = {
        "timestamp": time.time(),
        **(properties or {}),
    }

    ph = _init_posthog()
    if ph:
        try:
            ph.capture(distinct_id=user_id, event=event, properties=props)
        except Exception as exc:
            logger.debug("PostHog track failed: %s", exc)
    else:
        logger.debug("Analytics [%s] user=%s props=%s", event, user_id, props)


def identify(
    user_id: str,
    traits: dict[str, Any] | None = None,
) -> None:
    """Identify/update user profile."""
    ph = _init_posthog()
    if ph:
        try:
            ph.identify(distinct_id=user_id, properties=traits or {})
        except Exception as exc:
            logger.debug("PostHog identify failed: %s", exc)


def track_chat(user_id: str, *, intent: str, language: str, message_length: int) -> None:
    """Convenience: track a chat message."""
    track(user_id, Events.CHAT_MESSAGE_SENT, {
        "intent": intent,
        "language": language,
        "message_length": message_length,
    })


def track_design(user_id: str, *, brief: str, num_variants: int, provider: str) -> None:
    """Convenience: track outfit generation."""
    track(user_id, Events.DESIGN_OUTFIT_GENERATED, {
        "brief_length": len(brief),
        "num_variants": num_variants,
        "provider": provider,
    })


def track_product_click(user_id: str, *, product_id: str, platform: str, price: float) -> None:
    """Convenience: track product affiliate click."""
    track(user_id, Events.PRODUCT_AFFILIATE_CLICK, {
        "product_id": product_id,
        "platform": platform,
        "price_inr": price,
    })


def flush() -> None:
    """Flush pending events (call on shutdown)."""
    ph = _init_posthog()
    if ph:
        try:
            ph.flush()
        except Exception:
            pass
