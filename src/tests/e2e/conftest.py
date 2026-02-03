"""
E2E Test Fixtures

Shared fixtures for end-to-end tests.

IMPORTANT: E2E tests NEVER use mocks. All dependencies are real:
- Real in-memory SQLite database
- Real repositories
- Real ViewModels calling use cases directly

For unit tests with mocks, see src/presentation/viewmodels/tests/mocks.py
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts
from src.shared.infra.event_bus import EventBus

# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for E2E testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_contexts(engine)
    yield engine
    drop_all_contexts(engine)
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    """Create a database connection."""
    conn = db_engine.connect()
    yield conn
    conn.close()


# =============================================================================
# Event Bus Fixture
# =============================================================================


@pytest.fixture
def event_bus():
    """Create event bus for reactive updates."""
    return EventBus(history_size=100)


# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def case_repo(db_connection):
    """Create a real case repository."""
    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

    return SQLiteCaseRepository(db_connection)


@pytest.fixture
def code_repo(db_connection):
    """Create a real code repository."""
    from src.contexts.coding.infra.repositories import SQLiteCodeRepository

    return SQLiteCodeRepository(db_connection)


@pytest.fixture
def segment_repo(db_connection):
    """Create a real segment repository."""
    from src.contexts.coding.infra.repositories import SQLiteSegmentRepository

    return SQLiteSegmentRepository(db_connection)


@pytest.fixture
def category_repo(db_connection):
    """Create a real category repository."""
    from src.contexts.coding.infra.repositories import SQLiteCategoryRepository

    return SQLiteCategoryRepository(db_connection)


@pytest.fixture
def source_repo(db_connection):
    """Create a real source repository."""
    from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

    return SQLiteSourceRepository(db_connection)


# =============================================================================
# Context Fixtures (bundles of repositories)
# =============================================================================


@pytest.fixture
def cases_context(case_repo):
    """Create a real cases context."""
    from src.shared.infra.app_context import CasesContext

    return CasesContext(case_repo=case_repo)


@pytest.fixture
def coding_context_bundle(code_repo, segment_repo):
    """Create a real coding context bundle."""
    from src.shared.infra.app_context import CodingContext

    return CodingContext(
        code_repo=code_repo,
        category_repo=None,  # Not needed for most tests
        segment_repo=segment_repo,
    )


# =============================================================================
# Project State Fixture (with test project for E2E)
# =============================================================================


@pytest.fixture
def project_state():
    """
    Create a real project state with a test project.

    For E2E tests, we need state.project to be set (not None)
    because use cases check for an open project.
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from src.contexts.projects.core.entities import Project, ProjectId
    from src.shared.infra.state import ProjectState

    state = ProjectState()

    # Create a minimal project for testing
    project = Project(
        id=ProjectId(value="test-project"),
        name="Test Project",
        path=Path("/tmp/test_project.qda"),
        created_at=datetime.now(UTC),
    )

    # Set the project on state
    state.project = project

    return state


# =============================================================================
# ViewModel Fixtures (connected to REAL repositories)
# =============================================================================


@pytest.fixture
def case_viewmodel(case_repo, project_state, event_bus, cases_context):
    """
    Create a CaseManagerViewModel with real dependencies.

    This is the actual production setup, not a mock.
    """
    from src.contexts.cases.presentation import CaseManagerViewModel

    return CaseManagerViewModel(
        case_repo=case_repo,
        state=project_state,
        event_bus=event_bus,
        cases_ctx=cases_context,
    )
