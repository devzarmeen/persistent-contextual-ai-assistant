from __future__ import annotations

import re
from datetime import datetime, timezone
from math import exp
from typing import Optional

from google import genai
from google.genai import types
from sqlmodel import Session, select

from app.config import settings
from app.models.memory import Memory
from app.models.memory_conflict import MemoryConflict
from app.schemas.memory_intelligence import (
    MemoryComparisonResult,
    MemoryScoreBreakdown,
)


SOURCE_RELIABILITY: dict[str, float] = {
    "verified_external_action": 1.00,
    "verified_action": 1.00,
    "explicit_user": 0.98,
    "conversation": 0.90,
    "document": 0.88,
    "calendar": 0.86,
    "email": 0.82,
    "agent": 0.70,
    "inferred": 0.55,
}


def get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
    )


def calculate_recency_score(
    created_at: Optional[datetime],
) -> float:
    """
    Calculate a time-decay score.

    Newer memories receive a higher score.
    The decay is intentionally slow so that older,
    repeatedly confirmed memories remain useful.
    """
    if created_at is None:
        return 0.50

    if created_at.tzinfo is None:
        created_at = created_at.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    age_seconds = max(
        0.0,
        (now - created_at).total_seconds(),
    )

    age_days = age_seconds / 86400.0

    score = exp(-age_days / 180.0)

    return round(
        max(0.0, min(1.0, score)),
        4,
    )


def calculate_explicitness_score(
    content: str,
) -> float:
    """
    Estimate how explicitly the user stated a memory.
    """
    text = content.lower()

    patterns = [
        r"\bmy project\b",
        r"\bi am building\b",
        r"\bi'm building\b",
        r"\bi am working on\b",
        r"\bi'm working on\b",
        r"\bi work on\b",
        r"\bmy goal\b",
        r"\bmy deadline\b",
        r"\bmy preference\b",
        r"\bi prefer\b",
        r"\bi decided\b",
        r"\bi will\b",
        r"\bi need\b",
        r"\bremember that\b",
        r"\bnot the\b",
        r"\binstead of\b",
    ]

    matches = sum(
        1
        for pattern in patterns
        if re.search(pattern, text)
    )

    score = 0.50 + (matches * 0.08)

    return round(
        min(1.0, score),
        4,
    )


def calculate_confirmation_score(
    confirmation_count: int,
) -> float:
    """
    More confirmations increase confidence.
    """
    score = 0.50 + (
        max(0, confirmation_count) * 0.10
    )

    return round(
        min(1.0, score),
        4,
    )


def calculate_confidence_score(
    *,
    importance: float,
    source_type: str,
    created_at: Optional[datetime],
    content: str,
    confirmation_count: int = 0,
    has_conflict: bool = False,
) -> float:
    """
    Calculate final memory confidence.

    The existing weighting logic is preserved:
      importance       = 25%
      source reliability = 25%
      recency          = 15%
      explicitness     = 15%
      confirmation     = 15%
      conflict factor  = 5%
    """
    base_confidence = max(
        0.0,
        min(1.0, importance),
    )

    source_reliability = SOURCE_RELIABILITY.get(
        source_type,
        SOURCE_RELIABILITY["inferred"],
    )

    recency = calculate_recency_score(
        created_at
    )

    explicitness = calculate_explicitness_score(
        content
    )

    confirmation = calculate_confirmation_score(
        confirmation_count
    )

    conflict_factor = (
        0.65
        if has_conflict
        else 1.0
    )

    weighted_score = (
        base_confidence * 0.25
        + source_reliability * 0.25
        + recency * 0.15
        + explicitness * 0.15
        + confirmation * 0.15
        + conflict_factor * 0.05
    )

    final_score = max(
        0.0,
        min(1.0, weighted_score),
    )

    return round(
        final_score,
        4,
    )


def calculate_score_breakdown(
    *,
    importance: float,
    source_type: str,
    created_at: Optional[datetime],
    content: str,
    confirmation_count: int = 0,
    has_conflict: bool = False,
) -> MemoryScoreBreakdown:
    """
    Optional structured representation of the same
    confidence calculation.

    This does not change the scoring logic.
    """
    base_confidence = max(
        0.0,
        min(1.0, importance),
    )

    source_reliability = SOURCE_RELIABILITY.get(
        source_type,
        SOURCE_RELIABILITY["inferred"],
    )

    recency = calculate_recency_score(
        created_at
    )

    explicitness = calculate_explicitness_score(
        content
    )

    confirmation = calculate_confirmation_score(
        confirmation_count
    )

    conflict_factor = (
        0.65
        if has_conflict
        else 1.0
    )

    final_score = calculate_confidence_score(
        importance=importance,
        source_type=source_type,
        created_at=created_at,
        content=content,
        confirmation_count=confirmation_count,
        has_conflict=has_conflict,
    )

    return MemoryScoreBreakdown(
        base_confidence=base_confidence,
        source_reliability=source_reliability,
        recency=recency,
        explicitness=explicitness,
        confirmation=confirmation,
        conflict_factor=conflict_factor,
        final_score=final_score,
    )


def generate_intelligence_embedding(
    text: str,
) -> list[float]:
    """
    Generate the same 1536-dimensional embedding
    used by the memory database.
    """
    client = get_gemini_client()

    response = client.models.embed_content(
        model=settings.gemini_embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=1536,
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no embedding."
        )

    values = response.embeddings[0].values

    if values is None:
        raise RuntimeError(
            "Gemini returned an empty embedding."
        )

    embedding = list(values)

    if len(embedding) != 1536:
        raise RuntimeError(
            "Unexpected embedding dimension: "
            f"{len(embedding)}. Expected 1536."
        )

    return embedding


def find_related_memories(
    session: Session,
    user_id: int,
    content: str,
    limit: int = 8,
    exclude_memory_id: int | None = None,
) -> list[tuple[Memory, float]]:
    """
    Find semantically related active memories.

    Returns:
        [(memory, cosine_distance), ...]
    """
    embedding = generate_intelligence_embedding(
        content
    )

    statement = (
        select(
            Memory,
            Memory.embedding.cosine_distance(
                embedding
            ).label("distance"),
        )
        .where(
            Memory.user_id == user_id,
            Memory.is_active == True,
        )
    )

    if exclude_memory_id is not None:
        statement = statement.where(
            Memory.id != exclude_memory_id
        )

    statement = (
        statement
        .order_by(
            Memory.embedding.cosine_distance(
                embedding
            )
        )
        .limit(limit)
    )

    rows = session.exec(statement).all()

    return [
        (
            row[0],
            float(row[1]),
        )
        for row in rows
    ]


def _extract_explicit_dates(
    text: str,
) -> list[str]:
    """
    Extract common explicit date formats.
    """
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b(?:january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:january|february|march|april|may|"
        r"june|july|august|september|october|november|"
        r"december)\s+\d{4}\b",
    ]

    matches: list[str] = []

    for pattern in patterns:
        matches.extend(
            re.findall(
                pattern,
                text.lower(),
            )
        )

    return matches


def _normalize_text(
    text: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.strip().lower(),
    )


def _tokenize(
    text: str,
) -> set[str]:
    return set(
        re.findall(
            r"\b[a-z0-9]+\b",
            _normalize_text(text),
        )
    )


def _detect_deterministic_conflict(
    candidate: str,
    existing: str,
    memory_type: str,
) -> MemoryComparisonResult | None:
    """
    Deterministic conflict detection runs before Gemini.
    """
    candidate_normalized = _normalize_text(
        candidate
    )
    existing_normalized = _normalize_text(
        existing
    )

    if (
        candidate_normalized
        == existing_normalized
    ):
        return MemoryComparisonResult(
            comparison_type="DUPLICATE",
            conflict_type="NONE",
            explanation=(
                "The candidate memory is identical "
                "to the existing memory."
            ),
        )

    if memory_type == "PROJECT":
        candidate_text = candidate_normalized
        existing_text = existing_normalized

        candidate_contextai = (
            "contextai" in candidate_text
        )
        existing_contextai = (
            "contextai" in existing_text
        )

        candidate_hackathon = (
            "hackathon" in candidate_text
            or "builders" in candidate_text
        )
        existing_hackathon = (
            "hackathon" in existing_text
            or "builders" in existing_text
        )

        candidate_operations = (
            "operations" in candidate_text
            and "reliability" in candidate_text
        )
        existing_operations = (
            "operations" in existing_text
            and "reliability" in existing_text
        )

        if (
            candidate_contextai
            and existing_contextai
            and (
                (
                    candidate_hackathon
                    and existing_operations
                )
                or (
                    candidate_operations
                    and existing_hackathon
                )
            )
        ):
            return MemoryComparisonResult(
                comparison_type="CONFLICT",
                conflict_type=(
                    "PROJECT_CONTEXT_CHANGED"
                ),
                explanation=(
                    "Both memories refer to ContextAI "
                    "but identify different project contexts."
                ),
            )

    negative_patterns = [
        r"\bnot\s+the\s+(.+?)(?:\.|,|$)",
        r"\binstead\s+of\s+(.+?)(?:\.|,|$)",
        r"\bno\s+longer\s+(.+?)(?:\.|,|$)",
    ]

    existing_tokens = _tokenize(existing)

    for pattern in negative_patterns:
        match = re.search(
            pattern,
            candidate_normalized,
        )

        if not match:
            continue

        mentioned = match.group(1)
        mentioned_tokens = _tokenize(
            mentioned
        )

        if mentioned_tokens & existing_tokens:
            return MemoryComparisonResult(
                comparison_type="CONFLICT",
                conflict_type="VALUE_CHANGED",
                explanation=(
                    "The candidate explicitly changes "
                    "a value previously stated in the "
                    "existing memory."
                ),
            )

    if memory_type == "DEADLINE":
        candidate_dates = (
            _extract_explicit_dates(candidate)
        )
        existing_dates = (
            _extract_explicit_dates(existing)
        )

        if (
            candidate_dates
            and existing_dates
            and candidate_dates != existing_dates
        ):
            return MemoryComparisonResult(
                comparison_type="CONFLICT",
                conflict_type="DEADLINE_CHANGED",
                explanation=(
                    "The candidate contains a different "
                    "explicit deadline from the existing memory."
                ),
            )

    state_change_patterns = [
        r"\bchanged from\b",
        r"\bno longer\b",
        r"\binstead of\b",
        r"\bnow working on\b",
        r"\bswitched to\b",
        r"\bmoved to\b",
    ]

    for pattern in state_change_patterns:
        if re.search(
            pattern,
            candidate_normalized,
        ):
            return MemoryComparisonResult(
                comparison_type="CONFLICT",
                conflict_type="STATE_CHANGED",
                explanation=(
                    "The candidate explicitly indicates "
                    "that the previously stated state has changed."
                ),
            )

    return None


def _safe_comparison_fallback(
    candidate: str,
    existing: str,
    memory_type: str,
) -> MemoryComparisonResult:
    """
    Safe fallback if Gemini comparison fails.
    """
    deterministic = (
        _detect_deterministic_conflict(
            candidate,
            existing,
            memory_type,
        )
    )

    if deterministic is not None:
        return deterministic

    candidate_tokens = _tokenize(
        candidate
    )
    existing_tokens = _tokenize(
        existing
    )

    overlap = (
        len(candidate_tokens & existing_tokens)
        / max(
            1,
            len(
                candidate_tokens
                | existing_tokens
            ),
        )
    )

    if overlap < 0.10:
        return MemoryComparisonResult(
            comparison_type="UNRELATED",
            conflict_type="NONE",
            explanation=(
                "The memories have very little "
                "semantic/token overlap."
            ),
        )

    if overlap >= 0.35:
        return MemoryComparisonResult(
            comparison_type="RELATED",
            conflict_type="NONE",
            explanation=(
                "The memories appear related, "
                "but no deterministic conflict was found."
            ),
        )

    return MemoryComparisonResult(
        comparison_type="UNRELATED",
        conflict_type="NONE",
        explanation=(
            "No reliable conflict or duplicate "
            "relationship could be established."
        ),
    )


def compare_memories(
    candidate: str,
    existing: str,
    memory_type: str,
) -> MemoryComparisonResult:
    """
    Compare candidate and existing memory.

    Deterministic checks are always preferred.
    Gemini is used for cases requiring semantic judgment.
    """
    deterministic = (
        _detect_deterministic_conflict(
            candidate,
            existing,
            memory_type,
        )
    )

    if deterministic is not None:
        return deterministic

    try:
        client = get_gemini_client()

        prompt = f"""
Compare these two user memories.

Memory type:
{memory_type}

Candidate memory:
{candidate}

Existing memory:
{existing}

Return JSON matching this schema:

{{
  "comparison_type": "UNRELATED | DUPLICATE | CONFLICT | RELATED",
  "conflict_type": "NONE or a concise conflict type",
  "explanation": "brief explanation"
}}

Rules:
- DUPLICATE means the same information is stated.
- CONFLICT means the candidate changes or contradicts
  the existing memory.
- RELATED means they are connected but do not conflict.
- UNRELATED means they are about different subjects.
"""

        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MemoryComparisonResult,
            ),
        )

        if not response.parsed:
            raise RuntimeError(
                "Gemini returned no parsed comparison."
            )

        return MemoryComparisonResult.model_validate(
            response.parsed
        )

    except Exception:
        return _safe_comparison_fallback(
            candidate,
            existing,
            memory_type,
        )


def analyze_memory_candidate(
    session: Session,
    user_id: int,
    candidate: str,
    memory_type: str,
    exclude_memory_id: int | None = None,
) -> dict:
    """
    Analyze a candidate against existing active memories.

    Decision flow:
      1. Find semantically related memories.
      2. Ignore distant memories.
      3. Detect duplicates.
      4. Detect conflicts.
      5. Calculate scores.
      6. Return NEW when no conflict exists.
    """
    related_memories = find_related_memories(
        session=session,
        user_id=user_id,
        content=candidate,
        limit=8,
        exclude_memory_id=exclude_memory_id,
    )

    related_memories = [
        (memory, distance)
        for memory, distance in related_memories
        if distance <= 0.45
    ]

    if not related_memories:
        return {
            "decision": "NEW",
            "comparison": None,
            "existing_memory": None,
            "distance": None,
            "candidate_score": None,
            "existing_score": None,
        }

    best_conflict: dict | None = None
    best_duplicate: dict | None = None

    for existing, distance in related_memories:
        comparison = compare_memories(
            candidate=candidate,
            existing=existing.content,
            memory_type=memory_type,
        )

        if (
            comparison.comparison_type
            == "DUPLICATE"
        ):
            if (
                best_duplicate is None
                or distance < best_duplicate["distance"]
            ):
                best_duplicate = {
                    "comparison": comparison,
                    "existing_memory": existing,
                    "distance": distance,
                }

        elif (
            comparison.comparison_type
            == "CONFLICT"
        ):
            if (
                best_conflict is None
                or distance < best_conflict["distance"]
            ):
                best_conflict = {
                    "comparison": comparison,
                    "existing_memory": existing,
                    "distance": distance,
                }

    if best_duplicate is not None:
        existing = best_duplicate[
            "existing_memory"
        ]

        existing_score = (
            calculate_confidence_score(
                importance=existing.importance,
                source_type=existing.source_type,
                created_at=existing.created_at,
                content=existing.content,
                confirmation_count=(
                    existing.confirmation_count
                ),
                has_conflict=False,
            )
        )

        return {
            "decision": "DUPLICATE",
            "comparison": best_duplicate[
                "comparison"
            ],
            "existing_memory": existing,
            "distance": best_duplicate[
                "distance"
            ],
            "candidate_score": existing_score,
            "existing_score": existing_score,
        }

    if best_conflict is not None:
        existing = best_conflict[
            "existing_memory"
        ]

        candidate_score = (
            calculate_confidence_score(
                importance=0.70,
                source_type="agent",
                created_at=datetime.now(
                    timezone.utc
                ),
                content=candidate,
                confirmation_count=0,
                has_conflict=True,
            )
        )

        existing_score = (
            calculate_confidence_score(
                importance=existing.importance,
                source_type=existing.source_type,
                created_at=existing.created_at,
                content=existing.content,
                confirmation_count=(
                    existing.confirmation_count
                ),
                has_conflict=True,
            )
        )

        return {
            "decision": "CONFLICT",
            "comparison": best_conflict[
                "comparison"
            ],
            "existing_memory": existing,
            "distance": best_conflict[
                "distance"
            ],
            "candidate_score": candidate_score,
            "existing_score": existing_score,
        }

    return {
        "decision": "NEW",
        "comparison": None,
        "existing_memory": None,
        "distance": None,
        "candidate_score": None,
        "existing_score": None,
    }


def build_resolution_reason(
    *,
    comparison: MemoryComparisonResult,
    winner: str,
    candidate_score: float,
    existing_score: float,
    candidate_source: str,
    existing_source: str,
) -> str:
    """
    Build a human-readable explanation for conflict resolution.
    """
    if winner == "NEW_MEMORY_WINS":
        winner_text = "new memory"
    else:
        winner_text = "existing memory"

    candidate_reliability = SOURCE_RELIABILITY.get(
        candidate_source,
        SOURCE_RELIABILITY["inferred"],
    )

    existing_reliability = SOURCE_RELIABILITY.get(
        existing_source,
        SOURCE_RELIABILITY["inferred"],
    )

    return (
        f"{winner_text} selected based on confidence "
        f"scores. New score={candidate_score:.4f}, "
        f"existing score={existing_score:.4f}. "
        f"New source reliability="
        f"{candidate_reliability:.2f}, "
        f"existing source reliability="
        f"{existing_reliability:.2f}. "
        f"Conflict type={comparison.conflict_type}. "
        f"{comparison.explanation}"
    )


def create_memory_conflict(
    session: Session,
    *,
    user_id: int,
    existing_memory: Memory,
    new_memory: Memory,
    comparison: MemoryComparisonResult,
    existing_score: float,
    new_score: float,
    resolution: str,
    resolution_reason: str,
) -> MemoryConflict:
    """
    Persist a memory conflict using the actual
    MemoryConflict database model.
    """
    if existing_memory.id is None:
        raise ValueError(
            "Existing memory must have an ID."
        )

    if new_memory.id is None:
        raise ValueError(
            "New memory must have an ID."
        )

    if resolution == "NEW_MEMORY_WINS":
        winning_memory_id = new_memory.id
    else:
        winning_memory_id = existing_memory.id

    conflict = MemoryConflict(
        user_id=user_id,
        old_memory_id=existing_memory.id,
        new_memory_id=new_memory.id,
        winning_memory_id=winning_memory_id,
        comparison_type=(
            comparison.comparison_type
        ),
        conflict_type=(
            comparison.conflict_type
        ),
        old_confidence=existing_memory.confidence,
        new_confidence=new_memory.confidence,
        old_score=existing_score,
        new_score=new_score,
        resolution=resolution,
        reason=resolution_reason,
    )

    session.add(conflict)

    return conflict


def get_memory_conflict(
    session: Session,
    *,
    user_id: int,
    conflict_id: int,
) -> MemoryConflict | None:
    """
    Get one conflict belonging to the current user.
    """
    return session.exec(
        select(MemoryConflict).where(
            MemoryConflict.id == conflict_id,
            MemoryConflict.user_id == user_id,
        )
    ).first()


def get_user_conflicts(
    session: Session,
    *,
    user_id: int,
    limit: int = 100,
) -> list[MemoryConflict]:
    """
    Return recent conflict history for a user.
    """
    statement = (
        select(MemoryConflict)
        .where(
            MemoryConflict.user_id == user_id
        )
        .order_by(
            MemoryConflict.created_at.desc()
        )
        .limit(limit)
    )

    return list(
        session.exec(statement).all()
    )


def get_memory_history(
    session: Session,
    *,
    user_id: int,
    memory_id: int,
) -> list[MemoryConflict]:
    """
    Return conflicts involving a specific memory.
    """
    statement = (
        select(MemoryConflict)
        .where(
            MemoryConflict.user_id == user_id,
            (
                (MemoryConflict.old_memory_id == memory_id)
                | (
                    MemoryConflict.new_memory_id
                    == memory_id
                )
            ),
        )
        .order_by(
            MemoryConflict.created_at.desc()
        )
    )

    return list(
        session.exec(statement).all()
    )


def get_memory_intelligence_summary(
    session: Session,
    *,
    user_id: int,
) -> dict:
    """
    Generate summary statistics for the user's
    memory conflict history.
    """
    conflicts = get_user_conflicts(
        session=session,
        user_id=user_id,
        limit=100000,
    )

    new_memory_wins = sum(
        1
        for conflict in conflicts
        if conflict.resolution
        == "NEW_MEMORY_WINS"
    )

    existing_memory_wins = sum(
        1
        for conflict in conflicts
        if conflict.resolution
        == "EXISTING_MEMORY_WINS"
    )

    latest_conflict_at = (
        conflicts[0].created_at
        if conflicts
        else None
    )

    return {
        "total_conflicts": len(conflicts),
        "new_memory_wins": new_memory_wins,
        "existing_memory_wins": existing_memory_wins,
        "latest_conflict_at": latest_conflict_at,
    }


# ------------------------------------------------------------------
# Backward-compatible aliases
# ------------------------------------------------------------------

def get_memory_conflicts(
    session: Session,
    user_id: int,
) -> list[MemoryConflict]:
    return get_user_conflicts(
        session=session,
        user_id=user_id,
        limit=100000,
    )


def get_memory_conflict_summary(
    session: Session,
    user_id: int,
) -> dict:
    return get_memory_intelligence_summary(
        session=session,
        user_id=user_id,
    )