"""
Version Control Invariants - Pure Validation Predicates

Pure predicate functions that validate version control business rules.
These are composed by derivers to determine if an operation is valid.

Architecture:
    Invariant: (entity, context) -> bool
    - Pure function, no side effects
    - Returns True if rule is satisfied, False if violated
    - Named with is_* or can_* prefix
"""

from __future__ import annotations


def is_version_control_initialized(git_initialized: bool) -> bool:
    """
    Check that version control is initialized.

    VCS must be initialized before any version control operations.

    Args:
        git_initialized: Whether .git directory exists

    Returns:
        True if VCS is initialized
    """
    return git_initialized


def is_valid_snapshot_message(message: str) -> bool:
    """
    Check that a snapshot message is valid.

    Rules:
    - Must be non-empty
    - Must not be whitespace only
    - Must be 500 characters or fewer

    Args:
        message: The commit message to validate

    Returns:
        True if message is valid
    """
    if not message:
        return False
    stripped = message.strip()
    return bool(stripped) and len(stripped) <= 500


def is_valid_git_ref(ref: str, valid_refs: tuple[str, ...]) -> bool:
    """
    Check that a git ref is valid.

    Valid refs include:
    - HEAD and HEAD~N syntax (always valid)
    - Exact SHA matches from valid_refs

    Args:
        ref: The git reference to validate
        valid_refs: Tuple of known valid commit SHAs

    Returns:
        True if ref is valid
    """
    if not ref:
        return False

    # HEAD and HEAD~N syntax is always valid
    if ref.startswith("HEAD"):
        return True

    # Check against known valid refs
    return ref in valid_refs


def has_events_to_commit(events: tuple) -> bool:
    """
    Check that there are events to commit.

    Auto-commit requires at least one domain event.

    Args:
        events: Tuple of domain events to commit

    Returns:
        True if there is at least one event
    """
    return len(events) > 0


def can_restore_snapshot(
    is_initialized: bool,
    has_uncommitted: bool,
    ref_valid: bool,
) -> bool:
    """
    Check that all conditions are met to restore a snapshot.

    Requirements:
    - Version control must be initialized
    - No uncommitted changes (to avoid data loss)
    - Target ref must be valid

    Args:
        is_initialized: Whether VCS is initialized
        has_uncommitted: Whether there are uncommitted changes
        ref_valid: Whether the target ref is valid

    Returns:
        True if restore can proceed
    """
    return is_initialized and not has_uncommitted and ref_valid


# ============================================================
# Exports
# ============================================================

__all__ = [
    "is_version_control_initialized",
    "is_valid_snapshot_message",
    "is_valid_git_ref",
    "has_events_to_commit",
    "can_restore_snapshot",
]
