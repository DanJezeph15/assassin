"""User ORM model for optional account-based authentication."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.player import Player


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    username_lower: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships ------------------------------------------------------------
    players: Mapped[list["Player"]] = relationship(
        "Player",
        back_populates="user",
    )

    # Indexes ------------------------------------------------------------------
    __table_args__ = (Index("ix_users_username_lower", "username_lower", unique=True),)

    def __repr__(self) -> str:
        return f"<User username={self.username!r}>"
