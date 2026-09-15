from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class MemoryConflict(SQLModel, table=True):
    __tablename__ = "memory_conflicts"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    old_memory_id: int = Field(
        foreign_key="memories.id",
        index=True,
    )

    new_memory_id: int = Field(
        foreign_key="memories.id",
        index=True,
    )

    winning_memory_id: int = Field(
        foreign_key="memories.id",
        index=True,
    )

    comparison_type: str = Field(
        default="CONFLICT",
        index=True,
    )

    conflict_type: str = Field(
        default="FACT_UPDATE",
        index=True,
    )

    old_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    new_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    old_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    new_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    resolution: str = Field(
        default="NEW_MEMORY_WINS",
    )

    reason: str = Field(
        default="",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    resolved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )