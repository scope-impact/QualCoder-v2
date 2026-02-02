"""
Project Repository Tests.

Tests for SQLiteProjectRepository - .qda database creation and loading.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.domain.projects.entities import Project, ProjectSummary
from src.infrastructure.projects.project_repository import SQLiteProjectRepository

pytestmark = pytest.mark.integration


class TestSQLiteProjectRepository:
    """Tests for SQLiteProjectRepository."""

    def test_create_database_success(self, tmp_path: Path):
        """Test creating a new .qda database."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "test_project.qda"

        project = repo.create_database(
            path=db_path,
            name="My Research Project",
            owner="Test Researcher",
        )

        # Verify returned entity
        assert isinstance(project, Project)
        assert project.name == "My Research Project"
        assert project.owner == "Test Researcher"
        assert project.path == db_path
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.summary, ProjectSummary)

        # Verify file was created
        assert db_path.exists()

    def test_create_database_without_owner(self, tmp_path: Path):
        """Test creating a database without specifying owner."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "no_owner.qda"

        project = repo.create_database(path=db_path, name="Minimal Project")

        assert project.name == "Minimal Project"
        assert project.owner is None

    def test_create_database_file_exists_error(self, tmp_path: Path):
        """Test that creating a database at an existing path raises error."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "existing.qda"

        # Create an existing file
        db_path.touch()

        with pytest.raises(FileExistsError):
            repo.create_database(path=db_path, name="Project")

    def test_create_database_parent_not_exists_error(self, tmp_path: Path):
        """Test that creating a database in non-existent directory raises error."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "nonexistent" / "project.qda"

        with pytest.raises(ValueError, match="Parent directory does not exist"):
            repo.create_database(path=db_path, name="Project")

    def test_validate_database_valid(self, tmp_path: Path):
        """Test validating a valid .qda database."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "valid.qda"

        # Create a valid database
        repo.create_database(path=db_path, name="Valid Project")

        # Validate it
        assert repo.validate_database(db_path) is True

    def test_validate_database_nonexistent(self, tmp_path: Path):
        """Test validating a non-existent file returns False."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "nonexistent.qda"

        assert repo.validate_database(db_path) is False

    def test_validate_database_not_sqlite(self, tmp_path: Path):
        """Test validating a non-SQLite file returns False."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "not_sqlite.qda"

        # Write a non-SQLite file
        db_path.write_text("This is not a SQLite file")

        assert repo.validate_database(db_path) is False

    def test_validate_database_missing_tables(self, tmp_path: Path):
        """Test validating a SQLite file without required tables returns False."""
        import sqlite3

        repo = SQLiteProjectRepository()
        db_path = tmp_path / "incomplete.qda"

        # Create a SQLite database without required tables
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE other_table (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        assert repo.validate_database(db_path) is False

    def test_load_valid_database(self, tmp_path: Path):
        """Test loading metadata from a valid .qda database."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "loadable.qda"

        # Create a database
        original = repo.create_database(
            path=db_path,
            name="Load Test Project",
            owner="Researcher",
        )

        # Load it back
        loaded = repo.load(db_path)

        assert loaded is not None
        assert loaded.name == "Load Test Project"
        assert loaded.owner == "Researcher"
        assert loaded.path == db_path
        # last_opened_at should be updated on load
        assert loaded.last_opened_at >= original.last_opened_at

    def test_load_nonexistent_returns_none(self, tmp_path: Path):
        """Test loading a non-existent file returns None."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "nonexistent.qda"

        result = repo.load(db_path)
        assert result is None

    def test_load_invalid_database_returns_none(self, tmp_path: Path):
        """Test loading an invalid database returns None."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "invalid.qda"

        # Write a non-SQLite file
        db_path.write_text("Not a database")

        result = repo.load(db_path)
        assert result is None

    def test_load_uses_filename_as_fallback_name(self, tmp_path: Path):
        """Test that loading a database without project_name setting uses filename."""
        from sqlalchemy import create_engine

        from src.infrastructure.projects.schema import create_all_contexts

        repo = SQLiteProjectRepository()
        db_path = tmp_path / "my_project.qda"

        # Create a valid V2 database without project_name setting
        engine = create_engine(f"sqlite:///{db_path}")
        create_all_contexts(engine)
        engine.dispose()

        # Load it - should use filename as fallback
        loaded = repo.load(db_path)

        assert loaded is not None
        assert loaded.name == "my_project"  # Stem of filename

    def test_database_schema_includes_all_context_tables(self, tmp_path: Path):
        """Test that created database includes all bounded context tables."""
        from sqlalchemy import create_engine, inspect

        repo = SQLiteProjectRepository()
        db_path = tmp_path / "with_coding.qda"

        repo.create_database(path=db_path, name="Project")

        # Check that all context tables exist
        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        engine.dispose()

        # Projects context (prj_*)
        assert "prj_settings" in tables

        # Sources context (src_*)
        assert "src_source" in tables
        assert "src_folder" in tables

        # Cases context (cas_*)
        assert "cas_case" in tables
        assert "cas_attribute" in tables
        assert "cas_source_link" in tables

        # Coding context (cod_*)
        assert "cod_code" in tables
        assert "cod_category" in tables
        assert "cod_segment" in tables

    def test_project_summary_initially_empty(self, tmp_path: Path):
        """Test that new project has empty summary."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "empty_summary.qda"

        project = repo.create_database(path=db_path, name="Project")

        assert project.summary.total_sources == 0
        assert project.summary.total_codes == 0
        assert project.summary.total_segments == 0

    def test_created_at_is_utc(self, tmp_path: Path):
        """Test that created_at timestamp is UTC."""
        repo = SQLiteProjectRepository()
        db_path = tmp_path / "utc_test.qda"

        before = datetime.now(UTC)
        project = repo.create_database(path=db_path, name="Project")
        after = datetime.now(UTC)

        assert before <= project.created_at <= after
        assert project.created_at.tzinfo is not None
