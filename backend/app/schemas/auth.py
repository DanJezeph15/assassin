"""Pydantic schemas for authentication request/response models."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    username: str = Field(min_length=3, max_length=30, description="Unique username")
    password: str = Field(min_length=6, max_length=128, description="Account password")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores")
        return v


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Public user info returned in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    created_at: datetime


class AuthResponse(BaseModel):
    """Response after successful registration or login."""

    token: str
    user: UserResponse


class UserGameInfo(BaseModel):
    """Info about a game the user has participated in."""

    game_id: uuid.UUID
    game_code: str
    game_status: str
    player_name: str
    player_id: uuid.UUID


class SessionRestoreResponse(BaseModel):
    """Response for restoring a player session via JWT auth."""

    token: str
    player_id: uuid.UUID
    player_name: str


class LinkSessionsRequest(BaseModel):
    """Request body for linking existing player sessions to a user account."""

    tokens: list[str] = Field(description="List of X-Player-Token values to link")


class LinkSessionsResponse(BaseModel):
    """Response after linking player sessions."""

    linked_count: int
