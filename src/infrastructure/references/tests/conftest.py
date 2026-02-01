"""
Reference infrastructure test fixtures.

Uses shared fixtures from src.tests.fixtures for database.
"""

from __future__ import annotations

import pytest

# Import shared fixtures - pytest auto-discovers these
from src.tests.fixtures.database import db_connection, db_engine  # noqa: F401


@pytest.fixture
def ref_repo(db_connection):
    """Create a reference repository with test database."""
    from src.infrastructure.references.repositories import SQLiteReferenceRepository

    return SQLiteReferenceRepository(db_connection)
