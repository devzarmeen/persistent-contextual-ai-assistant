from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None

    # Optional document attached to the current chat message.
    #
    # The frontend receives this ID from the authenticated
    # document upload endpoint and sends it with the chat request.
    document_id: int | None = None


class AgentMetadata(BaseModel):
    action: str | None = None
    tool_name: str | None = None
    status: str | None = None
    verification_required: bool = False
    verification_action_id: int | None = None
    verification_status: str | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    user_message_id: int
    assistant_message_id: int
    response: str
    created_at: datetime

    agent: AgentMetadata | None = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(
    ConversationResponse
):
    messages: list[MessageResponse]