"""
DEPRECATED: Use src.contexts.shared.core.validation instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.shared.core.validation import (
    HasParent,
    ValidationFailure,
    ValidationResult,
    ValidationSuccess,
    all_exist,
    has_no_references,
    is_acyclic_hierarchy,
    is_in_range,
    is_invalid,
    is_name_unique,
    is_non_empty_string,
    is_non_negative,
    is_positive,
    is_unique_in_collection,
    is_valid,
    is_valid_hex_color,
    is_valid_range,
    is_within_bounds,
    is_within_length,
    none_exist,
    validate_all,
    validate_field,
)

__all__ = [
    # Validation Result Types
    "ValidationSuccess",
    "ValidationFailure",
    "ValidationResult",
    "is_valid",
    "is_invalid",
    # Common Invariant Helpers
    "is_non_empty_string",
    "is_within_length",
    "is_unique_in_collection",
    "is_name_unique",
    "is_valid_range",
    "is_within_bounds",
    "is_positive",
    "is_non_negative",
    "is_in_range",
    "is_valid_hex_color",
    # Hierarchy Validation
    "HasParent",
    "is_acyclic_hierarchy",
    # Collection Validation
    "all_exist",
    "none_exist",
    "has_no_references",
    # Composite Validation
    "validate_all",
    "validate_field",
]
