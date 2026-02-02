"""
DEPRECATED: Use src.contexts.projects.core.derivers instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.projects.core.derivers import (
    DuplicateFolderName,
    DuplicateSourceName,
    EmptyProjectName,
    FolderNotEmpty,
    FolderNotFound,
    FolderState,
    InvalidFolderName,
    InvalidProjectPath,
    InvalidSourceStatus,
    ParentNotWritable,
    ProjectAlreadyExists,
    ProjectNotFound,
    ProjectState,
    SourceFileNotFound,
    SourceNotFound,
    UnsupportedSourceType,
    derive_add_source,
    derive_create_folder,
    derive_create_project,
    derive_delete_folder,
    derive_move_source_to_folder,
    derive_open_project,
    derive_open_source,
    derive_remove_source,
    derive_rename_folder,
    derive_update_source,
)

__all__ = [
    # State Containers
    "ProjectState",
    "FolderState",
    # Failure Reasons
    "EmptyProjectName",
    "InvalidProjectPath",
    "ProjectAlreadyExists",
    "ParentNotWritable",
    "ProjectNotFound",
    "SourceFileNotFound",
    "DuplicateSourceName",
    "UnsupportedSourceType",
    "InvalidFolderName",
    "DuplicateFolderName",
    "FolderNotFound",
    "FolderNotEmpty",
    "SourceNotFound",
    "InvalidSourceStatus",
    # Derivers
    "derive_create_project",
    "derive_open_project",
    "derive_add_source",
    "derive_remove_source",
    "derive_open_source",
    "derive_update_source",
    "derive_create_folder",
    "derive_rename_folder",
    "derive_delete_folder",
    "derive_move_source_to_folder",
]
