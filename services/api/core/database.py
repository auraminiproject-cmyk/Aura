import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)

SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///./fashionai.db"
_MAX_RETRIES = 3
_RETRY_DELAY_BASE = 2  # seconds, doubles each retry


class Base(DeclarativeBase):
    pass


settings = get_settings()

# Auto-convert Render-style postgres:// to async driver
_db_url = settings.database_url
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql+psycopg2://"):
    _db_url = _db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

# asyncpg doesn't support query parameters like sslmode=require or channel_binding=require.
# The easiest fix is to strip the query string entirely. Neon requires SSL, and asyncpg will negotiate it.
if "?" in _db_url:
    _db_url = _db_url.split("?")[0]

engine = create_async_engine(_db_url, echo=settings.app_env == "development")
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _rebuild_engine(url: str) -> None:
    """Replace the module-level engine & session factory with a new URL."""
    global engine, SessionLocal
    logger.info("Rebuilding engine with URL: %s", url.split("@")[-1] if "@" in url else url)
    engine = create_async_engine(url, echo=settings.app_env == "development")
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialise the database, retrying on transient failures.

    If the primary DATABASE_URL is unreachable after *_MAX_RETRIES* attempts
    **and** the URL points to a remote (non-SQLite) database, the app falls
    back to a local SQLite file so it can still start in degraded mode.
    """
    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
                # Manual migrations
                from sqlalchemy import text
                from sqlalchemy.exc import OperationalError, ProgrammingError
                
                migrations = [
                    "ALTER TABLE users ADD COLUMN gender VARCHAR(16)",
                    "ALTER TABLE body_profiles ADD COLUMN profile_type VARCHAR(32) DEFAULT 'primary'",
                    "ALTER TABLE body_profiles ADD COLUMN profile_name VARCHAR(128)",
                    "ALTER TABLE body_profiles ADD COLUMN gender VARCHAR(16)",
                    "ALTER TABLE body_profiles ADD COLUMN avatar_image_url VARCHAR(512)",
                    "ALTER TABLE sessions ADD COLUMN status VARCHAR(32) DEFAULT 'active'",
                    "ALTER TABLE sessions ADD COLUMN context_json JSON",
                    "ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP",
                    "ALTER TABLE conversations ADD COLUMN language VARCHAR(8)",
                    "ALTER TABLE conversations ADD COLUMN metadata_json JSON",
                ]
                
                for migration in migrations:
                    try:
                        async with conn.begin_nested():
                            await conn.execute(text(migration))
                    except (OperationalError, ProgrammingError):
                        pass
                
            logger.info("Database initialised successfully (attempt %d).", attempt)
            return
        except Exception as exc:
            last_exc = exc
            delay = _RETRY_DELAY_BASE ** attempt
            logger.warning(
                "Database connection attempt %d/%d failed: %s. "
                "Retrying in %ds…",
                attempt,
                _MAX_RETRIES,
                exc,
                delay,
            )
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(delay)

    # --- All retries exhausted ---
    assert last_exc is not None
    is_remote = not settings.database_url.startswith("sqlite")

    if is_remote:
        logger.error(
            "All %d connection attempts to remote DB failed (%s). "
            "Falling back to local SQLite: %s",
            _MAX_RETRIES,
            last_exc,
            SQLITE_FALLBACK_URL,
        )
        _rebuild_engine(SQLITE_FALLBACK_URL)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
                # Manual migrations
                from sqlalchemy import text
                from sqlalchemy.exc import OperationalError, ProgrammingError
                
                migrations = [
                    "ALTER TABLE users ADD COLUMN gender VARCHAR(16)",
                    "ALTER TABLE body_profiles ADD COLUMN profile_type VARCHAR(32) DEFAULT 'primary'",
                    "ALTER TABLE body_profiles ADD COLUMN profile_name VARCHAR(128)",
                    "ALTER TABLE body_profiles ADD COLUMN gender VARCHAR(16)",
                    "ALTER TABLE body_profiles ADD COLUMN avatar_image_url VARCHAR(512)",
                    "ALTER TABLE sessions ADD COLUMN status VARCHAR(32) DEFAULT 'active'",
                    "ALTER TABLE sessions ADD COLUMN context_json JSON",
                    "ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP",
                    "ALTER TABLE conversations ADD COLUMN language VARCHAR(8)",
                    "ALTER TABLE conversations ADD COLUMN metadata_json JSON",
                ]
                
                for migration in migrations:
                    try:
                        async with conn.begin_nested():
                            await conn.execute(text(migration))
                    except (OperationalError, ProgrammingError):
                        pass
                
            logger.info("SQLite fallback initialised successfully.")
            return
        except Exception as fallback_exc:
            logger.critical("SQLite fallback also failed: %s", fallback_exc)
            raise fallback_exc from last_exc
    else:
        logger.critical(
            "Database initialisation failed after %d attempts: %s",
            _MAX_RETRIES,
            last_exc,
        )
        raise last_exc
