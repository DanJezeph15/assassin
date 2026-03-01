"""Auth router -- user registration, login, and account management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db
from app.models.game import Game
from app.models.player import Player
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LinkSessionsRequest,
    LinkSessionsResponse,
    LoginRequest,
    RegisterRequest,
    SessionRestoreResponse,
    UserGameInfo,
    UserResponse,
)
from app.services.auth_service import create_access_token, login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Register a new user account and return an auth token."""
    user = await register_user(db, body.username, body.password)
    token = create_access_token(user.id)
    await db.commit()

    return AuthResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login to an existing account",
)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Authenticate with username and password, receive a JWT."""
    user = await login_user(db, body.username, body.password)
    token = create_access_token(user.id)

    return AuthResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/me/games",
    response_model=list[UserGameInfo],
    summary="List games for current user",
)
async def get_my_games(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserGameInfo]:
    """Return all games the authenticated user has participated in."""
    result = await db.execute(
        select(Player).where(Player.user_id == current_user.id).options(selectinload(Player.game))
    )
    players = result.scalars().all()

    return [
        UserGameInfo(
            game_id=player.game.id,
            game_code=player.game.code,
            game_status=player.game.status.value,
            player_name=player.name,
            player_id=player.id,
        )
        for player in players
    ]


@router.post(
    "/me/games/{code}/restore-session",
    response_model=SessionRestoreResponse,
    summary="Restore a player session for a game",
)
async def restore_session(
    code: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionRestoreResponse:
    """Find the player record linked to the current user in the given game
    and return their player token so the client can restore the session.
    """
    result = await db.execute(
        select(Player)
        .join(Game, Player.game_id == Game.id)
        .where(
            Player.user_id == current_user.id,
            Game.code == code.upper(),
        )
    )
    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player session found for this user in the given game",
        )

    return SessionRestoreResponse(
        token=player.token,
        player_id=player.id,
        player_name=player.name,
    )


@router.post(
    "/me/link-sessions",
    response_model=LinkSessionsResponse,
    summary="Link existing player sessions to current user",
)
async def link_sessions(
    body: LinkSessionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LinkSessionsResponse:
    """Link anonymous player sessions to the authenticated user account.

    For each provided X-Player-Token, if the corresponding player exists
    and has no user_id set, it will be linked to the current user. Players
    already linked to another user are not modified.
    """
    linked_count = 0

    for token in body.tokens:
        result = await db.execute(select(Player).where(Player.token == token))
        player = result.scalar_one_or_none()

        if player is not None and player.user_id is None:
            player.user_id = current_user.id
            linked_count += 1

    await db.commit()

    return LinkSessionsResponse(linked_count=linked_count)
