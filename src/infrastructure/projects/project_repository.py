"""
Project Repository - SQLAlchemy Core Implementation.

Implements the repository for Project entities and .qda database operations.
"""

from __future__ import annotations

import contextlib
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

        except Exception as e:
            # Clean up partial database on failure
            if path.exists():
                with contextlib.suppress(OSError):
                    path.unlink()
            raise e

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
                    last_opened_str = self._get_setting(
                        conn, self.SETTING_LAST_OPENED_AT
                    )

                    # Parse timestamps
                    now = datetime.now(UTC)
                    created_at = (
                        datetime.fromisoformat(created_at_str)
                        if created_at_str
                        else now
                    )
                    # Note: last_opened_str is parsed but we use 'now' for the
                    # returned entity since we update last_opened on load
                    _ = last_opened_str  # Unused, but retrieved for completeness

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
        from sqlalchemy import func

        from src.infrastructure.coding.schema import cod_code, cod_segment
        from src.infrastructure.sources.schema import src_source

        # Count sources by type
        try:
            total_sources = (
                conn.execute(select(func.count()).select_from(src_source)).scalar() or 0
            )

            text_count = (
                conn.execute(
                    select(func.count()).where(src_source.c.source_type == "text")
                ).scalar()
                or 0
            )

            audio_count = (
                conn.execute(
                    select(func.count()).where(src_source.c.source_type == "audio")
                ).scalar()
                or 0
            )

            video_count = (
                conn.execute(
                    select(func.count()).where(src_source.c.source_type == "video")
                ).scalar()
                or 0
            )

            image_count = (
                conn.execute(
                    select(func.count()).where(src_source.c.source_type == "image")
                ).scalar()
                or 0
            )

            pdf_count = (
                conn.execute(
                    select(func.count()).where(src_source.c.source_type == "pdf")
                ).scalar()
                or 0
            )

            # Count codes
            total_codes = (
                conn.execute(select(func.count()).select_from(cod_code)).scalar() or 0
            )

            # Count segments (coded text)
            total_segments = (
                conn.execute(select(func.count()).select_from(cod_segment)).scalar()
                or 0
            )

            return ProjectSummary(
                total_sources=total_sources,
                text_count=text_count,
                audio_count=audio_count,
                video_count=video_count,
                image_count=image_count,
                pdf_count=pdf_count,
                total_codes=total_codes,
                total_segments=total_segments,
            )
        except Exception:
            # Return empty summary if tables don't exist or other error
            return ProjectSummary()
