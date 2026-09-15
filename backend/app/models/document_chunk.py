from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"

    id: int | None = Field(default=None, primary_key=True)

    document_id: int = Field(
        foreign_key="documents.id",
        index=True,
    )

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    chunk_index: int

    content: str = Field(
        sa_column=Column(Text, nullable=False)
    )

    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(1536))
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )