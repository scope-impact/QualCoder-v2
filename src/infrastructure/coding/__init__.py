"""
Infrastructure layer for the Coding bounded context.

Provides SQLAlchemy Core implementations of repository protocols.
"""

from src.infrastructure.coding.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.infrastructure.coding.schema import (
    code_cat,
    code_name,
    code_text,
    create_all,
    metadata,
)

__all__ = [
    "code_cat",
    "code_name",
    "code_text",
    "create_all",
    "metadata",
    "SQLiteCategoryRepository",
    "SQLiteCodeRepository",
    "SQLiteSegmentRepository",
]
