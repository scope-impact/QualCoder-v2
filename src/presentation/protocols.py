"""
Presentation Protocols - View Contracts

These interfaces define the CONTRACT between Presentation and Application layers.
Views implement these protocols; Controllers depend on them (Dependency Inversion).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

# ============================================================
# View Model DTOs (Data for Display)
# ============================================================


@dataclass(frozen=True)
class CodeViewModel:
    """Code data optimized for UI display"""

    id: int
    name: str
    color: str  # hex
    memo: str | None
    category_id: int | None
    category_name: str | None
    segment_count: int = 0


@dataclass(frozen=True)
class CategoryViewModel:
    """Category data optimized for UI display"""

    id: int
    name: str
    parent_id: int | None
    memo: str | None
    code_count: int = 0
    children_count: int = 0


@dataclass(frozen=True)
class SegmentViewModel:
    """Segment data optimized for UI display"""

    id: int
    code_id: int
    code_name: str
    code_color: str
    source_id: int
    source_name: str
    start: int
    end: int
    text: str
    memo: str | None
    importance: int = 0


@dataclass(frozen=True)
class SourceViewModel:
    """Source data optimized for UI display"""

    id: int
    name: str
    content: str
    media_type: str
    segment_count: int = 0
    char_count: int = 0


@dataclass(frozen=True)
class ActivityViewModel:
    """Agent activity item for display"""

    id: str
    timestamp: str
    client_name: str
    action: str
    description: str
    status: str  # "completed" | "pending" | "rejected" | "failed"
    payload: dict | None = None


# ============================================================
# View Protocols (Interfaces)
# ============================================================


class ICodingView(Protocol):
    """
    Contract for the Coding View.
    The View handles display and user input capture.
    It does NOT contain business logic.
    """

    # --- Display Methods ---

    def display_codes(self, codes: list[CodeViewModel]) -> None:
        """Display the list of codes in the codebook"""
        ...

    def display_categories(self, categories: list[CategoryViewModel]) -> None:
        """Display the category hierarchy"""
        ...

    def display_source(self, source: SourceViewModel) -> None:
        """Display a source document"""
        ...

    def display_segments(self, segments: list[SegmentViewModel]) -> None:
        """Display coded segments (highlights on source)"""
        ...

    def highlight_segment(
        self, start: int, end: int, color: str, flash: bool = False
    ) -> None:
        """Highlight a segment of text with optional flash animation"""
        ...

    def clear_highlights(self) -> None:
        """Remove all highlights from the source view"""
        ...

    def scroll_to_position(self, position: int) -> None:
        """Scroll the source view to a position"""
        ...

    def show_error(self, title: str, message: str) -> None:
        """Display an error message"""
        ...

    def show_success(self, message: str) -> None:
        """Display a success notification"""
        ...

    def set_loading(self, loading: bool) -> None:
        """Show/hide loading indicator"""
        ...

    # --- Input Capture ---

    def get_selected_text_range(self) -> tuple[int, int] | None:
        """Get currently selected text range (start, end)"""
        ...

    def get_selected_code_id(self) -> int | None:
        """Get currently selected code ID from the code tree"""
        ...

    def get_selected_source_id(self) -> int | None:
        """Get currently selected source ID"""
        ...

    # --- Event Callbacks (connected by Controller) ---

    def on_create_code_requested(
        self, handler: Callable[[str, str, str | None, int | None], None]
    ) -> None:
        """Register handler: (name, color, memo, category_id) -> None"""
        ...

    def on_apply_code_requested(
        self, handler: Callable[[int, int, int, int], None]
    ) -> None:
        """Register handler: (code_id, source_id, start, end) -> None"""
        ...

    def on_remove_code_requested(self, handler: Callable[[int], None]) -> None:
        """Register handler: (segment_id) -> None"""
        ...

    def on_delete_code_requested(self, handler: Callable[[int], None]) -> None:
        """Register handler: (code_id) -> None"""
        ...

    def on_rename_code_requested(self, handler: Callable[[int, str], None]) -> None:
        """Register handler: (code_id, new_name) -> None"""
        ...

    def on_source_selected(self, handler: Callable[[int], None]) -> None:
        """Register handler: (source_id) -> None"""
        ...

    def on_code_selected(self, handler: Callable[[int], None]) -> None:
        """Register handler: (code_id) -> None"""
        ...


class IAgentActivityView(Protocol):
    """
    Contract for the Agent Activity View.
    Shows real-time AI agent actions and approval requests.
    """

    def add_activity(self, activity: ActivityViewModel) -> None:
        """Add an activity item to the feed"""
        ...

    def update_activity_status(self, activity_id: str, new_status: str) -> None:
        """Update the status of an activity item"""
        ...

    def show_approval_request(
        self,
        request_id: str,
        action: str,
        description: str,
        on_approve: Callable[[], None],
        on_reject: Callable[[str | None], None],
    ) -> None:
        """Show an inline approval request"""
        ...

    def dismiss_approval_request(self, request_id: str) -> None:
        """Dismiss an approval request"""
        ...

    def set_agent_status(
        self,
        connected: bool,
        agent_name: str | None = None,
        actions_per_minute: int = 0,
    ) -> None:
        """Update agent connection status display"""
        ...

    def clear_activities(self) -> None:
        """Clear all activities from the feed"""
        ...


class IApprovalDialog(Protocol):
    """
    Contract for modal approval dialogs (high-risk actions).
    """

    def show(
        self,
        title: str,
        description: str,
        impact_items: list[str],
        on_approve: Callable[[], None],
        on_reject: Callable[[str | None], None],
    ) -> None:
        """Show the approval dialog"""
        ...

    def close(self) -> None:
        """Close the dialog"""
        ...
