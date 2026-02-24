"""
Folders Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate business rules for folder operations.
"""

from __future__ import annotations

from src.contexts.folders.core.entities import Folder
from src.contexts.projects.core.entities import Source
from src.shared.common.types import FolderId
from src.shared.core.validation import is_non_empty_string, is_within_length

# ============================================================
# Folder Name Validation
# ============================================================


def is_valid_folder_name(name: str) -> bool:
    """
    Check that a folder name is valid.

    Rules:
    - Not empty or whitespace-only
    - No path separators (/, \\)
    - Between 1 and 255 characters
    """
    return (
        is_non_empty_string(name)
        and is_within_length(name, 1, 255)
        and "/" not in name
        and "\\" not in name
    )


def is_folder_name_unique(
    name: str,
    parent_id: FolderId | None,
    existing_folders: tuple[Folder, ...],
) -> bool:
    """
    Check that a folder name is unique within its parent level.

    Folders must have unique names within the same parent folder.
    Different parent folders can have folders with the same name.

    Args:
        name: The proposed folder name
        parent_id: The parent folder ID (None for root level)
        existing_folders: All folders in the project

    Returns:
        True if name is unique at this parent level (case-insensitive)
    """
    for folder in existing_folders:
        if folder.parent_id == parent_id and folder.name.lower() == name.lower():
            return False
    return True


# ============================================================
# Folder Empty Check
# ============================================================


def is_folder_empty(
    folder_id: FolderId,
    sources: tuple[Source, ...],
) -> bool:
    """
    Check if a folder contains any sources.

    Args:
        folder_id: The folder ID to check
        sources: All sources in the project

    Returns:
        True if folder has no sources
    """
    return all(source.folder_id != folder_id for source in sources)


# ============================================================
# Folder Cycle Detection
# ============================================================


def would_create_cycle(
    folder_id: FolderId,
    new_parent_id: FolderId,
    folders: tuple[Folder, ...],
) -> bool:
    """
    Check if moving a folder would create a cycle in the folder tree.

    A cycle would occur if:
    - The folder is moved to itself
    - The folder is moved to one of its descendants

    Args:
        folder_id: The folder being moved
        new_parent_id: The proposed new parent
        folders: All folders in the project

    Returns:
        True if move would create a cycle
    """
    if folder_id == new_parent_id:
        return True

    current_id = new_parent_id
    folder_map = {folder.id: folder for folder in folders}

    while current_id is not None:
        if current_id == folder_id:
            return True
        current_folder = folder_map.get(current_id)
        if current_folder is None:
            break
        current_id = current_folder.parent_id

    return False
