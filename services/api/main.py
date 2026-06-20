import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import logging

from services.api.core.config import get_settings
from services.api.core.database import init_db
from services.api.core.rate_limit import limiter
from services.api.core.startup import seed_product_catalog
from services.api.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting Fashion AI API (env=%s, db=%s)",
        settings.app_env,
        settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
    )
    await init_db()
    seed_product_catalog()

    # Start keep-alive self-ping in production to prevent Render sleep
    keep_alive_task = None
    if settings.app_env == "production":
        from services.api.core.keep_alive import keep_alive_loop
        keep_alive_task = asyncio.create_task(keep_alive_loop())

    logger.info("Startup complete.")
    yield

    # Cancel keep-alive on shutdown
    if keep_alive_task:
        keep_alive_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Fashion AI API",
        version="1.0.0",
        description="AI-Powered Personal Fashion Designer",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    @app.get("/health")
    async def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
