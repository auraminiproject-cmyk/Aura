from fastapi import APIRouter

from services.api.core.config import get_settings
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
        "circuit_breakers": {
            "groq": breaker_state("groq"),
            "huggingface": breaker_state("huggingface"),
            "qdrant": breaker_state("qdrant"),
        },
        "cloudflare_r2": "disabled",
    }
