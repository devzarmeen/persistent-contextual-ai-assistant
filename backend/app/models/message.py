from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: int | None = Field(default=None, primary_key=True)

    conversation_id: int = Field(
        foreign_key="conversations.id",
        index=True,
    )

    role: str = Field(index=True)

    content: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )