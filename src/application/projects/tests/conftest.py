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
def coordinator(event_bus: EventBus, db_connection):  # noqa: F811
    """Create an ApplicationCoordinator for testing.

    NOTE: This uses ApplicationCoordinator (not CoordinatorAdapter) because
    the navigation tests specifically test coordinator features like
    .navigation property that are not part of the adapter interface.
    """
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.application.coordinator import ApplicationCoordinator

    # Create coordinator
    coordinator = ApplicationCoordinator()

    # Replace with test event bus
    coordinator._event_bus = event_bus
    coordinator._infra.event_bus = event_bus

    # Create contexts with the test connection and set on infrastructure
    coordinator._infra.sources_context = SourcesContext.create(db_connection)
    coordinator._infra.coding_context = CodingContext.create(db_connection)
    coordinator._infra.cases_context = CasesContext.create(db_connection)
    coordinator._infra.projects_context = ProjectsContext.create(db_connection)

    return coordinator


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
