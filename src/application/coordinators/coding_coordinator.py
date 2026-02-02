"""
Coding Coordinator - Code and Segment Management.

Handles all coding-related operations for codes, segments, and categories.
"""

from __future__ import annotations

from returns.result import Failure, Result

from src.application.coordinators.base import BaseCoordinator


class CodingCoordinator(BaseCoordinator):
    """
    Coordinator for coding operations.

    Manages:
    - Code CRUD (create, rename, change color, delete, merge)
    - Segment operations (apply code, remove)
    - Category operations
    - Code and segment queries

    Requires an open project for all operations.
    """

    # =========================================================================
    # Code Commands
    # =========================================================================

    def create_code(self, command) -> Result:
        """Create a new code in the codebook."""
        from src.application.coding.usecases import create_code

        if self.coding_context is None:
            return Failure("No project is currently open")
        return create_code(command, self.coding_context, self.event_bus)

    def rename_code(self, command) -> Result:
        """Rename an existing code."""
        from src.application.coding.usecases import rename_code

        if self.coding_context is None:
            return Failure("No project is currently open")
        return rename_code(command, self.coding_context, self.event_bus)

    def change_code_color(self, command) -> Result:
        """Change a code's color."""
        from src.application.coding.usecases import change_code_color

        if self.coding_context is None:
            return Failure("No project is currently open")
        return change_code_color(command, self.coding_context, self.event_bus)

    def delete_code(self, command) -> Result:
        """Delete a code from the codebook."""
        from src.application.coding.usecases import delete_code

        if self.coding_context is None:
            return Failure("No project is currently open")
        return delete_code(command, self.coding_context, self.event_bus)

    def merge_codes(self, command) -> Result:
        """Merge source code into target code."""
        from src.application.coding.usecases import merge_codes

        if self.coding_context is None:
            return Failure("No project is currently open")
        return merge_codes(command, self.coding_context, self.event_bus)

    def update_code_memo(self, command) -> Result:
        """Update a code's memo."""
        from src.application.coding.usecases import update_code_memo

        if self.coding_context is None:
            return Failure("No project is currently open")
        return update_code_memo(command, self.coding_context, self.event_bus)

    def move_code_to_category(self, command) -> Result:
        """Move a code to a different category."""
        from src.application.coding.usecases import move_code_to_category

        if self.coding_context is None:
            return Failure("No project is currently open")
        return move_code_to_category(command, self.coding_context, self.event_bus)

    # =========================================================================
    # Segment Commands
    # =========================================================================

    def apply_code(self, command) -> Result:
        """Apply a code to a text segment."""
        from src.application.coding.usecases import apply_code

        if self.coding_context is None:
            return Failure("No project is currently open")
        return apply_code(
            command,
            self.coding_context,
            self.event_bus,
            source_content_provider=None,  # TODO: wire up content provider
        )

    def remove_segment(self, command) -> Result:
        """Remove coding from a segment."""
        from src.application.coding.usecases import remove_segment

        if self.coding_context is None:
            return Failure("No project is currently open")
        return remove_segment(command, self.coding_context, self.event_bus)

    # =========================================================================
    # Category Commands
    # =========================================================================

    def create_category(self, command) -> Result:
        """Create a new code category."""
        from src.application.coding.usecases import create_category

        if self.coding_context is None:
            return Failure("No project is currently open")
        return create_category(command, self.coding_context, self.event_bus)

    def delete_category(self, command) -> Result:
        """Delete a code category."""
        from src.application.coding.usecases import delete_category

        if self.coding_context is None:
            return Failure("No project is currently open")
        return delete_category(command, self.coding_context, self.event_bus)

    # =========================================================================
    # Queries
    # =========================================================================

    def get_all_codes(self) -> list:
        """Get all codes in the project."""
        from src.application.coding.usecases import get_all_codes

        if self.coding_context is None:
            return []
        return get_all_codes(self.coding_context)

    def get_code(self, code_id: int):
        """Get a specific code by ID."""
        from src.application.coding.usecases import get_code

        if self.coding_context is None:
            return None
        return get_code(self.coding_context, code_id)

    def get_segments_for_source(self, source_id: int) -> list:
        """Get all segments for a source."""
        from src.application.coding.usecases import get_segments_for_source

        if self.coding_context is None:
            return []
        return get_segments_for_source(self.coding_context, source_id)

    def get_segments_for_code(self, code_id: int) -> list:
        """Get all segments with a specific code."""
        from src.application.coding.usecases import get_segments_for_code

        if self.coding_context is None:
            return []
        return get_segments_for_code(self.coding_context, code_id)

    def get_all_categories(self) -> list:
        """Get all categories."""
        from src.application.coding.usecases import get_all_categories

        if self.coding_context is None:
            return []
        return get_all_categories(self.coding_context)
