"""
Initialize Version Control Command Handler

Orchestrates initializing version control for a project.
Follows the 5-step command handler pattern.

Usage:
    result = initialize_version_control(
        command=InitializeVersionControlCommand(...),
        diffable_adapter=diffable_adapter,
        git_adapter=git_adapter,
        event_bus=event_bus,
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import InitializeVersionControlCommand
from src.contexts.projects.core.vcs_derivers import (
    VersionControlState,
    derive_initialize_version_control,
)
from src.contexts.projects.core.vcs_events import VersionControlInitialized
from src.contexts.projects.core.vcs_failure_events import VersionControlNotInitialized
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus

# ============================================================
# Constants
# ============================================================

# .gitignore content for QualCoder VCS
GITIGNORE_CONTENT = """\
# QualCoder VCS - Ignore binary SQLite files
# These are reconstructed from the diffable JSON snapshots

# Main database file (binary, not diffable)
data.sqlite

# SQLite journal files
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
    """
    Initialize version control for a project.

    Steps:
    1. Build state and call deriver to check if initialization can proceed
    2. Handle failure - return early if already initialized
    3. Execute I/O:
       - Git init
       - Create .gitignore
       - Initial dump of database
       - Initial commit
    4. Publish event

    Args:
        command: InitializeVersionControlCommand with project path
        diffable_adapter: Adapter for SQLite-to-JSON conversion
        git_adapter: Adapter for Git operations
        event_bus: Event bus for publishing domain events

    Returns:
        OperationResult.ok(data=VersionControlInitialized) on success
        OperationResult.fail() or OperationResult.from_failure() on failure
    """
    project_path = Path(command.project_path)

    # Step 1: Build state from adapters
    state = VersionControlState(
        is_initialized=git_adapter.is_initialized(),
        has_uncommitted_changes=False,
        valid_refs=(),
    )

    # Step 2: Call deriver (pure domain decision)
    result = derive_initialize_version_control(
        project_path=str(project_path),
        state=state,
    )

    # Step 3: Handle failure - return early if deriver rejects
    if isinstance(result, VersionControlNotInitialized):
        return OperationResult.from_failure(result)

    # Deriver returned success - proceed with I/O operations

    # Step 4a: Git init
    init_result = git_adapter.init()
    if init_result.is_failure:
        return init_result

    # Step 4b: Create .gitignore
    gitignore_result = _create_gitignore(project_path.parent)
    if gitignore_result.is_failure:
        return gitignore_result

    # Step 4c: Initial dump of database
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    db_path = project_path  # Assumes project_path is the .qda file

    dump_result = diffable_adapter.dump(db_path, vcs_dir)
    if dump_result.is_failure:
        return dump_result

    # Step 4d: Stage all files
    stage_gitignore = git_adapter.add_all(Path(".gitignore"))
    if stage_gitignore.is_failure:
        return stage_gitignore

    stage_vcs = git_adapter.add_all(vcs_dir.name)
    if stage_vcs.is_failure:
        return stage_vcs

    # Step 4e: Initial commit
    commit_result = git_adapter.commit("Initial version control snapshot")
    if commit_result.is_failure:
        return commit_result

    # Step 5: Publish event
    final_event = VersionControlInitialized.create(
        project_path=str(project_path),
    )
    event_bus.publish(final_event)

    return OperationResult.ok(data=final_event)


def _create_gitignore(project_dir: Path) -> OperationResult:
    """
    Create .gitignore file in the project directory.

    Args:
        project_dir: Directory containing the project

    Returns:
        OperationResult.ok() on success
        OperationResult.fail() on failure
    """
    gitignore_path = project_dir / ".gitignore"

    try:
        # Write .gitignore (overwrite if exists)
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
