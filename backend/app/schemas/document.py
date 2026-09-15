from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    file_size: int
    chunks: int
    created_at: datetime | None = None


class DocumentSearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    content: str
    similarity: float = Field(
        ge=0.0,
        le=1.0,
    )