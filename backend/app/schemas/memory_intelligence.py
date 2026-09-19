from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ComparisonType = Literal[
    "UNRELATED",
    "DUPLICATE",
    "CONFLICT",
    "RELATED",
]


class MemoryComparisonResult(BaseModel):
    comparison_type: ComparisonType

    conflict_type: str = Field(
        default="NONE",
        min_length=1,
        max_length=100,
    )

    explanation: str = Field(
        default="",
        max_length=2000,
    )


class MemoryScoreBreakdown(BaseModel):
    base_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    source_reliability: float = Field(
        ge=0.0,
        le=1.0,
    )

    recency: float = Field(
        ge=0.0,
        le=1.0,
    )

    explicitness: float = Field(
        ge=0.0,
        le=1.0,
    )

    confirmation: float = Field(
        ge=0.0,
        le=1.0,
    )

    conflict_factor: float = Field(
        ge=0.0,
        le=1.0,
    )

    final_score: float = Field(
        ge=0.0,
        le=1.0,
    )


class MemoryConflictResponse(BaseModel):
    id: int

    old_memory_id: int
    new_memory_id: int
    winning_memory_id: int

    comparison_type: str
    conflict_type: str

    old_confidence: float
    new_confidence: float

    old_score: float
    new_score: float

    resolution: str
    reason: str

    created_at: datetime
    resolved_at: datetime


class MemoryConflictDetailResponse(
    MemoryConflictResponse
):
    old_memory: dict
    new_memory: dict
    winning_memory: dict


class MemoryIntelligenceSummary(BaseModel):
    total_conflicts: int
    new_memory_wins: int
    existing_memory_wins: int
    latest_conflict_at: datetime | None