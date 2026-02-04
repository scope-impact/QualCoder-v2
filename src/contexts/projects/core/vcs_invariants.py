"""Version Control Invariants - Pure validation predicates for business rules."""

from __future__ import annotations


def is_version_control_initialized(is_initialized: bool) -> bool:
    """Check if version control is initialized."""
    return is_initialized


def has_events_to_commit(events: tuple) -> bool:
    """Check if there are events to commit."""
    return len(events) > 0


def is_valid_snapshot_message(message: str) -> bool:
    """Valid if non-empty, not whitespace-only, and <= 500 chars."""
    if not message:
        return False
    stripped = message.strip()
    return bool(stripped) and len(stripped) <= 500


def is_valid_git_ref(ref: str, valid_refs: tuple[str, ...]) -> bool:
    """Valid if HEAD/HEAD~N syntax or matches a known SHA."""
    if not ref:
        return False
    if ref.startswith("HEAD"):
        return True
    return ref in valid_refs
