"""
Codes Panel Organism

A panel displaying the hierarchical code tree for qualitative coding.
Includes a header with add/search/expand actions, and navigation buttons.

Implements QC-007.06 Code Tree Enhancements:
- AC #1: Context menu for code operations
- AC #2: Drag-and-drop reorganization
- AC #3: Code search/filter input
- AC #4: Sort options (name/count/color)
- AC #5: Selection tracking
- AC #6: Recent codes tracking (last 10)
- AC #7: Important codes filter toggle
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from design_system import (
    RADIUS,
    SPACING,
    CodeItem,
    CodeTree,
    ColorPalette,
    Icon,
    PanelHeader,
    get_colors,
)


class CodesPanel(QFrame):
    """
    Panel showing code tree and navigation.

    Signals:
        code_selected(dict): Emitted when a code is selected, with code data
        navigation_clicked(str): Emitted when navigation button is clicked (prev, next, all)
        code_move_requested(str, str): Emitted when drag-drop move is requested (code_id, category_id)
    """

    code_selected = Signal(dict)
    navigation_clicked = Signal(str)
    code_move_requested = Signal(str, str)  # code_id, target_category_id

    # Max number of recent codes to track
    MAX_RECENT_CODES = 10

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the codes panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected_code: dict[str, Any] = {}

        # Store raw categories data for filtering/sorting
        self._categories: list[dict[str, Any]] = []
        self._all_codes: list[dict[str, Any]] = []

        # Filter and sort state
        self._filter_text: str = ""
        self._sort_mode: str = "name"  # "name", "count"
        self._important_filter: bool = False

        # Recent codes tracking
        self._recent_codes: list[dict[str, Any]] = []

        # Drag drop enabled
        self._drag_enabled: bool = True

        self.setStyleSheet(f"""
            CodesPanel {{
                background: {self._colors.transparent};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = PanelHeader("Codes", icon="mdi6.label", colors=self._colors)
        header.add_action("mdi6.plus", tooltip="Add code")
        header.add_action("mdi6.magnify", tooltip="Search codes")
        header.add_action("mdi6.unfold-more-horizontal", tooltip="Expand all")
        layout.addWidget(header)

        # Code tree
        self._code_tree = CodeTree(colors=self._colors)
        self._code_tree.item_clicked.connect(self._on_code_click)
        layout.addWidget(self._code_tree, 1)

        # Navigation buttons
        nav = self._create_navigation()
        layout.addWidget(nav)

    def _create_navigation(self) -> QFrame:
        """Create the navigation buttons bar."""
        nav = QFrame()
        nav.setStyleSheet(f"border-top: 1px solid {self._colors.border};")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        nav_layout.setSpacing(SPACING.xs)

        nav_buttons = [
            ("mdi6.skip-previous", "Previous code instance", "prev"),
            ("mdi6.skip-next", "Next code instance", "next"),
            ("mdi6.view-grid", "Show all instances", "all"),
        ]

        for icon_name, tooltip, action_id in nav_buttons:
            btn = QFrame()
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {RADIUS.sm}px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(SPACING.md, 0, SPACING.md, 0)
            icon = Icon(
                icon_name,
                size=16,
                color=self._colors.text_secondary,
                colors=self._colors,
            )
            btn_layout.addWidget(icon)

            # Capture action_id in closure
            btn.mousePressEvent = (
                lambda _e, aid=action_id: self.navigation_clicked.emit(aid)
            )
            nav_layout.addWidget(btn, 1)

        return nav

    def set_codes(self, categories: list[dict[str, Any]]):
        """
        Set the code tree data.

        Args:
            categories: List of category dictionaries with keys:
                - name: Category name
                - codes: List of code dictionaries with:
                    - name: Code name
                    - color: Code color hex string
                    - count (optional): Number of instances
                    - has_important (optional): Whether code has important segments
        """
        # Store raw data for filtering/sorting
        self._categories = categories or []
        self._all_codes = []
        for cat in self._categories:
            if isinstance(cat, dict):
                for code in cat.get("codes", []):
                    if isinstance(code, dict):
                        self._all_codes.append(code)

        # Rebuild tree with current filter/sort
        self._rebuild_tree()

    def _rebuild_tree(self):
        """Rebuild tree based on current filter and sort settings."""
        if not self._categories:
            self._code_tree.set_items([])
            return

        items = []
        for cat in self._categories:
            if not isinstance(cat, dict):
                continue
            cat_name = cat.get("name", "Unnamed")
            children = []

            # Get and filter codes
            codes = cat.get("codes", [])
            filtered_codes = self._filter_codes(codes)
            sorted_codes = self._sort_codes(filtered_codes)

            for code in sorted_codes:
                if not isinstance(code, dict):
                    continue
                code_name = code.get("name", "")
                if not code_name:
                    continue
                children.append(
                    CodeItem(
                        id=code.get("id", code_name),
                        name=code_name,
                        color=code.get("color", self._colors.fallback_code_color),
                        count=code.get("count", 0),
                    )
                )

            # Only add category if it has visible codes or no filter active
            if children or not self._filter_text:
                items.append(
                    CodeItem(
                        id=cat_name,
                        name=cat_name,
                        color=self._colors.text_secondary,
                        count=len(children),
                        children=children,
                    )
                )
        self._code_tree.set_items(items)

    def _filter_codes(self, codes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter codes based on current filter text and important filter."""
        result = []
        for code in codes:
            if not isinstance(code, dict):
                continue

            # Text filter
            if self._filter_text:
                name = code.get("name", "").lower()
                if self._filter_text.lower() not in name:
                    continue

            # Important filter
            if self._important_filter and not code.get("has_important", False):
                continue

            result.append(code)
        return result

    def _sort_codes(self, codes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort codes based on current sort mode."""
        if self._sort_mode == "name":
            return sorted(codes, key=lambda c: c.get("name", "").lower())
        elif self._sort_mode == "count":
            return sorted(codes, key=lambda c: c.get("count", 0), reverse=True)
        return codes

    def _on_code_click(self, code_id: str):
        """Handle code click event."""
        self._selected_code = {"id": code_id}
        self.code_selected.emit(self._selected_code)

    def get_selected_code(self) -> dict[str, Any]:
        """Get the currently selected code data."""
        return self._selected_code.copy() if self._selected_code else {}

    def expand_all(self):
        """Expand all code tree nodes."""
        self._code_tree.expand_all()

    def collapse_all(self):
        """Collapse all code tree nodes."""
        self._code_tree.collapse_all()

    # =========================================================================
    # Filter and Sort (QC-007.06 AC #3, #4)
    # =========================================================================

    def set_filter_text(self, text: str):
        """
        Set the filter text for code search.

        Implements AC #3: Code search/filter input.

        Args:
            text: Filter text (case-insensitive partial match)
        """
        self._filter_text = text
        self._rebuild_tree()

    def get_filter_text(self) -> str:
        """Get the current filter text."""
        return self._filter_text

    def set_sort_mode(self, mode: str):
        """
        Set the sort mode for codes.

        Implements AC #4: Sort options.

        Args:
            mode: Sort mode - "name" (alphabetical) or "count" (by usage, descending)
        """
        if mode not in ("name", "count"):
            mode = "name"
        self._sort_mode = mode
        self._rebuild_tree()

    def get_sort_mode(self) -> str:
        """Get the current sort mode."""
        return self._sort_mode

    def get_sorted_codes(self) -> list[dict[str, Any]]:
        """Get all codes sorted by current mode."""
        return self._sort_codes(self._all_codes.copy())

    def get_visible_code_count(self) -> int:
        """Get count of currently visible codes (after filtering)."""
        count = 0
        for cat in self._categories:
            if isinstance(cat, dict):
                codes = cat.get("codes", [])
                filtered = self._filter_codes(codes)
                count += len(filtered)
        return count

    # =========================================================================
    # Important Filter (QC-007.06 AC #7)
    # =========================================================================

    def set_important_filter(self, enabled: bool):
        """
        Toggle important codes filter.

        Implements AC #7: Important codes filter toggle.

        Args:
            enabled: If True, only show codes with important segments
        """
        self._important_filter = enabled
        self._rebuild_tree()

    def is_important_filter_active(self) -> bool:
        """Check if important filter is active."""
        return self._important_filter

    # =========================================================================
    # Recent Codes Tracking (QC-007.06 AC #6)
    # =========================================================================

    def add_to_recent(self, code: dict[str, Any]):
        """
        Add a code to recent codes list.

        Implements AC #6: Recent codes tracking (last 10).

        Args:
            code: Code dict with at least 'id' key
        """
        code_id = code.get("id")
        if not code_id:
            return

        # Remove if already exists (will re-add at front)
        self._recent_codes = [c for c in self._recent_codes if c.get("id") != code_id]

        # Add to front
        self._recent_codes.insert(0, code)

        # Trim to max
        if len(self._recent_codes) > self.MAX_RECENT_CODES:
            self._recent_codes = self._recent_codes[: self.MAX_RECENT_CODES]

    def get_recent_codes(self) -> list[dict[str, Any]]:
        """
        Get list of recent codes.

        Returns:
            List of recent codes, most recent first
        """
        return self._recent_codes.copy()

    def clear_recent_codes(self):
        """Clear the recent codes list."""
        self._recent_codes.clear()

    # =========================================================================
    # Drag and Drop (QC-007.06 AC #2)
    # =========================================================================

    def request_code_move(self, code_id: str, target_category_id: str):
        """
        Request to move a code to a different category.

        Implements AC #2: Drag-and-drop reorganization.

        Args:
            code_id: ID of the code to move
            target_category_id: ID of the target category
        """
        self.code_move_requested.emit(code_id, target_category_id)

    def is_drag_enabled(self) -> bool:
        """Check if drag and drop is enabled."""
        return self._drag_enabled

    def set_drag_enabled(self, enabled: bool):
        """Enable or disable drag and drop."""
        self._drag_enabled = enabled
