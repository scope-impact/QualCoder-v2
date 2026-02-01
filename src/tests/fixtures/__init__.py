"""
Shared pytest fixtures.

Import these fixtures in your conftest.py to avoid duplication:

    from src.tests.fixtures.database import db_engine, db_connection
    from src.tests.fixtures.repositories import case_repo, source_repo

These fixtures can also be used with pytest_plugins in conftest.py.
"""

from src.tests.fixtures.database import db_connection, db_engine
from src.tests.fixtures.repositories import (
    case_repo,
    folder_repo,
    settings_repo,
    source_repo,
)

__all__ = [
    # Database fixtures
    "db_engine",
    "db_connection",
    # Repository fixtures
    "case_repo",
    "folder_repo",
    "settings_repo",
    "source_repo",
]
