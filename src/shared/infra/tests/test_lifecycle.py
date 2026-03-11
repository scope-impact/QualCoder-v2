"""
Tests for ProjectLifecycle database connection management.

Consolidated tests for open, close, and create database operations.
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest
from returns.result import Failure, Success

from src.shared.infra.lifecycle import ProjectLifecycle


@allure.epic("Shared")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.05 Application Lifecycle")
class TestProjectLifecycleInitialState:
    """Tests for initial state of ProjectLifecycle."""

    @allure.title("New lifecycle has no connection, no path, and is not open")
    def test_initial_state(self) -> None:
        lifecycle = ProjectLifecycle()

        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False


@allure.epic("Shared")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.05 Application Lifecycle")
class TestOpenDatabase:
    """Tests for ProjectLifecycle.open_database()."""

    @allure.title("Opening nonexistent file returns Failure")
    def test_open_nonexistent_file_returns_failure(self) -> None:
        lifecycle = ProjectLifecycle()
        path = Path("/nonexistent/path/to/database.qda")

        result = lifecycle.open_database(path)

        assert isinstance(result, Failure)
        assert "not found" in result.failure()

    @allure.title("Opening existing database sets connection, path, session, and WAL mode")
    def test_open_existing_database(self, tmp_path: Path) -> None:
        from sqlalchemy import text

        from src.shared.infra.session import Session

        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        result = lifecycle.open_database(db_path)

        assert isinstance(result, Success)
        assert lifecycle.is_open is True
        assert lifecycle.current_path == db_path
        assert lifecycle.connection is not None
        assert isinstance(lifecycle.session, Session)
        assert lifecycle.session.engine is lifecycle.engine

        # WAL mode enabled
        wal_result = lifecycle.connection.execute(text("PRAGMA journal_mode"))
        assert wal_result.fetchone()[0] == "wal"

        lifecycle.close_database()

    @allure.title("Opening second database closes previous connection")
    def test_open_database_closes_previous_connection(self, tmp_path: Path) -> None:
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

        lifecycle.close_database()


@allure.epic("Shared")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.05 Application Lifecycle")
class TestCloseDatabase:
    """Tests for ProjectLifecycle.close_database()."""

    @allure.title("Closing clears connection, path, session, and sets is_open False")
    def test_close_database_clears_state(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.qda"
        db_path.touch()

        lifecycle = ProjectLifecycle()
        lifecycle.open_database(db_path)
        lifecycle.close_database()

        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False
        assert lifecycle.session is None

    @allure.title("Closing is idempotent (safe to call multiple times)")
    def test_close_database_is_idempotent(self) -> None:
        lifecycle = ProjectLifecycle()

        lifecycle.close_database()
        lifecycle.close_database()
        lifecycle.close_database()

        assert lifecycle.is_open is False


@allure.epic("Shared")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.05 Application Lifecycle")
class TestCreateDatabase:
    """Tests for ProjectLifecycle.create_database()."""

    @allure.title("Creating fails if file exists or parent missing")
    def test_create_database_failure_cases(self, tmp_path: Path) -> None:
        lifecycle = ProjectLifecycle()

        # File already exists
        existing = tmp_path / "existing.qda"
        existing.touch()
        result = lifecycle.create_database(existing, "Test")
        assert isinstance(result, Failure)
        assert "already exists" in result.failure()

        # Parent directory missing
        missing_parent = Path("/nonexistent/parent/test.qda")
        result = lifecycle.create_database(missing_parent, "Test")
        assert isinstance(result, Failure)
        assert "Parent directory" in result.failure()

    @allure.title("Creating new database succeeds and returns Project entity")
    def test_create_database_success(self, tmp_path: Path) -> None:
        db_path = tmp_path / "new_project.qda"

        lifecycle = ProjectLifecycle()
        result = lifecycle.create_database(db_path, "New Project")

        assert isinstance(result, Success)
        assert db_path.exists()
        assert lifecycle.is_open is True

        project = result.unwrap()
        assert project.name == "New Project"
        assert project.path == db_path

        lifecycle.close_database()
