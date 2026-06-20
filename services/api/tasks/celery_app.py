"""Celery + Redis task queue with DLQ pattern (blueprint Phase 7)."""

import logging
import os

from celery import Celery

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
)


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
        logger.error("Body reconstruction failed: %s", exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(bind=True, max_retries=3)
def generate_outfit_task(self, brief: str, num_variants: int = 4):
    import asyncio

    from services.vision.generate_outfit import generate_outfits

    try:
        result = asyncio.run(generate_outfits(design_brief=brief, num_variants=num_variants))
        return {"variants": [v.__dict__ for v in result.variants]}
    except Exception as exc:
        logger.error("Outfit generation failed: %s", exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
