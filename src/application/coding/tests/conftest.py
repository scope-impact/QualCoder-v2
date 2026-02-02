"""Shared fixtures for Coding application tests."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.application.contexts.coding import CodingContext
from src.application.event_bus import EventBus
from src.contexts.coding.infra.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.contexts.coding.infra.schema import create_all
from src.presentation.factory import CodingOperations


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with schema."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def connection(engine):
    """Create a connection from the engine."""
    with engine.connect() as conn:
        yield conn


@pytest.fixture
def code_repo(connection) -> SQLiteCodeRepository:
    """Create a code repository."""
    return SQLiteCodeRepository(connection)


@pytest.fixture
def category_repo(connection) -> SQLiteCategoryRepository:
    """Create a category repository."""
    return SQLiteCategoryRepository(connection)


@pytest.fixture
def segment_repo(connection) -> SQLiteSegmentRepository:
    """Create a segment repository."""
    return SQLiteSegmentRepository(connection)


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus with history for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def coding_context(code_repo, category_repo, segment_repo) -> CodingContext:
    """Create a coding context for use cases."""
    return CodingContext(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
    )


@pytest.fixture
def controller(coding_context, event_bus) -> CodingOperations:
    """Create a coding operations adapter (replaces old controller)."""
    return CodingOperations(
        coding_ctx=coding_context,
        event_bus=event_bus,
    )
