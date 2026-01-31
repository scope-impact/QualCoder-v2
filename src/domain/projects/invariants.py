"""
Project Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate business rules for project operations.
These are composed by Derivers to determine if an operation is valid.

Architecture:
    Invariant: (entity, context) -> bool
    - Pure function, no side effects
    - Returns True if rule is satisfied, False if violated
    - Named with is_* or can_* prefix
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from src.domain.projects.entities import Source, SourceType
from src.domain.shared.types import SourceId
from src.domain.shared.validation import is_non_empty_string, is_within_length

# ============================================================
# File Extension Mappings
# ============================================================

TEXT_EXTENSIONS = frozenset({".txt", ".docx", ".doc", ".odt", ".rtf", ".md", ".epub"})
AUDIO_EXTENSIONS = frozenset({".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".mkv", ".wmv", ".webm", ".m4v"})
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"})
PDF_EXTENSIONS = frozenset({".pdf"})


# ============================================================
# Project Name Invariants
# ============================================================


def is_valid_project_name(name: str) -> bool:
    """
    Check that a project name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 200 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 200)


# ============================================================
# Project Path Invariants
# ============================================================


def is_valid_project_path(path: Path) -> bool:
    """
    Check that a project path has valid .qda extension.

    Rules:
    - Must have .qda extension
    - Filename must not be empty (not just ".qda")
    """
    if path.suffix.lower() != ".qda":
        return False

    # Check filename is not just ".qda"
    if path.stem == "":
        return False

    return True


def can_open_project(
    path: Path,
    path_exists: Callable[[Path], bool],
) -> bool:
    """
    Check if a project can be opened.

    Args:
        path: Path to the project file
        path_exists: Function to check if path exists

    Returns:
        True if project can be opened
    """
    if not is_valid_project_path(path):
        return False

    return path_exists(path)


def can_create_project(
    path: Path,
    path_exists: Callable[[Path], bool],
    parent_writable: Callable[[Path], bool],
) -> bool:
    """
    Check if a project can be created at the given path.

    Args:
        path: Path for the new project file
        path_exists: Function to check if path exists
        parent_writable: Function to check if parent directory is writable

    Returns:
        True if project can be created
    """
    if not is_valid_project_path(path):
        return False

    # Cannot overwrite existing file
    if path_exists(path):
        return False

    # Must be able to write to parent directory
    return parent_writable(path.parent)


# ============================================================
# Source Type Detection
# ============================================================


def detect_source_type(path: Path) -> SourceType:
    """
    Detect the source type based on file extension.

    Args:
        path: Path to the source file

    Returns:
        SourceType based on extension
    """
    ext = path.suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return SourceType.TEXT
    if ext in AUDIO_EXTENSIONS:
        return SourceType.AUDIO
    if ext in VIDEO_EXTENSIONS:
        return SourceType.VIDEO
    if ext in IMAGE_EXTENSIONS:
        return SourceType.IMAGE
    if ext in PDF_EXTENSIONS:
        return SourceType.PDF

    return SourceType.UNKNOWN


# ============================================================
# Source Name Invariants
# ============================================================


def is_source_name_unique(
    name: str,
    existing_sources: Iterable[Source],
    exclude_source_id: SourceId | None = None,
) -> bool:
    """
    Check that a source name is unique within the project.

    Args:
        name: The proposed source name
        existing_sources: All sources in the project
        exclude_source_id: Source ID to exclude (for renames)

    Returns:
        True if name is unique (case-insensitive)
    """
    for source in existing_sources:
        if exclude_source_id and source.id == exclude_source_id:
            continue
        if source.name.lower() == name.lower():
            return False
    return True


def is_valid_source_name(name: str) -> bool:
    """
    Check that a source name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 255 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 255)


# ============================================================
# Source Import Invariants
# ============================================================


def can_import_source(
    path: Path,
    path_exists: Callable[[Path], bool],
    existing_sources: Iterable[Source],
) -> bool:
    """
    Check if a source file can be imported.

    Args:
        path: Path to the source file
        path_exists: Function to check if path exists
        existing_sources: Existing sources for uniqueness check

    Returns:
        True if source can be imported
    """
    if not path_exists(path):
        return False

    # Check name uniqueness
    name = path.name
    return is_source_name_unique(name, existing_sources)


def is_supported_source_type(path: Path) -> bool:
    """
    Check if the source file type is supported.

    Args:
        path: Path to the source file

    Returns:
        True if file type is supported for import
    """
    source_type = detect_source_type(path)
    return source_type != SourceType.UNKNOWN
