"""
Cases Infrastructure Layer.

SQLAlchemy Core implementations for cases data persistence.
"""

from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
from src.contexts.cases.infra.schema import (
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
