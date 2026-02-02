"""
DEPRECATED: Use src.contexts.cases.core.invariants instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.cases.core.invariants import (
    MAX_ATTRIBUTE_NAME_LENGTH,
    MAX_CASE_NAME_LENGTH,
    VALID_ATTRIBUTE_TYPES,
    is_case_name_unique,
    is_valid_attribute_name,
    is_valid_attribute_type,
    is_valid_attribute_value,
    is_valid_case_name,
)

__all__ = [
    # Constants
    "MAX_CASE_NAME_LENGTH",
    "VALID_ATTRIBUTE_TYPES",
    "MAX_ATTRIBUTE_NAME_LENGTH",
    # Case Name Invariants
    "is_valid_case_name",
    "is_case_name_unique",
    # Attribute Invariants
    "is_valid_attribute_type",
    "is_valid_attribute_name",
    "is_valid_attribute_value",
]
