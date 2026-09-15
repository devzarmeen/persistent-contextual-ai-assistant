from datetime import datetime, timezone
from typing import Literal

from sqlmodel import Field, SQLModel


VerificationStatus = Literal[
    "PENDING",
    "APPROVED",
    "REJECTED",
    "EXECUTING",
    "VERIFIED",
    "FAILED",
]


class VerificationAction(SQLModel, table=True):
    __tablename__ = "verification_actions"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        index=True,
    )

    tool_name: str = Field(index=True)

    action_type: str = Field(index=True)

    request: str

    status: str = Field(
        default="PENDING",
        index=True,
    )

    result: str | None = None

    evidence: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: datetime | None = None

    approved_at: datetime | None = None

    rejected_at: datetime | None = None

    executing_at: datetime | None = None

    error: str | None = None