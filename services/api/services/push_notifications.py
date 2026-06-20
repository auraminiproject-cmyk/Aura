"""Firebase Cloud Messaging (FCM) push notification service.

Supports:
  - New outfit ready notifications
  - Product price drop alerts
  - Styling tip of the day
  - Conversation follow-ups

Requires: FIREBASE_SERVER_KEY env var (from Firebase Console → Project Settings → Cloud Messaging).
Falls back silently to no-op when FCM is not configured.
"""

import json
import logging
from typing import Any

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)

FCM_URL = "https://fcm.googleapis.com/fcm/send"


class NotificationType:
    OUTFIT_READY = "outfit_ready"
    PRICE_DROP = "price_drop"
    STYLE_TIP = "style_tip"
    CHAT_FOLLOWUP = "chat_followup"


# Notification templates
_TEMPLATES = {
    NotificationType.OUTFIT_READY: {
        "title": "✨ Your outfit is ready!",
        "body": "AURA has designed {count} outfit variants for your {occasion}. Tap to view!",
    },
    NotificationType.PRICE_DROP: {
        "title": "💰 Price Drop Alert!",
        "body": "{product_name} is now ₹{price} on {platform}. {discount}% off!",
    },
    NotificationType.STYLE_TIP: {
        "title": "👗 Style Tip of the Day",
        "body": "{tip}",
    },
    NotificationType.CHAT_FOLLOWUP: {
        "title": "💬 Your stylist has a suggestion",
        "body": "Based on our last chat, I have some new ideas for you!",
    },
}


async def send_push_notification(
    *,
    fcm_token: str,
    notification_type: str,
    data: dict[str, Any] | None = None,
) -> bool:
    """Send a push notification via FCM.

    Args:
        fcm_token: Device FCM registration token.
        notification_type: One of NotificationType constants.
        data: Template variables and custom payload data.

    Returns:
        True if sent successfully, False otherwise.
    """
    settings = get_settings()
    server_key = getattr(settings, "firebase_server_key", "")
    if not server_key:
        logger.debug("FCM not configured (no FIREBASE_SERVER_KEY) — notification skipped")
        return False

    template = _TEMPLATES.get(notification_type, {
        "title": "AURA Fashion AI",
        "body": "You have a new update!",
    })

    # Format template with data
    data = data or {}
    title = template["title"]
    body = template["body"]
    try:
        body = body.format(**data)
    except (KeyError, IndexError):
        pass  # Use template as-is if formatting fails

    payload = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
        },
        "data": {
            "type": notification_type,
            **{k: str(v) for k, v in data.items()},
        },
        "priority": "high",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                FCM_URL,
                headers={
                    "Authorization": f"key={server_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success", 0) > 0:
                    logger.info("FCM notification sent: %s", notification_type)
                    return True
                logger.warning("FCM delivery failed: %s", result)
            else:
                logger.warning("FCM HTTP %d: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("FCM send failed: %s", exc)

    return False


async def send_bulk_notification(
    *,
    fcm_tokens: list[str],
    notification_type: str,
    data: dict[str, Any] | None = None,
) -> int:
    """Send notifications to multiple devices. Returns success count."""
    success = 0
    for token in fcm_tokens:
        if await send_push_notification(
            fcm_token=token, notification_type=notification_type, data=data,
        ):
            success += 1
    return success
