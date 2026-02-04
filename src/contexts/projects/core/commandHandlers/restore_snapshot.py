"""
Restore Snapshot Command Handler

Orchestrates restoring the database to a previous version control snapshot.
Follows the 5-step command handler pattern.

Usage:
    result = restore_snapshot(
        command=RestoreSnapshotCommand(...),
        diffable_adapter=diffable_adapter,
        git_adapter=git_adapter,
        event_bus=event_bus,
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import RestoreSnapshotCommand
from src.contexts.projects.core.vcs_derivers import (
    VersionControlState,
    derive_restore_snapshot,
)
from src.contexts.projects.core.vcs_events import SnapshotRestored
from src.contexts.projects.core.vcs_failure_events import SnapshotNotRestored
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus


def restore_snapshot(
    command: RestoreSnapshotCommand,
    diffable_adapter: SqliteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Restore database to a previous version control snapshot.

    5-step pattern:
    1. Build state from adapters
    2. Call deriver (pure domain logic)
    3. Handle failure - return early if deriver rejects
    4. Execute I/O (git checkout, then load database)
    5. Publish event

    Args:
        command: RestoreSnapshotCommand with project path and ref
        diffable_adapter: Adapter for SQLite-to-JSON conversion
        git_adapter: Adapter for Git operations
        event_bus: Event bus for publishing domain events

    Returns:
        OperationResult.ok(data=SnapshotRestored) on success
        OperationResult.fail() or OperationResult.from_failure() on failure
    """
    project_path = Path(command.project_path)
    ref = command.ref

    # Step 1: Build state from adapters
    # Get valid refs for validation
    valid_refs_result = git_adapter.get_valid_refs()
    valid_refs = valid_refs_result.data if valid_refs_result.is_success else ()

    # Check for uncommitted changes
    staged_result = git_adapter.has_staged_changes()
    has_uncommitted = staged_result.data if staged_result.is_success else False

    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=has_uncommitted,
        valid_refs=valid_refs,
    )

    # Step 2: Call deriver (pure domain decision)
    result = derive_restore_snapshot(ref=ref, state=state)

    # Step 3: Handle failure - return early if deriver rejects
    if isinstance(result, SnapshotNotRestored):
        return OperationResult.from_failure(result)

    # Deriver returned success (result is SnapshotRestored)

    # Step 4: Execute I/O operations

    # 4a. Git checkout to the target ref
    checkout_result = git_adapter.checkout(ref)
    if checkout_result.is_failure:
        return checkout_result

    # 4b. Load database from diffable format
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    db_path = project_path  # Assumes project_path is the .qda file

    load_result = diffable_adapter.load(db_path, vcs_dir)
    if load_result.is_failure:
        return load_result

    # Step 5: Publish event
    final_event = SnapshotRestored.create(
        ref=ref,
        git_sha=ref,  # Could resolve to actual SHA if needed
    )
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)
