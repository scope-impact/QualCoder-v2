"""
Cases Infrastructure Layer.

DEPRECATED: This module re-exports from src.contexts.cases.infra for backward compatibility.
Use src.contexts.cases.infra directly in new code.
"""

from src.contexts.cases.infra import (
    SQLiteCaseRepository,
    cas_attribute,
    cas_case,
    cas_source_link,
    create_all,
    drop_all,
    metadata,
)

__all__ = [
    # Repository
    "SQLiteCaseRepository",
    # Schema
    "cas_attribute",
    "cas_case",
    "cas_source_link",
    "create_all",
    "drop_all",
    "metadata",
]
