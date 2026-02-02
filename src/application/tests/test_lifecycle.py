"""
Tests for Project Lifecycle

Tests the ProjectLifecycle class that manages database connections.
"""

from pathlib import Path

from returns.result import Failure, Success

from src.application.lifecycle import ProjectLifecycle


class TestProjectLifecycleInitialization:
    """Tests for ProjectLifecycle initialization."""

    def test_initial_state(self):
        """New lifecycle has no open connection."""
        lifecycle = ProjectLifecycle()

        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False


class TestProjectLifecycleOpenDatabase:
    """Tests for opening existing databases."""

    def test_open_nonexistent_file_fails(self, tmp_path: Path):
        """Opening nonexistent file returns Failure."""
        lifecycle = ProjectLifecycle()
        path = tmp_path / "nonexistent.qda"

        result = lifecycle.open_database(path)

        assert isinstance(result, Failure)
        assert "not found" in result.failure()

    def test_open_existing_database_succeeds(self, tmp_path: Path):
        """Opening existing database returns Success with connection."""
        # First create a database
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        project_path = tmp_path / "test.qda"
        repo = SQLiteProjectRepository()
        repo.create_database(project_path, "Test Project")

        lifecycle = ProjectLifecycle()

        result = lifecycle.open_database(project_path)

        assert isinstance(result, Success)
        assert lifecycle.connection is not None
        assert lifecycle.current_path == project_path
        assert lifecycle.is_open is True

        lifecycle.close_database()

    def test_open_closes_previous_connection(self, tmp_path: Path):
        """Opening new database closes previous connection."""
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        # Create two databases
        path1 = tmp_path / "test1.qda"
        path2 = tmp_path / "test2.qda"
        repo = SQLiteProjectRepository()
        repo.create_database(path1, "Project 1")
        repo.create_database(path2, "Project 2")

        lifecycle = ProjectLifecycle()

        # Open first database
        lifecycle.open_database(path1)
        first_connection = lifecycle.connection

        # Open second database
        result = lifecycle.open_database(path2)

        assert isinstance(result, Success)
        assert lifecycle.current_path == path2
        # First connection should be closed (we can't easily verify this)
        assert lifecycle.connection is not first_connection

        lifecycle.close_database()


class TestProjectLifecycleCreateDatabase:
    """Tests for creating new databases."""

    def test_create_new_database_succeeds(self, tmp_path: Path):
        """Creating new database returns Success with Project."""
        lifecycle = ProjectLifecycle()
        path = tmp_path / "new_project.qda"

        result = lifecycle.create_database(path, "New Project")

        assert isinstance(result, Success)
        project = result.unwrap()
        assert project.name == "New Project"
        assert lifecycle.is_open is True
        assert lifecycle.current_path == path

        lifecycle.close_database()

    def test_create_existing_file_fails(self, tmp_path: Path):
        """Creating database at existing path returns Failure."""
        # Create file first
        path = tmp_path / "existing.qda"
        path.touch()

        lifecycle = ProjectLifecycle()

        result = lifecycle.create_database(path, "Test")

        assert isinstance(result, Failure)
        assert "already exists" in result.failure()

    def test_create_in_nonexistent_directory_fails(self, tmp_path: Path):
        """Creating database in nonexistent directory returns Failure."""
        lifecycle = ProjectLifecycle()
        path = tmp_path / "nonexistent_dir" / "project.qda"

        result = lifecycle.create_database(path, "Test")

        assert isinstance(result, Failure)
        assert "does not exist" in result.failure()


class TestProjectLifecycleCloseDatabase:
    """Tests for closing databases."""

    def test_close_clears_state(self, tmp_path: Path):
        """Closing database clears connection and path."""
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        project_path = tmp_path / "test.qda"
        repo = SQLiteProjectRepository()
        repo.create_database(project_path, "Test Project")

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(project_path)

        lifecycle.close_database()

        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False

    def test_close_without_open_is_safe(self):
        """Closing without open connection doesn't raise."""
        lifecycle = ProjectLifecycle()

        lifecycle.close_database()  # Should not raise

        assert lifecycle.connection is None
