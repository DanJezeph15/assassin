"""Pydantic schemas for death and leaderboard response models."""

from pydantic import BaseModel, ConfigDict


class DeathResponse(BaseModel):
    """Response after a player confirms their death."""

    model_config = ConfigDict(from_attributes=True)

    killer_name: str
    kill_count: int
    game_over: bool
    winner_name: str | None = None


class LeaderboardEntry(BaseModel):
    """A single entry in the kill leaderboard."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    kills: int
    is_alive: bool
