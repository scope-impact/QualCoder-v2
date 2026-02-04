"""
Tests for ProjectLifecycle database connection management.
"""

from __future__ import annotations

from pathlib import Path

from returns.result import Failure, Success

from src.shared.infra.lifecycle import ProjectLifecycle


class TestProjectLifecycleInitialState:
    """Tests for initial state of ProjectLifecycle."""

    def test_initial_connection_is_none(self) -> None:
        """New lifecycle should have no connection."""
        lifecycle = ProjectLifecycle()

        assert lifecycle.connection is None

    def test_initial_current_path_is_none(self) -> None:
        """New lifecycle should have no current path."""
        lifecycle = ProjectLifecycle()

        assert lifecycle.current_path is None

    def test_initial_is_open_is_false(self) -> None:
        """New lifecycle should not be open."""
        lifecycle = ProjectLifecycle()

        assert lifecycle.is_open is False


class TestOpenDatabase:
    """Tests for ProjectLifecycle.open_database()."""

    def test_open_nonexistent_file_returns_failure(self) -> None:
        """open_database() should fail for nonexistent file."""
        lifecycle = ProjectLifecycle()
        path = Path("/nonexistent/path/to/database.qda")

        result = lifecycle.open_database(path)

        assert isinstance(result, Failure)
        assert "not found" in result.failure()

    def test_open_existing_database_returns_success(self, tmp_path: Path) -> None:
        """open_database() should succeed for existing database file."""
        # Create a minimal SQLite database
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        result = lifecycle.open_database(db_path)

        assert isinstance(result, Success)
        assert lifecycle.is_open is True
        assert lifecycle.current_path == db_path

        # Cleanup
        lifecycle.close_database()

    def test_open_database_sets_connection(self, tmp_path: Path) -> None:
        """open_database() should set the connection property."""
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path)

        assert lifecycle.connection is not None

        # Cleanup
        lifecycle.close_database()

    def test_open_database_closes_previous_connection(self, tmp_path: Path) -> None:
        """open_database() should close any existing connection first."""
        db_path1 = tmp_path / "test1.qda"
        db_path1.touch()
        db_path2 = tmp_path / "test2.qda"
        db_path2.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path1)
        first_connection = lifecycle.connection

        lifecycle.open_database(db_path2)

        assert lifecycle.current_path == db_path2
        assert lifecycle.connection is not first_connection

        # Cleanup
        lifecycle.close_database()


class TestCloseDatabase:
    """Tests for ProjectLifecycle.close_database()."""

    def test_close_database_clears_connection(self, tmp_path: Path) -> None:
        """close_database() should clear the connection."""
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path)
        lifecycle.close_database()

        assert lifecycle.connection is None

    def test_close_database_clears_path(self, tmp_path: Path) -> None:
        """close_database() should clear the current path."""
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path)
        lifecycle.close_database()

        assert lifecycle.current_path is None

    def test_close_database_sets_is_open_false(self, tmp_path: Path) -> None:
        """close_database() should set is_open to False."""
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path)
        lifecycle.close_database()

        assert lifecycle.is_open is False

    def test_close_database_is_idempotent(self) -> None:
        """close_database() should be safe to call multiple times."""
        lifecycle = ProjectLifecycle()

        # Should not raise
        lifecycle.close_database()
        lifecycle.close_database()
        lifecycle.close_database()

        assert lifecycle.is_open is False


class TestCreateDatabase:
    """Tests for ProjectLifecycle.create_database()."""

    def test_create_database_fails_if_file_exists(self, tmp_path: Path) -> None:
        """create_database() should fail if file already exists."""
        db_path = tmp_path / "existing.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        result = lifecycle.create_database(db_path, "Test Project")

        assert isinstance(result, Failure)
        assert "already exists" in result.failure()

    def test_create_database_fails_if_parent_missing(self) -> None:
        """create_database() should fail if parent directory doesn't exist."""
        db_path = Path("/nonexistent/parent/test.qda")

        lifecycle = ProjectLifecycle()
        result = lifecycle.create_database(db_path, "Test Project")

        assert isinstance(result, Failure)
        assert "Parent directory" in result.failure()

    def test_create_database_creates_file(self, tmp_path: Path) -> None:
        """create_database() should create the database file."""
        db_path = tmp_path / "new_project.qda"

        lifecycle = ProjectLifecycle()
        result = lifecycle.create_database(db_path, "New Project")

        assert isinstance(result, Success)
        assert db_path.exists()
        assert lifecycle.is_open is True

        # Cleanup
        lifecycle.close_database()

    def test_create_database_returns_project(self, tmp_path: Path) -> None:
        """create_database() should return Project entity on success."""
        db_path = tmp_path / "new_project.qda"

        lifecycle = ProjectLifecycle()
        result = lifecycle.create_database(db_path, "New Project")

        assert isinstance(result, Success)
        project = result.unwrap()
        assert project.name == "New Project"
        assert project.path == db_path

        # Cleanup
        lifecycle.close_database()
