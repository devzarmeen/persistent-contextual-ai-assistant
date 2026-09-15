from io import BytesIO
from pathlib import Path

from google import genai
from google.genai import types
from sqlmodel import Session, select

from app.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
EMBEDDING_DIMENSIONS = 1536


def get_gemini_client() -> genai.Client:
    """
    Create a Gemini client using the configured API key.
    """
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def extract_text(
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> str:
    """
    Extract plain text from supported document types.
    """

    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".md", ".csv", ".json"}:
        return file_bytes.decode(
            "utf-8",
            errors="ignore",
        )

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        pages: list[str] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:
                print(
                    f"PDF page {page_number} extraction error: "
                    f"{type(exc).__name__}: {exc}"
                )
                page_text = ""

            if page_text.strip():
                pages.append(page_text)

        return "\n\n".join(pages)

    raise ValueError(
        "Unsupported file type. "
        "Supported: TXT, MD, CSV, JSON, PDF"
    )


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split document text into overlapping chunks.

    Example:
        chunk size = 1200
        overlap = 200

    This preserves context between adjacent chunks.
    """

    text = text.strip()

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def generate_embedding(text: str) -> list[float]:
    """
    Generate one 1536-dimensional Gemini embedding.
    """

    client = get_gemini_client()

    response = client.models.embed_content(
        model=settings.gemini_embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS,
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

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Invalid embedding dimensions. "
            f"Expected {EMBEDDING_DIMENSIONS}, "
            f"received {len(embedding)}."
        )

    return list(embedding)


def create_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate Gemini embeddings for document chunks.

    Embeddings are generated one chunk at a time intentionally.
    This keeps the implementation reliable and easy to retry
    when Gemini temporarily returns a 5xx error.
    """

    if not texts:
        return []

    embeddings: list[list[float]] = []

    for index, text in enumerate(texts):
        try:
            embedding = generate_embedding(text)
            embeddings.append(embedding)

        except Exception as exc:
            raise RuntimeError(
                "Failed to generate embedding for "
                f"document chunk {index}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    return embeddings


def save_document(
    session: Session,
    user_id: int,
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> Document:
    """
    Extract, store, chunk, embed, and persist a document.
    """

    text = extract_text(
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
    )

    if not text.strip():
        raise ValueError(
            "Could not extract readable text from the document."
        )

    document = Document(
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        file_size=len(file_bytes),
        content=text,
    )

    session.add(document)
    session.commit()
    session.refresh(document)

    chunks = split_text(text)

    if not chunks:
        raise ValueError(
            "Document does not contain enough text to create chunks."
        )

    try:
        embeddings = create_embeddings(chunks)

        for index, chunk in enumerate(chunks):
            document_chunk = DocumentChunk(
                document_id=document.id,
                user_id=user_id,
                chunk_index=index,
                content=chunk,
                embedding=embeddings[index],
            )

            session.add(document_chunk)

        session.commit()

    except Exception:
        session.rollback()

        # Remove the document created during this failed upload
        # so we don't leave an incomplete document behind.
        failed_document = session.get(
            Document,
            document.id,
        )

        if failed_document:
            session.delete(failed_document)
            session.commit()

        raise

    return document


def search_documents(
    session: Session,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[tuple[DocumentChunk, Document, float]]:
    """
    Semantic search over the authenticated user's document chunks.

    Returns:
        (chunk, document, similarity)

    similarity:
        1.0 = highly similar
        0.0 = dissimilar
    """

    query = query.strip()

    if not query:
        return []

    query_embedding = generate_embedding(query)

    distance_expression = (
        DocumentChunk.embedding.cosine_distance(
            query_embedding
        )
    )

    statement = (
        select(
            DocumentChunk,
            Document,
            distance_expression,
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            DocumentChunk.user_id == user_id,
            Document.user_id == user_id,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(distance_expression)
        .limit(limit)
    )

    rows = list(session.exec(statement))

    results: list[
        tuple[DocumentChunk, Document, float]
    ] = []

    for chunk, document, distance in rows:
        similarity = max(
            0.0,
            1.0 - float(distance),
        )

        results.append(
            (
                chunk,
                document,
                similarity,
            )
        )

    return results