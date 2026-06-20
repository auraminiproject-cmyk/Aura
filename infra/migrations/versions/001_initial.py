"""Initial schema — mirrors services/api/core/models.py

Revision ID: 001
"""

revision = "001"
down_revision = None

from services.api.core.database import Base, engine  # noqa: E402


def upgrade() -> None:
    import asyncio

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())


def downgrade() -> None:
    pass
