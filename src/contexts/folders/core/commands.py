"""
Folders Context: Commands

Command objects for folder operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateFolderCommand:
    """Command to create a new folder."""

    name: str
    parent_id: str | None = None


@dataclass(frozen=True)
class RenameFolderCommand:
    """Command to rename a folder."""

    folder_id: str
    new_name: str


@dataclass(frozen=True)
class DeleteFolderCommand:
    """Command to delete an empty folder."""

    folder_id: str


@dataclass(frozen=True)
class MoveSourceToFolderCommand:
    """Command to move a source to a folder."""

    source_id: str
    folder_id: str | None  # None = move to root (no folder)
