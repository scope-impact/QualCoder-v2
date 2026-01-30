"""Shared fixtures for Coding infrastructure tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine

from src.infrastructure.coding.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.infrastructure.coding.schema import create_all


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with schema."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def connection(engine) -> Iterator:
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
