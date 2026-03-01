"""FastAPI application entry point.

Configures CORS, lifespan (table creation), and includes all routers.
Run with:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import games, players, rooms, weapons


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hook.

    On startup we ensure the SQLite database has all tables created.
    This is safe to call even when tables already exist (uses IF NOT EXISTS).
    In production, Alembic migrations are the canonical way to evolve the schema.
    """
    # Import models so Base.metadata knows about them.
    import app.models  # noqa: F401
    from app.database import Base

    async with engine.begin() as conn:
        # Enable WAL mode for SQLite (persists at file level).
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(games.router)
app.include_router(players.router)
app.include_router(rooms.router)
app.include_router(weapons.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}
