"""
Version Control Derivers - Pure Event Derivation

Pure functions that compose invariants and derive decision events.
These are the core of the Functional DDD pattern.

Architecture:
    Deriver: (command/data, state) -> DecisionEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (decision or failure event)
    - Command handler creates actual domain events after I/O
    - Fully testable in isolation
"""

from __future__ import annotations

from collections import Counter

from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import (
    AutoCommitDecided,
    InitializeDecided,
    RestoreDecided,
)
from src.contexts.projects.core.vcs_failure_events import (
    AutoCommitSkipped,
    SnapshotNotRestored,
    VersionControlNotInitialized,
)
from src.contexts.projects.core.vcs_invariants import (
    is_valid_git_ref,
)

# ============================================================
# Auto-Commit Deriver
# ============================================================


def derive_auto_commit(
    events: tuple,
    state: VersionControlState,
) -> AutoCommitDecided | AutoCommitSkipped:
    """
    Derive auto-commit decision from batched domain events.

    PURE - no I/O. Called by command handler after debounce.

    Pattern: (events, state) -> DecisionEvent | FailureEvent

    Args:
        events: Tuple of domain events to commit
        state: Current version control state

    Returns:
        AutoCommitDecided if commit should proceed
        AutoCommitSkipped on failure with reason
    """
    # Check: VCS must be initialized
    if not state.is_initialized:
        return AutoCommitSkipped.not_initialized()

    # Check: Must have events to commit
    if len(events) == 0:
        return AutoCommitSkipped.no_events()

    # Generate commit message from events
    message = _generate_commit_message(events)

    # Return decision event - handler creates actual SnapshotCreated after I/O
    return AutoCommitDecided(message=message, event_count=len(events))


# ============================================================
# Restore Snapshot Deriver
# ============================================================


def derive_restore_snapshot(
    ref: str,
    state: VersionControlState,
) -> RestoreDecided | SnapshotNotRestored:
    """
    Derive restore snapshot decision.

    PURE - no I/O. Validates that restore operation can proceed.

    Pattern: (ref, state) -> DecisionEvent | FailureEvent

    Args:
        ref: Git reference to restore to (SHA or HEAD~N)
        state: Current version control state

    Returns:
        RestoreDecided if restore should proceed
        SnapshotNotRestored on failure with reason
    """
    # Check: VCS must be initialized
    if not state.is_initialized:
        return SnapshotNotRestored.not_initialized()

    # Check: Cannot restore with uncommitted changes
    if state.has_uncommitted_changes:
        return SnapshotNotRestored.uncommitted_changes()

    # Check: Ref must be valid
    if not is_valid_git_ref(ref, state.valid_refs):
        return SnapshotNotRestored.invalid_ref(ref)

    # Return decision event - handler creates actual SnapshotRestored after I/O
    return RestoreDecided(ref=ref)


# ============================================================
# Initialize Version Control Deriver
# ============================================================


def derive_initialize_version_control(
    project_path: str,
    state: VersionControlState,
) -> InitializeDecided | VersionControlNotInitialized:
    """
    Derive version control initialization decision.

    PURE - no I/O. Validates that initialization can proceed.

    Pattern: (project_path, state) -> DecisionEvent | FailureEvent

    Args:
        project_path: Path to the project directory
        state: Current version control state

    Returns:
        InitializeDecided if initialization should proceed
        VersionControlNotInitialized on failure with reason
    """
    # Check: VCS must NOT already be initialized
    if state.is_initialized:
        return VersionControlNotInitialized.already_initialized(project_path)

    # Return decision event - handler creates actual VersionControlInitialized after I/O
    return InitializeDecided(project_path=project_path)


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
