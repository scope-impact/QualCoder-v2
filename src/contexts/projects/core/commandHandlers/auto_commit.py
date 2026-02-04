"""Auto-Commit Command Handler - Orchestrates automatic VCS commits."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import AutoCommitCommand
from src.contexts.projects.core.vcs_derivers import derive_auto_commit
from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import AutoCommitDecided, SnapshotCreated
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

    Steps:
    1. Build state from adapters
    2. Call deriver (domain decides)
    3. Handle failure
    4. Execute I/O (dump, stage, commit)
    5. Publish domain event
    """
    project_path = Path(command.project_path)
    events = tuple(command.events)

    # 1. Build state
    state = VersionControlState(is_initialized=git_adapter.is_initialized())

    # 2. Call deriver (domain decides)
    decision = derive_auto_commit(events=events, state=state)

    # 3. Handle failure
    if isinstance(decision, AutoCommitSkipped):
        return OperationResult.from_failure(decision)

    # Decision is AutoCommitDecided - extract message and count
    assert isinstance(decision, AutoCommitDecided)
    commit_message = decision.message
    event_count = decision.event_count

    # 4. Execute I/O: dump database, stage, commit
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)

    dump_result = diffable_adapter.dump(project_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    stage_result = git_adapter.add_all(vcs_dir.name)
    if stage_result.is_failure:
        return stage_result

    commit_result = git_adapter.commit(commit_message)
    if commit_result.is_failure:
        if commit_result.error_code == "GIT_NOT_COMMITTED/NOTHING_TO_COMMIT":
            # No actual changes to commit - return success without publishing event
            return OperationResult.ok(
                data=SnapshotCreated.create("no-changes", commit_message, event_count)
            )
        return commit_result

    # 5. Create and publish domain event with actual SHA
    final_event = SnapshotCreated.create(
        git_sha=commit_result.data or "",
        message=commit_message,
        event_count=event_count,
    )
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)
