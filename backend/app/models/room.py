"""Room ORM model."""

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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

    # Relationships ------------------------------------------------------------
    game: Mapped["Game"] = relationship(  # noqa: F821
        "Game",
        back_populates="rooms",
    )
    assignments: Mapped[list["Assignment"]] = relationship(  # noqa: F821
        "Assignment",
        back_populates="room",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_rooms_game_id", "game_id"),
    )

    def __repr__(self) -> str:
        return f"<Room name={self.name!r}>"
