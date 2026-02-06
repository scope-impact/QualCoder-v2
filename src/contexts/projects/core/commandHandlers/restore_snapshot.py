"""Restore Snapshot Command Handler - Orchestrates restoring to a previous VCS snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import RestoreSnapshotCommand
from src.contexts.projects.core.vcs_derivers import derive_restore_snapshot
from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import RestoreDecided, SnapshotRestored
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

    Steps:
    1. Build state from adapters
    2. Call deriver (domain decides)
    3. Handle failure
    4. Execute I/O (checkout, load)
    5. Publish domain event
    """
    project_path = Path(command.project_path)
    ref = command.ref

    # 1. Build state from adapters
    valid_refs_result = git_adapter.get_valid_refs()
    valid_refs = valid_refs_result.data if valid_refs_result.is_success else ()

    staged_result = git_adapter.has_staged_changes()
    has_uncommitted = staged_result.data if staged_result.is_success else False

    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=has_uncommitted,
        valid_refs=valid_refs,
    )

    # 2. Call deriver (domain decides)
    decision = derive_restore_snapshot(ref=ref, state=state)

    # 3. Handle failure
    if isinstance(decision, SnapshotNotRestored):
        return OperationResult.from_failure(decision)

    # Decision is RestoreDecided - extract ref
    assert isinstance(decision, RestoreDecided)
    target_ref = decision.ref

    # 4. Execute I/O: git checkout then load database
    checkout_result = git_adapter.checkout(target_ref)
    if checkout_result.is_failure:
        return checkout_result

    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    load_result = diffable_adapter.load(project_path, vcs_dir)
    if load_result.is_failure:
        return load_result

    # 5. Create and publish domain event
    final_event = SnapshotRestored.create(ref=target_ref, git_sha=target_ref)
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)
