"""
Text Coding Screen

The main text coding interface for QualCoder.
This screen wraps the TextCodingPage and implements the ScreenProtocol
for integration with AppShell.

Implements QC-007.02 Code Application Workflow:
- AC #1: Apply selected code via Q key (quick mark)
- AC #2: In-vivo coding: create new code from selected text (V key)
- AC #3: Apply code from recent codes submenu (R key)
- AC #4: Remove code at cursor position (U key - unmark)
- AC #5: Undo last unmark operation (Ctrl+Z)
- AC #6: Visual feedback (flash/highlight) on code application
- AC #7: Code counts update in tree after apply/remove
- AC #8: text_selected signal enables code application buttons
- AC #9: code_selected signal sets active code for quick-mark
- AC #10: code_applied signal triggers highlight update

Structure:
┌─────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                     │
│ [Text][Image][A/V][PDF] | Coder: [▼] | [icons...] | Search  │
├────────────┬─────────────────────────────────┬──────────────┤
│ LEFT PANEL │     CENTER PANEL                │  RIGHT PANEL │
│ ┌────────┐ │  ┌─────────────────────┐        │ ┌──────────┐ │
│ │ FILES  │ │  │ Editor Header       │        │ │ Selected │ │
│ └────────┘ │  │ ID2.odt [badge]     │        │ │ Code     │ │
│ ┌────────┐ │  ├─────────────────────┤        │ └──────────┘ │
│ │ CODES  │ │  │ Text content with   │        │ ┌──────────┐ │
│ │ tree   │ │  │ coded highlights    │        │ │ Overlaps │ │
│ └────────┘ │  └─────────────────────┘        │ └──────────┘ │
│ [nav btns] │                                 │              │
└────────────┴─────────────────────────────────┴──────────────┘
"""

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QVBoxLayout, QWidget
from returns.result import Success

from design_system import ColorPalette, get_colors
from src.application.coding.auto_coding_controller import AutoCodingController
from src.contexts.coding.core.services.text_matcher import MatchScope, MatchType

from ..dialogs.auto_code_dialog import AutoCodeDialog
from ..dto import TextCodingDataDTO
from ..pages import TextCodingPage
from ..sample_data import create_sample_text_coding_data
from ..viewmodels import AICodingViewModel, TextCodingViewModel


@dataclass
class ActiveCode:
    """Currently selected code for quick-mark."""

    code_id: str = ""
    code_name: str = ""
    code_color: str = ""


@dataclass
class TextSelection:
    """Current text selection."""

    start: int = 0
    end: int = 0
    text: str = ""


@dataclass
class UnmarkHistory:
    """History entry for undo unmark."""

    code_id: str
    code_name: str
    code_color: str
    start: int
    end: int


class TextCodingScreen(QWidget):
    """
    Complete text coding screen.

    Implements ScreenProtocol for use with AppShell.
    This screen wraps TextCodingPage and provides:
    - Code application workflow (Q/V/R/U keys)
    - Undo unmark (Ctrl+Z)
    - Visual feedback on code operations
    - Code count updates

    Signals:
        file_selected(dict): A file was selected
        code_selected(dict): A code was selected
        text_selected(str, int, int): Text was selected
        code_applied(str, int, int): Code applied (code_id, start, end)
        code_removed(str, int, int): Code removed (code_id, start, end)
        code_created(str): New code created (code_name)
        highlight_flashed(int, int): Flash animation triggered (start, end)
        navigation_clicked(str): Navigation button clicked (prev/next)
        editor_code_applied(str, int, int): Code applied in editor
        ai_chat_clicked(): AI chat button clicked
        ai_suggest_clicked(): AI suggest button clicked
        media_type_changed(str): Media type filter changed
        search_changed(str): Search query changed
    """

    # Existing signals
    file_selected = Signal(dict)
    code_selected = Signal(dict)
    text_selected = Signal(str, int, int)

    # Code application signals (AC #10)
    code_applied = Signal(str, int, int)  # code_id, start, end
    code_removed = Signal(str, int, int)  # code_id, start, end
    code_created = Signal(str)  # code_name

    # Visual feedback signal (AC #6)
    highlight_flashed = Signal(int, int)  # start, end

    # Signal routing (QC-007.05)
    navigation_clicked = Signal(str)  # prev/next
    editor_code_applied = Signal(str, int, int)  # code_id, start, end
    ai_chat_clicked = Signal()
    ai_suggest_clicked = Signal()
    media_type_changed = Signal(str)
    search_changed = Signal(str)

    def __init__(
        self,
        data: TextCodingDataDTO | None = None,
        viewmodel: TextCodingViewModel | None = None,
        ai_viewmodel: AICodingViewModel | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the text coding screen.

        Args:
            data: Data to display (uses sample data if None and no viewmodel)
            viewmodel: Optional viewmodel for data and signal routing
            ai_viewmodel: Optional AI coding viewmodel for suggestions
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._data: TextCodingDataDTO | None = None
        self._viewmodel: TextCodingViewModel | None = viewmodel
        self._ai_viewmodel: AICodingViewModel | None = ai_viewmodel
        self._source_id: int = 0

        # Initialize state variables
        self._current_file_index: int = 0
        self._show_important_only: bool = False
        self._show_annotations: bool = True

        # Code application state (AC #1, #8, #9)
        self._active_code: ActiveCode = ActiveCode()
        self._text_selection: TextSelection = TextSelection()
        self._quick_mark_enabled: bool = False

        # Recent codes (AC #3)
        self._recent_codes: list[dict[str, str]] = []
        self._recent_codes_menu_visible: bool = False

        # Undo history (AC #5)
        self._unmark_history: list[UnmarkHistory] = []

        # Code counts cache (AC #7)
        self._code_counts: dict[str, int] = {}

        # Keyboard shortcuts registry
        self._shortcuts: dict[str, QShortcut] = {}

        # Auto-coding controller (fDDD architecture)
        self._auto_coding_controller = AutoCodingController()
        self._auto_code_dialog: AutoCodeDialog | None = None

        # Determine data source: viewmodel, provided data, or sample data
        if viewmodel is not None:
            data = viewmodel.load_initial_data()
        elif data is None:
            data = create_sample_text_coding_data()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the page
        self._page = TextCodingPage(
            coders=data.coders,
            selected_coder=data.selected_coder,
            colors=self._colors,
        )

        # Connect page signals
        self._page.file_selected.connect(self.file_selected.emit)
        self._page.code_selected.connect(self._on_code_selected)
        self._page.text_selected.connect(self._on_text_selected)
        self._page.action_triggered.connect(self._on_action)

        # Signal routing (QC-007.05)
        self._page.navigation_clicked.connect(self.navigation_clicked.emit)
        self._page.editor_code_applied.connect(self.editor_code_applied.emit)
        self._page.ai_chat_clicked.connect(self.ai_chat_clicked.emit)
        self._page.ai_suggest_clicked.connect(self.ai_suggest_clicked.emit)
        self._page.media_type_changed.connect(self.media_type_changed.emit)
        self._page.search_changed.connect(self.search_changed.emit)

        # Connect popup action signals from editor panel
        self._page.editor_panel.popup_code_clicked.connect(self.quick_mark)
        self._page.editor_panel.popup_in_vivo_clicked.connect(self.in_vivo_code)
        self._page.editor_panel.popup_memo_clicked.connect(self.add_memo)
        self._page.editor_panel.popup_annotate_clicked.connect(self.annotate_selection)

        layout.addWidget(self._page)

        # Load the data
        self.load_data(data)

        # Setup keyboard shortcuts (AC #1-5)
        self._setup_shortcuts()

        # Connect to viewmodel if provided
        if self._viewmodel is not None:
            self._connect_viewmodel()

        # Connect to AI viewmodel if provided
        if self._ai_viewmodel is not None:
            self._connect_ai_viewmodel()

    # =========================================================================
    # ViewModel Connection
    # =========================================================================

    def _connect_viewmodel(self):
        """Connect screen signals to viewmodel and vice versa."""
        if self._viewmodel is None:
            return

        # Connect screen signals to viewmodel
        self.code_applied.connect(self._on_code_applied_to_viewmodel)
        self.code_removed.connect(self._on_code_removed_from_viewmodel)

        # Connect viewmodel signals to screen
        self._viewmodel.codes_changed.connect(self._on_viewmodel_codes_changed)
        self._viewmodel.segments_changed.connect(self._on_viewmodel_segments_changed)

    def _on_code_applied_to_viewmodel(self, code_id: str, start: int, end: int):
        """Route code_applied signal to viewmodel."""
        if self._viewmodel is None:
            return
        try:
            code_id_int = int(code_id)
            self._viewmodel.apply_code_to_selection(
                code_id=code_id_int,
                source_id=self._source_id,
                start=start,
                end=end,
            )
        except (ValueError, TypeError):
            print(f"TextCodingScreen: Invalid code_id '{code_id}'")

    def _on_code_removed_from_viewmodel(self, _code_id: str, start: int, end: int):
        """Route code_removed signal to viewmodel."""
        if self._viewmodel is None:
            return
        # Find the segment at this position and remove it
        segment_id = self._viewmodel.find_segment_at_position(
            self._source_id, start, end
        )
        if segment_id is not None:
            self._viewmodel.remove_segment(segment_id)

    def _on_viewmodel_codes_changed(self, categories):
        """Handle codes_changed from viewmodel."""
        # Convert category DTOs to dicts for page
        cat_dicts = [
            {
                "name": cat.name,
                "codes": [
                    {"id": c.id, "name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ],
            }
            for cat in categories
        ]
        self._page.set_codes(cat_dicts)

    def _on_viewmodel_segments_changed(self, segments: list[dict]):
        """Handle segments_changed from viewmodel - update highlights."""
        # Clear existing highlights
        self._page.editor_panel.clear_highlights()

        # Apply new highlights
        for seg in segments:
            self._page.editor_panel.highlight_range(
                start=seg["start"],
                end=seg["end"],
                color=seg["color"],
            )

    def set_current_source(self, source_id: int):
        """
        Set the current source document ID.

        This ID is used for code application and segment queries.

        Args:
            source_id: The source document ID
        """
        self._source_id = source_id
        if self._viewmodel is not None:
            self._viewmodel.set_current_source(source_id)

    # =========================================================================
    # AI ViewModel Connection
    # =========================================================================

    def _connect_ai_viewmodel(self):
        """Connect AI coding viewmodel signals."""
        if self._ai_viewmodel is None:
            return

        # Connect user action signals to AI viewmodel
        self.ai_suggest_clicked.connect(self._on_ai_suggest_clicked)

        # Connect AI viewmodel signals to UI updates
        self._ai_viewmodel.suggestions_loading.connect(self._on_suggestions_loading)
        self._ai_viewmodel.suggestions_received.connect(self._on_suggestions_received)
        self._ai_viewmodel.suggestion_approved.connect(self._on_suggestion_approved)
        self._ai_viewmodel.suggestion_rejected.connect(self._on_suggestion_rejected)
        self._ai_viewmodel.error_occurred.connect(self._on_ai_error)

        # Connect details panel signals to AI viewmodel
        self._page.details_panel.suggestion_approved.connect(
            self._on_panel_suggestion_approved
        )
        self._page.details_panel.suggestion_rejected.connect(
            self._on_panel_suggestion_rejected
        )
        self._page.details_panel.suggestions_dismissed.connect(
            self._on_panel_suggestions_dismissed
        )

    def _on_ai_suggest_clicked(self):
        """Handle AI suggest button click."""
        if self._ai_viewmodel is None:
            return

        # Get current text selection
        text = self._text_selection.text
        if not text or not text.strip():
            # No selection - use entire document
            if self._page and hasattr(self._page, "editor_panel"):
                text = self._page.editor_panel.get_text() or ""
            if not text:
                print("TextCodingScreen: No text available for AI suggestions")
                return

        # Request suggestions
        self._ai_viewmodel.request_suggestions(
            text=text,
            source_id=self._source_id,
            max_suggestions=5,
        )

    def _on_suggestions_loading(self):
        """Handle suggestions loading state."""
        self._page.details_panel.show_suggestions_loading()

    def _on_suggestions_received(self, suggestions: list):
        """Handle suggestions received from AI."""
        # Convert DTOs to dicts for panel
        suggestion_dicts = [
            {
                "suggestion_id": s.suggestion_id,
                "name": s.name,
                "color": s.color,
                "rationale": s.rationale,
                "confidence": s.confidence,
                "context_preview": s.context_preview,
            }
            for s in suggestions
        ]
        self._page.details_panel.set_suggestions(suggestion_dicts)

    def _on_suggestion_approved(self, suggestion_id: str, _code_id: int):
        """Handle suggestion approved - remove from panel."""
        self._page.details_panel.remove_suggestion(suggestion_id)
        # The code was created and code_created event will refresh the codes panel

    def _on_suggestion_rejected(self, suggestion_id: str):
        """Handle suggestion rejected - remove from panel."""
        self._page.details_panel.remove_suggestion(suggestion_id)

    def _on_ai_error(self, operation: str, message: str):
        """Handle AI error."""
        self._page.details_panel.show_suggestions_error(f"{operation}: {message}")

    def _on_panel_suggestion_approved(self, suggestion_id: str):
        """Handle approval from panel - route to viewmodel."""
        if self._ai_viewmodel is not None:
            self._ai_viewmodel.approve_suggestion(suggestion_id)

    def _on_panel_suggestion_rejected(self, suggestion_id: str):
        """Handle rejection from panel - route to viewmodel."""
        if self._ai_viewmodel is not None:
            self._ai_viewmodel.reject_suggestion(suggestion_id)

    def _on_panel_suggestions_dismissed(self):
        """Handle dismiss all from panel - route to viewmodel."""
        if self._ai_viewmodel is not None:
            self._ai_viewmodel.dismiss_all_suggestions()

    def set_ai_viewmodel(self, ai_viewmodel: AICodingViewModel):
        """
        Set the AI coding viewmodel (can be set after construction).

        Args:
            ai_viewmodel: The AI coding viewmodel
        """
        self._ai_viewmodel = ai_viewmodel
        self._connect_ai_viewmodel()

    # =========================================================================
    # Keyboard Shortcuts Setup (QC-007.10)
    # =========================================================================

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for code application."""
        # === Coding Operations ===
        # Q - Quick mark (AC #1)
        self._register_shortcut("Q", self.quick_mark)

        # U - Unmark (AC #2)
        self._register_shortcut("U", self.unmark)

        # N - New code dialog (AC #3)
        self._register_shortcut("N", self.show_new_code_dialog)

        # V - In-vivo coding (AC #4)
        self._register_shortcut("V", self.in_vivo_code)

        # M - Add/edit memo (AC #5)
        self._register_shortcut("M", self.add_memo)

        # A - Annotate selection (AC #6)
        self._register_shortcut("A", self.annotate_selection)

        # R - Recent codes (AC #7)
        self._register_shortcut("R", self.show_recent_codes)

        # I - Toggle important (AC #8)
        self._register_shortcut("I", self.toggle_important)

        # Ctrl+Z - Undo last unmark (AC #9)
        self._register_shortcut("Ctrl+Z", self.undo_unmark)

        # === Navigation ===
        # Ctrl+F - Focus search (AC #10)
        self._register_shortcut("Ctrl+F", self.focus_search)

        # O - Cycle overlapping codes (AC #13)
        self._register_shortcut("O", self.cycle_overlapping_codes)

        # === Display ===
        # H - Toggle side panels (AC #19)
        self._register_shortcut("H", self.toggle_panels)

    def _register_shortcut(self, key: str, callback):
        """Register a keyboard shortcut."""
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.activated.connect(callback)
        self._shortcuts[key] = shortcut

    def get_registered_shortcuts(self) -> list[str]:
        """Get list of registered shortcut keys."""
        return list(self._shortcuts.keys())

    # =========================================================================
    # Code Application State (AC #8, #9)
    # =========================================================================

    def set_active_code(self, code_id: str, code_name: str, code_color: str):
        """
        Set the active code for quick-mark.

        Implements AC #9: code_selected signal sets active code.

        Args:
            code_id: Code identifier
            code_name: Code display name
            code_color: Code color hex string
        """
        self._active_code = ActiveCode(
            code_id=code_id,
            code_name=code_name,
            code_color=code_color,
        )
        # Add to recent codes
        self.add_to_recent_codes(code_id, code_name, code_color)

    def get_active_code(self) -> dict[str, str]:
        """Get the currently active code."""
        return {
            "id": self._active_code.code_id,
            "name": self._active_code.code_name,
            "color": self._active_code.code_color,
        }

    def set_text_selection(self, start: int, end: int):
        """
        Set the current text selection programmatically.

        Args:
            start: Start position
            end: End position
        """
        text = ""
        if self._page and hasattr(self._page, "editor_panel"):
            full_text = self._page.editor_panel.get_text()
            if full_text and 0 <= start < end <= len(full_text):
                text = full_text[start:end]
                self._page.editor_panel.select_range(start, end)

        self._text_selection = TextSelection(start=start, end=end, text=text)
        self._quick_mark_enabled = start < end
        self.text_selected.emit(text, start, end)

    def clear_text_selection(self):
        """Clear the current text selection."""
        self._text_selection = TextSelection()
        self._quick_mark_enabled = False

    def is_quick_mark_enabled(self) -> bool:
        """
        Check if quick mark is enabled.

        Implements AC #8: text_selected enables quick mark.
        """
        return self._quick_mark_enabled

    def set_cursor_position(self, position: int):
        """Set cursor position in editor."""
        if self._page and hasattr(self._page, "editor_panel"):
            self._page.editor_panel.scroll_to_position(position)

    # =========================================================================
    # Navigation (QC-026 AC #6)
    # =========================================================================

    def navigate_to_segment(self, start_pos: int, end_pos: int, highlight: bool = True):
        """
        Navigate to a specific segment position in the text.

        Implements QC-026 AC #6: Agent can navigate to a specific source or segment.

        This method:
        1. Scrolls the editor to make the segment visible
        2. Selects the text range
        3. Optionally highlights/flashes the segment

        Args:
            start_pos: The start character position
            end_pos: The end character position
            highlight: Whether to flash/highlight the segment (default True)
        """
        if self._page and hasattr(self._page, "editor_panel"):
            # Scroll to position
            self._page.editor_panel.scroll_to_position(start_pos)

            # Select the range
            self._page.editor_panel.select_range(start_pos, end_pos)

            # Update internal selection state
            text = ""
            full_text = self._page.editor_panel.get_text()
            if full_text and 0 <= start_pos < end_pos <= len(full_text):
                text = full_text[start_pos:end_pos]

            self._text_selection = TextSelection(
                start=start_pos, end=end_pos, text=text
            )
            self._quick_mark_enabled = start_pos < end_pos

            # Flash highlight if requested
            if highlight:
                self._flash_highlight(start_pos, end_pos)

    def on_navigated_to_segment(self, payload):
        """
        Handle NavigatedToSegment signal from ProjectSignalBridge.

        This slot can be connected to the signal bridge's navigated_to_segment signal
        to respond to navigation commands from agents or other parts of the system.

        Args:
            payload: NavigationPayload with source_id, position_start, position_end
        """
        # Extract payload data
        start_pos = getattr(payload, "position_start", None)
        end_pos = getattr(payload, "position_end", None)

        if start_pos is None or end_pos is None:
            return

        # Navigate to the segment
        self.navigate_to_segment(start_pos, end_pos, highlight=True)

    # =========================================================================
    # Quick Mark (AC #1)
    # =========================================================================

    def quick_mark(self):
        """
        Apply the active code to the current text selection.

        Implements AC #1: Apply selected code via Q key.
        """
        # Check prerequisites
        if not self._active_code.code_id:
            print("TextCodingScreen: No code selected for quick mark")
            return

        if (
            not self._text_selection.text
            or self._text_selection.start >= self._text_selection.end
        ):
            print("TextCodingScreen: No text selected for quick mark")
            return

        # Apply the code
        self._apply_code(
            code_id=self._active_code.code_id,
            code_name=self._active_code.code_name,
            code_color=self._active_code.code_color,
            start=self._text_selection.start,
            end=self._text_selection.end,
        )

    def _apply_code(
        self,
        code_id: str,
        code_name: str,  # noqa: ARG002 - reserved for future use (e.g., logging)
        code_color: str,
        start: int,
        end: int,
    ):
        """Internal method to apply a code to a range."""
        # Apply highlight to editor (AC #10)
        if self._page and hasattr(self._page, "editor_panel"):
            self._page.editor_panel.highlight_range(start, end, code_color)

        # Update code count (AC #7)
        self._increment_code_count(code_id)

        # Visual feedback - flash (AC #6)
        self._flash_highlight(start, end)

        # Emit signal
        self.code_applied.emit(code_id, start, end)

    # =========================================================================
    # In-Vivo Coding (AC #2)
    # =========================================================================

    def in_vivo_code(self):
        """
        Create a new code from the selected text.

        Implements QC-007.10 AC #4: In-vivo coding (V key).
        Creates a code using the selected text as name, then applies it.
        """
        if not self._text_selection.text:
            print("TextCodingScreen: No text selected for in-vivo coding")
            return

        # Use selected text as code name (truncate if too long)
        code_name = self._text_selection.text.strip()
        if len(code_name) > 50:
            code_name = code_name[:47] + "..."

        # Generate a random color for the new code
        import random

        colors = ["#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33", "#33FFF5"]
        code_color = random.choice(colors)

        # Create the code via viewmodel if available
        if self._viewmodel:
            success = self._viewmodel.create_code(code_name, code_color)
            if success:
                # Find the created code and apply it
                categories = self._viewmodel.load_codes()
                for cat in categories:
                    for code in cat.codes:
                        if code.name == code_name:
                            # Set as active and apply
                            self.set_active_code(code.id, code.name, code.color)
                            self._apply_code(
                                code_id=code.id,
                                code_name=code.name,
                                code_color=code.color,
                                start=self._text_selection.start,
                                end=self._text_selection.end,
                            )
                            return
        else:
            # No viewmodel - just emit signal for external handling
            self.code_created.emit(code_name)

    # =========================================================================
    # Recent Codes (AC #3)
    # =========================================================================

    def add_to_recent_codes(self, code_id: str, code_name: str, code_color: str):
        """Add a code to the recent codes list."""
        # Remove if already exists
        self._recent_codes = [c for c in self._recent_codes if c["id"] != code_id]
        # Add to front
        self._recent_codes.insert(
            0,
            {
                "id": code_id,
                "name": code_name,
                "color": code_color,
            },
        )
        # Keep only last 10
        self._recent_codes = self._recent_codes[:10]

    def show_recent_codes(self):
        """
        Show the recent codes menu.

        Implements AC #3: Apply code from recent codes (R key).
        """
        self._recent_codes_menu_visible = True
        # The actual popup would be shown here
        # For now, just mark it as visible for testing

    def has_recent_codes_menu(self) -> bool:
        """Check if recent codes menu is visible."""
        return self._recent_codes_menu_visible

    def apply_recent_code(self, code_id: str):
        """Apply a code from the recent codes list."""
        # Find the code in recent
        code = next((c for c in self._recent_codes if c["id"] == code_id), None)
        if not code:
            return

        if not self._text_selection.text:
            return

        self._apply_code(
            code_id=code["id"],
            code_name=code["name"],
            code_color=code["color"],
            start=self._text_selection.start,
            end=self._text_selection.end,
        )

    # =========================================================================
    # Unmark (AC #4)
    # =========================================================================

    def unmark(self):
        """
        Remove code at the current cursor position.

        Implements AC #4: Remove code at cursor (U key).
        """
        # For now, check if there's a text selection and remove that
        # In full implementation, would check codes at cursor position
        if (
            not self._text_selection.text
            and self._text_selection.start == self._text_selection.end
        ):
            print("TextCodingScreen: No code at cursor to unmark")
            return

        # Save to history for undo (AC #5)
        if self._active_code.code_id:
            self._unmark_history.append(
                UnmarkHistory(
                    code_id=self._active_code.code_id,
                    code_name=self._active_code.code_name,
                    code_color=self._active_code.code_color,
                    start=self._text_selection.start,
                    end=self._text_selection.end,
                )
            )

        # Decrement code count (AC #7)
        if self._active_code.code_id:
            self._decrement_code_count(self._active_code.code_id)

        # Visual feedback (AC #6)
        self._flash_highlight(self._text_selection.start, self._text_selection.end)

        # Emit signal
        self.code_removed.emit(
            self._active_code.code_id,
            self._text_selection.start,
            self._text_selection.end,
        )

    # =========================================================================
    # Undo Unmark (AC #5)
    # =========================================================================

    def undo_unmark(self):
        """
        Undo the last unmark operation.

        Implements AC #5: Undo last unmark (Ctrl+Z).
        """
        if not self._unmark_history:
            print("TextCodingScreen: No unmark history to undo")
            return

        # Pop last unmark from history
        history = self._unmark_history.pop()

        # Re-apply the code
        self._apply_code(
            code_id=history.code_id,
            code_name=history.code_name,
            code_color=history.code_color,
            start=history.start,
            end=history.end,
        )

    # =========================================================================
    # New Code Dialog (QC-007.10 AC #3)
    # =========================================================================

    def show_new_code_dialog(self):
        """
        Show dialog to create a new code.

        Implements QC-007.10 AC #3: N key opens new code dialog.
        """
        # Emit signal - dialog would be shown by parent/controller
        self.code_created.emit("")  # Empty name signals "open dialog"

    # =========================================================================
    # Memo Operations (QC-007.10 AC #5)
    # =========================================================================

    def add_memo(self):
        """
        Add or edit memo for segment at cursor.

        Implements QC-007.10 AC #5: M key adds/edits memo.
        """
        if self._text_selection.start == self._text_selection.end:
            # No selection - try to find segment at cursor
            print(
                "TextCodingScreen: M key - would open memo dialog for segment at cursor"
            )
        else:
            # Has selection - add memo to this selection
            print(
                f"TextCodingScreen: M key - would add memo to selection {self._text_selection.start}-{self._text_selection.end}"
            )

    # =========================================================================
    # Annotation (QC-007.10 AC #6)
    # =========================================================================

    def annotate_selection(self):
        """
        Add annotation to current selection.

        Implements QC-007.10 AC #6: A key annotates selection.
        """
        if not self._text_selection.text:
            print("TextCodingScreen: A key - no text selected to annotate")
            return

        print(
            f"TextCodingScreen: A key - would open annotation dialog for '{self._text_selection.text[:30]}...'"
        )

    # =========================================================================
    # Toggle Important (QC-007.10 AC #8)
    # =========================================================================

    def toggle_important(self):
        """
        Toggle important flag on segment at cursor.

        Implements QC-007.10 AC #8: I key toggles importance.
        """
        if self._text_selection.start == self._text_selection.end:
            print("TextCodingScreen: I key - no segment selected to mark important")
            return

        # Find segment at selection and toggle its importance
        if self._viewmodel:
            segment_id = self._viewmodel.find_segment_at_position(
                self._source_id,
                self._text_selection.start,
                self._text_selection.end,
            )
            if segment_id:
                print(
                    f"TextCodingScreen: I key - would toggle importance for segment {segment_id}"
                )
            else:
                print("TextCodingScreen: I key - no segment found at selection")

    # =========================================================================
    # Navigation Shortcuts (QC-007.10)
    # =========================================================================

    def focus_search(self):
        """
        Focus the search box.

        Implements QC-007.10 AC #10: Ctrl+F focuses search.
        """
        if hasattr(self._page, "toolbar") and hasattr(
            self._page.toolbar, "focus_search"
        ):
            self._page.toolbar.focus_search()
        else:
            print("TextCodingScreen: Ctrl+F - would focus search box")

    def cycle_overlapping_codes(self):
        """
        Cycle through overlapping codes at cursor.

        Implements QC-007.10 AC #13: O key cycles overlaps.
        """
        if (
            not self._text_selection.text
            and self._text_selection.start == self._text_selection.end
        ):
            print("TextCodingScreen: O key - no position selected to check overlaps")
            return

        # Get overlapping regions from editor
        if hasattr(self._page, "editor_panel"):
            overlaps = self._page.editor_panel.get_overlap_regions()
            if overlaps:
                print(
                    f"TextCodingScreen: O key - found {len(overlaps)} overlap regions"
                )
            else:
                print("TextCodingScreen: O key - no overlapping codes at cursor")

    # =========================================================================
    # Display Toggles (QC-007.10 AC #19)
    # =========================================================================

    _panels_visible: bool = True

    def toggle_panels(self):
        """
        Toggle visibility of side panels.

        Implements QC-007.10 AC #19: H key toggles panels.
        """
        self._panels_visible = not self._panels_visible
        if hasattr(self._page, "toggle_panels"):
            self._page.toggle_panels(self._panels_visible)
        else:
            # Fallback: toggle individual panels
            if hasattr(self._page, "files_panel"):
                self._page.files_panel.setVisible(self._panels_visible)
            if hasattr(self._page, "codes_panel"):
                self._page.codes_panel.setVisible(self._panels_visible)
            if hasattr(self._page, "details_panel"):
                self._page.details_panel.setVisible(self._panels_visible)
        print(
            f"TextCodingScreen: H key - panels {'shown' if self._panels_visible else 'hidden'}"
        )

    def are_panels_visible(self) -> bool:
        """Check if side panels are visible."""
        return self._panels_visible

    # =========================================================================
    # Visual Feedback (AC #6)
    # =========================================================================

    def _flash_highlight(self, start: int, end: int):
        """
        Trigger a flash animation on a text range.

        Implements AC #6: Visual feedback on code application.
        """
        self.highlight_flashed.emit(start, end)
        # The actual flash animation would be implemented in the editor panel

    # =========================================================================
    # Code Count Updates (AC #7)
    # =========================================================================

    def _increment_code_count(self, code_id: str):
        """Increment the count for a code."""
        if code_id in self._code_counts:
            self._code_counts[code_id] += 1
        else:
            self._code_counts[code_id] = 1

    def _decrement_code_count(self, code_id: str):
        """Decrement the count for a code."""
        if code_id in self._code_counts and self._code_counts[code_id] > 0:
            self._code_counts[code_id] -= 1

    def get_code_count(self, code_id: str) -> int:
        """Get the current count for a code."""
        return self._code_counts.get(code_id, 0)

    # =========================================================================
    # Signal Handlers (AC #8, #9, #10)
    # =========================================================================

    def _on_text_selected(self, text: str, start: int, end: int):
        """
        Handle text selection from editor.

        Implements AC #8: text_selected enables code application.
        """
        self._text_selection = TextSelection(start=start, end=end, text=text)
        self._quick_mark_enabled = bool(text) and start < end
        self.text_selected.emit(text, start, end)

    def _on_code_selected(self, code_data: dict):
        """
        Handle code selection from codes panel.

        Implements AC #9: code_selected sets active code.
        """
        code_id = code_data.get("id", "")
        # In a full implementation, we'd look up the name and color
        # For now, set with available data
        self._active_code = ActiveCode(
            code_id=code_id,
            code_name=code_data.get("name", ""),
            code_color=code_data.get("color", self._colors.fallback_code_color),
        )
        self.code_selected.emit(code_data)

    # =========================================================================
    # Data Loading
    # =========================================================================

    def load_data(self, data: TextCodingDataDTO):
        """
        Load data into the screen.

        Args:
            data: The data transfer object containing all display data
        """
        if data is None:
            print("TextCodingScreen: Cannot load None data")
            return

        self._data = data
        self._current_file_index = 0

        # Files - convert DTOs to dicts for Page
        files = []
        if data.files:
            for f in data.files:
                if f is not None:
                    files.append(
                        {
                            "name": getattr(f, "name", "") or "",
                            "type": getattr(f, "file_type", "text") or "text",
                            "meta": getattr(f, "meta", "") or "",
                        }
                    )
        self._page.set_files(files)

        # Codes - convert DTOs to nested dicts for Page
        categories = [
            {
                "name": cat.name,
                "codes": [
                    {"id": c.id, "name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ],
            }
            for cat in data.categories
        ]
        self._page.set_codes(categories)

        # Initialize code counts from data
        for cat in data.categories:
            for code in cat.codes:
                self._code_counts[str(code.id)] = code.count

        # Document
        if data.document:
            self._page.set_document(
                data.document.title, data.document.badge, data.document.content
            )

        # Document stats
        if data.document_stats:
            stats = data.document_stats
            self._page.set_document_stats(
                [
                    ("mdi6.layers", f"{stats.overlapping_count} overlapping"),
                    ("mdi6.label", f"{stats.codes_applied} codes applied"),
                    ("mdi6.format-size", f"{stats.word_count} words"),
                ]
            )

        # Selected code details
        if data.selected_code:
            sc = data.selected_code
            self._page.set_selected_code(sc.color, sc.name, sc.memo, sc.example_text)

        # Overlapping codes
        if data.overlapping_segments:
            overlaps = [
                (seg.segment_label, seg.colors) for seg in data.overlapping_segments
            ]
            self._page.set_overlapping_codes(overlaps)

        # File memo
        if data.file_memo:
            self._page.set_file_memo(data.file_memo.memo, data.file_memo.progress)

        # Navigation
        if data.navigation:
            self._page.set_navigation(data.navigation.current, data.navigation.total)

    def _on_action(self, action_id: str):
        """Handle toolbar action."""
        # Dispatch to specific handlers
        handlers = {
            "help": self._action_help,
            "text_size": self._action_text_size,
            "important": self._action_toggle_important,
            "annotations": self._action_toggle_annotations,
            "prev": self._action_prev_file,
            "next": self._action_next_file,
            "auto_exact": self._action_auto_exact,
            "auto_fragment": self._action_auto_fragment,
            "speakers": self._action_mark_speakers,
            "undo_auto": self._action_undo_auto,
            "memo": self._action_add_memo,
            "annotate": self._action_annotate,
        }

        handler = handlers.get(action_id)
        if handler:
            try:
                handler()
            except Exception as e:
                print(f"TextCodingScreen: Error in action '{action_id}': {e}")
        else:
            print(f"TextCodingScreen: Unknown action: {action_id}")

    # =========================================================================
    # Action Handlers
    # =========================================================================

    def _action_help(self):
        """Show help dialog."""
        print("TODO: Show help dialog")

    def _action_text_size(self):
        """Change text size."""
        print("TODO: Show text size options")

    def _action_toggle_important(self):
        """Toggle showing only important codes."""
        self._show_important_only = not self._show_important_only
        print(f"Important only: {self._show_important_only}")

    def _action_toggle_annotations(self):
        """Toggle showing annotations."""
        self._show_annotations = not self._show_annotations
        print(f"Show annotations: {self._show_annotations}")

    def _action_prev_file(self):
        """Navigate to previous file."""
        if self._current_file_index > 0:
            self._current_file_index -= 1
            self._navigate_to_file(self._current_file_index)

    def _action_next_file(self):
        """Navigate to next file."""
        total_files = self._page.files_panel.get_file_count()
        if total_files > 0 and self._current_file_index < total_files - 1:
            self._current_file_index += 1
            self._navigate_to_file(self._current_file_index)

    def _navigate_to_file(self, index: int):
        """Navigate to file at index and update navigation display."""
        total_files = self._page.files_panel.get_file_count()
        if total_files == 0:
            return

        # Bounds check
        if not (0 <= index < total_files):
            print(f"TextCodingScreen: Invalid file index {index}, total={total_files}")
            return

        # Update selection in files panel
        if not self._page.files_panel.select_file(index):
            return

        file_data = self._page.files_panel.get_selected_file()
        if not file_data:
            return

        self._page.set_navigation(index + 1, total_files)
        # Update document display
        self._page.set_document(
            file_data.get("name", ""),
            f"File {index + 1}",
            f"Content of {file_data.get('name', '')}...\n\n(Load actual content here)",
        )
        print(f"Navigated to file: {file_data.get('name')}")

    def _get_selected_text(self) -> str:
        """Safely get selected text from editor panel."""
        try:
            if self._page and hasattr(self._page, "editor_panel"):
                return self._page.editor_panel.get_selected_text() or ""
        except Exception as e:
            print(f"TextCodingScreen: Error getting selected text: {e}")
        return ""

    def _action_auto_exact(self):
        """
        Auto-code exact text matches.

        Opens the AutoCodeDialog with 'exact' match type pre-selected.
        Dialog signals are connected to the AutoCodingController.
        """
        if not self._active_code.code_id:
            print("TextCodingScreen: Select a code first for auto-coding")
            return

        selection = self._get_selected_text()
        document_text = ""
        if self._page and hasattr(self._page, "editor_panel"):
            document_text = self._page.editor_panel.get_text() or ""

        if not document_text:
            print("TextCodingScreen: No document loaded for auto-coding")
            return

        self._show_auto_code_dialog(
            pattern=selection,
            match_type="exact",
            text=document_text,
        )

    def _action_auto_fragment(self):
        """
        Auto-code similar text fragments.

        Opens the AutoCodeDialog with 'contains' match type pre-selected.
        """
        if not self._active_code.code_id:
            print("TextCodingScreen: Select a code first for auto-coding")
            return

        selection = self._get_selected_text()
        document_text = ""
        if self._page and hasattr(self._page, "editor_panel"):
            document_text = self._page.editor_panel.get_text() or ""

        if not document_text:
            print("TextCodingScreen: No document loaded for auto-coding")
            return

        self._show_auto_code_dialog(
            pattern=selection,
            match_type="contains",
            text=document_text,
        )

    def _action_mark_speakers(self):
        """
        Mark speaker turns in transcript.

        Uses the AutoCodingController to detect speakers and highlights
        each speaker's segments with a unique color.
        """
        document_text = ""
        if self._page and hasattr(self._page, "editor_panel"):
            document_text = self._page.editor_panel.get_text() or ""

        if not document_text:
            print("TextCodingScreen: No document loaded for speaker detection")
            return

        # Use controller to detect speakers
        result = self._auto_coding_controller.detect_speakers(document_text)

        if isinstance(result, Success):
            speakers = result.unwrap()
            if not speakers:
                print(
                    "TextCodingScreen: No speaker patterns detected. "
                    "Expected patterns like 'INTERVIEWER:' or 'John Smith:'"
                )
                return

            # Assign colors to speakers
            speaker_colors = [
                "#E91E63",  # Pink
                "#2196F3",  # Blue
                "#4CAF50",  # Green
                "#FF9800",  # Orange
                "#9C27B0",  # Purple
                "#00BCD4",  # Cyan
                "#F44336",  # Red
                "#8BC34A",  # Light Green
            ]

            # Get segments for each speaker and highlight them
            total_segments = 0
            for i, speaker in enumerate(speakers):
                color = speaker_colors[i % len(speaker_colors)]

                # Get segments for this speaker
                segments_result = self._auto_coding_controller.get_speaker_segments(
                    document_text, speaker.name
                )

                if isinstance(segments_result, Success):
                    segments = segments_result.unwrap()
                    for seg in segments:
                        if self._page and hasattr(self._page, "editor_panel"):
                            self._page.editor_panel.highlight_range(
                                seg.start, seg.end, color
                            )
                        total_segments += 1

                print(
                    f"TextCodingScreen: Highlighted '{speaker.name}' "
                    f"({speaker.count} occurrences) in {color}"
                )

            print(f"TextCodingScreen: Marked {total_segments} speaker segments total")
        else:
            print(f"TextCodingScreen: Speaker detection failed: {result.failure()}")

    def _action_undo_auto(self):
        """
        Undo last auto-coding operation.

        Uses the AutoCodingController to undo the last batch.
        """
        if not self._auto_coding_controller.can_undo():
            print("TextCodingScreen: Nothing to undo")
            return

        result = self._auto_coding_controller.undo_last_batch()

        if isinstance(result, Success):
            batch = result.unwrap()
            # Remove highlights for undone segments
            # (In full implementation, would refresh highlights from database)
            print(
                f"TextCodingScreen: Undone batch '{batch.batch_id}' "
                f"(pattern: '{batch.pattern}', {batch.segment_count} segments)"
            )
        else:
            print(f"TextCodingScreen: Undo failed: {result.failure()}")

    # =========================================================================
    # Auto-Code Dialog (fDDD wiring)
    # =========================================================================

    def _show_auto_code_dialog(
        self,
        pattern: str = "",
        _match_type: str = "exact",
        text: str = "",
    ):
        """
        Show the auto-code dialog with proper signal wiring.

        This follows the fDDD architecture:
        - Dialog emits signals for operations
        - Controller receives and processes them
        - Results flow back to dialog via slots
        """
        dialog = AutoCodeDialog(colors=self._colors, parent=self)
        self._auto_code_dialog = dialog

        # Configure dialog
        dialog.set_text(text)
        dialog.set_pattern(pattern)
        dialog.set_code(
            {
                "id": self._active_code.code_id,
                "name": self._active_code.code_name,
                "color": self._active_code.code_color,
            }
        )

        # Wire dialog signals to controller via adapter methods
        dialog.find_matches_requested.connect(self._on_find_matches_requested)
        dialog.apply_auto_code_requested.connect(self._on_apply_auto_code_requested)

        # Show dialog
        dialog.exec()
        self._auto_code_dialog = None

    def _on_find_matches_requested(
        self,
        text: str,
        pattern: str,
        match_type: str,
        scope: str,
        case_sensitive: bool,
    ):
        """
        Handle find_matches_requested signal from dialog.

        Routes to controller and sends results back to dialog.
        """
        # Convert string types to domain enums
        mt = {
            "exact": MatchType.EXACT,
            "contains": MatchType.CONTAINS,
            "regex": MatchType.REGEX,
        }.get(match_type, MatchType.EXACT)

        sc = {
            "all": MatchScope.ALL,
            "first": MatchScope.FIRST,
            "last": MatchScope.LAST,
        }.get(scope, MatchScope.ALL)

        # Call controller
        result = self._auto_coding_controller.find_matches(
            text=text,
            pattern=pattern,
            match_type=mt,
            scope=sc,
            case_sensitive=case_sensitive,
        )

        # Send results back to dialog
        if self._auto_code_dialog is not None:
            if isinstance(result, Success):
                matches = result.unwrap()
                # Convert TextMatch objects to tuples for dialog
                match_tuples = [(m.start, m.end) for m in matches]
                self._auto_code_dialog.on_matches_found(match_tuples)
            else:
                self._auto_code_dialog.on_error("find_matches", str(result.failure()))

    def _on_apply_auto_code_requested(self, config: dict):
        """
        Handle apply_auto_code_requested signal from dialog.

        Applies highlights for all matches and tracks batch for undo.
        """
        pattern = config.get("pattern", "")
        code = config.get("code", {})
        code_color = code.get("color", self._colors.fallback_code_color)

        # Get cached matches from dialog
        if self._auto_code_dialog is None:
            return

        matches = self._auto_code_dialog.get_cached_matches()
        if not matches:
            # No cached matches - find them first
            text = self._auto_code_dialog._text
            match_type = config.get("match_type", "exact")
            scope = config.get("scope", "all")

            mt = {
                "exact": MatchType.EXACT,
                "contains": MatchType.CONTAINS,
                "regex": MatchType.REGEX,
            }.get(match_type, MatchType.EXACT)

            sc = {
                "all": MatchScope.ALL,
                "first": MatchScope.FIRST,
                "last": MatchScope.LAST,
            }.get(scope, MatchScope.ALL)

            result = self._auto_coding_controller.find_matches(
                text=text,
                pattern=pattern,
                match_type=mt,
                scope=sc,
            )

            if isinstance(result, Success):
                domain_matches = result.unwrap()
                matches = [(m.start, m.end) for m in domain_matches]

        if not matches:
            return

        # Apply highlights for each match
        for start, end in matches:
            if self._page and hasattr(self._page, "editor_panel"):
                self._page.editor_panel.highlight_range(start, end, code_color)

            # Update code count
            self._increment_code_count(code.get("id", ""))

            # Emit code_applied signal
            self.code_applied.emit(code.get("id", ""), start, end)

        # Log success
        print(
            f"TextCodingScreen: Applied '{code.get('name', 'code')}' "
            f"to {len(matches)} matches"
        )

    def _action_add_memo(self):
        """Add memo to current selection or file."""
        selection = self._get_selected_text()
        if selection:
            preview = selection[:50] + "..." if len(selection) > 50 else selection
            print(f"TODO: Add memo to selection: '{preview}'")
        else:
            print("TODO: Add memo to file")

    def _action_annotate(self):
        """Add annotation to current selection."""
        selection = self._get_selected_text()
        if selection:
            preview = selection[:50] + "..." if len(selection) > 50 else selection
            print(f"TODO: Annotate selection: '{preview}'")
        else:
            print("Select text first to annotate")

    # =========================================================================
    # ScreenProtocol implementation
    # =========================================================================

    def get_toolbar_content(self) -> QWidget:
        """Return the coding toolbar (already part of page, return None)."""
        # The toolbar is already embedded in the page
        # Return None to indicate no separate toolbar needed
        return None

    def get_content(self) -> QWidget:
        """Return self as the content."""
        return self

    def get_status_message(self) -> str:
        """Return status bar message."""
        return "Ready"

    # =========================================================================
    # Public API - Delegate to page
    # =========================================================================

    def set_files(self, files: list[dict[str, Any]]):
        """Set the list of files."""
        self._page.set_files(files)

    def set_codes(self, categories: list[dict[str, Any]]):
        """Set the code tree."""
        self._page.set_codes(categories)

        # Update code counts cache
        for cat in categories:
            for code in cat.get("codes", []):
                code_id = str(code.get("id", ""))
                if code_id:
                    self._code_counts[code_id] = code.get("count", 0)

    def set_document(self, title: str, badge: str = None, text: str = ""):
        """Set the document."""
        self._page.set_document(title, badge, text)

    @property
    def page(self) -> TextCodingPage:
        """Get the underlying page."""
        return self._page


# =============================================================================
# DEMO
# =============================================================================


def main():
    """Run the text coding screen demo."""
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_colors()

    window = QMainWindow()
    window.setWindowTitle("Text Coding Screen")
    window.setMinimumSize(1400, 900)
    window.setStyleSheet(f"background-color: {colors.background};")

    screen = TextCodingScreen(colors=colors)
    window.setCentralWidget(screen)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
