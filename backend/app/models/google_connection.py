from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class GoogleConnection(SQLModel, table=True):
    __tablename__ = "google_connections"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        unique=True,
        index=True,
    )

    google_email: str
    access_token: str
    refresh_token: str | None = None
    token_uri: str = "https://oauth2.googleapis.com/token"
    client_id: str
    client_secret: str

    scopes: str

    expires_at: datetime | None = None

    is_active: bool = Field(
        default=True,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )