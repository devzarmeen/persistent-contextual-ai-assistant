from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.database import get_session
from app.models.memory import Memory
from app.models.memory_conflict import MemoryConflict
from app.schemas.memory_intelligence import (
    MemoryConflictDetailResponse,
    MemoryConflictResponse,
    MemoryIntelligenceSummary,
)
from app.services.auth import (
    get_current_user,
    security,
)
from app.services.memory_intelligence import (
    get_memory_conflict,
    get_memory_history,
    get_memory_intelligence_summary,
    get_user_conflicts,
)


router = APIRouter(
    prefix="/api/memory-intelligence",
    tags=["Memory Intelligence"],
)


def _memory_to_dict(
    memory: Memory | None,
) -> dict:
    if memory is None:
        return {}

    return {
        "id": memory.id,
        "memory_type": memory.memory_type,
        "content": memory.content,
        "importance": memory.importance,
        "confidence": memory.confidence,
        "source_type": memory.source_type,
        "source_id": memory.source_id,
        "is_active": memory.is_active,
        "confirmation_count": memory.confirmation_count,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at,
    }


def _conflict_to_response(
    conflict: MemoryConflict,
) -> MemoryConflictResponse:
    return MemoryConflictResponse(
        id=int(conflict.id),
        old_memory_id=conflict.old_memory_id,
        new_memory_id=conflict.new_memory_id,
        winning_memory_id=conflict.winning_memory_id,
        comparison_type=conflict.comparison_type,
        conflict_type=conflict.conflict_type,
        old_confidence=conflict.old_confidence,
        new_confidence=conflict.new_confidence,
        old_score=conflict.old_score,
        new_score=conflict.new_score,
        resolution=conflict.resolution,
        reason=conflict.reason,
        created_at=conflict.created_at,
        resolved_at=conflict.resolved_at,
    )


@router.get(
    "/conflicts",
    response_model=list[MemoryConflictResponse],
)
def list_memory_conflicts(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_current_user(
        credentials,
        session,
    )

    conflicts = get_user_conflicts(
        session=session,
        user_id=user.id,
        limit=100,
    )

    return [
        _conflict_to_response(conflict)
        for conflict in conflicts
    ]


@router.get(
    "/conflicts/{conflict_id}",
    response_model=MemoryConflictDetailResponse,
)
def get_memory_conflict_detail(
    conflict_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_current_user(
        credentials,
        session,
    )

    conflict = get_memory_conflict(
        session=session,
        user_id=user.id,
        conflict_id=conflict_id,
    )

    if conflict is None:
        raise HTTPException(
            status_code=404,
            detail="Memory conflict not found.",
        )

    old_memory = session.exec(
        select(Memory).where(
            Memory.id == conflict.old_memory_id,
            Memory.user_id == user.id,
        )
    ).first()

    new_memory = session.exec(
        select(Memory).where(
            Memory.id == conflict.new_memory_id,
            Memory.user_id == user.id,
        )
    ).first()

    winning_memory = session.exec(
        select(Memory).where(
            Memory.id == conflict.winning_memory_id,
            Memory.user_id == user.id,
        )
    ).first()

    if (
        old_memory is None
        or new_memory is None
        or winning_memory is None
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Conflict history references "
                "a missing memory."
            ),
        )

    return MemoryConflictDetailResponse(
        **_conflict_to_response(conflict).model_dump(),
        old_memory=_memory_to_dict(
            old_memory
        ),
        new_memory=_memory_to_dict(
            new_memory
        ),
        winning_memory=_memory_to_dict(
            winning_memory
        ),
    )


@router.get(
    "/memories/{memory_id}/history",
    response_model=list[MemoryConflictResponse],
)
def get_memory_history_route(
    memory_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_current_user(
        credentials,
        session,
    )

    memory = session.exec(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == user.id,
        )
    ).first()

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found.",
        )

    conflicts = get_memory_history(
        session=session,
        user_id=user.id,
        memory_id=memory_id,
    )

    return [
        _conflict_to_response(conflict)
        for conflict in conflicts
    ]


@router.get(
    "/summary",
    response_model=MemoryIntelligenceSummary,
)
def memory_intelligence_summary(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    session: Session = Depends(get_session),
):
    user = get_current_user(
        credentials,
        session,
    )

    summary = get_memory_intelligence_summary(
        session=session,
        user_id=user.id,
    )

    return MemoryIntelligenceSummary(
        **summary
    )