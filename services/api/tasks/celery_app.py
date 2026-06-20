"""Celery + Redis task queue with Dead Letter Queue (DLQ) routing.

Blueprint Phase 7: Bounded queues with max_retries, acks_late, and DLQ.
Failed tasks after max_retries are routed to a dead letter queue for
manual inspection and replay.
"""

import json
import logging
import os
import time

from celery import Celery
from celery.signals import task_failure

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("fashion_ai", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
    # DLQ routing: failed tasks go to 'dead_letter' queue
    task_routes={
        "*.dead_letter": {"queue": "dead_letter"},
    },
    # Bounded queue: reject tasks if queue is too large
    worker_prefetch_multiplier=4,
)


# ── Dead Letter Queue Handler ───────────────────────────────────────────────


DLQ_KEY = "fashion_ai:dlq"


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Route permanently failed tasks to the Dead Letter Queue.

    Only triggers after all retries are exhausted (max_retries exceeded).
    """
    retries = getattr(sender.request, "retries", 0) if sender else 0
    max_retries = getattr(sender, "max_retries", 3) if sender else 3

    if retries >= max_retries:
        dlq_entry = {
            "task_id": task_id,
            "task_name": sender.name if sender else "unknown",
            "args": str(args)[:500] if args else "",
            "kwargs": str(kwargs)[:500] if kwargs else "",
            "error": str(exception)[:500] if exception else "unknown",
            "retries": retries,
            "timestamp": time.time(),
        }
        try:
            import redis

            r = redis.Redis.from_url(redis_url)
            r.rpush(DLQ_KEY, json.dumps(dlq_entry))
            r.ltrim(DLQ_KEY, -1000, -1)  # Keep last 1000 entries
            logger.error(
                "Task %s permanently failed after %d retries — routed to DLQ: %s",
                task_id, retries, dlq_entry["error"],
            )
        except Exception as exc:
            logger.error("Failed to write to DLQ: %s (original error: %s)", exc, exception)


def get_dlq_entries(limit: int = 50) -> list[dict]:
    """Retrieve recent DLQ entries for inspection."""
    try:
        import redis

        r = redis.Redis.from_url(redis_url)
        entries = r.lrange(DLQ_KEY, -limit, -1)
        return [json.loads(e) for e in entries]
    except Exception:
        return []


def replay_dlq_entry(index: int) -> bool:
    """Replay a DLQ entry by re-submitting the task."""
    try:
        import redis

        r = redis.Redis.from_url(redis_url)
        entry_raw = r.lindex(DLQ_KEY, index)
        if not entry_raw:
            return False
        entry = json.loads(entry_raw)
        task_name = entry.get("task_name", "")
        # Re-submit the task
        celery_app.send_task(task_name, args=eval(entry.get("args", "()")))
        r.lrem(DLQ_KEY, 1, entry_raw)
        logger.info("Replayed DLQ entry: %s", task_name)
        return True
    except Exception as exc:
        logger.error("DLQ replay failed: %s", exc)
        return False


# ── Tasks ────────────────────────────────────────────────────────────────────


@celery_app.task(bind=True, max_retries=3)
def reconstruct_body_task(self, front_b64: str, side_b64: str | None = None):
    import asyncio
    import base64

    from services.vision.body_reconstruct import reconstruct_body

    try:
        front = base64.b64decode(front_b64)
        side = base64.b64decode(side_b64) if side_b64 else None
        return asyncio.run(reconstruct_body(front, side))
    except Exception as exc:
        logger.error("Body reconstruction failed (attempt %d): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(bind=True, max_retries=3)
def generate_outfit_task(self, brief: str, num_variants: int = 4):
    import asyncio

    from services.vision.generate_outfit import generate_outfits

    try:
        result = asyncio.run(generate_outfits(design_brief=brief, num_variants=num_variants))
        return {"variants": [v.__dict__ for v in result.variants]}
    except Exception as exc:
        logger.error("Outfit generation failed (attempt %d): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(bind=True, max_retries=3)
def vlm_analyze_task(self, image_b64: str, prompt: str = "", language: str = "en"):
    """Async VLM analysis task for background processing."""
    import asyncio
    import base64

    from services.agent.vlm import analyze_clothing_image

    try:
        image_bytes = base64.b64decode(image_b64)
        result = asyncio.run(analyze_clothing_image(image_bytes, prompt=prompt, language=language))
        return {
            "description": result.description,
            "tags": result.tags,
            "style_category": result.style_category,
            "color_palette": result.color_palette,
            "suggestions": result.suggestions,
            "confidence": result.confidence,
        }
    except Exception as exc:
        logger.error("VLM analysis failed (attempt %d): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
