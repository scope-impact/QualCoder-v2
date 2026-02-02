"""
Shared Validation Utilities - Foundation for Invariant Functions

Provides common validation patterns used across all bounded contexts.
These utilities help build pure predicate functions (invariants) that
validate business rules.

Architecture:
    Invariants are pure boolean functions: (data, context) -> bool
    They are composed by Derivers to produce Result[Event, Failure]
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import (
    Any,
    Protocol,
    TypeVar,
)

T = TypeVar("T")
E = TypeVar("E")


# ============================================================
# Validation Result Types
# ============================================================


@dataclass(frozen=True)
class ValidationSuccess:
    """Validation passed."""

    pass


@dataclass(frozen=True)
class ValidationFailure:
    """Validation failed with a reason."""

    reason: str
    field: str | None = None
    value: Any = None

    def __str__(self) -> str:
        if self.field:
            return f"{self.field}: {self.reason}"
        return self.reason


ValidationResult = ValidationSuccess | ValidationFailure


def is_valid(result: ValidationResult) -> bool:
    """Check if a validation result indicates success."""
    return isinstance(result, ValidationSuccess)


def is_invalid(result: ValidationResult) -> bool:
    """Check if a validation result indicates failure."""
    return isinstance(result, ValidationFailure)


# ============================================================
# Common Invariant Helpers
# ============================================================


def is_non_empty_string(value: str) -> bool:
    """Check that a string is not empty or whitespace-only."""
    return bool(value and value.strip())


def is_within_length(value: str, min_len: int = 0, max_len: int = 1000) -> bool:
    """Check that a string length is within bounds."""
    length = len(value) if value else 0
    return min_len <= length <= max_len


def is_unique_in_collection(
    value: T,
    collection: Iterable[T],
    key: Callable[[T], Any] | None = None,
    exclude: T | None = None,
) -> bool:
    """
    Check that a value is unique within a collection.

    Args:
        value: The value to check for uniqueness
        collection: The collection to check against
        key: Optional function to extract comparison key
        exclude: Optional item to exclude from comparison (for updates)

    Returns:
        True if value is unique, False if duplicate exists
    """
    if key is None:

        def key(x):
            return x

    target_key = key(value)

    for item in collection:
        if exclude is not None and item == exclude:
            continue
        if key(item) == target_key:
            return False

    return True


def is_name_unique(
    name: str,
    existing_names: Iterable[str],
    case_sensitive: bool = False,
    exclude_name: str | None = None,
) -> bool:
    """
    Check that a name is unique (common pattern for entities).

    Args:
        name: The name to check
        existing_names: Collection of existing names
        case_sensitive: Whether comparison is case-sensitive
        exclude_name: Name to exclude (for renames)

    Returns:
        True if name is unique
    """
    if not case_sensitive:
        name = name.lower()
        existing_names = (n.lower() for n in existing_names)
        if exclude_name:
            exclude_name = exclude_name.lower()

    for existing in existing_names:
        if exclude_name and existing == exclude_name:
            continue
        if existing == name:
            return False

    return True


def is_valid_range(start: int, end: int) -> bool:
    """Check that start < end (valid range)."""
    return start < end


def is_within_bounds(start: int, end: int, length: int) -> bool:
    """Check that a range [start, end) is within bounds [0, length)."""
    return 0 <= start < end <= length


def is_positive(value: int) -> bool:
    """Check that a value is positive (> 0)."""
    return value > 0


def is_non_negative(value: int) -> bool:
    """Check that a value is non-negative (>= 0)."""
    return value >= 0


def is_in_range(value: int, min_val: int, max_val: int) -> bool:
    """Check that a value is within a range [min, max]."""
    return min_val <= value <= max_val


def is_valid_hex_color(color: str) -> bool:
    """Check that a string is a valid hex color (#RRGGBB)."""
    if not color or len(color) != 7:
        return False
    if color[0] != "#":
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False


# ============================================================
# Hierarchy Validation
# ============================================================


class HasParent(Protocol):
    """Protocol for entities with parent references."""

    @property
    def id(self) -> Any: ...

    @property
    def parent_id(self) -> Any | None: ...


def is_acyclic_hierarchy(
    node_id: Any,
    new_parent_id: Any | None,
    get_parent: Callable[[Any], Any | None],
    max_depth: int = 100,
) -> bool:
    """
    Check that setting a new parent won't create a cycle.

    Walks up from new_parent to root, ensuring we don't hit node_id.

    Args:
        node_id: The node being moved
        new_parent_id: The proposed new parent
        get_parent: Function to get parent of a node
        max_depth: Maximum depth to prevent infinite loops

    Returns:
        True if hierarchy remains acyclic
    """
    if new_parent_id is None:
        return True  # Moving to root is always safe

    if new_parent_id == node_id:
        return False  # Can't be your own parent

    # Walk up from new_parent
    current = new_parent_id
    depth = 0

    while current is not None and depth < max_depth:
        if current == node_id:
            return False  # Found a cycle
        current = get_parent(current)
        depth += 1

    return True


# ============================================================
# Collection Validation
# ============================================================


def all_exist(
    ids: Sequence[Any],
    exists_fn: Callable[[Any], bool],
) -> bool:
    """Check that all IDs in a sequence exist."""
    return all(exists_fn(id) for id in ids)


def none_exist(
    ids: Sequence[Any],
    exists_fn: Callable[[Any], bool],
) -> bool:
    """Check that none of the IDs exist (for creation)."""
    return not any(exists_fn(id) for id in ids)


def has_no_references(
    entity_id: Any,
    count_references: Callable[[Any], int],
) -> bool:
    """Check that an entity has no references (safe to delete)."""
    return count_references(entity_id) == 0


# ============================================================
# Composite Validation
# ============================================================


def validate_all(*results: ValidationResult) -> ValidationResult:
    """
    Combine multiple validation results, returning first failure.

    Args:
        *results: Validation results to combine

    Returns:
        ValidationSuccess if all pass, first ValidationFailure otherwise
    """
    for result in results:
        if isinstance(result, ValidationFailure):
            return result
    return ValidationSuccess()


def validate_field(
    field_name: str,
    value: Any,
    predicate: Callable[[Any], bool],
    error_message: str,
) -> ValidationResult:
    """
    Validate a single field with a predicate.

    Args:
        field_name: Name of the field being validated
        value: The value to validate
        predicate: Function that returns True if valid
        error_message: Message if validation fails

    Returns:
        ValidationSuccess or ValidationFailure
    """
    if predicate(value):
        return ValidationSuccess()
    return ValidationFailure(
        reason=error_message,
        field=field_name,
        value=value,
    )
