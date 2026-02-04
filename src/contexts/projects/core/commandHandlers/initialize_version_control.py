"""Initialize Version Control Command Handler - Orchestrates VCS initialization."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import InitializeVersionControlCommand
from src.contexts.projects.core.vcs_derivers import derive_initialize_version_control
from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import VersionControlInitialized
from src.contexts.projects.core.vcs_failure_events import VersionControlNotInitialized
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus

GITIGNORE_CONTENT = """\
# QualCoder VCS - Ignore binary SQLite files
data.sqlite
*.sqlite-journal
*.sqlite-wal
*.sqlite-shm
"""


def initialize_version_control(
    command: InitializeVersionControlCommand,
    diffable_adapter: SqliteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """Initialize version control for a project."""
    project_path = Path(command.project_path)

    # Build state and call deriver
    state = VersionControlState(is_initialized=git_adapter.is_initialized())
    result = derive_initialize_version_control(str(project_path), state)

    if isinstance(result, VersionControlNotInitialized):
        return OperationResult.from_failure(result)

    # Execute I/O: git init, create .gitignore, dump database, commit
    init_result = git_adapter.init()
    if init_result.is_failure:
        return init_result

    gitignore_result = _create_gitignore(project_path.parent)
    if gitignore_result.is_failure:
        return gitignore_result

    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    dump_result = diffable_adapter.dump(project_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    stage_gitignore = git_adapter.add_all(Path(".gitignore"))
    if stage_gitignore.is_failure:
        return stage_gitignore

    stage_vcs = git_adapter.add_all(vcs_dir.name)
    if stage_vcs.is_failure:
        return stage_vcs

    commit_result = git_adapter.commit("Initial version control snapshot")
    if commit_result.is_failure:
        return commit_result

    # Publish event
    final_event = VersionControlInitialized.create(str(project_path))
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)


def _create_gitignore(project_dir: Path) -> OperationResult:
    """Create .gitignore file in the project directory."""
    gitignore_path = project_dir / ".gitignore"
    try:
        gitignore_path.write_text(GITIGNORE_CONTENT, encoding="utf-8")
        return OperationResult.ok()
    except PermissionError:
        return OperationResult.fail(
            error=f"Permission denied writing .gitignore: {gitignore_path}",
            error_code="VERSION_CONTROL_NOT_INITIALIZED/PERMISSION_DENIED",
            suggestions=("Check write permissions for the project directory",),
        )
    except OSError as e:
        return OperationResult.fail(
            error=f"Failed to create .gitignore: {e}",
            error_code="VERSION_CONTROL_NOT_INITIALIZED/OS_ERROR",
        )
