"""
DEPRECATED: Use src.contexts.projects.core.invariants instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.projects.core.invariants import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
    can_create_project,
    can_import_source,
    can_open_project,
    detect_source_type,
    is_folder_empty,
    is_folder_name_unique,
    is_source_name_unique,
    is_supported_source_type,
    is_valid_folder_name,
    is_valid_project_name,
    is_valid_project_path,
    is_valid_source_name,
    would_create_cycle,
)

__all__ = [
    # Extension constants
    "TEXT_EXTENSIONS",
    "AUDIO_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "PDF_EXTENSIONS",
    # Project invariants
    "is_valid_project_name",
    "is_valid_project_path",
    "can_open_project",
    "can_create_project",
    # Source type detection
    "detect_source_type",
    # Source invariants
    "is_source_name_unique",
    "is_valid_source_name",
    "can_import_source",
    "is_supported_source_type",
    # Folder invariants
    "is_valid_folder_name",
    "is_folder_name_unique",
    "is_folder_empty",
    "would_create_cycle",
]
