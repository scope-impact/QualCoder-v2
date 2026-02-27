"""View Diff Command Handler - Returns diff output between snapshots."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter

logger = logging.getLogger("qualcoder.projects.core")


@metered_command("view_diff")
def view_diff(
    from_ref: str, to_ref: str, git_adapter: GitRepositoryAdapter
) -> OperationResult:
    """View differences between two snapshots."""
    logger.debug("view_diff: from_ref=%s, to_ref=%s", from_ref, to_ref)
    if not git_adapter.is_initialized():
        logger.error("view_diff: version control not initialized")
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="DIFF_NOT_VIEWED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )
    result = git_adapter.diff(from_ref=from_ref, to_ref=to_ref)
    if result.is_success:
        logger.info("view_diff: diff computed from_ref=%s, to_ref=%s", from_ref, to_ref)
    return result
