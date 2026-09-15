import math
import re
from datetime import datetime, timezone
from typing import Any

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


# ============================================================
# SOURCE RELIABILITY
# ============================================================

SOURCE_RELIABILITY: dict[str, float] = {
    # Highest trust
    "verified_external_action": 1.00,
    "verified_action": 1.00,

    # Explicit user information
    "explicit_user": 0.98,
    "conversation": 0.90,

    # External sources
    "document": 0.88,
    "calendar": 0.86,
    "email": 0.82,

    # Agent-generated information
    "agent": 0.70,

    # Lowest trust
    "inferred": 0.55,
}


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client() -> genai.Client:
    """
    Create and return the Gemini client.
    """

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.gemini_api_key,
    )


# ============================================================
# SOURCE RELIABILITY
# ============================================================

def get_source_reliability(
    source_type: str,
) -> float:
    """
    Return a controlled reliability score for a memory source.

    Unknown sources intentionally receive a conservative score.
    """

    normalized = (
        source_type or "conversation"
    ).strip().lower()

    return SOURCE_RELIABILITY.get(
        normalized,
        0.60,
    )


# ============================================================
# RECENCY
# ============================================================

def calculate_recency_score(
    created_at: datetime,
) -> float:
    """
    Calculate a 0–1 recency score.

    The score decays gradually instead of making old memories
    immediately invalid.
    """

    now = datetime.now(timezone.utc)

    if created_at.tzinfo is None:
        created_at = created_at.replace(
            tzinfo=timezone.utc
        )

    age_seconds = max(
        0.0,
        (
            now - created_at
        ).total_seconds(),
    )

    age_days = age_seconds / 86400.0

    return max(
        0.0,
        min(
            1.0,
            math.exp(-age_days / 180.0),
        ),
    )


# ============================================================
# EXPLICITNESS
# ============================================================

EXPLICIT_PATTERNS = [
    r"\bi prefer\b",
    r"\bi like\b",
    r"\bi dislike\b",
    r"\bi want\b",
    r"\bi need\b",
    r"\bi decided\b",
    r"\bi chose\b",
    r"\bmy deadline\b",
    r"\bdeadline is\b",
    r"\bthe deadline is\b",
    r"\bhas been moved\b",
    r"\bchanged to\b",
    r"\bupdated to\b",
    r"\bmy project\b",
    r"\bi am working on\b",
    r"\bi'm working on\b",
    r"\bi use\b",
    r"\bi always\b",
    r"\bi never\b",
]


def calculate_explicitness(
    content: str,
) -> float:
    """
    Estimate how explicitly a fact is stated.

    This is deliberately deterministic so the confidence score
    remains explainable.
    """

    text = content.strip().lower()

    if not text:
        return 0.0

    matches = sum(
        1
        for pattern in EXPLICIT_PATTERNS
        if re.search(pattern, text)
    )

    if matches >= 2:
        return 1.0

    if matches == 1:
        return 0.95

    if len(text.split()) >= 4:
        return 0.80

    return 0.65


# ============================================================
# REPEATED CONFIRMATION
# ============================================================

def calculate_confirmation_score(
    confirmation_count: int,
) -> float:
    """
    Repeated confirmation increases confidence.

    0 confirmations -> 0.50
    1 confirmation  -> 0.60
    ...
    5+ confirmations -> 1.00
    """

    count = max(
        0,
        confirmation_count,
    )

    return min(
        1.0,
        0.50 + (count * 0.10),
    )


# ============================================================
# CONFIDENCE SCORE
# ============================================================

def calculate_confidence_score(
    *,
    base_confidence: float,
    source_type: str,
    created_at: datetime,
    content: str,
    confirmation_count: int,
    has_conflict: bool,
) -> MemoryScoreBreakdown:
    """
    Calculate the Phase 10 explainable confidence score.

    Weights:
        base confidence     25%
        source reliability  25%
        recency             15%
        explicitness        15%
        confirmation        15%
        conflict factor      5%
    """

    base = max(
        0.0,
        min(
            1.0,
            float(base_confidence),
        ),
    )

    source = get_source_reliability(
        source_type
    )

    recency = calculate_recency_score(
        created_at
    )

    explicitness = calculate_explicitness(
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
        (base * 0.25)
        + (source * 0.25)
        + (recency * 0.15)
        + (explicitness * 0.15)
        + (confirmation * 0.15)
        + (conflict_factor * 0.05)
    )

    final_score = max(
        0.0,
        min(
            1.0,
            weighted_score,
        ),
    )

    return MemoryScoreBreakdown(
        base_confidence=round(
            base,
            4,
        ),
        source_reliability=round(
            source,
            4,
        ),
        recency=round(
            recency,
            4,
        ),
        explicitness=round(
            explicitness,
            4,
        ),
        confirmation=round(
            confirmation,
            4,
        ),
        conflict_factor=round(
            conflict_factor,
            4,
        ),
        final_score=round(
            final_score,
            4,
        ),
    )


# ============================================================
# EMBEDDING
# ============================================================

def generate_intelligence_embedding(
    text: str,
) -> list[float]:
    """
    Generate the same 1536-dimensional Gemini embedding
    used by the existing Memory model.
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
            "Gemini did not return an embedding."
        )

    embedding = response.embeddings[0].values

    if not embedding:
        raise RuntimeError(
            "Gemini returned an empty embedding."
        )

    if len(embedding) != 1536:
        raise RuntimeError(
            "Expected 1536 dimensions, "
            f"received {len(embedding)}."
        )

    return list(embedding)


# ============================================================
# RELATED MEMORY SEARCH
# ============================================================

def find_related_memories(
    session: Session,
    user_id: int,
    embedding: list[float],
    limit: int = 8,
) -> list[tuple[Memory, float]]:
    """
    Find active memories that are semantically related
    to the new candidate.
    """

    distance_expression = (
        Memory.embedding.cosine_distance(
            embedding
        ).label("distance")
    )

    statement = (
        select(
            Memory,
            distance_expression,
        )
        .where(
            Memory.user_id == user_id,
            Memory.is_active.is_(True),
            Memory.embedding.is_not(None),
        )
        .order_by(
            distance_expression
        )
        .limit(limit)
    )

    results = session.exec(
        statement
    ).all()

    return [
        (
            memory,
            float(distance),
        )
        for memory, distance in results
    ]


# ============================================================
# DETERMINISTIC DATE EXTRACTION
# ============================================================

MONTH_NAMES = (
    "January|February|March|April|May|June|July|"
    "August|September|October|November|December"
)


def _extract_explicit_dates(
    content: str,
) -> list[str]:
    """
    Extract common written date formats from memory text.

    Supported examples:

        September 12, 2099
        September 15, 2099
        Sep 12, 2099
        Sep 15, 2099

    The function intentionally focuses on explicit dates.
    It does not attempt broad natural-language date inference.
    """

    pattern = re.compile(
        rf"\b({MONTH_NAMES})\s+"
        r"([0-9]{1,2}),\s*"
        r"([0-9]{4})\b",
        re.IGNORECASE,
    )

    matches = pattern.findall(content)

    normalized_dates: list[str] = []

    for month, day, year in matches:
        normalized = (
            f"{month.lower()} "
            f"{int(day):02d}, "
            f"{year}"
        )

        normalized_dates.append(
            normalized
        )

    return normalized_dates


# ============================================================
# DETERMINISTIC MEMORY COMPARISON
# ============================================================

def deterministic_memory_comparison(
    *,
    new_content: str,
    existing_content: str,
    memory_type: str,
) -> MemoryComparisonResult:
    """
    Deterministic fallback used when Gemini comparison is
    unavailable.

    This fallback is intentionally conservative.

    Currently supported high-confidence rule:

        DEADLINE + two explicit different dates
        -> CONFLICT / DEADLINE_CHANGED

    If there is not enough deterministic evidence, the function
    returns RELATED rather than inventing a conflict.
    """

    normalized_type = (
        memory_type or ""
    ).strip().upper()

    # --------------------------------------------------------
    # Deadline-specific deterministic conflict detection.
    # --------------------------------------------------------

    if normalized_type == "DEADLINE":
        existing_dates = _extract_explicit_dates(
            existing_content
        )

        new_dates = _extract_explicit_dates(
            new_content
        )

        # We only make a deterministic conflict decision when
        # exactly one explicit date exists in each memory.
        if (
            len(existing_dates) == 1
            and len(new_dates) == 1
        ):
            existing_date = existing_dates[0]
            new_date = new_dates[0]

            if existing_date != new_date:
                return MemoryComparisonResult(
                    comparison_type="CONFLICT",
                    conflict_type="DEADLINE_CHANGED",
                    explanation=(
                        "The existing and new deadline memories "
                        "refer to the same deadline context but "
                        "contain different explicit dates. "
                        f"Existing date: {existing_date}; "
                        f"new date: {new_date}."
                    ),
                )

            return MemoryComparisonResult(
                comparison_type="RELATED",
                conflict_type="NONE",
                explanation=(
                    "Both deadline memories contain the same "
                    "explicit date."
                ),
            )

    # --------------------------------------------------------
    # Safe fallback for unsupported/ambiguous cases.
    # --------------------------------------------------------

    return MemoryComparisonResult(
        comparison_type="RELATED",
        conflict_type="NONE",
        explanation=(
            "Deterministic memory comparison did not find "
            "enough evidence to classify the memories as a "
            "conflict."
        ),
    )


# ============================================================
# SAFE GEMINI FALLBACK
# ============================================================

def _safe_comparison_fallback(
    *,
    reason: str,
    new_content: str,
    existing_content: str,
    memory_type: str,
) -> MemoryComparisonResult:
    """
    Safely handle Gemini comparison failures.

    Gemini remains the primary intelligence layer.

    When Gemini is unavailable, deterministic rules are used
    for high-confidence cases such as explicit deadline changes.

    Unknown cases remain RELATED so the system never invents
    a conflict without sufficient evidence.
    """

    deterministic_result = (
        deterministic_memory_comparison(
            new_content=new_content,
            existing_content=existing_content,
            memory_type=memory_type,
        )
    )

    if deterministic_result.comparison_type == "CONFLICT":
        return MemoryComparisonResult(
            comparison_type="CONFLICT",
            conflict_type=deterministic_result.conflict_type,
            explanation=(
                f"{deterministic_result.explanation} "
                f"Gemini comparison was unavailable "
                f"({reason}), so the deterministic "
                "high-confidence fallback was used."
            ),
        )

    if deterministic_result.comparison_type == "DUPLICATE":
        return deterministic_result

    return MemoryComparisonResult(
        comparison_type="RELATED",
        conflict_type="NONE",
        explanation=(
            "Memory intelligence comparison was unavailable. "
            "No deterministic conflict was established, so "
            "the memory was preserved without automatic "
            f"conflict resolution. Reason: {reason}"
        ),
    )


# ============================================================
# GEMINI MEMORY COMPARISON
# ============================================================

def compare_memories(
    new_content: str,
    existing_content: str,
    memory_type: str,
) -> MemoryComparisonResult:
    """
    Ask Gemini whether two semantically related memories are
    duplicates, conflicts, merely related, or unrelated.

    Gemini is the primary comparison engine.

    If Gemini temporarily fails, the deterministic fallback
    handles high-confidence cases.
    """

    try:
        client = get_gemini_client()

        prompt = f"""
You are the memory conflict detection component of a
persistent AI assistant.

Compare the EXISTING memory with the NEW memory.

Memory type:
{memory_type}

EXISTING MEMORY:
{existing_content}

NEW MEMORY:
{new_content}

Classify the relationship as exactly one of:

UNRELATED
DUPLICATE
CONFLICT
RELATED

Rules:

1. DUPLICATE:
   Both memories express essentially the same fact.
   A duplicate should NOT create a new competing memory.

2. CONFLICT:
   Both memories refer to the same underlying fact,
   preference, decision, task, project, person, or deadline,
   but their values or states cannot both represent the
   current truth.

3. RELATED:
   The memories are connected but can both remain true.

4. UNRELATED:
   They concern different facts.

For conflicts:
- Identify the conflict type.
- Explain the conflict briefly.
- Do not invent information.
- Prefer explicit factual differences.

Return JSON only.
"""

        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MemoryComparisonResult,
            ),
        )

    except Exception as exc:
        error_type = type(exc).__name__

        print(
            "Memory comparison service unavailable: "
            f"{error_type}: {exc}"
        )

        return _safe_comparison_fallback(
            reason=error_type,
            new_content=new_content,
            existing_content=existing_content,
            memory_type=memory_type,
        )

    if not response.text:
        return _safe_comparison_fallback(
            reason="Gemini returned an empty response.",
            new_content=new_content,
            existing_content=existing_content,
            memory_type=memory_type,
        )

    try:
        return MemoryComparisonResult.model_validate_json(
            response.text
        )

    except Exception as exc:
        error_type = type(exc).__name__

        print(
            "Memory comparison parsing error: "
            f"{error_type}: {exc}"
        )

        return _safe_comparison_fallback(
            reason=f"response parsing error ({error_type})",
            new_content=new_content,
            existing_content=existing_content,
            memory_type=memory_type,
        )


# ============================================================
# CANDIDATE ANALYSIS
# ============================================================

def analyze_memory_candidate(
    session: Session,
    user_id: int,
    *,
    content: str,
    memory_type: str,
    confidence: float,
    source_type: str,
    source_id: str | None,
    embedding: list[float],
) -> dict[str, Any]:
    """
    Analyze a new memory candidate against existing active memories.

    No database mutation occurs here.
    """

    related = find_related_memories(
        session=session,
        user_id=user_id,
        embedding=embedding,
        limit=8,
    )

    # Only reasonably similar memories should reach comparison.
    related = [
        (
            memory,
            distance,
        )
        for memory, distance in related
        if distance <= 0.45
    ]

    best_conflict: dict[str, Any] | None = None

    for existing, distance in related:
        comparison = compare_memories(
            new_content=content,
            existing_content=existing.content,
            memory_type=memory_type,
        )

        # ----------------------------------------------------
        # Exact semantic duplicate.
        # ----------------------------------------------------

        if comparison.comparison_type == "DUPLICATE":
            return {
                "decision": "DUPLICATE",
                "existing_memory": existing,
                "distance": distance,
                "comparison": comparison,
            }

        # ----------------------------------------------------
        # Only conflicts continue into score comparison.
        # ----------------------------------------------------

        if comparison.comparison_type != "CONFLICT":
            continue

        # ----------------------------------------------------
        # Score the new candidate.
        # ----------------------------------------------------

        candidate_score = calculate_confidence_score(
            base_confidence=confidence,
            source_type=source_type,
            created_at=datetime.now(timezone.utc),
            content=content,
            confirmation_count=0,
            has_conflict=True,
        )

        # ----------------------------------------------------
        # Score the existing memory.
        # ----------------------------------------------------

        existing_score = calculate_confidence_score(
            base_confidence=existing.confidence,
            source_type=existing.source_type,
            created_at=existing.created_at,
            content=existing.content,
            confirmation_count=existing.confirmation_count,
            has_conflict=True,
        )

        conflict_data = {
            "decision": "CONFLICT",
            "existing_memory": existing,
            "distance": distance,
            "comparison": comparison,
            "candidate_score": candidate_score,
            "existing_score": existing_score,
        }

        # ----------------------------------------------------
        # Keep the closest conflicting memory.
        # ----------------------------------------------------

        if (
            best_conflict is None
            or distance
            < best_conflict["distance"]
        ):
            best_conflict = conflict_data

    # --------------------------------------------------------
    # A conflict was found.
    # --------------------------------------------------------

    if best_conflict:
        return best_conflict

    # --------------------------------------------------------
    # No conflict and no duplicate.
    # --------------------------------------------------------

    return {
        "decision": "NEW",
        "existing_memory": None,
        "distance": None,
        "comparison": None,
    }


# ============================================================
# RESOLUTION REASON
# ============================================================

def build_resolution_reason(
    *,
    existing: Memory,
    new_content: str,
    existing_score: MemoryScoreBreakdown,
    new_score: MemoryScoreBreakdown,
    winner: str,
    comparison: MemoryComparisonResult,
    new_source_type: str = "conversation",
) -> str:
    """
    Build a human-readable explanation of the resolution.

    new_source_type is optional for backward compatibility.
    """

    if winner == "NEW":
        winner_text = (
            "The new memory was selected as current."
        )
    else:
        winner_text = (
            "The existing memory was retained as current."
        )

    new_source_reliability = get_source_reliability(
        new_source_type
    )

    return (
        f"{comparison.explanation} "
        f"{winner_text} "
        f"Existing score={existing_score.final_score:.2f}; "
        f"new score={new_score.final_score:.2f}. "
        f"Existing source={existing.source_type}; "
        f"new source={new_source_type} "
        f"with reliability "
        f"{new_source_reliability:.2f}."
    )


# ============================================================
# CONFLICT RECORD
# ============================================================

def create_memory_conflict(
    session: Session,
    *,
    user_id: int,
    old_memory: Memory,
    new_memory: Memory,
    winning_memory: Memory,
    comparison: MemoryComparisonResult,
    old_score: MemoryScoreBreakdown,
    new_score: MemoryScoreBreakdown,
    reason: str,
) -> MemoryConflict:
    """
    Persist a complete Phase 10 conflict-resolution record.
    """

    resolution = (
        "NEW_MEMORY_WINS"
        if winning_memory.id == new_memory.id
        else "EXISTING_MEMORY_WINS"
    )

    conflict = MemoryConflict(
        user_id=user_id,
        old_memory_id=int(old_memory.id),
        new_memory_id=int(new_memory.id),
        winning_memory_id=int(
            winning_memory.id
        ),
        comparison_type="CONFLICT",
        conflict_type=comparison.conflict_type,
        old_confidence=old_memory.confidence,
        new_confidence=new_memory.confidence,
        old_score=old_score.final_score,
        new_score=new_score.final_score,
        resolution=resolution,
        reason=reason,
    )

    session.add(conflict)

    return conflict


# ============================================================
# CONFLICT LISTING
# ============================================================

def get_user_conflicts(
    session: Session,
    user_id: int,
    limit: int = 50,
) -> list[MemoryConflict]:
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
        session.exec(statement)
    )


def get_memory_conflict(
    session: Session,
    user_id: int,
    conflict_id: int,
) -> MemoryConflict | None:
    statement = (
        select(MemoryConflict)
        .where(
            MemoryConflict.id == conflict_id,
            MemoryConflict.user_id == user_id,
        )
    )

    return session.exec(
        statement
    ).first()


def get_memory_history(
    session: Session,
    user_id: int,
    memory_id: int,
) -> list[MemoryConflict]:
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
        session.exec(statement)
    )


# ============================================================
# SUMMARY
# ============================================================

def get_memory_intelligence_summary(
    session: Session,
    user_id: int,
) -> dict[str, Any]:
    conflicts = get_user_conflicts(
        session=session,
        user_id=user_id,
        limit=10000,
    )

    new_wins = sum(
        1
        for conflict in conflicts
        if conflict.resolution
        == "NEW_MEMORY_WINS"
    )

    existing_wins = sum(
        1
        for conflict in conflicts
        if conflict.resolution
        == "EXISTING_MEMORY_WINS"
    )

    latest = (
        conflicts[0].created_at
        if conflicts
        else None
    )

    return {
        "total_conflicts": len(conflicts),
        "new_memory_wins": new_wins,
        "existing_memory_wins": existing_wins,
        "latest_conflict_at": latest,
    }