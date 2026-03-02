"""
Project Repository - SQLAlchemy Core Implementation.

Implements the repository for Project entities and .qda database operations.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import create_engine, func, inspect, select, update

from src.contexts.projects.core.entities import Project, ProjectId, ProjectSummary
from src.contexts.projects.infra.schema import (
    create_all_contexts,
    project_settings,
)

if TYPE_CHECKING:
    from sqlalchemy import Connection, Engine

logger = logging.getLogger("qualcoder.projects.infra")


class SQLiteProjectRepository:
    """
    Repository for project database operations.

    Handles creation, validation, and loading of .qda project databases.
    """

    # Well-known settings keys for project metadata
    SETTING_PROJECT_NAME = "project_name"
    SETTING_PROJECT_OWNER = "owner"
    SETTING_PROJECT_MEMO = "project_memo"
    SETTING_CREATED_AT = "created_at"
    SETTING_LAST_OPENED_AT = "last_opened_at"

    # Tables required for a valid QualCoder V2 database
    REQUIRED_TABLES_V2 = frozenset(
        {"src_source", "prj_settings", "cod_code", "cod_category"}
    )
    # Tables for legacy V1 database (for backward compatibility)
    REQUIRED_TABLES_V1 = frozenset(
        {"source", "project_settings", "code_name", "code_cat"}
    )

    def __init__(self, connection: Connection | None = None) -> None:
        """
        Initialize the repository.

        Args:
            connection: Optional SQLAlchemy connection for operations on an
                       already-opened database. Not needed for create_database
                       or validate_database operations.
        """
        self._conn = connection

    def create_database(
        self, path: Path, name: str, owner: str | None = None
    ) -> Project:
        """
        Create a new .qda SQLite database with full schema.

        Steps:
        1. Validate path doesn't already exist
        2. Create SQLite database file at path
        3. Create all tables from both schemas (projects + coding)
        4. Initialize project_settings with name, owner, created_at
        5. Return Project entity

        Args:
            path: Path where the .qda file should be created
            name: Project name
            owner: Optional owner/creator name

        Returns:
            Project entity representing the new database

        Raises:
            FileExistsError: If a file already exists at the given path
            PermissionError: If the path is not writable
            ValueError: If path is not a valid file path
        """
        logger.debug("create_database: %s (name=%s)", path, name)
        # Step 1: Validate path doesn't already exist
        path = Path(path).resolve()
        if path.exists():
            raise FileExistsError(f"File already exists: {path}")

        # Ensure parent directory exists and is writable
        parent_dir = path.parent
        if not parent_dir.exists():
            raise ValueError(f"Parent directory does not exist: {parent_dir}")
        if not parent_dir.is_dir():
            raise ValueError(f"Parent path is not a directory: {parent_dir}")

        # Step 2: Create SQLite database file
        engine = self._create_engine(path)

        try:
            # Step 3: Create all tables from all bounded contexts
            create_all_contexts(engine)

            # Step 4: Initialize project_settings with metadata
            now = datetime.now(UTC)
            with engine.connect() as conn:
                self._set_setting(conn, self.SETTING_PROJECT_NAME, name)
                if owner:
                    self._set_setting(conn, self.SETTING_PROJECT_OWNER, owner)
                self._set_setting(conn, self.SETTING_CREATED_AT, now.isoformat())
                self._set_setting(conn, self.SETTING_LAST_OPENED_AT, now.isoformat())
                conn.commit()

            # Step 5: Return Project entity
            return Project(
                id=ProjectId.from_path(path),
                name=name,
                path=path,
                owner=owner,
                created_at=now,
                last_opened_at=now,
                summary=ProjectSummary(),
            )

        except Exception:
            logger.error("create_database failed: %s", path)
            # Clean up partial database on failure
            if path.exists():
                with contextlib.suppress(OSError):
                    path.unlink()
            raise

        finally:
            engine.dispose()

    def validate_database(self, path: Path) -> bool:
        """
        Check if path is a valid QualCoder .qda database.

        Validates that:
        - File exists and is readable
        - File is a valid SQLite database
        - Database contains required QualCoder tables

        Args:
            path: Path to the .qda file to validate

        Returns:
            True if valid QualCoder database, False otherwise
        """
        path = Path(path).resolve()

        # Check file exists
        if not path.exists() or not path.is_file():
            return False

        # Check it's a valid SQLite file
        try:
            # Quick SQLite header check
            with open(path, "rb") as f:
                header = f.read(16)
                if not header.startswith(b"SQLite format 3"):
                    return False
        except OSError:
            logger.error("validate_database: cannot read file %s", path)
            return False

        # Check required tables exist (supports both V1 and V2 schemas)
        try:
            engine = self._create_engine(path)
            try:
                inspector = inspect(engine)
                existing_tables = set(inspector.get_table_names())
                # Accept either V2 (new) or V1 (legacy) tables
                is_v2 = self.REQUIRED_TABLES_V2.issubset(existing_tables)
                is_v1 = self.REQUIRED_TABLES_V1.issubset(existing_tables)
                return is_v2 or is_v1
            finally:
                engine.dispose()
        except Exception:
            logger.error(
                "validate_database: inspection failed for %s", path, exc_info=True
            )
            return False

    def load(self, path: Path) -> Project | None:
        """
        Load project metadata from existing .qda database.

        Args:
            path: Path to the .qda file

        Returns:
            Project entity if database is valid, None otherwise
        """
        path = Path(path).resolve()
        logger.debug("load: %s", path)

        if not self.validate_database(path):
            return None

        try:
            engine = self._create_engine(path)
            try:
                with engine.connect() as conn:
                    # Load settings
                    name = self._get_setting(conn, self.SETTING_PROJECT_NAME)
                    owner = self._get_setting(conn, self.SETTING_PROJECT_OWNER)
                    memo = self._get_setting(conn, self.SETTING_PROJECT_MEMO)
                    created_at_str = self._get_setting(conn, self.SETTING_CREATED_AT)

                    # Parse timestamps
                    now = datetime.now(UTC)
                    created_at = (
                        datetime.fromisoformat(created_at_str)
                        if created_at_str
                        else now
                    )

                    # Compute summary statistics
                    summary = self._compute_summary(conn)

                    # Update last opened timestamp
                    self._update_setting(
                        conn, self.SETTING_LAST_OPENED_AT, now.isoformat()
                    )
                    conn.commit()

                    return Project(
                        id=ProjectId.from_path(path),
                        name=name or path.stem,
                        path=path,
                        memo=memo,
                        owner=owner,
                        created_at=created_at,
                        last_opened_at=now,
                        summary=summary,
                    )
            finally:
                engine.dispose()

        except Exception:
            logger.error("load failed: %s", path, exc_info=True)
            return None

    def _create_engine(self, path: Path) -> Engine:
        """Create a SQLAlchemy engine for the given database path."""
        db_url = f"sqlite:///{path}"
        return create_engine(db_url, echo=False)

    def _get_setting(self, conn: Connection, key: str) -> str | None:
        """Get a project setting value."""
        stmt = select(project_settings.c.value).where(project_settings.c.key == key)
        result = conn.execute(stmt)
        row = result.fetchone()
        return row.value if row else None

    def _set_setting(self, conn: Connection, key: str, value: str) -> None:
        """Set a project setting value (insert only, assumes key doesn't exist)."""
        stmt = project_settings.insert().values(
            key=key, value=value, updated_at=datetime.now(UTC)
        )
        conn.execute(stmt)

    def _update_setting(self, conn: Connection, key: str, value: str) -> None:
        """Update an existing project setting value."""
        exists_stmt = select(func.count()).where(project_settings.c.key == key)
        exists = conn.execute(exists_stmt).scalar() > 0

        if exists:
            stmt = (
                update(project_settings)
                .where(project_settings.c.key == key)
                .values(value=value, updated_at=datetime.now(UTC))
            )
        else:
            stmt = project_settings.insert().values(
                key=key, value=value, updated_at=datetime.now(UTC)
            )
        conn.execute(stmt)

    def _compute_summary(self, conn: Connection) -> ProjectSummary:
        """Compute project summary statistics from the database."""
        from src.contexts.coding.infra.schema import cod_code, cod_segment
        from src.contexts.sources.infra.schema import src_source

        def _count_where(table, condition=None) -> int:
            """Count rows in a table, optionally filtered by condition."""
            stmt = select(func.count()).select_from(table)
            if condition is not None:
                stmt = select(func.count()).where(condition)
            return conn.execute(stmt).scalar() or 0

        try:
            return ProjectSummary(
                total_sources=_count_where(src_source),
                text_count=_count_where(src_source, src_source.c.source_type == "text"),
                audio_count=_count_where(
                    src_source, src_source.c.source_type == "audio"
                ),
                video_count=_count_where(
                    src_source, src_source.c.source_type == "video"
                ),
                image_count=_count_where(
                    src_source, src_source.c.source_type == "image"
                ),
                pdf_count=_count_where(src_source, src_source.c.source_type == "pdf"),
                total_codes=_count_where(cod_code),
                total_segments=_count_where(cod_segment),
            )
        except Exception:
            return ProjectSummary()
