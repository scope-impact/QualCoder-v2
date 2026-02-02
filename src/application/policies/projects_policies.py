"""
Projects Context Policies

Declarative policies for cross-context reactions to projects domain events.
These policies replace the imperative SourceSyncHandler pattern.

Policies defined:
- Source renamed: sync denormalized source_name in segments and case links
- Source removed: cleanup segments and case links
- Folder deleted: orphan sources (if needed)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.application.policies import configure_policy
from src.contexts.projects.core.events import (
    FolderDeleted,
    SourceRemoved,
    SourceRenamed,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type alias for repository getter - set during initialization
_segment_repo: Any = None
_case_repo: Any = None


def set_policy_repositories(
    segment_repo: Any = None,
    case_repo: Any = None,
) -> None:
    """
    Configure repository references for policy actions.

    Called during application initialization to provide repositories
    that policies need to perform their work.

    Args:
        segment_repo: Repository for segment operations
        case_repo: Repository for case link operations
    """
    global _segment_repo, _case_repo
    _segment_repo = segment_repo
    _case_repo = case_repo


# ============================================================
# Policy Actions
# ============================================================


def sync_segment_source_name_on_rename(event: SourceRenamed) -> None:
    """
    Update denormalized source_name in cod_segment table.

    This keeps the source_name column in sync when a source is renamed.
    """
    if _segment_repo is None:
        logger.debug("No segment repo configured - skipping segment name sync")
        return

    try:
        _segment_repo.update_source_name(event.source_id, event.new_name)
        logger.debug(
            "Synced segment source_name: %s -> %s (source_id=%d)",
            event.old_name,
            event.new_name,
            event.source_id.value,
        )
    except Exception as e:
        logger.error("Failed to sync segment source_name: %s", e)
        raise


def sync_case_link_source_name_on_rename(event: SourceRenamed) -> None:
    """
    Update denormalized source_name in cas_source_link table.

    This keeps the source_name column in sync when a source is renamed.
    """
    if _case_repo is None:
        logger.debug("No case repo configured - skipping case link name sync")
        return

    try:
        _case_repo.update_source_name(event.source_id, event.new_name)
        logger.debug(
            "Synced case link source_name: %s -> %s (source_id=%d)",
            event.old_name,
            event.new_name,
            event.source_id.value,
        )
    except Exception as e:
        logger.error("Failed to sync case link source_name: %s", e)
        raise


def delete_segments_on_source_remove(event: SourceRemoved) -> None:
    """
    Delete segments when a source is removed.

    Note: This may be handled by CASCADE delete in the database,
    but having an explicit policy allows for additional cleanup
    or logging if needed.
    """
    logger.debug(
        "Source removed: %s (id=%d), segments_removed=%d",
        event.name,
        event.source_id.value,
        event.segments_removed,
    )
    # Segments are typically cascade-deleted by the database
    # This policy is here for logging and potential future actions


def unlink_cases_on_source_remove(event: SourceRemoved) -> None:
    """
    Handle case links when a source is removed.

    May mark links as orphaned or remove them entirely,
    depending on application policy.
    """
    if _case_repo is None:
        logger.debug("No case repo configured - skipping case unlink")
        return

    try:
        # Note: actual implementation depends on CaseRepository API
        # This could be: remove links, mark as orphaned, etc.
        if hasattr(_case_repo, "remove_links_for_source"):
            _case_repo.remove_links_for_source(event.source_id)
            logger.debug(
                "Removed case links for source: %s (id=%d)",
                event.name,
                event.source_id.value,
            )
    except Exception as e:
        logger.error("Failed to unlink cases: %s", e)
        raise


def orphan_sources_on_folder_delete(event: FolderDeleted) -> None:
    """
    Handle sources when their folder is deleted.

    This policy could:
    - Move sources to root level
    - Mark sources as needing attention
    - Log for admin review
    """
    logger.debug(
        "Folder deleted: %s (id=%d) - sources will be orphaned to root",
        event.name,
        event.folder_id.value,
    )
    # Sources are typically moved to root by the use case that deletes the folder
    # This policy is here for additional logging/cleanup if needed


# ============================================================
# Policy Configuration
# ============================================================


def configure_projects_policies() -> None:
    """
    Configure all policies for the projects context.

    Call this during application initialization, before starting
    the PolicyExecutor.
    """
    # Source rename policies
    configure_policy(
        event_type=SourceRenamed,
        actions={
            "SYNC_SEGMENT_NAME": sync_segment_source_name_on_rename,
            "SYNC_CASE_LINK_NAME": sync_case_link_source_name_on_rename,
        },
        description="Sync denormalized source names when source is renamed",
    )

    # Source removal policies
    configure_policy(
        event_type=SourceRemoved,
        actions={
            "LOG_SEGMENTS_REMOVED": delete_segments_on_source_remove,
            "UNLINK_CASES": unlink_cases_on_source_remove,
        },
        description="Cleanup when a source is removed from the project",
    )

    # Folder deletion policies
    configure_policy(
        event_type=FolderDeleted,
        actions={
            "ORPHAN_SOURCES": orphan_sources_on_folder_delete,
        },
        description="Handle sources when their folder is deleted",
    )

    logger.info("Projects policies configured")


__all__ = [
    "configure_projects_policies",
    "set_policy_repositories",
    # Individual actions for testing/extension
    "sync_segment_source_name_on_rename",
    "sync_case_link_source_name_on_rename",
    "delete_segments_on_source_remove",
    "unlink_cases_on_source_remove",
    "orphan_sources_on_folder_delete",
]
