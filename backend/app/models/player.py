"""Player ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_alive: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    kills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships ------------------------------------------------------------
    game: Mapped["Game"] = relationship(  # noqa: F821
        "Game",
        back_populates="players",
        foreign_keys=[game_id],
    )

    # Assignments where this player is the killer.
    assignments_as_killer: Mapped[list["Assignment"]] = relationship(  # noqa: F821
        "Assignment",
        back_populates="killer",
        foreign_keys="Assignment.killer_id",
    )

    # Assignments where this player is the target.
    assignments_as_target: Mapped[list["Assignment"]] = relationship(  # noqa: F821
        "Assignment",
        back_populates="target",
        foreign_keys="Assignment.target_id",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_players_game_id", "game_id"),
        Index("ix_players_token", "token", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Player name={self.name!r} alive={self.is_alive}>"
