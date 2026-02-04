"""
Version Control Derivers - Pure Event Derivation

Pure functions that compose invariants and derive domain events.
These are the core of the Functional DDD pattern.

Architecture:
    Deriver: (command/data, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import (
    SnapshotCreated,
    SnapshotRestored,
    VersionControlInitialized,
)
from src.contexts.projects.core.vcs_failure_events import (
    AutoCommitSkipped,
    SnapshotNotRestored,
    VersionControlNotInitialized,
)
from src.contexts.projects.core.vcs_invariants import (
    has_events_to_commit,
    is_valid_git_ref,
    is_version_control_initialized,
)

if TYPE_CHECKING:
    pass


# ============================================================
# Auto-Commit Deriver
# ============================================================


def derive_auto_commit(
    events: tuple,
    state: VersionControlState,
) -> SnapshotCreated | AutoCommitSkipped:
    """
    Derive auto-commit event from batched domain events.

    PURE - no I/O. Called by command handler after debounce.

    Pattern: (events, state) -> SuccessEvent | FailureEvent

    Args:
        events: Tuple of domain events to commit
        state: Current version control state

    Returns:
        SnapshotCreated on success (git_sha will be "pending" until command handler fills it)
        AutoCommitSkipped on failure with reason
    """
    # Check: VCS must be initialized
    if not is_version_control_initialized(state.is_initialized):
        return AutoCommitSkipped.not_initialized()

    # Check: Must have events to commit
    if not has_events_to_commit(events):
        return AutoCommitSkipped.no_events()

    # Generate commit message from events
    message = _generate_commit_message(events)

    # Return success event
    # Note: git_sha is "pending" - command handler will fill in the real SHA
    return SnapshotCreated.create(
        git_sha="pending",
        message=message,
        event_count=len(events),
    )


# ============================================================
# Restore Snapshot Deriver
# ============================================================


def derive_restore_snapshot(
    ref: str,
    state: VersionControlState,
) -> SnapshotRestored | SnapshotNotRestored:
    """
    Derive restore snapshot event.

    PURE - no I/O. Validates that restore operation can proceed.

    Pattern: (ref, state) -> SuccessEvent | FailureEvent

    Args:
        ref: Git reference to restore to (SHA or HEAD~N)
        state: Current version control state

    Returns:
        SnapshotRestored on success
        SnapshotNotRestored on failure with reason
    """
    # Check: VCS must be initialized
    if not is_version_control_initialized(state.is_initialized):
        return SnapshotNotRestored.not_initialized()

    # Check: Cannot restore with uncommitted changes
    if state.has_uncommitted_changes:
        return SnapshotNotRestored.uncommitted_changes()

    # Check: Ref must be valid
    if not is_valid_git_ref(ref, state.valid_refs):
        return SnapshotNotRestored.invalid_ref(ref)

    # Return success event
    return SnapshotRestored.create(
        ref=ref,
        git_sha=ref,  # Command handler may resolve to actual SHA
    )


# ============================================================
# Initialize Version Control Deriver
# ============================================================


def derive_initialize_version_control(
    project_path: str,
    state: VersionControlState,
) -> VersionControlInitialized | VersionControlNotInitialized:
    """
    Derive version control initialization event.

    PURE - no I/O. Validates that initialization can proceed.

    Pattern: (project_path, state) -> SuccessEvent | FailureEvent

    Args:
        project_path: Path to the project directory
        state: Current version control state

    Returns:
        VersionControlInitialized on success
        VersionControlNotInitialized on failure with reason
    """
    # Check: VCS must NOT already be initialized
    if state.is_initialized:
        return VersionControlNotInitialized.already_initialized(project_path)

    # Return success event
    return VersionControlInitialized.create(project_path=project_path)


# ============================================================
# Helper Functions (Pure)
# ============================================================


def _generate_commit_message(events: tuple) -> str:
    """
    Generate a commit message from batched events.

    Pure function - no I/O.

    Strategy:
    - Single event: Use the event type directly
    - Multiple events: Group by context and summarize

    Args:
        events: Tuple of domain events

    Returns:
        Human-readable commit message

    Examples:
        Single: "coding.code_created"
        Multiple: "coding: 2 events, sources: 1 event"
    """
    if len(events) == 0:
        return "Empty commit"

    if len(events) == 1:
        event = events[0]
        # Use event_type if available, otherwise use class name
        if hasattr(event, "event_type"):
            return str(event.event_type)
        return type(event).__name__

    # Group by context (first part of event_type)
    context_counts: Counter[str] = Counter()
    for event in events:
        if hasattr(event, "event_type"):
            event_type = str(event.event_type)
            context = event_type.split(".")[0] if "." in event_type else "other"
        else:
            context = "other"
        context_counts[context] += 1

    # Build message
    parts = []
    for context, count in sorted(context_counts.items()):
        event_word = "event" if count == 1 else "events"
        parts.append(f"{context}: {count} {event_word}")

    return ", ".join(parts)


# ============================================================
# Exports
# ============================================================

__all__ = [
    "derive_auto_commit",
    "derive_restore_snapshot",
    "derive_initialize_version_control",
    "VersionControlState",
]
