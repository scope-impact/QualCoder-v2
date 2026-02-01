"""
Reference application test fixtures.

Uses shared fixtures from src.tests.fixtures for database.
"""

from __future__ import annotations

import pytest

# Import shared fixtures
from src.tests.fixtures.database import db_connection, db_engine  # noqa: F401


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    from src.application.event_bus import EventBus

    return EventBus(history_size=100)


@pytest.fixture
def ref_repo(db_connection):
    """Create a reference repository with test database."""
    from src.infrastructure.references.repositories import SQLiteReferenceRepository

    return SQLiteReferenceRepository(db_connection)


@pytest.fixture
def ref_controller(ref_repo, event_bus):
    """Create a references controller with dependencies."""
    from src.application.references.controller import ReferencesControllerImpl

    return ReferencesControllerImpl(
        event_bus=event_bus,
        ref_repo=ref_repo,
    )
