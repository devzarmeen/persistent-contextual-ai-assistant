from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.database import get_session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.document import DocumentResponse, DocumentSearchResult
from app.services.auth import get_current_user, security
from app.services.documents import save_document, search_documents


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def build_document_response(
    session: Session,
    document: Document,
) -> DocumentResponse:
    chunks = list(
        session.exec(
            select(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            )
        )
    )

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        chunks=len(chunks),
        created_at=document.created_at,
    )


@router.post(
    "/upload",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    filename = (file.filename or "document").strip()
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            "Unsupported file type. Use TXT, MD, CSV, JSON, or PDF.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "Maximum file size is 10 MB.")

    try:
        document = save_document(
            session=session,
            user_id=user.id,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )

    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    except RuntimeError as exc:
        raise HTTPException(
            503,
            "Document processing service is temporarily unavailable.",
        ) from exc

    except Exception as exc:
        print(
            "Document upload error:",
            type(exc).__name__,
            exc,
        )
        raise HTTPException(
            500,
            "Document processing failed.",
        ) from exc

    return build_document_response(session, document)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    documents = list(
        session.exec(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
        )
    )

    return [
        build_document_response(session, document)
        for document in documents
    ]


@router.get("/search", response_model=list[DocumentSearchResult])
def search_document_chunks(
    q: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    query = q.strip()

    if not query:
        raise HTTPException(
            400,
            "Search query cannot be empty.",
        )

    try:
        results = search_documents(
            session,
            user.id,
            query,
            5,
        )
    except Exception as exc:
        raise HTTPException(
            503,
            "Document search is temporarily unavailable.",
        ) from exc

    return [
        DocumentSearchResult(
            document_id=document.id,
            filename=document.filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            similarity=round(similarity, 4),
        )
        for chunk, document, similarity in results
    ]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user.id,
        )
    ).first()

    if not document:
        raise HTTPException(
            404,
            "Document not found.",
        )

    chunks = list(
        session.exec(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document.id,
                DocumentChunk.user_id == user.id,
            )
            .order_by(DocumentChunk.chunk_index)
        )
    )

    return {
        "id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "content": document.content,
        "created_at": document.created_at,
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
            }
            for chunk in chunks
        ],
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    user = get_current_user(credentials, session)

    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user.id,
        )
    ).first()

    if not document:
        raise HTTPException(
            404,
            "Document not found.",
        )

    chunks = list(
        session.exec(
            select(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            )
        )
    )

    for chunk in chunks:
        session.delete(chunk)

    session.flush()
    session.delete(document)
    session.commit()

    return {
        "success": True,
        "id": document_id,
        "deleted": True,
    }