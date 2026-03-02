"""List Snapshots Command Handler - Returns commit history from Git."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter

logger = logging.getLogger("qualcoder.projects.core")


@metered_command("list_snapshots")
def list_snapshots(limit: int, git_adapter: GitRepositoryAdapter) -> OperationResult:
    """List version control snapshots (commit history)."""
    logger.debug("list_snapshots: limit=%s", limit)
    if not git_adapter.is_initialized():
        logger.error("list_snapshots: version control not initialized")
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="SNAPSHOTS_NOT_LISTED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )
    result = git_adapter.log(limit=limit)
    if result.is_success:
        logger.info("list_snapshots: returned snapshots, limit=%s", limit)
    return result
