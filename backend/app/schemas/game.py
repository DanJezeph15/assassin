"""Pydantic schemas for Game request/response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.game import GameStatus


class GameCreate(BaseModel):
    """Request body for creating a new game. Empty -- games start with defaults."""

    pass


class GameResponse(BaseModel):
    """Response after creating a game. Minimal info for the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    status: GameStatus


class RoomInfo(BaseModel):
    """Minimal room info embedded in GameDetail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID | None


class WeaponInfo(BaseModel):
    """Minimal weapon info embedded in GameDetail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID | None


class PlayerInfo(BaseModel):
    """Player info embedded in GameDetail (no token exposed)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_alive: bool
    kills: int


class GameDetail(BaseModel):
    """Full game state returned by GET /api/games/{code}.

    Includes players, rooms, and weapons lists for the lobby/game view.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    status: GameStatus
    host_id: uuid.UUID | None
    created_at: datetime
    players: list[PlayerInfo]
    rooms: list[RoomInfo]
    weapons: list[WeaponInfo]
