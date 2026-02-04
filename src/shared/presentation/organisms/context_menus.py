"""
Context Menu Components

Implements QC-007.03 Context Menus:
- Text Editor Context Menu: mark, unmark, memo, annotate, copy
- Code Tree Context Menu: add, rename, delete, color, move, memo
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction

from design_system import (
    ColorPalette,
    ContextMenu,
    get_colors,
)


class TextEditorContextMenu(ContextMenu):
    """
    Context menu for text editor panel.

    Shows actions based on:
    - Whether text is selected
    - Whether cursor is at a coded segment
    - Currently selected code in tree

    Signals:
        action_triggered(str): Emitted when menu action is triggered
        code_selected_for_mark(dict): Emitted when a code is selected from recent codes
    """

    action_triggered = Signal(str)
    code_selected_for_mark = Signal(dict)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(colors=colors, parent=parent)
        self._colors = colors or get_colors()

        self._has_selection = False
        self._selected_code: dict[str, Any] | None = None
        self._codes_at_cursor: list[dict[str, Any]] = []
        self._recent_codes: list[dict[str, Any]] = []

        self._actions: dict[str, QAction] = {}
        self._build_menu()

    def _build_menu(self):
        """Build the context menu structure."""
        # Mark with selected code
        self._actions["mark"] = self.add_item(
            "Mark with Code",
            icon="mdi6.tag-plus",
            shortcut="Q",
            on_click=lambda: self.action_triggered.emit("mark"),
            enabled=False,
        )

        # Recent codes submenu
        self._recent_submenu = self.add_submenu("Recent Codes")
        self._recent_submenu.setIcon(
            self._recent_submenu.style().standardIcon(
                self._recent_submenu.style().StandardPixmap.SP_ArrowRight
            )
        )

        # New code (in-vivo)
        self._actions["in_vivo"] = self.add_item(
            "New Code from Selection",
            icon="mdi6.creation",
            shortcut="V",
            on_click=lambda: self.action_triggered.emit("in_vivo"),
            enabled=False,
        )

        self.add_separator()

        # Unmark
        self._actions["unmark"] = self.add_item(
            "Unmark Code",
            icon="mdi6.tag-remove",
            shortcut="U",
            on_click=lambda: self.action_triggered.emit("unmark"),
            enabled=False,
        )

        # Memo (for coded segment)
        self._actions["memo"] = self.add_item(
            "Add Memo",
            icon="mdi6.note-plus",
            shortcut="M",
            on_click=lambda: self.action_triggered.emit("memo"),
            enabled=False,
        )

        # Toggle important
        self._actions["important"] = self.add_item(
            "Toggle Important",
            icon="mdi6.star-outline",
            on_click=lambda: self.action_triggered.emit("important"),
            enabled=False,
        )

        self.add_separator()

        # Annotate
        self._actions["annotate"] = self.add_item(
            "Annotate Selection",
            icon="mdi6.comment-plus",
            shortcut="A",
            on_click=lambda: self.action_triggered.emit("annotate"),
            enabled=False,
        )

        self.add_separator()

        # Copy
        self._actions["copy"] = self.add_item(
            "Copy",
            icon="mdi6.content-copy",
            shortcut="Ctrl+C",
            on_click=lambda: self.action_triggered.emit("copy"),
            enabled=False,
        )

    def set_has_selection(self, has_selection: bool):
        """Update menu based on text selection state."""
        self._has_selection = has_selection
        self._update_actions()

    def set_selected_code(self, code: dict[str, Any] | None):
        """Set the currently selected code in the tree."""
        self._selected_code = code
        self._update_actions()

    def set_codes_at_cursor(self, codes: list[dict[str, Any]]):
        """Set codes at the current cursor position."""
        self._codes_at_cursor = codes
        self._update_actions()

    def set_recent_codes(self, codes: list[dict[str, Any]]):
        """Set the list of recent codes for the submenu."""
        self._recent_codes = codes
        self._build_recent_submenu()

    def _build_recent_submenu(self):
        """Rebuild the recent codes submenu."""
        self._recent_submenu.clear()

        if not self._recent_codes:
            action = self._recent_submenu.addAction("No recent codes")
            action.setEnabled(False)
            return

        for code in self._recent_codes[:10]:  # Max 10 recent codes
            action = self._recent_submenu.addAction(code.get("name", "Unnamed"))
            action.triggered.connect(
                lambda _checked, c=code: self.code_selected_for_mark.emit(c)
            )

    def _update_actions(self):
        """Update action enabled states."""
        has_selected_code = self._selected_code is not None
        has_codes_at_cursor = len(self._codes_at_cursor) > 0

        # Mark requires selection AND selected code
        self._actions["mark"].setEnabled(self._has_selection and has_selected_code)

        # In-vivo and annotate require selection
        self._actions["in_vivo"].setEnabled(self._has_selection)
        self._actions["annotate"].setEnabled(self._has_selection)

        # Copy requires selection
        self._actions["copy"].setEnabled(self._has_selection)

        # Unmark, memo, important require codes at cursor
        self._actions["unmark"].setEnabled(has_codes_at_cursor)
        self._actions["unmark"].setVisible(has_codes_at_cursor)
        self._actions["memo"].setEnabled(has_codes_at_cursor)
        self._actions["important"].setEnabled(has_codes_at_cursor)

    def get_action(self, action_id: str) -> QAction | None:
        """Get an action by its ID."""
        return self._actions.get(action_id)


class CodeTreeContextMenu(ContextMenu):
    """
    Context menu for code tree panel.

    Shows actions for codes and categories.

    Signals:
        action_triggered(str): Emitted when menu action is triggered
        move_to_category(str): Emitted when move to category is selected
    """

    action_triggered = Signal(str)
    move_to_category = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(colors=colors, parent=parent)
        self._colors = colors or get_colors()

        self._selected_item: dict[str, Any] | None = None
        self._categories: list[dict[str, Any]] = []

        self._actions: dict[str, QAction] = {}
        self._build_menu()

    def _build_menu(self):
        """Build the context menu structure."""
        # Add code
        self._actions["add_code"] = self.add_item(
            "Add New Code",
            icon="mdi6.plus",
            on_click=lambda: self.action_triggered.emit("add_code"),
        )

        # Add sub-category
        self._actions["add_category"] = self.add_item(
            "Add Sub-category",
            icon="mdi6.folder-plus",
            on_click=lambda: self.action_triggered.emit("add_category"),
        )

        self.add_separator()

        # Rename
        self._actions["rename"] = self.add_item(
            "Rename",
            icon="mdi6.pencil",
            shortcut="F2",
            on_click=lambda: self.action_triggered.emit("rename"),
            enabled=False,
        )

        # Change color (codes only)
        self._actions["change_color"] = self.add_item(
            "Change Color",
            icon="mdi6.palette",
            on_click=lambda: self.action_triggered.emit("change_color"),
            enabled=False,
        )

        # Memo
        self._actions["memo"] = self.add_item(
            "View/Edit Memo",
            icon="mdi6.note-text",
            on_click=lambda: self.action_triggered.emit("memo"),
            enabled=False,
        )

        self.add_separator()

        # Move to category submenu
        self._move_submenu = self.add_submenu("Move to Category")
        self._actions["move"] = self._move_submenu.menuAction()

        self.add_separator()

        # Show all files
        self._actions["show_files"] = self.add_item(
            "Show All Files with This Code",
            icon="mdi6.file-search",
            on_click=lambda: self.action_triggered.emit("show_files"),
            enabled=False,
        )

        self.add_separator()

        # Delete
        self._actions["delete"] = self.add_item(
            "Delete",
            icon="mdi6.delete",
            variant="danger",
            on_click=lambda: self.action_triggered.emit("delete"),
            enabled=False,
        )

    def set_selected_item(self, item: dict[str, Any] | None):
        """Set the currently selected tree item."""
        self._selected_item = item
        self._update_actions()

    def set_categories(self, categories: list[dict[str, Any]]):
        """Set available categories for move action."""
        self._categories = categories
        self._build_move_submenu()

    def _build_move_submenu(self):
        """Rebuild the move to category submenu."""
        self._move_submenu.clear()

        if not self._categories:
            action = self._move_submenu.addAction("No categories available")
            action.setEnabled(False)
            return

        for category in self._categories:
            action = self._move_submenu.addAction(category.get("name", "Unnamed"))
            cat_id = category.get("id", "")
            action.triggered.connect(
                lambda _checked, cid=cat_id: self.move_to_category.emit(cid)
            )

    def _update_actions(self):
        """Update action enabled states based on selected item."""
        has_item = self._selected_item is not None
        is_code = has_item and self._selected_item.get("type") == "code"

        # Rename works for both
        self._actions["rename"].setEnabled(has_item)

        # Change color only for codes
        self._actions["change_color"].setEnabled(is_code)
        self._actions["change_color"].setVisible(is_code)

        # Memo for codes
        self._actions["memo"].setEnabled(is_code)

        # Move for codes
        self._actions["move"].setEnabled(is_code and len(self._categories) > 0)
        self._actions["move"].setVisible(is_code)

        # Show files for codes
        self._actions["show_files"].setEnabled(is_code)
        self._actions["show_files"].setVisible(is_code)

        # Delete for both
        self._actions["delete"].setEnabled(has_item)

    def get_action(self, action_id: str) -> QAction | None:
        """Get an action by its ID."""
        return self._actions.get(action_id)
