"""Assignment ORM model.

An assignment tells one player (killer) to eliminate another player (target)
in a specific room with a specific weapon.  Each player has at most one
active assignment at a time.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )
    killer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    weapon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("weapons.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships ------------------------------------------------------------
    game: Mapped["Game"] = relationship(  # noqa: F821
        "Game",
        back_populates="assignments",
    )
    killer: Mapped["Player"] = relationship(  # noqa: F821
        "Player",
        back_populates="assignments_as_killer",
        foreign_keys=[killer_id],
    )
    target: Mapped["Player"] = relationship(  # noqa: F821
        "Player",
        back_populates="assignments_as_target",
        foreign_keys=[target_id],
    )
    room: Mapped["Room"] = relationship(  # noqa: F821
        "Room",
        back_populates="assignments",
    )
    weapon: Mapped["Weapon"] = relationship(  # noqa: F821
        "Weapon",
        back_populates="assignments",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_assignments_killer_active", "killer_id", "is_active"),
        Index("ix_assignments_game_active", "game_id", "is_active"),
        Index("ix_assignments_target_active", "target_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<Assignment killer={self.killer_id} target={self.target_id} active={self.is_active}>"
        )
