"""Pydantic schemas for Room request/response models."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreate(BaseModel):
    """Request body for adding a room to a game."""

    name: str = Field(min_length=1, max_length=100, description="Room name")

    @field_validator("name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Room name must not be blank")
        return v


class RoomResponse(BaseModel):
    """Room info returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
