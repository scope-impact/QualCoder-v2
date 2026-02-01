"""
References Context: Test Fixtures

Shared fixtures for domain layer tests.
"""

from __future__ import annotations

import pytest

# Import shared database fixtures from the tests package
from src.tests.fixtures.database import db_connection, db_engine  # noqa: F401
