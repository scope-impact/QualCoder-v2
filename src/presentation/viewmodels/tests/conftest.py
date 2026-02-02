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
    """Create a test controller implementing FileManagerController.

    Uses AppContext internally and exposes coding_context for tests
    that need to manipulate segments directly.
    """
    import tempfile

    from src.application.app_context import AppContext
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.application.lifecycle import ProjectLifecycle
    from src.application.state import ProjectState
    from src.contexts.projects.core.entities import Project, ProjectId
    from src.contexts.settings.infra import UserSettingsRepository
    from src.main import FileManagerService

    # Create state with test event bus
    state = ProjectState()

    # Create AppContext
    ctx = AppContext(
        event_bus=project_event_bus,
        state=state,
        lifecycle=ProjectLifecycle(),
        settings_repo=UserSettingsRepository(),
    )

    # Set contexts with the test connection (no underscore - dataclass attributes)
    ctx.sources_context = SourcesContext.create(connection)
    ctx.coding_context = CodingContext.create(connection)
    ctx.cases_context = CasesContext.create(connection)
    ctx.projects_context = ProjectsContext.create(connection)

    # Create a project state so we can add sources
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "test_project.qda"
        project = Project(
            id=ProjectId.from_path(project_path),
            name="Test Project",
            path=project_path,
        )
        ctx.state.project = project

        # Create adapter (coding_context is exposed as a property)
        adapter = FileManagerService(ctx)
        yield adapter


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
