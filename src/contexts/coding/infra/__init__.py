"""
Infrastructure layer for the Coding bounded context.

Provides SQLAlchemy Core implementations of repository protocols.
"""

from src.contexts.coding.infra.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.contexts.coding.infra.schema import (
    # V2 prefixed tables (preferred)
    cod_category,
    cod_code,
    cod_segment,
    # Compatibility aliases
    code_cat,
    code_name,
    code_text,
    create_all,
    drop_all,
    metadata,
)

__all__ = [
    # V2 prefixed tables
    "cod_category",
    "cod_code",
    "cod_segment",
    # Compatibility aliases
    "code_cat",
    "code_name",
    "code_text",
    # Schema utilities
    "create_all",
    "drop_all",
    "metadata",
    # Repositories
    "SQLiteCategoryRepository",
    "SQLiteCodeRepository",
    "SQLiteSegmentRepository",
]
