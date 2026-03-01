"""Pydantic schemas for Weapon request/response models."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeaponCreate(BaseModel):
    """Request body for adding a weapon to a game."""

    name: str = Field(min_length=1, max_length=100, description="Weapon name")

    @field_validator("name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Weapon name must not be blank")
        return v


class WeaponResponse(BaseModel):
    """Weapon info returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID | None
