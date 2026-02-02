"""
Project Commands - Command DTOs for project operations.

These dataclasses represent the input for controller operations.
All commands are immutable (frozen) and contain only primitive types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ============================================================
# Project Commands
# ============================================================


@dataclass(frozen=True)
class CreateProjectCommand:
    """Command to create a new project."""

    name: str
    path: str  # String path for cross-platform compatibility
    memo: str | None = None


@dataclass(frozen=True)
class OpenProjectCommand:
    """Command to open an existing project."""

    path: str


# ============================================================
# Source Commands
# ============================================================


@dataclass(frozen=True)
class AddSourceCommand:
    """Command to add a source file to the project."""

    source_path: str
    origin: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class RemoveSourceCommand:
    """Command to remove a source from the project."""

    source_id: int


@dataclass(frozen=True)
class OpenSourceCommand:
    """Command to open a source for viewing/coding."""

    source_id: int


@dataclass(frozen=True)
class UpdateSourceCommand:
    """Command to update source metadata."""

    source_id: int
    memo: str | None = None
    origin: str | None = None
    status: str | None = None


# ============================================================
# Navigation Commands
# ============================================================


@dataclass(frozen=True)
class NavigateToScreenCommand:
    """Command to navigate to a different screen."""

    screen_name: str


@dataclass(frozen=True)
class NavigateToSegmentCommand:
    """Command to navigate to a specific segment position in a source."""

    source_id: int
    start_pos: int
    end_pos: int
    highlight: bool = True


# ============================================================
# Case Commands
# ============================================================


@dataclass(frozen=True)
class CreateCaseCommand:
    """Command to create a new case."""

    name: str
    description: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class UpdateCaseCommand:
    """Command to update an existing case."""

    case_id: int
    name: str
    description: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class RemoveCaseCommand:
    """Command to remove a case."""

    case_id: int


@dataclass(frozen=True)
class LinkSourceToCaseCommand:
    """Command to link a source to a case."""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class UnlinkSourceFromCaseCommand:
    """Command to unlink a source from a case."""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class SetCaseAttributeCommand:
    """Command to set an attribute on a case."""

    case_id: int
    attr_name: str
    attr_type: str  # text, number, date, boolean
    attr_value: Any


# ============================================================
# Folder Commands
# ============================================================


@dataclass(frozen=True)
class CreateFolderCommand:
    """Command to create a new folder."""

    name: str
    parent_id: int | None = None


@dataclass(frozen=True)
class RenameFolderCommand:
    """Command to rename a folder."""

    folder_id: int
    new_name: str


@dataclass(frozen=True)
class DeleteFolderCommand:
    """Command to delete an empty folder."""

    folder_id: int


@dataclass(frozen=True)
class MoveSourceToFolderCommand:
    """Command to move a source to a folder."""

    source_id: int
    folder_id: int | None  # None = move to root (no folder)
