"""Initialize Version Control Command Handler - Orchestrates VCS initialization."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.vcs_commands import InitializeVersionControlCommand
from src.contexts.projects.core.vcs_derivers import derive_initialize_version_control
from src.contexts.projects.core.vcs_entities import VersionControlState
from src.contexts.projects.core.vcs_events import (
    InitializeDecided,
    VersionControlInitialized,
)
from src.contexts.projects.core.vcs_failure_events import VersionControlNotInitialized
from src.contexts.projects.core.vcs_invariants import (
    resolve_db_path,
    resolve_project_dir,
)
from src.shared.common.operation_result import OperationResult
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.projects.core")

GITIGNORE_CONTENT = """\
# QualCoder VCS - Ignore binary SQLite files
data.sqlite
*.sqlite-journal
*.sqlite-wal
*.sqlite-shm
"""


@metered_command("initialize_version_control")
def initialize_version_control(
    command: InitializeVersionControlCommand,
    diffable_adapter: SqliteDiffableAdapter,
    git_adapter: GitRepositoryAdapter,
    event_bus: EventBus,
) -> OperationResult:
    """
    Initialize version control for a project.

    Steps:
    1. Build state from adapters
    2. Call deriver (domain decides)
    3. Handle failure
    4. Execute I/O (init, gitignore, dump, commit)
    5. Publish domain event
    """
    logger.debug("initialize_version_control: project_path=%s", command.project_path)
    project_path = Path(command.project_path)

    # 1. Build state
    state = VersionControlState(is_initialized=git_adapter.is_initialized())

    # 2. Call deriver (domain decides)
    decision = derive_initialize_version_control(str(project_path), state)

    # 3. Handle failure
    if isinstance(decision, VersionControlNotInitialized):
        logger.error("initialize_version_control: deriver rejected for project_path=%s", project_path)
        return OperationResult.from_failure(decision)

    # Decision is InitializeDecided - extract project path
    assert isinstance(decision, InitializeDecided)
    target_path = decision.project_path

    # 4. Execute I/O: git init, create .gitignore, dump database, commit
    init_result = git_adapter.init()
    if init_result.is_failure:
        logger.error("initialize_version_control: git init failed for project_path=%s", project_path)
        return init_result

    gitignore_result = _create_gitignore(resolve_project_dir(project_path))
    if gitignore_result.is_failure:
        logger.error("initialize_version_control: gitignore creation failed for project_path=%s", project_path)
        return gitignore_result

    db_path = resolve_db_path(project_path)
    vcs_dir = diffable_adapter.get_vcs_dir(project_path)
    dump_result = diffable_adapter.dump(db_path, vcs_dir)
    if dump_result.is_failure:
        logger.error("initialize_version_control: dump failed for project_path=%s", project_path)
        return dump_result

    stage_gitignore = git_adapter.add_all(Path(".gitignore"))
    if stage_gitignore.is_failure:
        logger.error("initialize_version_control: stage gitignore failed for project_path=%s", project_path)
        return stage_gitignore

    stage_vcs = git_adapter.add_all(vcs_dir.name)
    if stage_vcs.is_failure:
        logger.error("initialize_version_control: stage vcs failed for project_path=%s", project_path)
        return stage_vcs

    commit_result = git_adapter.commit("Initial version control snapshot")
    if commit_result.is_failure:
        logger.error("initialize_version_control: initial commit failed for project_path=%s", project_path)
        return commit_result

    # 5. Create and publish domain event
    final_event = VersionControlInitialized.create(target_path)
    event_bus.publish(final_event)

    logger.info("initialize_version_control: initialized VCS for project_path=%s", target_path)
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
