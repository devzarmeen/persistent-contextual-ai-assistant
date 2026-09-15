from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    filename: str

    content_type: str

    file_size: int = 0

    content: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )