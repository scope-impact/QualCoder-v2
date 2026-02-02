"""
Pytest fixtures for ViewModel tests.

Note: All fixtures are inherited from parent conftest.py files:
- qapp, colors: from root conftest.py
- coding_context, viewmodel: from presentation/tests/conftest.py

This file can contain viewmodel-specific fixtures if needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.event_bus import EventBus


@pytest.fixture
def project_event_bus() -> EventBus:
    """Create an event bus for project tests."""
    return EventBus(history_size=100)


@pytest.fixture
def coordinator(project_event_bus: EventBus, connection):
    """Create an ApplicationCoordinator for testing.

    NOTE: Uses ApplicationCoordinator (not CoordinatorAdapter) because
    tests need access to internal properties like ._state and .coding_context
    that are not part of the adapter interface.
    """
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.application.coordinator import ApplicationCoordinator
    from src.contexts.projects.core.entities import Project, ProjectId

    # Create coordinator
    coordinator = ApplicationCoordinator()

    # Replace with test event bus
    coordinator._event_bus = project_event_bus
    coordinator._infra.event_bus = project_event_bus

    # Create contexts with the test connection and set on infrastructure
    coordinator._infra.sources_context = SourcesContext.create(connection)
    coordinator._infra.coding_context = CodingContext.create(connection)
    coordinator._infra.cases_context = CasesContext.create(connection)
    coordinator._infra.projects_context = ProjectsContext.create(connection)

    # Create a project state so we can add sources
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "test_project.qda"
        project = Project(
            id=ProjectId.from_path(project_path),
            name="Test Project",
            path=project_path,
        )
        coordinator._state.project = project
        yield coordinator


@pytest.fixture
def file_manager_vm(coordinator, project_event_bus):
    """Create a FileManagerViewModel for testing."""
    from src.presentation.viewmodels.file_manager_viewmodel import (
        FileManagerViewModel,
    )

    return FileManagerViewModel(
        controller=coordinator,
        event_bus=project_event_bus,
    )


@pytest.fixture
def sample_source_file(tmp_path: Path) -> Path:
    """Create a sample source file for testing."""
    source_file = tmp_path / "interview.txt"
    source_file.write_text("Sample interview content for testing.")
    return source_file


# ============================================================
# Case Manager Fixtures
# ============================================================


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    from sqlalchemy import create_engine

    from src.contexts.projects.infra.schema import (
        create_all_contexts,
        drop_all_contexts,
    )

    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_contexts(engine)
    yield engine
    drop_all_contexts(engine)
    engine.dispose()


@pytest.fixture
def connection(engine):
    """Create a database connection."""
    conn = engine.connect()
    yield conn
    conn.close()


@pytest.fixture
def case_repo(connection):
    """Create a case repository."""
    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

    return SQLiteCaseRepository(connection)


@pytest.fixture
def folder_repo(connection):
    """Create a folder repository."""
    from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository

    return SQLiteFolderRepository(connection)


@pytest.fixture
def source_repo(connection):
    """Create a source repository."""
    from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

    return SQLiteSourceRepository(connection)


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus for case manager tests."""
    return EventBus(history_size=100)
