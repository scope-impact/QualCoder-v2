"""
Coding Context Policies

Declarative policies for cross-context reactions to coding domain events.

Policies defined:
- Category deleted: orphan codes (move to uncategorized)
- Code deleted: cleanup related data
- Code merged: log merge operation for audit
"""

from __future__ import annotations

import logging
from typing import Any

from src.application.policies import configure_policy
from src.contexts.coding.core.events import (
    CategoryDeleted,
    CodeDeleted,
    CodesMerged,
)

logger = logging.getLogger(__name__)

# Repository references - set during initialization
_code_repo: Any = None
_segment_repo: Any = None


def set_coding_policy_repositories(
    code_repo: Any = None,
    segment_repo: Any = None,
) -> None:
    """
    Configure repository references for coding policy actions.

    Args:
        code_repo: Repository for code operations
        segment_repo: Repository for segment operations
    """
    global _code_repo, _segment_repo
    _code_repo = code_repo
    _segment_repo = segment_repo


# ============================================================
# Policy Actions
# ============================================================


def orphan_codes_on_category_delete(event: CategoryDeleted) -> None:
    """
    Move codes to uncategorized when their category is deleted.

    The codes_orphaned field in the event tells us how many codes
    will need their category_id set to NULL.
    """
    logger.debug(
        "Category deleted: %s (id=%d), codes_orphaned=%d",
        event.name,
        event.category_id.value,
        event.codes_orphaned,
    )

    if _code_repo is None:
        logger.debug("No code repo configured - skipping orphan codes")
        return

    if event.codes_orphaned == 0:
        return

    try:
        # Note: This would typically be done by the use case,
        # but having a policy allows for additional actions
        if hasattr(_code_repo, "uncategorize_codes_in_category"):
            _code_repo.uncategorize_codes_in_category(event.category_id)
            logger.debug(
                "Orphaned %d codes from category %s",
                event.codes_orphaned,
                event.name,
            )
    except Exception as e:
        logger.error("Failed to orphan codes: %s", e)
        raise


def log_code_deletion(event: CodeDeleted) -> None:
    """
    Log code deletion for audit purposes.

    Records the code name and how many segments were removed.
    """
    logger.info(
        "Code deleted: %s (id=%d), segments_removed=%d",
        event.name,
        event.code_id.value,
        event.segments_removed,
    )


def log_code_merge(event: CodesMerged) -> None:
    """
    Log code merge for audit purposes.

    Records which codes were merged and how many segments moved.
    """
    logger.info(
        "Codes merged: %s (id=%d) -> %s (id=%d), segments_moved=%d",
        event.source_code_name,
        event.source_code_id.value,
        event.target_code_name,
        event.target_code_id.value,
        event.segments_moved,
    )


def cleanup_after_code_delete(event: CodeDeleted) -> None:
    """
    Perform additional cleanup after a code is deleted.

    The segments are typically cascade-deleted by the database,
    but this policy can handle additional cleanup like:
    - Cleaning up code-specific caches
    - Notifying external systems
    - Updating statistics
    """
    # Segments are cascade-deleted by database foreign key
    # This policy exists for extensibility
    pass


# ============================================================
# Policy Configuration
# ============================================================


def configure_coding_policies() -> None:
    """
    Configure all policies for the coding context.

    Call this during application initialization, before starting
    the PolicyExecutor.
    """
    # Category deletion policies
    configure_policy(
        event_type=CategoryDeleted,
        actions={
            "ORPHAN_CODES": orphan_codes_on_category_delete,
        },
        description="Handle orphaned codes when category is deleted",
    )

    # Code deletion policies
    configure_policy(
        event_type=CodeDeleted,
        actions={
            "LOG_DELETION": log_code_deletion,
            "CLEANUP": cleanup_after_code_delete,
        },
        description="Audit and cleanup after code deletion",
    )

    # Code merge policies
    configure_policy(
        event_type=CodesMerged,
        actions={
            "LOG_MERGE": log_code_merge,
        },
        description="Audit code merge operations",
    )

    logger.info("Coding policies configured")


__all__ = [
    "configure_coding_policies",
    "set_coding_policy_repositories",
    # Individual actions for testing/extension
    "orphan_codes_on_category_delete",
    "log_code_deletion",
    "log_code_merge",
    "cleanup_after_code_delete",
]
