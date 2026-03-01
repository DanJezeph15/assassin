"""Game ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.player import Player
    from app.models.room import Room
    from app.models.weapon import Weapon


class GameStatus(str, enum.Enum):
    """Possible states a game can be in."""

    LOBBY = "lobby"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )
    status: Mapped[GameStatus] = mapped_column(
        Enum(
            GameStatus,
            native_enum=False,
            length=20,
            values_callable=lambda e: [member.value for member in e],
        ),
        default=GameStatus.LOBBY,
        nullable=False,
    )
    host_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", use_alter=True, name="fk_game_host_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships ------------------------------------------------------------
    # The host player (nullable until the first player joins).
    host: Mapped["Player | None"] = relationship(
        "Player",
        foreign_keys=[host_id],
        lazy="selectin",
    )
    players: Mapped[list["Player"]] = relationship(
        "Player",
        back_populates="game",
        foreign_keys="Player.game_id",
        lazy="selectin",
    )
    rooms: Mapped[list["Room"]] = relationship(
        "Room",
        back_populates="game",
        lazy="selectin",
    )
    weapons: Mapped[list["Weapon"]] = relationship(
        "Weapon",
        back_populates="game",
        lazy="selectin",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="game",
        lazy="selectin",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (Index("ix_games_code", "code", unique=True),)

    def __repr__(self) -> str:
        return f"<Game code={self.code!r} status={self.status.value!r}>"
