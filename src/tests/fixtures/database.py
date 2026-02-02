"""
Database fixtures for testing.

Provides in-memory SQLite database fixtures for testing repository
implementations without needing real database files.

Usage in conftest.py:
    from src.tests.fixtures.database import db_engine, db_connection
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts


@pytest.fixture
def db_engine():
    """
    Create an in-memory SQLite engine for testing.

    Creates all tables from all bounded contexts on setup and drops them on teardown.
    Each test gets a fresh, isolated database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Create tables from all bounded contexts
    create_all_contexts(engine)
    yield engine
    drop_all_contexts(engine)
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    """
    Create a database connection from the engine.

    The connection is automatically closed after the test.
    """
    conn = db_engine.connect()
    yield conn
    conn.close()
