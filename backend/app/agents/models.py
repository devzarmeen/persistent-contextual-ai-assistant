from typing import Any, Literal

from pydantic import BaseModel, Field


ToolName = Literal[
    "search_memory",
    "search_documents",
    "get_document",
    "get_user_context",
    "save_memory",
    "search_emails",
    "get_email",
    "draft_email",
    "send_email",
    "get_calendar_events",
    "find_free_slot",
    "create_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
]


class SearchMemoryArguments(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class SearchDocumentsArguments(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class GetDocumentArguments(BaseModel):
    document_id: int = Field(ge=1)


class GetUserContextArguments(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)


class SaveMemoryArguments(BaseModel):
    memory_type: Literal[
        "FACT",
        "PREFERENCE",
        "DECISION",
        "TASK",
        "DEADLINE",
        "PERSON",
        "PROJECT",
        "CONVERSATION",
    ]
    content: str = Field(min_length=1)
    importance: float = Field(default=0.7, ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class SearchEmailsArguments(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=20)


class GetEmailArguments(BaseModel):
    message_id: str = Field(min_length=1)


class SendEmailArguments(BaseModel):
    to: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)


class DraftEmailArguments(SendEmailArguments):
    pass


class GetCalendarEventsArguments(BaseModel):
    calendar_id: str = Field(default="primary", min_length=1)
    days: int = Field(default=7, ge=1, le=90)
    limit: int = Field(default=20, ge=1, le=100)


class FindFreeSlotArguments(BaseModel):
    start_time: str = Field(min_length=1)
    end_time: str = Field(min_length=1)
    duration_minutes: int = Field(default=30, ge=5, le=480)
    calendar_id: str = Field(default="primary", min_length=1)
    time_zone: str = Field(default="UTC", min_length=1)


class CreateCalendarEventArguments(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    start_time: str = Field(min_length=1)
    end_time: str = Field(min_length=1)
    description: str | None = None
    location: str | None = None
    calendar_id: str = Field(default="primary", min_length=1)
    time_zone: str = Field(default="UTC", min_length=1)


class UpdateCalendarEventArguments(BaseModel):
    event_id: str = Field(min_length=1)
    summary: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    description: str | None = None
    location: str | None = None
    calendar_id: str = Field(default="primary", min_length=1)
    time_zone: str = Field(default="UTC", min_length=1)


class DeleteCalendarEventArguments(BaseModel):
    event_id: str = Field(min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)


ToolArguments = (
    SearchMemoryArguments
    | SearchDocumentsArguments
    | GetDocumentArguments
    | GetUserContextArguments
    | SaveMemoryArguments
    | SearchEmailsArguments
    | GetEmailArguments
    | DraftEmailArguments
    | SendEmailArguments
    | GetCalendarEventsArguments
    | FindFreeSlotArguments
    | CreateCalendarEventArguments
    | UpdateCalendarEventArguments
    | DeleteCalendarEventArguments
)


class ToolCall(BaseModel):
    tool_name: ToolName
    arguments: ToolArguments


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class AgentDecision(BaseModel):
    action: Literal["tool", "final_answer"]
    tool_call: ToolCall | None = None
    answer: str | None = None