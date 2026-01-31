"""
Project application test fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from src.application.event_bus import EventBus
from src.infrastructure.projects.schema import create_all, drop_all


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus with history enabled for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    create_all(eng)
    yield eng
    drop_all(eng)
    eng.dispose()


@pytest.fixture
def connection(engine):
    """Create a database connection."""
    conn = engine.connect()
    yield conn
    conn.close()


@pytest.fixture
def source_repo(connection):
    """Create a source repository."""
    from src.infrastructure.projects.repositories import SQLiteSourceRepository

    return SQLiteSourceRepository(connection)


@pytest.fixture
def case_repo(connection):
    """Create a case repository."""
    from src.infrastructure.projects.repositories import SQLiteCaseRepository

    return SQLiteCaseRepository(connection)


@pytest.fixture
def project_controller(event_bus: EventBus, source_repo, case_repo):
    """Create a ProjectController with the test event bus and repositories."""
    from src.application.projects.controller import ProjectControllerImpl

    return ProjectControllerImpl(
        event_bus=event_bus,
        source_repo=source_repo,
        project_repo=None,
        case_repo=case_repo,
    )


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
