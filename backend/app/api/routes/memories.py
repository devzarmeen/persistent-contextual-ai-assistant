from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.database import get_session
from app.models.memory import Memory
from app.schemas.memory import MemoryResponse, MemorySearchRequest
from app.services.auth import get_current_user, security
from app.services.memory import get_user_memories, search_memories


router = APIRouter(
    prefix="/api/memories",
    tags=["Memory"],
)


class MemoryUpdateRequest(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


def _response(memory: Memory) -> MemoryResponse:
    return MemoryResponse(
        id=memory.id,
        memory_type=memory.memory_type,
        content=memory.content,
        importance=memory.importance,
        confidence=memory.confidence,
        source_type=memory.source_type,
        source_id=memory.source_id,
        is_active=memory.is_active,
        confirmation_count=memory.confirmation_count,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.get("", response_model=list[MemoryResponse])
def list_memories(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    return [
        _response(memory)
        for memory in get_user_memories(
            session,
            user.id,
            100,
        )
    ]


@router.post("/search")
def search_memory(
    request: MemorySearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    results = search_memories(
        session,
        user.id,
        request.query,
        request.limit,
    )

    return {
        "query": request.query,
        "results": [
            {
                "id": memory.id,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "confirmation_count": memory.confirmation_count,
                "similarity_distance": distance,
                "source_type": memory.source_type,
                "source_id": memory.source_id,
            }
            for memory, distance in results
        ],
    }


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(
    memory_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    memory = session.get(Memory, memory_id)

    if not memory or memory.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="Memory not found.",
        )

    return _response(memory)


@router.patch("/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: int,
    request: MemoryUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    memory = session.get(Memory, memory_id)

    if not memory or memory.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="Memory not found.",
        )

    if not memory.is_active:
        raise HTTPException(
            status_code=409,
            detail="Inactive memory cannot be edited.",
        )

    if request.content is not None:
        memory.content = request.content.strip()

    if request.importance is not None:
        memory.importance = request.importance

    if request.confidence is not None:
        memory.confidence = request.confidence

    memory.updated_at = datetime.now(timezone.utc)

    session.add(memory)
    session.commit()
    session.refresh(memory)

    return _response(memory)


@router.delete("/{memory_id}")
def forget_memory(
    memory_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    memory = session.get(Memory, memory_id)

    if not memory or memory.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="Memory not found.",
        )

    memory.is_active = False
    memory.updated_at = datetime.now(timezone.utc)

    session.add(memory)
    session.commit()

    return {
        "success": True,
        "id": memory_id,
        "forgotten": True,
    }