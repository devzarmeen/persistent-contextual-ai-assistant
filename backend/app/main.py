from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

# ---------------------------------------------------------------------------
# Existing Phase 0-9 routers
# ---------------------------------------------------------------------------
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.google import router as google_router
from app.api.routes.memories import router as memories_router
from fastapi.middleware.cors import CORSMiddleware
# ---------------------------------------------------------------------------
# Phase 10 routers
# ---------------------------------------------------------------------------
from app.api.routes.memory_intelligence import (
    router as memory_intelligence_router,
)

from app.api.routes.verifications import (
    router as verification_router,
)

# ---------------------------------------------------------------------------
# Configuration / database
# ---------------------------------------------------------------------------
from app.config import settings

from app.database import (
    engine,
    ensure_phase10_schema,
)

# ---------------------------------------------------------------------------
# Model imports
#
# These imports ensure that SQLModel knows about all application tables
# before SQLModel.metadata.create_all(engine) is executed.
# ---------------------------------------------------------------------------
from app.models import (
    Conversation,
    Document,
    DocumentChunk,
    GoogleConnection,
    Memory,
    MemoryConflict,
    Message,
    User,
    VerificationAction,
)


# ===========================================================================
# Application lifespan
# ===========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Startup:
        1. Create missing database tables.
        2. Apply the Phase 10 compatibility migration.

    Important:
        create_all() does not delete existing tables or rows.
        ensure_phase10_schema() only adds the missing column when necessary.
    """

    # -----------------------------------------------------------------------
    # Step 1:
    # Create missing SQLModel tables.
    #
    # Existing tables and existing rows are preserved.
    # -----------------------------------------------------------------------
    SQLModel.metadata.create_all(engine)

    # -----------------------------------------------------------------------
    # Step 2:
    # Apply Phase 10 database compatibility migration.
    #
    # This adds confirmation_count to an existing memories table if needed.
    # -----------------------------------------------------------------------
    ensure_phase10_schema()

    # -----------------------------------------------------------------------
    # Application is ready.
    # -----------------------------------------------------------------------
    yield


# ===========================================================================
# FastAPI application
# ===========================================================================

app = FastAPI(
    title=settings.app_name,
    version="0.8.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ===========================================================================
# Existing Phase 0-9 routes
# ===========================================================================

app.include_router(auth_router)

app.include_router(chat_router)

app.include_router(memories_router)

app.include_router(documents_router)

app.include_router(google_router)


# ===========================================================================
# Phase 10 routes
# ===========================================================================

app.include_router(memory_intelligence_router)


# ===========================================================================
# Verification routes
#
# IMPORTANT:
# Keep this router enabled because later phases depend on verification.
# ===========================================================================

app.include_router(verification_router)


# ===========================================================================
# Root endpoint
# ===========================================================================

@app.get("/")
def root() -> dict[str, str]:
    """
    Basic API information endpoint.
    """

    return {
        "message": "Persistent Contextual AI Assistant API",
        "status": "running",
        "version": "0.8.0",
    }


# ===========================================================================
# Health endpoint
# ===========================================================================

@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Basic application health endpoint.

    This endpoint intentionally remains lightweight.
    """

    return {
        "status": "healthy",
        "service": settings.app_name,
    }