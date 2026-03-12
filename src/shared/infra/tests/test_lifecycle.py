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


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.05 Application Lifecycle")
class TestProjectLifecycleOpenClose:
    """Tests for initial state, open, and close operations."""

    @allure.title("New lifecycle has no connection; open sets state; close resets state")
    def test_initial_open_and_close(self, tmp_path: Path) -> None:
        from sqlalchemy import text

        from src.shared.infra.session import Session

        lifecycle = ProjectLifecycle()

        # Initial state
        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False

        # Open existing database
        db_path = tmp_path / "test.qda"
        db_path.touch()
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

        # Close resets state
        lifecycle.close_database()
        assert lifecycle.connection is None
        assert lifecycle.current_path is None
        assert lifecycle.is_open is False
        assert lifecycle.session is None

    @allure.title("Opening nonexistent file returns Failure; close is idempotent")
    def test_open_failure_and_close_idempotent(self) -> None:
        lifecycle = ProjectLifecycle()

        result = lifecycle.open_database(Path("/nonexistent/path/to/database.qda"))
        assert isinstance(result, Failure)
        assert "not found" in result.failure()

        # Close is idempotent
        lifecycle.close_database()
        lifecycle.close_database()
        lifecycle.close_database()
        assert lifecycle.is_open is False

    @allure.title("Opening second database closes previous; creating database works")
    def test_open_second_and_create(self, tmp_path: Path) -> None:
        lifecycle = ProjectLifecycle()

        # Open first, then second
        db_path1 = tmp_path / "test1.qda"
        db_path1.touch()
        db_path2 = tmp_path / "test2.qda"
        db_path2.touch()

        lifecycle.open_database(db_path1)
        first_connection = lifecycle.connection
        lifecycle.open_database(db_path2)

        assert lifecycle.current_path == db_path2
        assert lifecycle.connection is not first_connection
        lifecycle.close_database()

        # Create database - failure cases
        existing = tmp_path / "existing.qda"
        existing.touch()
        result = lifecycle.create_database(existing, "Test")
        assert isinstance(result, Failure)
        assert "already exists" in result.failure()

        missing_parent = Path("/nonexistent/parent/test.qda")
        result = lifecycle.create_database(missing_parent, "Test")
        assert isinstance(result, Failure)
        assert "Parent directory" in result.failure()

        # Create database - success
        db_path = tmp_path / "new_project.qda"
        result = lifecycle.create_database(db_path, "New Project")
        assert isinstance(result, Success)
        assert db_path.exists()
        assert lifecycle.is_open is True

        project = result.unwrap()
        assert project.name == "New Project"
        assert project.path == db_path
        lifecycle.close_database()
