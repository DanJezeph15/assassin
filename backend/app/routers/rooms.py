"""Rooms router -- add and remove rooms from a game lobby."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_player, get_db
from app.models.player import Player
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomResponse
from app.services import game_service

router = APIRouter(prefix="/api/games/{code}/rooms", tags=["rooms"])


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a room to a game",
)
async def add_room(
    code: str,
    body: RoomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> RoomResponse:
    """Add a room to a game in the lobby.

    Requires a valid player token. The game must be in LOBBY status.
    Room names must be unique within the game (case-insensitive).
    """
    game = await game_service.validate_game_lobby(db, code, current_player)

    # Check for duplicate room name (case-insensitive).
    for existing_room in game.rooms:
        if existing_room.name.lower() == body.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room '{body.name}' already exists in this game",
            )

    room = Room(game_id=game.id, name=body.name)
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return RoomResponse.model_validate(room)


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a room from a game",
)
async def remove_room(
    code: str,
    room_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> Response:
    """Remove a room from a game in the lobby.

    Requires a valid player token. The game must be in LOBBY status.
    The room must belong to the specified game.
    """
    game = await game_service.validate_game_lobby(db, code, current_player)

    # Find the room in this game.
    target_room = None
    for room in game.rooms:
        if room.id == room_id:
            target_room = room
            break

    if target_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found in this game",
        )

    await db.delete(target_room)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
