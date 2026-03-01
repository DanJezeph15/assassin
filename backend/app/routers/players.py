"""Players router -- join a game."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.player import PlayerJoin, PlayerWithToken
from app.services import game_service

router = APIRouter(prefix="/api/games/{code}/players", tags=["players"])


@router.post(
    "",
    response_model=PlayerWithToken,
    status_code=status.HTTP_201_CREATED,
    summary="Join a game",
)
async def join_game(
    code: str,
    body: PlayerJoin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerWithToken:
    """Join a game by its code.

    The player receives a token that must be sent as the X-Player-Token
    header in subsequent requests. The first player to join becomes the
    game host.
    """
    player = await game_service.join_game(db, code, body.name)
    return PlayerWithToken.model_validate(player)
