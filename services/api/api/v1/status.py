from fastapi import APIRouter
from fastapi.responses import Response

from services.api.core.config import get_settings
from services.api.core.metrics import metrics_response
from services.api.core.resilience import breaker_state

router = APIRouter()


@router.get("/services")
async def service_status():
    settings = get_settings()
    return {
        "stack": "zero-card",
        "storage_backend": settings.storage_backend,
        "database": "sqlite" if "sqlite" in settings.database_url else "postgres",
        "groq_configured": bool(settings.groq_api_key),
        "huggingface_configured": bool(settings.huggingface_api_key),
        "langfuse_configured": bool(settings.langfuse_public_key),
        "posthog_configured": bool(settings.posthog_api_key),
        "firebase_configured": bool(settings.firebase_server_key),
        "circuit_breakers": {
            "groq": breaker_state("groq"),
            "huggingface": breaker_state("huggingface"),
            "qdrant": breaker_state("qdrant"),
        },
        "cloudflare_r2": "disabled",
    }


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for Grafana scraping."""
    return Response(
        content=metrics_response(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
