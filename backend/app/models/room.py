"""Room ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.game import Game
    from app.models.player import Player


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
    )

    # Relationships ------------------------------------------------------------
    creator: Mapped["Player | None"] = relationship(
        "Player",
        foreign_keys=[created_by],
    )
    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="rooms",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="room",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (Index("ix_rooms_game_id", "game_id"),)

    def __repr__(self) -> str:
        return f"<Room name={self.name!r}>"
