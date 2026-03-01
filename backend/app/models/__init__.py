"""SQLAlchemy ORM models for Airbnb Games.

Importing this module ensures all models are registered with Base.metadata,
which is required for Alembic migrations and the lifespan table-creation hook.
"""

from app.models.assignment import Assignment
from app.models.game import Game, GameStatus
from app.models.player import Player
from app.models.room import Room
from app.models.user import User
from app.models.weapon import Weapon

__all__ = [
    "Assignment",
    "Game",
    "GameStatus",
    "Player",
    "Room",
    "User",
    "Weapon",
]
