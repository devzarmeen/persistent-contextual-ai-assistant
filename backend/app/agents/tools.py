from typing import Any

from sqlmodel import Session, select

from app.agents.models import (
    CreateCalendarEventArguments,
    DeleteCalendarEventArguments,
    DraftEmailArguments,
    FindFreeSlotArguments,
    GetCalendarEventsArguments,
    GetDocumentArguments,
    GetEmailArguments,
    GetUserContextArguments,
    SaveMemoryArguments,
    SearchDocumentsArguments,
    SearchEmailsArguments,
    SearchMemoryArguments,
    SendEmailArguments,
    ToolArguments,
    UpdateCalendarEventArguments,
)
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.memory import ExtractedMemory
from app.services.calendar import (
    create_calendar_event,
    delete_calendar_event,
    find_free_slot,
    get_calendar_events,
    update_calendar_event,
)
from app.services.documents import search_documents
from app.services.gmail import (
    draft_email,
    get_email,
    search_emails,
    send_email,
)
from app.services.memory import (
    get_user_memories,
    save_memory,
    search_memories,
)


def search_memory_tool(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    try:
        query = query.strip()

        if not query:
            return {
                "success": False,
                "error": "Memory search query cannot be empty.",
            }

        memories = search_memories(
            session,
            user_id,
            query,
            limit,
        )

        return {
            "success": True,
            "query": query,
            "count": len(memories),
            "results": [
                {
                    "id": memory.id,
                    "memory_type": memory.memory_type,
                    "content": memory.content,
                    "importance": memory.importance,
                    "confidence": memory.confidence,
                    "source_type": memory.source_type,
                    "source_id": memory.source_id,
                    "similarity": round(
                        max(0.0, 1.0 - float(distance)),
                        4,
                    ),
                }
                for memory, distance in memories
            ],
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Memory search failed: {exc}",
        }


def search_documents_tool(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    try:
        query = query.strip()

        if not query:
            return {
                "success": False,
                "error": "Document search query cannot be empty.",
            }

        results = search_documents(
            session,
            user_id,
            query,
            limit,
        )

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": [
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "similarity": round(
                        float(similarity),
                        4,
                    ),
                }
                for chunk, document, similarity in results
            ],
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Document search failed: {exc}",
        }


def get_document_tool(
    session: Session,
    user_id: int,
    document_id: int,
) -> dict[str, Any]:
    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
    ).first()

    if not document:
        return {
            "success": False,
            "error": "Document not found.",
        }

    chunks = list(
        session.exec(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document.id,
                DocumentChunk.user_id == user_id,
            )
            .order_by(DocumentChunk.chunk_index)
        )
    )

    return {
        "success": True,
        "document": {
            "id": document.id,
            "filename": document.filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "created_at": document.created_at.isoformat(),
            "content": document.content,
            "chunks": [
                {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                }
                for chunk in chunks
            ],
        },
    }


def get_user_context_tool(
    session: Session,
    user_id: int,
    limit: int = 20,
) -> dict[str, Any]:
    memories = get_user_memories(
        session,
        user_id,
        limit,
    )

    return {
        "success": True,
        "count": len(memories),
        "memories": [
            {
                "id": memory.id,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "confirmation_count": memory.confirmation_count,
            }
            for memory in memories
        ],
    }


def save_memory_tool(
    session: Session,
    user_id: int,
    memory_type: str,
    content: str,
    importance: float = 0.7,
    confidence: float = 0.9,
) -> dict[str, Any]:
    try:
        memory = save_memory(
            session=session,
            user_id=user_id,
            extracted_memory=ExtractedMemory(
                memory_type=memory_type,
                content=content.strip(),
                importance=importance,
                confidence=confidence,
            ),
            source_type="agent",
        )

        if memory is None:
            return {
                "success": False,
                "error": "Memory could not be saved.",
            }

        return {
            "success": True,
            "memory": {
                "id": memory.id,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance": memory.importance,
                "confidence": memory.confidence,
            },
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Memory save failed: {exc}",
        }


def search_emails_tool(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 10,
):
    return search_emails(
        session,
        user_id,
        query,
        limit,
    )


def get_email_tool(
    session: Session,
    user_id: int,
    message_id: str,
):
    return get_email(
        session,
        user_id,
        message_id,
    )


def draft_email_tool(
    session: Session,
    user_id: int,
    to: str,
    subject: str,
    body: str,
):
    return draft_email(
        session,
        user_id,
        to,
        subject,
        body,
    )


def send_email_tool(
    session: Session,
    user_id: int,
    to: str,
    subject: str,
    body: str,
):
    return send_email(
        session,
        user_id,
        to,
        subject,
        body,
    )


def execute_tool(
    session: Session,
    user_id: int,
    tool_name: str,
    arguments: ToolArguments | dict[str, Any],
) -> dict[str, Any]:

    data = (
        arguments.model_dump()
        if hasattr(arguments, "model_dump")
        else arguments
    )

    try:
        if tool_name == "search_memory":
            a = SearchMemoryArguments.model_validate(data)
            return search_memory_tool(
                session, user_id, a.query, a.limit
            )

        if tool_name == "search_documents":
            a = SearchDocumentsArguments.model_validate(data)
            return search_documents_tool(
                session, user_id, a.query, a.limit
            )

        if tool_name == "get_document":
            a = GetDocumentArguments.model_validate(data)
            return get_document_tool(
                session, user_id, a.document_id
            )

        if tool_name == "get_user_context":
            a = GetUserContextArguments.model_validate(data)
            return get_user_context_tool(
                session, user_id, a.limit
            )

        if tool_name == "save_memory":
            a = SaveMemoryArguments.model_validate(data)
            return save_memory_tool(
                session,
                user_id,
                a.memory_type,
                a.content,
                a.importance,
                a.confidence,
            )

        if tool_name == "search_emails":
            a = SearchEmailsArguments.model_validate(data)
            return search_emails_tool(
                session, user_id, a.query, a.limit
            )

        if tool_name == "get_email":
            a = GetEmailArguments.model_validate(data)
            return get_email_tool(
                session, user_id, a.message_id
            )

        if tool_name == "draft_email":
            a = DraftEmailArguments.model_validate(data)
            return draft_email_tool(
                session,
                user_id,
                a.to,
                a.subject,
                a.body,
            )

        if tool_name == "send_email":
            a = SendEmailArguments.model_validate(data)
            return send_email_tool(
                session,
                user_id,
                a.to,
                a.subject,
                a.body,
            )

        if tool_name == "get_calendar_events":
            a = GetCalendarEventsArguments.model_validate(data)
            return get_calendar_events(
                session=session,
                user_id=user_id,
                calendar_id=a.calendar_id,
                days=a.days,
                limit=a.limit,
            )

        if tool_name == "find_free_slot":
            a = FindFreeSlotArguments.model_validate(data)
            return find_free_slot(
                session=session,
                user_id=user_id,
                start_time=a.start_time,
                end_time=a.end_time,
                duration_minutes=a.duration_minutes,
                calendar_id=a.calendar_id,
                timezone_name=a.time_zone,
            )

        if tool_name == "create_calendar_event":
            a = CreateCalendarEventArguments.model_validate(data)
            return create_calendar_event(
                session=session,
                user_id=user_id,
                summary=a.summary,
                start_time=a.start_time,
                end_time=a.end_time,
                description=a.description or "",
                location=a.location or "",
                calendar_id=a.calendar_id,
                timezone_name=a.time_zone,
            )

        if tool_name == "update_calendar_event":
            a = UpdateCalendarEventArguments.model_validate(data)
            return update_calendar_event(
                session=session,
                user_id=user_id,
                event_id=a.event_id,
                summary=a.summary,
                start_time=a.start_time,
                end_time=a.end_time,
                description=a.description,
                location=a.location,
                calendar_id=a.calendar_id,
                timezone_name=a.time_zone,
            )

        if tool_name == "delete_calendar_event":
            a = DeleteCalendarEventArguments.model_validate(data)
            return delete_calendar_event(
                session=session,
                user_id=user_id,
                event_id=a.event_id,
                calendar_id=a.calendar_id,
            )

        return {
            "success": False,
            "error": f"Unknown agent tool: {tool_name}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"{tool_name} failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }