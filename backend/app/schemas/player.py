"""Pydantic schemas for Player request/response models."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlayerJoin(BaseModel):
    """Request body for joining a game."""

    name: str = Field(min_length=1, max_length=50, description="Display name in the game")

    @field_validator("name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be blank")
        return v


class PlayerResponse(BaseModel):
    """Public player info (no token)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_alive: bool
    kills: int


class PlayerWithToken(BaseModel):
    """Returned on join so the client can store the token for future requests."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    token: str
