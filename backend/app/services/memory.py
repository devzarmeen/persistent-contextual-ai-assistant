from datetime import datetime, timezone

from google import genai
from google.genai import types
from sqlmodel import Session, select

from app.config import settings
from app.models.memory import Memory
from app.schemas.memory import (
    ExtractedMemory,
    MemoryExtractionResponse,
)
from app.services.memory_intelligence import (
    analyze_memory_candidate,
    build_resolution_reason,
    calculate_confidence_score,
    create_memory_conflict,
)


MEMORY_EXTRACTION_INSTRUCTION = """
You are the long-term memory extraction component of a persistent AI assistant.

Your job is to identify ONLY information from the user's message that is
useful across future conversations.

Store durable information such as:

- FACT: stable facts about the user
- PREFERENCE: user preferences
- DECISION: decisions the user has made
- TASK: meaningful ongoing tasks
- DEADLINE: dates or deadlines
- PERSON: important people and relationships
- PROJECT: projects the user is working on
- CONVERSATION: durable context that may matter later

Do NOT store:

- greetings
- casual conversation
- temporary wording
- generic questions
- information that is only useful for the current response
- assistant-generated information
- secrets, passwords, API keys, access tokens, or credentials

Be conservative.

Only extract a memory when it is genuinely useful later.

For every memory:
- write a clear standalone sentence
- assign importance from 0 to 1
- assign confidence from 0 to 1

If there is nothing worth remembering, return an empty memories list.
"""


def get_gemini_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.gemini_api_key,
    )


def extract_memories(
    user_message: str,
) -> list[ExtractedMemory]:
    """
    Ask Gemini to identify durable information
    from the user's message.
    """

    client = get_gemini_client()

    prompt = f"""
{MEMORY_EXTRACTION_INSTRUCTION}

USER MESSAGE:
{user_message}
"""

    response = client.models.generate_content(
        model=settings.gemini_chat_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MemoryExtractionResponse,
        ),
    )

    if not response.text:
        return []

    try:
        parsed = MemoryExtractionResponse.model_validate_json(
            response.text
        )

        return parsed.memories

    except Exception as exc:
        print(
            "Memory extraction parsing error: "
            f"{type(exc).__name__}: {exc}"
        )

        return []


def generate_embedding(
    text: str,
) -> list[float]:
    """
    Generate a 1536-dimensional Gemini embedding.

    The database uses Vector(1536), so this dimension
    must remain exactly 1536.
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
            f"Expected 1536 dimensions, "
            f"received {len(embedding)}."
        )

    return list(embedding)


def memory_already_exists(
    session: Session,
    user_id: int,
    content: str,
) -> Memory | None:
    """
    Avoid storing the exact same active memory repeatedly.
    """

    statement = (
        select(Memory)
        .where(
            Memory.user_id == user_id,
            Memory.content == content,
            Memory.is_active.is_(True),
        )
    )

    return session.exec(statement).first()


def _increment_confirmation(
    session: Session,
    memory: Memory,
) -> Memory:
    """
    Phase 10 repeated-confirmation handling.
    """

    memory.confirmation_count += 1

    score = calculate_confidence_score(
        base_confidence=memory.confidence,
        source_type=memory.source_type,
        created_at=memory.created_at,
        content=memory.content,
        confirmation_count=memory.confirmation_count,
        has_conflict=False,
    )

    memory.confidence = score.final_score
    memory.updated_at = datetime.now(timezone.utc)

    session.add(memory)
    session.commit()
    session.refresh(memory)

    return memory


def save_memory(
    session: Session,
    user_id: int,
    extracted_memory: ExtractedMemory,
    source_type: str = "conversation",
    source_id: str | None = None,
) -> Memory | None:
    """
    Save a durable memory with vector embedding.

    Phase 10:
    - exact duplicate confirmation
    - semantic duplicate detection
    - related-memory detection
    - deterministic/Gemini conflict detection
    - confidence scoring
    - winner selection
    - historical conflict preservation
    - losing-memory deactivation
    """

    # ========================================================
    # SOURCE METADATA
    # ========================================================
    #
    # The explicit function arguments remain the primary source.
    #
    # If the ExtractedMemory schema also carries source metadata,
    # preserve it when the caller did not explicitly override it.
    #
    extracted_source_type = getattr(
        extracted_memory,
        "source_type",
        None,
    )

    extracted_source_id = getattr(
        extracted_memory,
        "source_id",
        None,
    )

    if (
        source_type == "conversation"
        and extracted_source_type
    ):
        source_type = extracted_source_type

    if (
        source_id is None
        and extracted_source_id
    ):
        source_id = extracted_source_id

    # ========================================================
    # EXACT DUPLICATE
    # ========================================================

    existing = memory_already_exists(
        session=session,
        user_id=user_id,
        content=extracted_memory.content,
    )

    if existing:
        return _increment_confirmation(
            session=session,
            memory=existing,
        )

    # ========================================================
    # EMBEDDING
    # ========================================================

    embedding = generate_embedding(
        extracted_memory.content
    )

    # ========================================================
    # PHASE 10 ANALYSIS
    # ========================================================

    analysis = analyze_memory_candidate(
        session=session,
        user_id=user_id,
        content=extracted_memory.content,
        memory_type=extracted_memory.memory_type,
        confidence=extracted_memory.confidence,
        source_type=source_type,
        source_id=source_id,
        embedding=embedding,
    )

    decision = analysis["decision"]

    # ========================================================
    # SEMANTIC DUPLICATE
    # ========================================================

    if decision == "DUPLICATE":
        existing_memory = analysis["existing_memory"]

        if existing_memory is None:
            return None

        return _increment_confirmation(
            session=session,
            memory=existing_memory,
        )

    # ========================================================
    # CREATE NEW MEMORY
    # ========================================================

    now = datetime.now(timezone.utc)

    new_memory = Memory(
        user_id=user_id,
        memory_type=extracted_memory.memory_type,
        content=extracted_memory.content,
        importance=extracted_memory.importance,
        confidence=extracted_memory.confidence,
        source_type=source_type,
        source_id=source_id,
        embedding=embedding,
        is_active=True,
        confirmation_count=0,
        created_at=now,
        updated_at=now,
    )

    # ========================================================
    # NORMAL NEW MEMORY
    # ========================================================

    if decision == "NEW":
        score = calculate_confidence_score(
            base_confidence=extracted_memory.confidence,
            source_type=source_type,
            created_at=now,
            content=extracted_memory.content,
            confirmation_count=0,
            has_conflict=False,
        )

        new_memory.confidence = score.final_score

        session.add(new_memory)
        session.commit()
        session.refresh(new_memory)

        return new_memory

    # ========================================================
    # CONFLICT
    # ========================================================

    if decision == "CONFLICT":
        existing_memory = analysis["existing_memory"]
        comparison = analysis["comparison"]
        existing_score = analysis["existing_score"]
        new_score = analysis["candidate_score"]

        if existing_memory is None:
            new_memory.confidence = new_score.final_score

            session.add(new_memory)
            session.commit()
            session.refresh(new_memory)

            return new_memory

        # ----------------------------------------------------
        # Persist calculated confidence on new memory.
        # ----------------------------------------------------

        new_memory.confidence = new_score.final_score

        # ----------------------------------------------------
        # WINNER SELECTION
        #
        # Phase 10 rule:
        # The memory with the higher calculated intelligence
        # score becomes the current memory.
        #
        # If scores are exactly equal, retain the existing
        # memory to avoid unnecessary replacement.
        # ----------------------------------------------------

        if (
            new_score.final_score
            > existing_score.final_score
        ):
            winner = "NEW"
        else:
            winner = "EXISTING"

        # ----------------------------------------------------
        # Insert new memory first so the conflict record can
        # reference its database ID.
        # ----------------------------------------------------

        session.add(new_memory)
        session.flush()

        # ----------------------------------------------------
        # NEW MEMORY WINS
        # ----------------------------------------------------

        if winner == "NEW":
            existing_memory.is_active = False
            existing_memory.updated_at = datetime.now(
                timezone.utc
            )

            new_memory.is_active = True

            reason = build_resolution_reason(
                existing=existing_memory,
                new_content=new_memory.content,
                existing_score=existing_score,
                new_score=new_score,
                winner="NEW",
                comparison=comparison,
            )

            create_memory_conflict(
                session=session,
                user_id=user_id,
                old_memory=existing_memory,
                new_memory=new_memory,
                winning_memory=new_memory,
                comparison=comparison,
                old_score=existing_score,
                new_score=new_score,
                reason=reason,
            )

        # ----------------------------------------------------
        # EXISTING MEMORY WINS
        # ----------------------------------------------------

        else:
            new_memory.is_active = False

            existing_memory.is_active = True
            existing_memory.updated_at = datetime.now(
                timezone.utc
            )

            reason = build_resolution_reason(
                existing=existing_memory,
                new_content=new_memory.content,
                existing_score=existing_score,
                new_score=new_score,
                winner="EXISTING",
                comparison=comparison,
            )

            create_memory_conflict(
                session=session,
                user_id=user_id,
                old_memory=existing_memory,
                new_memory=new_memory,
                winning_memory=existing_memory,
                comparison=comparison,
                old_score=existing_score,
                new_score=new_score,
                reason=reason,
            )

        session.commit()
        session.refresh(new_memory)

        return new_memory

    # ========================================================
    # DEFENSIVE FALLBACK
    # ========================================================

    score = calculate_confidence_score(
        base_confidence=extracted_memory.confidence,
        source_type=source_type,
        created_at=now,
        content=extracted_memory.content,
        confirmation_count=0,
        has_conflict=False,
    )

    new_memory.confidence = score.final_score

    session.add(new_memory)
    session.commit()
    session.refresh(new_memory)

    return new_memory


def extract_and_save_memories(
    session: Session,
    user_id: int,
    user_message: str,
    source_type: str = "conversation",
    source_id: str | None = None,
) -> list[Memory]:
    """
    Extract durable memories from a user message and save them.

    Phase 10 intelligence is automatically triggered inside
    save_memory().
    """

    extracted_memories = extract_memories(
        user_message
    )

    saved_memories: list[Memory] = []

    for extracted_memory in extracted_memories:

        if extracted_memory.importance < 0.50:
            continue

        memory = save_memory(
            session=session,
            user_id=user_id,
            extracted_memory=extracted_memory,
            source_type=source_type,
            source_id=source_id,
        )

        if memory:
            saved_memories.append(memory)

    return saved_memories


def search_memories(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[tuple[Memory, float]]:
    """
    Semantic search over the user's active long-term memories.

    Superseded memories are intentionally excluded.
    They remain available through Phase 10 conflict history.
    """

    query_embedding = generate_embedding(query)

    distance_expression = (
        Memory.embedding.cosine_distance(
            query_embedding
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
        .order_by(distance_expression)
        .limit(limit)
    )

    results = session.exec(statement).all()

    return [
        (
            memory,
            float(distance),
        )
        for memory, distance in results
    ]


def get_user_memories(
    session: Session,
    user_id: int,
    limit: int = 50,
) -> list[Memory]:
    """
    Return the user's current active memories.
    """

    statement = (
        select(Memory)
        .where(
            Memory.user_id == user_id,
            Memory.is_active.is_(True),
        )
        .order_by(
            Memory.updated_at.desc()
        )
        .limit(limit)
    )

    return list(session.exec(statement))


def format_memories_for_prompt(
    memories: list[tuple[Memory, float]],
) -> str:
    """
    Convert retrieved memories into safe context for Gemini.
    """

    if not memories:
        return (
            "No relevant long-term memories were found."
        )

    lines: list[str] = []

    for memory, distance in memories:
        lines.append(
            f"- [{memory.memory_type}] "
            f"{memory.content} "
            f"(confidence={memory.confidence:.2f}, "
            f"confirmation_count="
            f"{memory.confirmation_count}, "
            f"similarity_distance="
            f"{distance:.4f})"
        )

    return "\n".join(lines)