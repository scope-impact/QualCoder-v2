"""
E2E Test Fixtures

Shared fixtures for end-to-end tests.

IMPORTANT: E2E tests NEVER use mocks. All dependencies are real:
- Real in-memory SQLite database
- Real services (CaseManagerService, AICodingService, etc.)
- Real repositories
- Real ViewModels

For unit tests with mocks, see src/presentation/viewmodels/tests/mocks.py
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.application.event_bus import EventBus
from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts

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
    from src.application.contexts import CasesContext

    return CasesContext(case_repo=case_repo)


@pytest.fixture
def coding_context_bundle(code_repo, segment_repo):
    """Create a real coding context bundle."""
    from src.application.contexts import CodingContext

    return CodingContext(
        code_repo=code_repo,
        category_repo=None,  # Not needed for most tests
        segment_repo=segment_repo,
    )


# =============================================================================
# Project State Fixture (with mock project for E2E)
# =============================================================================


@pytest.fixture
def project_state():
    """
    Create a real project state with a mock project.

    For E2E tests, we need state.project to be set (not None)
    because use cases check for an open project.
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from src.application.state import ProjectState
    from src.contexts.projects.core.entities import Project, ProjectId

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
# Service Fixtures (REAL services, not mocks)
# =============================================================================


@pytest.fixture
def case_service(project_state, cases_context, event_bus):
    """
    Create a REAL CaseManagerService.

    This is the actual production service, not a mock.
    """
    from src.application.cases.service import CaseManagerService

    return CaseManagerService(
        state=project_state,
        cases_ctx=cases_context,
        event_bus=event_bus,
    )


# =============================================================================
# ViewModel Fixtures (connected to REAL services)
# =============================================================================


@pytest.fixture
def case_viewmodel(case_service):
    """
    Create a CaseManagerViewModel connected to REAL service.

    This is the actual production setup, not a mock.
    """
    from src.presentation.viewmodels.case_manager_viewmodel import CaseManagerViewModel

    return CaseManagerViewModel(provider=case_service)
