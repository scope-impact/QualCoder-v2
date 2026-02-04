"""
Auto-Commit Command Handler

Orchestrates automatic version control commits after domain events.
Follows the 5-step command handler pattern.

Usage:
    result = auto_commit(
        command=AutoCommitCommand(...),
        diffable_adapter=diffable_adapter,
        git_adapter=git_adapter,
        event_bus=event_bus,
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import AutoCommitCommand
from src.contexts.projects.core.vcs_derivers import (
    VersionControlState,
    derive_auto_commit,
)
from src.contexts.projects.core.vcs_events import SnapshotCreated
from src.contexts.projects.core.vcs_failure_events import AutoCommitSkipped
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus


def auto_commit(
    command: AutoCommitCommand,
    diffable_adapter: SqliteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Auto-commit pending domain events to version control.

    5-step pattern:
    1. Build state from adapters
    2. Call deriver (pure domain logic)
    3. Handle failure - return early if deriver rejects
    4. Execute I/O (dump database, stage, commit)
    5. Publish event

    Args:
        command: AutoCommitCommand with project path and events
        diffable_adapter: Adapter for SQLite-to-JSON conversion
        git_adapter: Adapter for Git operations
        event_bus: Event bus for publishing domain events

    Returns:
        OperationResult.ok(data=SnapshotCreated) on success
        OperationResult.fail() or OperationResult.from_failure() on failure
    """
    project_path = Path(command.project_path)
    events = tuple(command.events)

    # Step 1: Build state from adapters
    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=False,  # Auto-commit doesn't check this
        valid_refs=(),  # Not needed for auto-commit
    )

    # Step 2: Call deriver (pure domain decision)
    result = derive_auto_commit(events=events, state=state)

    # Step 3: Handle failure - return early if deriver rejects
    if isinstance(result, AutoCommitSkipped):
        return OperationResult.from_failure(result)

    # Deriver returned success - extract commit message
    derived_event: SnapshotCreated = result
    commit_message = derived_event.message

    # Step 4: Execute I/O operations

    # 4a. Dump database to diffable format
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    db_path = project_path  # Assumes project_path is the .qda file

    dump_result = diffable_adapter.dump(db_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    # 4b. Stage changes
    stage_result = git_adapter.add_all(vcs_dir.name)
    if stage_result.is_failure:
        return stage_result

    # 4c. Commit changes
    commit_result = git_adapter.commit(commit_message)
    if commit_result.is_failure:
        # If nothing to commit, that's actually okay for auto-commit
        if commit_result.error_code == "GIT_NOT_COMMITTED/NOTHING_TO_COMMIT":
            return OperationResult.ok(
                data=SnapshotCreated.create(
                    git_sha="no-changes",
                    message=commit_message,
                    event_count=len(events),
                )
            )
        return commit_result

    # Get the actual SHA from the commit
    git_sha = commit_result.data or ""

    # Step 5: Publish event with actual SHA
    final_event = SnapshotCreated.create(
        git_sha=git_sha,
        message=commit_message,
        event_count=len(events),
    )
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)
