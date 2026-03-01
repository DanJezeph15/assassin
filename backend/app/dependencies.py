"""FastAPI dependencies for database sessions and authentication."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.player import Player


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, closing it when the request finishes."""
    async with async_session_factory() as session:
        yield session


async def get_current_player(
    x_player_token: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Player:
    """Authenticate a player by the X-Player-Token header.

    Looks up the player by their unique token. Raises 401 if the token is
    missing or does not match any player.
    """
    result = await db.execute(select(Player).where(Player.token == x_player_token))
    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing player token",
        )

    return player
