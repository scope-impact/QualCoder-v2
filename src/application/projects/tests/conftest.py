"""
Project application test fixtures.

Uses shared fixtures from src.tests.fixtures for database and repositories.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.event_bus import EventBus

# Import shared fixtures - pytest auto-discovers these
from src.tests.fixtures.database import db_connection, db_engine  # noqa: F401
from src.tests.fixtures.repositories import (  # noqa: F401, F811
    case_repo,
    folder_repo,
    segment_repo,
    source_repo,
)


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus with history enabled for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def sample_project_path(tmp_path: Path) -> Path:
    """Create a sample project path in temp directory."""
    return tmp_path / "test_project.qda"


@pytest.fixture
def existing_project_path(tmp_path: Path) -> Path:
    """Create an existing project file for open tests."""
    project_path = tmp_path / "existing_project.qda"
    project_path.touch()
    return project_path


@pytest.fixture
def sample_source_path(tmp_path: Path) -> Path:
    """Create a sample source file."""
    source_path = tmp_path / "interview.txt"
    source_path.write_text("Sample interview content")
    return source_path
