"""
Repository fixtures for testing.

Provides repository instances configured with test database connections.
These fixtures depend on the database fixtures from database.py.

Usage in conftest.py:
    from src.tests.fixtures.repositories import case_repo, source_repo
"""

from __future__ import annotations

import pytest

# Import repositories from new bounded context locations
from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
from src.contexts.coding.infra.repositories import SQLiteSegmentRepository
from src.contexts.projects.infra.settings_repository import (
    SQLiteProjectSettingsRepository,
)
from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
from src.contexts.sources.infra.source_repository import SQLiteSourceRepository


@pytest.fixture
def source_repo(db_connection):
    """Create a source repository connected to the test database."""
    return SQLiteSourceRepository(db_connection)


@pytest.fixture
def settings_repo(db_connection):
    """Create a settings repository connected to the test database."""
    return SQLiteProjectSettingsRepository(db_connection)


@pytest.fixture
def case_repo(db_connection):
    """Create a case repository connected to the test database."""
    return SQLiteCaseRepository(db_connection)


@pytest.fixture
def folder_repo(db_connection):
    """Create a folder repository connected to the test database."""
    return SQLiteFolderRepository(db_connection)


@pytest.fixture
def segment_repo(db_connection):
    """Create a segment repository connected to the test database."""
    return SQLiteSegmentRepository(db_connection)
