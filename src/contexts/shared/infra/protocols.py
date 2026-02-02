"""
Infrastructure Protocols - Repository Contracts

These interfaces define the CONTRACT for data access.
Implementations (SQLite, in-memory, etc.) must conform to these protocols.
"""

from typing import Protocol

from src.contexts.shared.core.types import CategoryId, CodeId, SegmentId, SourceId

# Forward references for entities that will be in their respective contexts
# These will need to be updated once coding context is migrated
from src.domain.coding.entities import (
    Category,
    Code,
    TextSegment,
)

# ============================================================
# Coding Context Repositories
# ============================================================


class CodeRepository(Protocol):
    """Interface for Code persistence"""

    def get_all(self) -> list[Code]:
        """Get all codes in the project"""
        ...

    def get_by_id(self, code_id: CodeId) -> Code | None:
        """Get a code by its ID"""
        ...

    def get_by_name(self, name: str) -> Code | None:
        """Get a code by its name (for uniqueness checks)"""
        ...

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        """Get all codes in a category"""
        ...

    def save(self, code: Code) -> None:
        """Save a code (insert or update)"""
        ...

    def delete(self, code_id: CodeId) -> None:
        """Delete a code by ID"""
        ...

    def exists(self, code_id: CodeId) -> bool:
        """Check if a code exists"""
        ...

    def name_exists(self, name: str, exclude_id: CodeId | None = None) -> bool:
        """Check if a code name is already taken"""
        ...


class CategoryRepository(Protocol):
    """Interface for Category persistence"""

    def get_all(self) -> list[Category]:
        """Get all categories"""
        ...

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID"""
        ...

    def get_by_parent(self, parent_id: CategoryId | None) -> list[Category]:
        """Get child categories of a parent (None for root)"""
        ...

    def save(self, category: Category) -> None:
        """Save a category"""
        ...

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category"""
        ...

    def name_exists(self, name: str, exclude_id: CategoryId | None = None) -> bool:
        """Check if a category name is already taken"""
        ...


class SegmentRepository(Protocol):
    """Interface for Segment persistence (text, image, AV)"""

    def get_all(self) -> list[TextSegment]:
        """Get all text segments"""
        ...

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        """Get a segment by ID"""
        ...

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        """Get all segments for a source"""
        ...

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        """Get all segments with a specific code"""
        ...

    def get_by_source_and_code(
        self, source_id: SourceId, code_id: CodeId
    ) -> list[TextSegment]:
        """Get segments for a source with a specific code"""
        ...

    def save(self, segment: TextSegment) -> None:
        """Save a segment"""
        ...

    def delete(self, segment_id: SegmentId) -> None:
        """Delete a segment by ID"""
        ...

    def delete_by_code(self, code_id: CodeId) -> int:
        """Delete all segments with a code, returns count deleted"""
        ...

    def count_by_code(self, code_id: CodeId) -> int:
        """Count segments with a specific code"""
        ...

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        """Reassign all segments from one code to another, returns count"""
        ...


# ============================================================
# Source Context Repositories (referenced by Coding)
# ============================================================


class SourceRepository(Protocol):
    """Interface for Source persistence (minimal for Coding context)"""

    def get_by_id(self, source_id: SourceId) -> object | None:
        """Get a source by ID (returns Source entity)"""
        ...

    def exists(self, source_id: SourceId) -> bool:
        """Check if a source exists"""
        ...

    def get_content(self, source_id: SourceId) -> str | None:
        """Get the text content of a source"""
        ...

    def get_length(self, source_id: SourceId) -> int | None:
        """Get the length of a source's content"""
        ...
