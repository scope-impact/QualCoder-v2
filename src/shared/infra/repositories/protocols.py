"""
Repository Protocol Definitions.

These protocols define the contracts that all repository implementations
must follow, enabling backend-agnostic code in the domain layer.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case, CaseAttribute
    from src.contexts.coding.core.entities import Category, Code, TextSegment
    from src.contexts.sources.core.entities import Folder, Source
    from src.shared.common.types import (
        CaseId,
        CategoryId,
        CodeId,
        FolderId,
        SegmentId,
        SourceId,
    )


class BackendType(str, Enum):
    """Supported database backend types."""

    SQLITE = "sqlite"
    CONVEX = "convex"


@runtime_checkable
class CodeRepositoryProtocol(Protocol):
    """Protocol for Code repository implementations."""

    def get_all(self) -> list[Code]:
        """Get all codes in the project."""
        ...

    def get_by_id(self, code_id: CodeId) -> Code | None:
        """Get a code by its ID."""
        ...

    def get_by_name(self, name: str) -> Code | None:
        """Get a code by its name (case-insensitive)."""
        ...

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        """Get all codes in a category."""
        ...

    def save(self, code: Code) -> None:
        """Save a code (insert or update)."""
        ...

    def delete(self, code_id: CodeId) -> None:
        """Delete a code by ID."""
        ...

    def exists(self, code_id: CodeId) -> bool:
        """Check if a code exists."""
        ...

    def name_exists(self, name: str, exclude_id: CodeId | None = None) -> bool:
        """Check if a code name is already taken."""
        ...


@runtime_checkable
class CategoryRepositoryProtocol(Protocol):
    """Protocol for Category repository implementations."""

    def get_all(self) -> list[Category]:
        """Get all categories."""
        ...

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID."""
        ...

    def get_by_parent(self, parent_id: CategoryId | None) -> list[Category]:
        """Get child categories of a parent (None for root)."""
        ...

    def save(self, category: Category) -> None:
        """Save a category."""
        ...

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category."""
        ...

    def name_exists(self, name: str, exclude_id: CategoryId | None = None) -> bool:
        """Check if a category name is already taken."""
        ...


@runtime_checkable
class SegmentRepositoryProtocol(Protocol):
    """Protocol for TextSegment repository implementations."""

    def get_all(self) -> list[TextSegment]:
        """Get all text segments."""
        ...

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        """Get a segment by ID."""
        ...

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        """Get all segments for a source."""
        ...

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        """Get all segments with a specific code."""
        ...

    def get_by_source_and_code(
        self, source_id: SourceId, code_id: CodeId
    ) -> list[TextSegment]:
        """Get segments for a source with a specific code."""
        ...

    def save(self, segment: TextSegment) -> None:
        """Save a segment."""
        ...

    def delete(self, segment_id: SegmentId) -> None:
        """Delete a segment by ID."""
        ...

    def delete_by_code(self, code_id: CodeId) -> int:
        """Delete all segments with a code, returns count deleted."""
        ...

    def delete_by_source(self, source_id: SourceId) -> int:
        """Delete all segments for a source, returns count deleted."""
        ...

    def count_by_code(self, code_id: CodeId) -> int:
        """Count segments with a specific code."""
        ...

    def count_by_source(self, source_id: SourceId) -> int:
        """Count segments for a specific source."""
        ...

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        """Reassign all segments from one code to another, returns count."""
        ...

    def update_source_name(self, source_id: SourceId, new_name: str) -> None:
        """Update denormalized source_name for all segments of a source."""
        ...


@runtime_checkable
class SourceRepositoryProtocol(Protocol):
    """Protocol for Source repository implementations."""

    def get_all(self) -> list[Source]:
        """Get all sources."""
        ...

    def get_by_id(self, source_id: SourceId) -> Source | None:
        """Get a source by ID."""
        ...

    def get_by_name(self, name: str) -> Source | None:
        """Get a source by name."""
        ...

    def get_by_type(self, source_type: str) -> list[Source]:
        """Get all sources of a specific type."""
        ...

    def get_by_status(self, status: str) -> list[Source]:
        """Get all sources with a specific status."""
        ...

    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]:
        """Get all sources in a folder (None for root)."""
        ...

    def save(self, source: Source) -> None:
        """Save a source (insert or update)."""
        ...

    def delete(self, source_id: SourceId) -> None:
        """Delete a source by ID."""
        ...

    def exists(self, source_id: SourceId) -> bool:
        """Check if a source exists."""
        ...


@runtime_checkable
class FolderRepositoryProtocol(Protocol):
    """Protocol for Folder repository implementations."""

    def get_all(self) -> list[Folder]:
        """Get all folders."""
        ...

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        """Get a folder by ID."""
        ...

    def get_children(self, parent_id: FolderId | None) -> list[Folder]:
        """Get child folders of a parent (None for root)."""
        ...

    def get_root_folders(self) -> list[Folder]:
        """Get all root-level folders."""
        ...

    def get_descendants(self, folder_id: FolderId) -> list[Folder]:
        """Get all descendants of a folder."""
        ...

    def save(self, folder: Folder) -> None:
        """Save a folder (insert or update)."""
        ...

    def delete(self, folder_id: FolderId) -> None:
        """Delete a folder by ID."""
        ...

    def update_parent(self, folder_id: FolderId, new_parent_id: FolderId | None) -> None:
        """Move a folder to a new parent."""
        ...


@runtime_checkable
class CaseRepositoryProtocol(Protocol):
    """Protocol for Case repository implementations."""

    def get_all(self) -> list[Case]:
        """Get all cases."""
        ...

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by ID."""
        ...

    def get_by_name(self, name: str) -> Case | None:
        """Get a case by name."""
        ...

    def save(self, case: Case) -> None:
        """Save a case (insert or update)."""
        ...

    def delete(self, case_id: CaseId) -> None:
        """Delete a case by ID."""
        ...

    def get_cases_for_source(self, source_id: SourceId) -> list[Case]:
        """Get all cases linked to a source."""
        ...

    def link_source(
        self, case_id: CaseId, source_id: SourceId, source_name: str, owner: str
    ) -> None:
        """Link a source to a case."""
        ...

    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> None:
        """Unlink a source from a case."""
        ...

    def save_attribute(self, case_id: CaseId, attribute: CaseAttribute) -> None:
        """Save a case attribute."""
        ...

    def get_attributes(self, case_id: CaseId) -> list[CaseAttribute]:
        """Get all attributes for a case."""
        ...

    def delete_attribute(self, case_id: CaseId, attribute_name: str) -> None:
        """Delete an attribute from a case."""
        ...
