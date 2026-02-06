"""Version Control Invariants - Pure validation predicates for business rules."""

from __future__ import annotations


def is_valid_snapshot_message(message: str) -> bool:
    """
    Validate a commit message.

    Valid if:
    - Non-empty
    - Not whitespace-only
    - <= 500 characters

    Args:
        message: The commit message to validate

    Returns:
        True if the message is valid
    """
    if not message:
        return False
    stripped = message.strip()
    return bool(stripped) and len(stripped) <= 500


def is_valid_git_ref(ref: str, valid_refs: tuple[str, ...]) -> bool:
    """
    Validate a git reference.

    Valid if:
    - HEAD or HEAD~N syntax (e.g., "HEAD", "HEAD~1", "HEAD~10")
    - Matches a known commit SHA from valid_refs

    Args:
        ref: The git reference to validate
        valid_refs: Tuple of known valid commit SHAs

    Returns:
        True if the ref is valid
    """
    if not ref:
        return False
    # HEAD or HEAD~N syntax is always valid
    if ref.startswith("HEAD"):
        return True
    # Otherwise, must be a known SHA
    return ref in valid_refs


__all__ = [
    "is_valid_snapshot_message",
    "is_valid_git_ref",
]
