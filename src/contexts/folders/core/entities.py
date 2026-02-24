"""
Folders Context: Entities

Domain entities for the folders bounded context.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from src.shared.common.types import FolderId


@dataclass(frozen=True)
class Folder:
    """
    A folder for organizing sources in a project.

    Folders can contain sources and be nested within other folders.
    """

    id: FolderId
    name: str
    parent_id: FolderId | None = None  # None means root level
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_name(self, new_name: str) -> Folder:
        """Return new Folder with updated name."""
        return replace(self, name=new_name)

    def with_parent(self, new_parent_id: FolderId | None) -> Folder:
        """Return new Folder with updated parent."""
        return replace(self, parent_id=new_parent_id)
