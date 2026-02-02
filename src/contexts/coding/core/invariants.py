"""
Coding Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate business rules.
These are composed by Derivers to determine if an operation is valid.

Architecture:
    Invariant: (entity, context) -> bool
    - Pure function, no side effects
    - Returns True if rule is satisfied, False if violated
    - Named with is_* or can_* prefix
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from src.contexts.coding.core.entities import (
    Category,
    Code,
    Color,
    ImageRegion,
    Segment,
    TextPosition,
    TextSegment,
    TimeRange,
)
from src.contexts.shared.core.types import CategoryId, CodeId, SourceId
from src.contexts.shared.core.validation import (
    is_acyclic_hierarchy,
    is_in_range,
    is_non_empty_string,
    is_within_bounds,
    is_within_length,
)

# ============================================================
# Code Invariants
# ============================================================


def is_valid_code_name(name: str) -> bool:
    """
    Check that a code name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 100 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 100)


def is_code_name_unique(
    name: str,
    existing_codes: Iterable[Code],
    exclude_code_id: CodeId | None = None,
) -> bool:
    """
    Check that a code name is unique within the project.

    Args:
        name: The proposed code name
        existing_codes: All codes in the project
        exclude_code_id: Code ID to exclude (for renames)

    Returns:
        True if name is unique (case-insensitive)
    """
    for code in existing_codes:
        if exclude_code_id and code.id == exclude_code_id:
            continue
        if code.name.lower() == name.lower():
            return False
    return True


def is_valid_color(color: Color) -> bool:
    """
    Check that a color is valid.

    Rules:
    - RGB values between 0-255 (enforced by Color class)
    """
    return (
        is_in_range(color.red, 0, 255)
        and is_in_range(color.green, 0, 255)
        and is_in_range(color.blue, 0, 255)
    )


def can_code_be_deleted(
    code_id: CodeId,
    segments: Iterable[Segment],
    allow_with_segments: bool = False,
) -> bool:
    """
    Check if a code can be deleted.

    Args:
        code_id: The code to delete
        segments: All segments in the project
        allow_with_segments: If True, allow deletion even with segments

    Returns:
        True if code can be deleted
    """
    if allow_with_segments:
        return True

    # Check if any segments reference this code
    return all(segment.code_id != code_id for segment in segments)


def are_codes_mergeable(
    source_code_id: CodeId,
    target_code_id: CodeId,
    code_exists: Callable[[CodeId], bool],
) -> bool:
    """
    Check if two codes can be merged.

    Rules:
    - Both codes must exist
    - Codes must be different

    Args:
        source_code_id: Code to merge from (will be deleted)
        target_code_id: Code to merge into (will remain)
        code_exists: Function to check if a code exists

    Returns:
        True if merge is valid
    """
    if source_code_id == target_code_id:
        return False

    if not code_exists(source_code_id):
        return False

    return code_exists(target_code_id)


# ============================================================
# Category Invariants
# ============================================================


def is_valid_category_name(name: str) -> bool:
    """
    Check that a category name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 100 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 100)


def is_category_name_unique(
    name: str,
    existing_categories: Iterable[Category],
    exclude_category_id: CategoryId | None = None,
) -> bool:
    """
    Check that a category name is unique.

    Args:
        name: The proposed category name
        existing_categories: All categories in the project
        exclude_category_id: Category ID to exclude (for renames)

    Returns:
        True if name is unique (case-insensitive)
    """
    for category in existing_categories:
        if exclude_category_id and category.id == exclude_category_id:
            continue
        if category.name.lower() == name.lower():
            return False
    return True


def is_category_hierarchy_valid(
    category_id: CategoryId,
    new_parent_id: CategoryId | None,
    categories: Iterable[Category],
) -> bool:
    """
    Check that moving a category to a new parent won't create a cycle.

    Args:
        category_id: The category being moved
        new_parent_id: The proposed new parent (None = root)
        categories: All categories for parent lookup

    Returns:
        True if hierarchy remains acyclic
    """
    if new_parent_id is None:
        return True  # Moving to root is always valid

    if new_parent_id == category_id:
        return False  # Can't be your own parent

    # Build parent lookup
    parent_map = {cat.id: cat.parent_id for cat in categories}

    def get_parent(cat_id: CategoryId) -> CategoryId | None:
        return parent_map.get(cat_id)

    return is_acyclic_hierarchy(
        node_id=category_id,
        new_parent_id=new_parent_id,
        get_parent=get_parent,
    )


def can_category_be_deleted(
    category_id: CategoryId,
    codes: Iterable[Code],
    categories: Iterable[Category],
    allow_with_children: bool = False,
) -> bool:
    """
    Check if a category can be deleted.

    Args:
        category_id: The category to delete
        codes: All codes in the project
        categories: All categories in the project
        allow_with_children: If True, allow deletion with orphan handling

    Returns:
        True if category can be deleted
    """
    if allow_with_children:
        return True

    # Check for codes in this category
    if not all(code.category_id != category_id for code in codes):
        return False

    # Check for child categories
    return all(cat.parent_id != category_id for cat in categories)


# ============================================================
# Segment Invariants
# ============================================================


def is_valid_text_position(
    position: TextPosition,
    source_length: int,
) -> bool:
    """
    Check that a text position is valid for a source.

    Args:
        position: The position to validate
        source_length: Length of the source text

    Returns:
        True if position is within bounds
    """
    return is_within_bounds(position.start, position.end, source_length)


def is_valid_image_region(
    region: ImageRegion,
    image_width: int,
    image_height: int,
) -> bool:
    """
    Check that an image region is valid for an image source.

    Args:
        region: The region to validate
        image_width: Width of the source image
        image_height: Height of the source image

    Returns:
        True if region is within bounds
    """
    return (
        region.x >= 0
        and region.y >= 0
        and region.x + region.width <= image_width
        and region.y + region.height <= image_height
    )


def is_valid_time_range(
    time_range: TimeRange,
    duration_ms: int,
) -> bool:
    """
    Check that a time range is valid for an A/V source.

    Args:
        time_range: The time range to validate
        duration_ms: Duration of the source in milliseconds

    Returns:
        True if time range is within bounds
    """
    return is_within_bounds(time_range.start_ms, time_range.end_ms, duration_ms)


def is_valid_importance(importance: int) -> bool:
    """
    Check that importance value is valid.

    Rules:
    - Must be 0 (normal), 1 (important), or 2 (very important)
    """
    return importance in (0, 1, 2)


def does_segment_overlap(
    new_position: TextPosition,
    existing_segments: Iterable[TextSegment],
    same_code_id: CodeId,
) -> bool:
    """
    Check if a new segment would overlap with existing segments of the same code.

    Note: Overlaps are allowed in QualCoder, this is informational only.

    Args:
        new_position: Position of the new segment
        existing_segments: Existing segments to check against
        same_code_id: Only check segments with this code

    Returns:
        True if there is an overlap
    """
    for segment in existing_segments:
        if segment.code_id != same_code_id:
            continue
        if new_position.overlaps(segment.position):
            return True
    return False


# ============================================================
# Cross-Entity Invariants
# ============================================================


def does_code_exist(
    code_id: CodeId,
    codes: Iterable[Code],
) -> bool:
    """Check if a code exists."""
    return any(c.id == code_id for c in codes)


def does_category_exist(
    category_id: CategoryId,
    categories: Iterable[Category],
) -> bool:
    """Check if a category exists."""
    return any(c.id == category_id for c in categories)


def does_source_exist(
    source_id: SourceId,
    source_exists_fn: Callable[[SourceId], bool],
) -> bool:
    """
    Check if a source exists.

    Args:
        source_id: The source ID to check
        source_exists_fn: Function to check source existence

    Returns:
        True if source exists
    """
    return source_exists_fn(source_id)


def count_segments_for_code(
    code_id: CodeId,
    segments: Iterable[Segment],
) -> int:
    """Count segments that reference a code."""
    return sum(1 for s in segments if s.code_id == code_id)


def count_codes_in_category(
    category_id: CategoryId,
    codes: Iterable[Code],
) -> int:
    """Count codes in a category."""
    return sum(1 for c in codes if c.category_id == category_id)
