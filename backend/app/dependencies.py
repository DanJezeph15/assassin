"""FastAPI dependencies for database sessions and authentication."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.player import Player
from app.models.user import User
from app.services.auth_service import decode_access_token


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


async def get_current_user(
    authorization: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Authenticate a user by the Authorization header (Bearer JWT).

    Parses the "Bearer <token>" header, decodes the JWT, and looks up the
    User by id. Raises 401 if the header is missing, malformed, or the
    token is invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[7:]  # Strip "Bearer " prefix
    user_id = decode_access_token(token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_optional_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """Optionally authenticate a user by the Authorization header.

    Returns the User if a valid Bearer JWT is provided, or None if the
    header is missing or invalid. Never raises an error.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]

    try:
        user_id = decode_access_token(token)
    except HTTPException:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
