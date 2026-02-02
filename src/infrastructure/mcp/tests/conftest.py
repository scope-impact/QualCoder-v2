"""
MCP infrastructure test fixtures.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.contexts.projects.infra.schema import (
    create_all_contexts,
    drop_all_contexts,
)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
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
