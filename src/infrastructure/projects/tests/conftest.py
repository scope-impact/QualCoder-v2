"""
Project infrastructure test fixtures.

Uses shared fixtures from src.tests.fixtures for database and repositories.
"""

from __future__ import annotations

# Import shared fixtures - pytest auto-discovers these
from src.tests.fixtures.database import db_connection, db_engine  # noqa: F401
from src.tests.fixtures.repositories import (  # noqa: F401
    case_repo,
    folder_repo,
    settings_repo,
    source_repo,
)
