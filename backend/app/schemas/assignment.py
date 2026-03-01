"""Pydantic schemas for Assignment request/response models."""

from pydantic import BaseModel, ConfigDict


class AssignmentResponse(BaseModel):
    """A player's active assignment -- their secret prompt.

    Tells the player who to kill, in which room, with which weapon.
    """

    model_config = ConfigDict(from_attributes=True)

    target_name: str
    room_name: str
    weapon_name: str
