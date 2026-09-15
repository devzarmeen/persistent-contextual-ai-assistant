from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class Memory(SQLModel, table=True):
    __tablename__ = "memories"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    memory_type: str = Field(
        index=True,
    )

    content: str = Field(
        sa_column=Column(
            Text,
            nullable=False,
        )
    )

    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
    )

    source_type: str = Field(
        default="conversation",
        index=True,
    )

    source_id: str | None = None

    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(
            Vector(1536)
        ),
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )

    # Phase 10:
    # Number of times this memory has been explicitly
    # confirmed or repeated.
    confirmation_count: int = Field(
        default=0,
        ge=0,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )