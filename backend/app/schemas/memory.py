from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MemoryType = Literal[
    "FACT",
    "PREFERENCE",
    "DECISION",
    "TASK",
    "DEADLINE",
    "PERSON",
    "PROJECT",
    "CONVERSATION",
]

class MemoryComparison(BaseModel):
    comparison_type: str
    conflict_type: str = "NONE"
    explanation: str

class ExtractedMemory(BaseModel):
    memory_type: MemoryType

    content: str = Field(
        min_length=3,
        max_length=1000,
    )

    importance: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class MemoryExtractionResponse(BaseModel):
    memories: list[ExtractedMemory]


class MemoryResponse(BaseModel):
    id: int
    memory_type: str
    content: str
    importance: float
    confidence: float
    source_type: str
    source_id: str | None
    is_active: bool
    confirmation_count: int
    created_at: datetime
    updated_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )