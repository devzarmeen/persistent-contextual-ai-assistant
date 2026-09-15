from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine

from app.config import settings


# ===========================================================================
# Database engine
# ===========================================================================

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


# ===========================================================================
# Database session dependency
# ===========================================================================

def get_session() -> Generator[Session, None, None]:
    """
    Provide a SQLModel database session.

    The session is automatically closed after the request finishes.
    """

    with Session(engine) as session:
        yield session


# ===========================================================================
# Phase 10 compatibility migration
# ===========================================================================

def ensure_phase10_schema() -> None:
    """
    Safely apply the Phase 10 database compatibility migration.

    Phase 10 introduced:

        memories.confirmation_count

    SQLModel.metadata.create_all() creates missing tables, but it does not
    add new columns to an already-existing table.

    Therefore this function:

        1. Checks whether the memories table exists.
        2. Checks whether confirmation_count exists.
        3. Adds confirmation_count only when it is missing.

    Safety:
        - Does not drop tables.
        - Does not delete rows.
        - Does not modify existing memory content.
        - Does not modify existing memory IDs.
        - Safe to execute repeatedly.
    """

    # -----------------------------------------------------------------------
    # Inspect current database schema.
    # -----------------------------------------------------------------------

    inspector = inspect(engine)

    tables = set(inspector.get_table_names())

    # -----------------------------------------------------------------------
    # If memories table does not exist, there is nothing to migrate.
    #
    # Normally SQLModel.metadata.create_all() runs before this function.
    # -----------------------------------------------------------------------

    if "memories" not in tables:
        return

    # -----------------------------------------------------------------------
    # Get existing columns from memories table.
    # -----------------------------------------------------------------------

    columns = {
        column["name"]
        for column in inspector.get_columns("memories")
    }

    # -----------------------------------------------------------------------
    # If confirmation_count already exists, do nothing.
    # -----------------------------------------------------------------------

    if "confirmation_count" in columns:
        return

    # -----------------------------------------------------------------------
    # Add Phase 10 confirmation_count column.
    #
    # Existing rows receive 0.
    # -----------------------------------------------------------------------

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE memories
                ADD COLUMN confirmation_count
                INTEGER NOT NULL DEFAULT 0
                """
            )
        )