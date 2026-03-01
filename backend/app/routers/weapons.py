"""Weapons router -- add and remove weapons from a game lobby."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_player, get_db
from app.models.player import Player
from app.models.weapon import Weapon
from app.schemas.weapon import WeaponCreate, WeaponResponse
from app.services import game_service

router = APIRouter(prefix="/api/games/{code}/weapons", tags=["weapons"])


@router.post(
    "",
    response_model=WeaponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a weapon to a game",
)
async def add_weapon(
    code: str,
    body: WeaponCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> WeaponResponse:
    """Add a weapon to a game in the lobby.

    Requires a valid player token. The game must be in LOBBY status.
    Weapon names must be unique within the game (case-insensitive).
    """
    game = await game_service.validate_game_lobby(db, code, current_player)

    # Check for duplicate weapon name (case-insensitive).
    for existing_weapon in game.weapons:
        if existing_weapon.name.lower() == body.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weapon '{body.name}' already exists in this game",
            )

    weapon = Weapon(game_id=game.id, name=body.name, created_by=current_player.id)
    db.add(weapon)
    await db.commit()
    await db.refresh(weapon)

    return WeaponResponse.model_validate(weapon)


@router.delete(
    "/{weapon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a weapon from a game",
)
async def remove_weapon(
    code: str,
    weapon_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> Response:
    """Remove a weapon from a game in the lobby.

    Requires a valid player token. The game must be in LOBBY status.
    The weapon must belong to the specified game.
    """
    game = await game_service.validate_game_lobby(db, code, current_player)

    # Find the weapon in this game.
    target_weapon = None
    for weapon in game.weapons:
        if weapon.id == weapon_id:
            target_weapon = weapon
            break

    if target_weapon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weapon not found in this game",
        )

    # Host can remove any item; others can only remove their own.
    if current_player.id != game.host_id and target_weapon.created_by != current_player.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove items you added",
        )

    await db.delete(target_weapon)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
