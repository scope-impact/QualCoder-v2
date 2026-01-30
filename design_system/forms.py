"""
Form components
Input fields, selects, and form controls
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors


class SearchBox(QFrame):
    """
    Search input with icon.

    Usage:
        search = SearchBox(placeholder="Search files...")
        search.text_changed.connect(self.filter_results)
        search.search_submitted.connect(self.do_search)
    """

    text_changed = Signal(str)
    search_submitted = Signal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
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
        layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.xs)
        layout.setSpacing(SPACING.sm)

        # Search icon
        icon = QLabel("🔍")
        icon.setStyleSheet(f"color: {self._colors.text_disabled}; font-size: 16px;")
        layout.addWidget(icon)

        # Input
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                padding: {SPACING.xs}px;
            }}
        """)
        self._input.textChanged.connect(self.text_changed.emit)
        self._input.returnPressed.connect(lambda: self.search_submitted.emit(self._input.text()))
        layout.addWidget(self._input, 1)

    def text(self) -> str:
        return self._input.text()

    def setText(self, text: str):
        self._input.setText(text)

    def clear(self):
        self._input.clear()


class Select(QComboBox):
    """
    Styled dropdown select.

    Usage:
        select = Select(placeholder="Choose option...")
        select.add_items(["Option 1", "Option 2", "Option 3"])
        select.value_changed.connect(self.on_change)
    """

    value_changed = Signal(str)

    def __init__(
        self,
        placeholder: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        if placeholder:
            self.addItem(placeholder)
            self.setCurrentIndex(0)

        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                padding-right: {SPACING.xxl}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                min-height: 32px;
            }}
            QComboBox:hover {{
                border-color: {self._colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self._colors.text_secondary};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                selection-background-color: {self._colors.surface_light};
                padding: {SPACING.xs}px;
            }}
        """)

        self.currentTextChanged.connect(self.value_changed.emit)

    def add_items(self, items: List[str]):
        self.addItems(items)

    def value(self) -> str:
        return self.currentText()

    def setValue(self, value: str):
        index = self.findText(value)
        if index >= 0:
            self.setCurrentIndex(index)


class MultiSelect(QFrame):
    """
    Multiple selection dropdown.

    Usage:
        multi = MultiSelect(placeholder="Select items...")
        multi.add_items(["Item 1", "Item 2", "Item 3"])
        multi.selection_changed.connect(self.on_change)
    """

    selection_changed = Signal(list)

    def __init__(
        self,
        placeholder: str = "Select...",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected = []
        self._expanded = False

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton(placeholder)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                padding: {SPACING.sm}px {SPACING.md}px;
                text-align: left;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        self._header.clicked.connect(self._toggle_dropdown)
        layout.addWidget(self._header)

        # Dropdown list
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self._colors.surface};
                border: none;
                border-top: 1px solid {self._colors.border};
            }}
            QListWidget::item {{
                padding: {SPACING.sm}px {SPACING.md}px;
            }}
            QListWidget::item:selected {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)
        self._list.itemSelectionChanged.connect(self._on_selection_change)
        self._list.hide()
        layout.addWidget(self._list)

    def add_items(self, items: List[str]):
        for item in items:
            self._list.addItem(item)

    def _toggle_dropdown(self):
        self._expanded = not self._expanded
        self._list.setVisible(self._expanded)

    def _on_selection_change(self):
        self._selected = [item.text() for item in self._list.selectedItems()]
        self._update_header()
        self.selection_changed.emit(self._selected)

    def _update_header(self):
        if self._selected:
            text = ", ".join(self._selected[:2])
            if len(self._selected) > 2:
                text += f" +{len(self._selected) - 2}"
            self._header.setText(text)
            self._header.setStyleSheet(self._header.styleSheet().replace(
                self._colors.text_secondary, self._colors.text_primary
            ))

    def selected_items(self) -> List[str]:
        return self._selected


class Textarea(QTextEdit):
    """
    Multi-line text input.

    Usage:
        textarea = Textarea(placeholder="Enter description...")
        textarea.text_changed.connect(self.on_change)
    """

    text_changed = Signal(str)

    def __init__(
        self,
        placeholder: str = "",
        min_height: int = 100,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(min_height)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_base}px;
            }}
            QTextEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)

        self.textChanged.connect(lambda: self.text_changed.emit(self.toPlainText()))

    def value(self) -> str:
        return self.toPlainText()

    def setValue(self, text: str):
        self.setPlainText(text)


class NumberInput(QFrame):
    """
    Numeric input with optional min/max and step.

    Usage:
        num_input = NumberInput(min_val=0, max_val=100, step=1)
        num_input.value_changed.connect(self.on_change)
    """

    value_changed = Signal(float)

    def __init__(
        self,
        min_val: float = 0,
        max_val: float = 100,
        step: float = 1,
        decimals: int = 0,
        label: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            layout.addWidget(lbl)

        if decimals > 0:
            self._input = QDoubleSpinBox()
            self._input.setDecimals(decimals)
        else:
            self._input = QSpinBox()

        self._input.setMinimum(int(min_val) if decimals == 0 else min_val)
        self._input.setMaximum(int(max_val) if decimals == 0 else max_val)
        self._input.setSingleStep(int(step) if decimals == 0 else step)

        self._input.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {self._colors.primary};
            }}
        """)

        self._input.valueChanged.connect(lambda v: self.value_changed.emit(float(v)))
        layout.addWidget(self._input)

    def value(self) -> float:
        return self._input.value()

    def setValue(self, value: float):
        self._input.setValue(value)


class RangeSlider(QFrame):
    """
    Range slider with labels.

    Usage:
        slider = RangeSlider(min_val=0, max_val=100, label="Volume")
        slider.value_changed.connect(self.on_change)
    """

    value_changed = Signal(int)

    def __init__(
        self,
        min_val: int = 0,
        max_val: int = 100,
        value: int = 50,
        label: str = "",
        show_value: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # Header with label and value
        if label or show_value:
            header = QHBoxLayout()
            if label:
                lbl = QLabel(label)
                lbl.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
                header.addWidget(lbl)
            header.addStretch()
            if show_value:
                self._value_label = QLabel(str(value))
                self._value_label.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_sm}px;")
                header.addWidget(self._value_label)
            layout.addLayout(header)

        # Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(min_val)
        self._slider.setMaximum(max_val)
        self._slider.setValue(value)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background-color: {self._colors.surface_lighter};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background-color: {self._colors.primary};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {self._colors.primary_light};
            }}
            QSlider::sub-page:horizontal {{
                background-color: {self._colors.primary};
                border-radius: 2px;
            }}
        """)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider)

    def _on_change(self, value: int):
        if hasattr(self, '_value_label'):
            self._value_label.setText(str(value))
        self.value_changed.emit(value)

    def value(self) -> int:
        return self._slider.value()

    def setValue(self, value: int):
        self._slider.setValue(value)


class ColorPicker(QFrame):
    """
    Color selection with swatches.

    Usage:
        picker = ColorPicker()
        picker.color_selected.connect(self.on_color_pick)
    """

    color_selected = Signal(str)

    DEFAULT_COLORS = [
        "#FFC107", "#F44336", "#4CAF50", "#9C27B0",
        "#2196F3", "#E91E63", "#FF5722", "#00BCD4",
        "#FFEB3B", "#8BC34A", "#673AB7", "#3F51B5",
    ]

    def __init__(
        self,
        colors_list: List[str] = None,
        selected: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._color_list = colors_list or self.DEFAULT_COLORS
        self._selected = selected

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        self._swatches = []
        for color in self._color_list:
            swatch = self._create_swatch(color)
            self._swatches.append(swatch)
            layout.addWidget(swatch)

        layout.addStretch()

    def _create_swatch(self, color: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("color", color)

        is_selected = color == self._selected
        border = f"2px solid {self._colors.primary}" if is_selected else "none"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: {border};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid {self._colors.text_secondary};
            }}
        """)
        btn.clicked.connect(lambda: self._select_color(color))
        return btn

    def _select_color(self, color: str):
        self._selected = color
        for swatch in self._swatches:
            swatch_color = swatch.property("color")
            is_selected = swatch_color == color
            border = f"2px solid {self._colors.primary}" if is_selected else "none"
            swatch.setStyleSheet(f"""
                QPushButton {{
                    background-color: {swatch_color};
                    border: {border};
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid {self._colors.text_secondary};
                }}
            """)
        self.color_selected.emit(color)

    def selected_color(self) -> Optional[str]:
        return self._selected


class FormGroup(QFrame):
    """
    Form group with label and input.

    Usage:
        group = FormGroup("Email", required=True)
        group.set_input(Input(placeholder="Enter email"))
        group.set_error("Invalid email format")
    """

    def __init__(
        self,
        label: str,
        required: bool = False,
        hint: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, SPACING.lg)
        layout.setSpacing(SPACING.xs)

        # Label
        label_layout = QHBoxLayout()
        label_layout.setSpacing(SPACING.xs)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            text-transform: uppercase;
        """)
        label_layout.addWidget(lbl)

        if required:
            req = QLabel("*")
            req.setStyleSheet(f"color: {self._colors.error}; font-size: {TYPOGRAPHY.text_sm}px;")
            label_layout.addWidget(req)

        label_layout.addStretch()
        layout.addLayout(label_layout)

        # Input placeholder
        self._input_container = QVBoxLayout()
        layout.addLayout(self._input_container)

        # Hint/Error
        self._message = QLabel(hint)
        self._message.setStyleSheet(f"color: {self._colors.text_hint}; font-size: {TYPOGRAPHY.text_sm}px;")
        self._message.setVisible(bool(hint))
        layout.addWidget(self._message)

    def set_input(self, widget: QWidget):
        # Clear existing
        while self._input_container.count():
            item = self._input_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._input_container.addWidget(widget)

    def set_error(self, message: str):
        self._message.setText(message)
        self._message.setStyleSheet(f"color: {self._colors.error}; font-size: {TYPOGRAPHY.text_sm}px;")
        self._message.setVisible(True)

    def set_hint(self, message: str):
        self._message.setText(message)
        self._message.setStyleSheet(f"color: {self._colors.text_hint}; font-size: {TYPOGRAPHY.text_sm}px;")
        self._message.setVisible(True)

    def clear_message(self):
        self._message.setVisible(False)


class CoderSelector(QFrame):
    """
    Labeled dropdown for selecting current coder.

    A light wrapper around Select that adds a label prefix.

    Usage:
        selector = CoderSelector(
            coders=["colin", "sarah", "james"],
            selected="colin"
        )
        selector.coder_changed.connect(on_coder_changed)
    """

    coder_changed = Signal(str)

    def __init__(
        self,
        coders: List[str] = None,
        selected: str = None,
        label: str = "Coder:",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._coders = coders or []

        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Label
        self._label = QLabel(label)
        self._label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(self._label)

        # Select dropdown
        self._select = Select(colors=self._colors)
        self._select.add_items(coders)
        if selected and selected in coders:
            self._select.setValue(selected)
        self._select.value_changed.connect(self.coder_changed.emit)
        layout.addWidget(self._select)

    def set_coders(self, coders: List[str]):
        """Update the list of coders"""
        self._coders = coders
        self._select._combo.clear()
        self._select.add_items(coders)

    def set_selected(self, coder: str):
        """Select a coder"""
        if coder in self._coders:
            self._select.setValue(coder)

    def selected(self) -> str:
        """Get currently selected coder"""
        return self._select.value()
