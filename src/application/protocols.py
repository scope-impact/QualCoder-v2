"""
Application Protocols - Controller Contracts

These interfaces define the CONTRACT for application layer services.
Controllers coordinate between the domain layer and infrastructure.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from src.domain.coding.events import CodingEvent
from src.domain.shared.types import Result

# ============================================================
# Command DTOs (Input to Controllers)
# ============================================================


@dataclass(frozen=True)
class CreateCodeCommand:
    """Command to create a new code"""

    name: str
    color: str  # hex color
    memo: str | None = None
    category_id: int | None = None


@dataclass(frozen=True)
class RenameCodeCommand:
    """Command to rename an existing code"""

    code_id: int
    new_name: str


@dataclass(frozen=True)
class ChangeCodeColorCommand:
    """Command to change a code's color"""

    code_id: int
    new_color: str  # hex color


@dataclass(frozen=True)
class DeleteCodeCommand:
    """Command to delete a code"""

    code_id: int
    delete_segments: bool = (
        False  # If true, delete segments; if false, fail if segments exist
    )


@dataclass(frozen=True)
class MergeCodesCommand:
    """Command to merge one code into another"""

    source_code_id: int
    target_code_id: int


@dataclass(frozen=True)
class ApplyCodeCommand:
    """Command to apply a code to a segment of text"""

    code_id: int
    source_id: int
    start_position: int
    end_position: int
    memo: str | None = None
    importance: int = 0


@dataclass(frozen=True)
class RemoveCodeCommand:
    """Command to remove a code from a segment"""

    segment_id: int


@dataclass(frozen=True)
class CreateCategoryCommand:
    """Command to create a new category"""

    name: str
    parent_id: int | None = None
    memo: str | None = None


@dataclass(frozen=True)
class DeleteCategoryCommand:
    """Command to delete a category"""

    category_id: int
    orphan_strategy: str = "move_to_parent"  # "move_to_parent" | "delete_codes"


# ============================================================
# Controller Protocols
# ============================================================


class CodingController(Protocol):
    """
    Contract for the Coding Controller.
    Handles all coding-related commands and queries.
    """

    # --- Code Commands ---

    def create_code(self, command: CreateCodeCommand) -> Result:
        """Create a new code in the codebook"""
        ...

    def rename_code(self, command: RenameCodeCommand) -> Result:
        """Rename an existing code"""
        ...

    def change_code_color(self, command: ChangeCodeColorCommand) -> Result:
        """Change a code's color"""
        ...

    def delete_code(self, command: DeleteCodeCommand) -> Result:
        """Delete a code from the codebook"""
        ...

    def merge_codes(self, command: MergeCodesCommand) -> Result:
        """Merge source code into target code"""
        ...

    # --- Segment Commands ---

    def apply_code(self, command: ApplyCodeCommand) -> Result:
        """Apply a code to a text segment"""
        ...

    def remove_code(self, command: RemoveCodeCommand) -> Result:
        """Remove coding from a segment"""
        ...

    # --- Category Commands ---

    def create_category(self, command: CreateCategoryCommand) -> Result:
        """Create a new code category"""
        ...

    def delete_category(self, command: DeleteCategoryCommand) -> Result:
        """Delete a code category"""
        ...

    # --- Queries ---

    def get_all_codes(self) -> list[Any]:
        """Get all codes in the project"""
        ...

    def get_code(self, code_id: int) -> Any | None:
        """Get a specific code by ID"""
        ...

    def get_segments_for_source(self, source_id: int) -> list[Any]:
        """Get all segments for a source"""
        ...

    def get_segments_for_code(self, code_id: int) -> list[Any]:
        """Get all segments with a specific code"""
        ...

    def get_all_categories(self) -> list[Any]:
        """Get all categories"""
        ...


# ============================================================
# Event Bus Protocol
# ============================================================

EventHandler = Callable[[CodingEvent], None]


class EventBus(Protocol):
    """
    Contract for the Event Bus.
    Enables publish-subscribe communication between components.
    """

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe to events of a specific type"""
        ...

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events"""
        ...

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """Unsubscribe from events of a specific type"""
        ...

    def publish(self, event: CodingEvent) -> None:
        """Publish an event to all subscribers"""
        ...

    def clear(self) -> None:
        """Clear all subscriptions"""
        ...
