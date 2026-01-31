"""
Cases Context: Invariants

Pure predicate functions for validating case business rules.
No I/O, no side effects - just boolean checks.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.cases.entities import Case

# =============================================================================
# Case Name Invariants
# =============================================================================

MAX_CASE_NAME_LENGTH = 100


def is_valid_case_name(name: str) -> bool:
    """
    Check if case name meets requirements.

    Args:
        name: The case name to validate

    Returns:
        True if name is 1-100 non-whitespace characters
    """
    if not name:
        return False
    stripped = name.strip()
    if not stripped:
        return False
    return 1 <= len(stripped) <= MAX_CASE_NAME_LENGTH


def is_case_name_unique(
    name: str,
    existing_cases: list[Case],
    exclude_id: int | None = None,
) -> bool:
    """
    Check if case name is unique among existing cases.

    Args:
        name: The case name to check
        existing_cases: List of existing cases
        exclude_id: Optional case ID to exclude (for updates)

    Returns:
        True if name is unique (case-insensitive)
    """
    name_lower = name.lower().strip()
    for case in existing_cases:
        if exclude_id is not None and case.id.value == exclude_id:
            continue
        if case.name.lower().strip() == name_lower:
            return False
    return True


# =============================================================================
# Attribute Type Invariants
# =============================================================================

VALID_ATTRIBUTE_TYPES = frozenset({"text", "number", "date", "boolean"})


def is_valid_attribute_type(attr_type: str) -> bool:
    """
    Check if attribute type is valid.

    Args:
        attr_type: The attribute type to validate

    Returns:
        True if type is one of: text, number, date, boolean
    """
    return attr_type.lower() in VALID_ATTRIBUTE_TYPES


# =============================================================================
# Attribute Name Invariants
# =============================================================================

MAX_ATTRIBUTE_NAME_LENGTH = 50


def is_valid_attribute_name(name: str) -> bool:
    """
    Check if attribute name meets requirements.

    Args:
        name: The attribute name to validate

    Returns:
        True if name is 1-50 non-whitespace characters
    """
    if not name:
        return False
    stripped = name.strip()
    if not stripped:
        return False
    return 1 <= len(stripped) <= MAX_ATTRIBUTE_NAME_LENGTH


# =============================================================================
# Attribute Value Invariants
# =============================================================================


def is_valid_attribute_value(value: Any, attr_type: str) -> bool:
    """
    Check if attribute value matches the expected type.

    Args:
        value: The value to validate
        attr_type: The expected attribute type

    Returns:
        True if value matches the type requirements
    """
    attr_type_lower = attr_type.lower()

    if attr_type_lower == "text":
        return isinstance(value, str)

    if attr_type_lower == "number":
        if isinstance(value, int | float) and not isinstance(value, bool):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False

    if attr_type_lower == "date":
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            return _is_valid_date_string(value)
        return False

    if attr_type_lower == "boolean":
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ("true", "false")
        return False

    return False


def _is_valid_date_string(value: str) -> bool:
    """Check if string is a valid ISO date format (YYYY-MM-DD)."""
    if not value:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False
