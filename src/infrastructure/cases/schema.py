"""
Cases Context: SQLAlchemy Core Schema

DEPRECATED: This module re-exports from src.contexts.cases.infra.schema for backward compatibility.
Use src.contexts.cases.infra.schema directly in new code.
"""

from src.contexts.cases.infra.schema import (
    cas_attribute,
    cas_case,
    cas_source_link,
    create_all,
    drop_all,
    metadata,
)

__all__ = [
    "cas_attribute",
    "cas_case",
    "cas_source_link",
    "create_all",
    "drop_all",
    "metadata",
]
