"""
DEPRECATED: Use src.contexts.coding.infra instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.infra import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
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
