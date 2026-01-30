"""
Filter/Search components
Filter panels, chips, search inputs, and view toggles
"""

from typing import List, Optional, Dict, Any

import qtawesome as qta

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors


class FilterPanel(QFrame):
    """
    Collapsible filter panel with multiple filter sections.

    Usage:
        panel = FilterPanel()
        panel.add_section("Status", ["Active", "Archived", "Draft"])
        panel.add_section("Type", ["Text", "Audio", "Video"])
        panel.filters_changed.connect(self.apply_filters)
    """

    filters_changed = Signal(dict)  # {section: [selected_values]}

    def __init__(
        self,
        title: str = "Filters",
        collapsible: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._sections = {}
        self._collapsed = False
        self._collapsible = collapsible

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px {RADIUS.md}px 0 0;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        if collapsible:
            self._toggle_btn = QPushButton()
            self._toggle_btn.setIcon(qta.icon("mdi6.chevron-down", color=self._colors.text_secondary))
            self._toggle_btn.setFixedSize(24, 24)
            self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                }}
            """)
            self._toggle_btn.clicked.connect(self._toggle)
            header_layout.addWidget(self._toggle_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.primary};
                border: none;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        clear_btn.clicked.connect(self.clear_filters)
        header_layout.addWidget(clear_btn)

        self._main_layout.addWidget(header)

        # Content
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        self._content_layout.setSpacing(SPACING.md)

        self._main_layout.addWidget(self._content)

    def add_section(self, name: str, options: List[str]):
        section = FilterSection(name, options, colors=self._colors)
        section.selection_changed.connect(lambda: self._emit_changes())
        self._sections[name] = section
        self._content_layout.addWidget(section)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        icon_name = "mdi6.chevron-right" if self._collapsed else "mdi6.chevron-down"
        self._toggle_btn.setIcon(qta.icon(icon_name, color=self._colors.text_secondary))

    def _emit_changes(self):
        filters = {}
        for name, section in self._sections.items():
            selected = section.get_selected()
            if selected:
                filters[name] = selected
        self.filters_changed.emit(filters)

    def clear_filters(self):
        for section in self._sections.values():
            section.clear_selection()
        self.filters_changed.emit({})

    def get_filters(self) -> Dict[str, List[str]]:
        filters = {}
        for name, section in self._sections.items():
            selected = section.get_selected()
            if selected:
                filters[name] = selected
        return filters


class FilterSection(QFrame):
    """Individual filter section with checkboxes"""

    selection_changed = Signal()

    def __init__(
        self,
        name: str,
        options: List[str],
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._checkboxes = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Section title
        title = QLabel(name)
        title.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            text-transform: uppercase;
        """)
        layout.addWidget(title)

        # Options
        for option in options:
            cb = QCheckBox(option)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {self._colors.text_primary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                    spacing: {SPACING.sm}px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 4px;
                    border: 2px solid {self._colors.border};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {self._colors.primary};
                    border-color: {self._colors.primary};
                }}
            """)
            cb.stateChanged.connect(lambda: self.selection_changed.emit())
            self._checkboxes.append(cb)
            layout.addWidget(cb)

    def get_selected(self) -> List[str]:
        return [cb.text() for cb in self._checkboxes if cb.isChecked()]

    def clear_selection(self):
        for cb in self._checkboxes:
            cb.setChecked(False)


class FilterChip(QFrame):
    """
    Active filter chip with remove button.

    Usage:
        chip = FilterChip("Status: Active")
        chip.removed.connect(self.remove_filter)
    """

    removed = Signal()
    clicked = Signal()

    def __init__(
        self,
        text: str,
        removable: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.primary}26;
                border: 1px solid {self._colors.primary};
                border-radius: {RADIUS.full}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self._colors.primary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        layout.addWidget(label)

        if removable:
            remove_btn = QPushButton()
            remove_btn.setIcon(qta.icon("mdi6.close", color=self._colors.primary))
            remove_btn.setFixedSize(16, 16)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.error}20;
                    border-radius: 8px;
                }}
            """)
            remove_btn.clicked.connect(self.removed.emit)
            layout.addWidget(remove_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class FilterChipGroup(QFrame):
    """
    Group of active filter chips.

    Usage:
        group = FilterChipGroup()
        group.add_chip("Status: Active", "status")
        group.chip_removed.connect(self.remove_filter)
    """

    chip_removed = Signal(str)  # chip_id
    clear_all = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._chips = {}

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.sm)

        # Clear all button (hidden initially)
        self._clear_btn = QPushButton("Clear all")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                color: {self._colors.primary};
            }}
        """)
        self._clear_btn.clicked.connect(self._clear_all)
        self._clear_btn.hide()

    def add_chip(self, text: str, chip_id: str):
        if chip_id in self._chips:
            return

        chip = FilterChip(text, colors=self._colors)
        chip.removed.connect(lambda: self._remove_chip(chip_id))
        self._chips[chip_id] = chip

        # Insert before clear button
        self._layout.insertWidget(self._layout.count(), chip)

        # Show clear button if we have chips
        if len(self._chips) > 0:
            if self._clear_btn.parent() is None:
                self._layout.addWidget(self._clear_btn)
            self._clear_btn.show()

    def _remove_chip(self, chip_id: str):
        if chip_id in self._chips:
            chip = self._chips.pop(chip_id)
            chip.deleteLater()
            self.chip_removed.emit(chip_id)

        if len(self._chips) == 0:
            self._clear_btn.hide()

    def _clear_all(self):
        for chip_id in list(self._chips.keys()):
            self._remove_chip(chip_id)
        self.clear_all.emit()


class SearchInput(QFrame):
    """
    Search input with icon and clear button.

    Usage:
        search = SearchInput(placeholder="Search files...")
        search.search_changed.connect(self.filter_results)
    """

    search_changed = Signal(str)
    search_submitted = Signal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
        show_icon: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
            QFrame:focus-within {{
                border-color: {self._colors.primary};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.sm)

        # Search icon
        if show_icon:
            icon = QLabel()
            icon.setPixmap(qta.icon("mdi6.magnify", color=self._colors.text_secondary).pixmap(16, 16))
            layout.addWidget(icon)

        # Input
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        self._input.textChanged.connect(self.search_changed.emit)
        self._input.returnPressed.connect(lambda: self.search_submitted.emit(self._input.text()))
        layout.addWidget(self._input, 1)

        # Clear button
        self._clear_btn = QPushButton()
        self._clear_btn.setIcon(qta.icon("mdi6.close", color=self._colors.text_secondary))
        self._clear_btn.setFixedSize(20, 20)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
                border-radius: 10px;
            }}
        """)
        self._clear_btn.clicked.connect(self._clear)
        self._clear_btn.hide()
        layout.addWidget(self._clear_btn)

        self._input.textChanged.connect(self._update_clear_btn)

    def _clear(self):
        self._input.clear()
        self._input.setFocus()

    def _update_clear_btn(self, text: str):
        self._clear_btn.setVisible(bool(text))

    def text(self) -> str:
        return self._input.text()

    def set_text(self, text: str):
        self._input.setText(text)

    def focus(self):
        self._input.setFocus()


class SearchOptions(QFrame):
    """
    Search options panel with advanced filters.

    Usage:
        options = SearchOptions()
        options.add_option("case_sensitive", "Case sensitive")
        options.add_option("whole_word", "Whole word")
        options.options_changed.connect(self.update_search)
    """

    options_changed = Signal(dict)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._options = {}

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        self._layout.setSpacing(SPACING.lg)

    def add_option(self, key: str, label: str, default: bool = False):
        cb = QCheckBox(label)
        cb.setChecked(default)
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid {self._colors.border};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self._colors.primary};
                border-color: {self._colors.primary};
            }}
        """)
        cb.stateChanged.connect(lambda: self._emit_options())
        self._options[key] = cb
        self._layout.addWidget(cb)

    def _emit_options(self):
        values = {key: cb.isChecked() for key, cb in self._options.items()}
        self.options_changed.emit(values)

    def get_options(self) -> Dict[str, bool]:
        return {key: cb.isChecked() for key, cb in self._options.items()}


class ViewToggle(QFrame):
    """
    Toggle between different view modes (grid/list/etc).

    Usage:
        toggle = ViewToggle(["grid", "list", "table"])
        toggle.view_changed.connect(self.switch_view)
    """

    view_changed = Signal(str)

    def __init__(
        self,
        views: List[str] = None,
        current: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._views = views or ["grid", "list"]
        self._current = current or self._views[0]
        self._buttons = {}

        view_icons = {
            "grid": "mdi6.view-grid",
            "list": "mdi6.view-list",
            "table": "mdi6.table",
            "cards": "mdi6.card-outline",
            "tree": "mdi6.file-tree",
        }

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        layout.setSpacing(0)

        for view in self._views:
            icon_name = view_icons.get(view, "mdi6.view-list")
            btn = QPushButton()
            btn.setIcon(qta.icon(icon_name, color=self._colors.text_secondary))
            btn.setFixedSize(32, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(view.capitalize())
            btn.clicked.connect(lambda checked, v=view: self._select(v))
            self._buttons[view] = (btn, icon_name)
            layout.addWidget(btn)

        self._update_styles()

    def _select(self, view: str):
        if view != self._current:
            self._current = view
            self._update_styles()
            self.view_changed.emit(view)

    def _update_styles(self):
        for view, (btn, icon_name) in self._buttons.items():
            if view == self._current:
                btn.setIcon(qta.icon(icon_name, color="white"))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self._colors.primary};
                        border: none;
                        border-radius: {RADIUS.sm}px;
                    }}
                """)
            else:
                btn.setIcon(qta.icon(icon_name, color=self._colors.text_secondary))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border: none;
                        border-radius: {RADIUS.sm}px;
                    }}
                    QPushButton:hover {{
                        background-color: {self._colors.surface_lighter};
                    }}
                """)

    def set_view(self, view: str):
        if view in self._views:
            self._current = view
            self._update_styles()

    def current_view(self) -> str:
        return self._current
