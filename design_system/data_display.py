"""
Data display components
Tables, cells, and data presentation widgets
"""

from typing import List, Dict, Any, Optional

from .qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QGridLayout,
    Qt, Signal, QColor,
)

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class DataTable(QFrame):
    """
    Styled data table with headers, selection, and actions.

    Usage:
        table = DataTable(
            columns=["Name", "Type", "Size", "Modified"],
            selectable=True
        )
        table.set_data([
            {"Name": "file.txt", "Type": "Text", "Size": "12KB", "Modified": "Jan 28"},
            ...
        ])
        table.row_clicked.connect(self.on_row_click)
    """

    row_clicked = Signal(int, dict)
    row_double_clicked = Signal(int, dict)
    selection_changed = Signal(list)

    def __init__(
        self,
        columns: List[str],
        selectable: bool = False,
        show_header: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._columns = columns
        self._selectable = selectable
        self._data = []

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Table widget
        self._table = QTableWidget()
        self._table.setColumnCount(len(columns) + (1 if selectable else 0))

        headers = [""] + columns if selectable else columns
        self._table.setHorizontalHeaderLabels(headers)

        self._table.horizontalHeader().setVisible(show_header)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                text-transform: uppercase;
                padding: {SPACING.md}px {SPACING.lg}px;
                border: none;
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection if selectable
            else QAbstractItemView.SelectionMode.SingleSelection
        )

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self._colors.surface};
                border: none;
                gridline-color: {self._colors.border};
            }}
            QTableWidget::item {{
                padding: {SPACING.md}px {SPACING.lg}px;
                border-bottom: 1px solid {self._colors.border};
                color: {self._colors.text_primary};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(0, 150, 136, 0.1);
            }}
            QTableWidget::item:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        self._table.cellClicked.connect(self._on_cell_click)
        self._table.cellDoubleClicked.connect(self._on_cell_double_click)

        layout.addWidget(self._table)

    def set_data(self, data: List[Dict[str, Any]]):
        self._data = data
        self._table.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            col_offset = 0

            # Checkbox column
            if self._selectable:
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(lambda: self._on_selection_change())
                self._table.setCellWidget(row_idx, 0, checkbox)
                col_offset = 1

            # Data columns
            for col_idx, col_name in enumerate(self._columns):
                value = row_data.get(col_name, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_idx, col_idx + col_offset, item)

    def _on_cell_click(self, row: int, col: int):
        if row < len(self._data):
            self.row_clicked.emit(row, self._data[row])

    def _on_cell_double_click(self, row: int, col: int):
        if row < len(self._data):
            self.row_double_clicked.emit(row, self._data[row])

    def _on_selection_change(self):
        selected = []
        for row in range(self._table.rowCount()):
            checkbox = self._table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected.append(self._data[row])
        self.selection_changed.emit(selected)

    def selected_rows(self) -> List[Dict]:
        if not self._selectable:
            return []
        selected = []
        for row in range(self._table.rowCount()):
            checkbox = self._table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected.append(self._data[row])
        return selected


class FileCell(QFrame):
    """
    File display cell with icon, name, and metadata.

    Usage:
        cell = FileCell(
            name="Interview_01.txt",
            file_type="text",
            size="12.4 KB",
            modified="Jan 28, 2025"
        )
    """

    clicked = Signal()

    def __init__(
        self,
        name: str,
        file_type: str = "text",
        size: str = "",
        modified: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # File type icon
        type_icons = {
            "text": ("📄", self._colors.file_text),
            "audio": ("🎵", self._colors.file_audio),
            "video": ("🎬", self._colors.file_video),
            "image": ("🖼️", self._colors.file_image),
            "pdf": ("📕", self._colors.file_pdf),
        }
        icon, color = type_icons.get(file_type, ("📄", self._colors.file_text))

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"""
            background-color: {color}26;
            border-radius: {RADIUS.md}px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 18px; color: {color};")
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_frame)

        # File info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        info_layout.addWidget(name_label)

        if size or modified:
            meta = " • ".join(filter(None, [size, modified]))
            meta_label = QLabel(meta)
            meta_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            info_layout.addWidget(meta_label)

        layout.addLayout(info_layout, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class EntityCell(QFrame):
    """
    Entity display cell with avatar and label.

    Usage:
        cell = EntityCell(
            name="Participant 01",
            subtitle="3 files • 47 codings",
            avatar="P1"
        )
    """

    clicked = Signal()

    def __init__(
        self,
        name: str,
        subtitle: str = "",
        avatar: str = "",
        avatar_color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Avatar
        avatar_widget = QLabel(avatar or name[0].upper())
        avatar_widget.setFixedSize(40, 40)
        avatar_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_color = avatar_color or self._colors.primary
        avatar_widget.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(avatar_widget)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        info_layout.addWidget(name_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            info_layout.addWidget(sub_label)

        layout.addLayout(info_layout, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class InfoCard(QFrame):
    """
    Information card with titled header and content slot.

    Used for side panel info sections. Supports qtawesome icons,
    collapsible content, and widget-based content.

    Usage:
        # Simple text content
        card = InfoCard(title="Selected Code", icon="mdi6.information")
        card.set_text("Code details here...")

        # Widget content (slot)
        card = InfoCard(title="File Memo", icon="mdi6.bookmark")
        card.set_content(my_custom_widget)

        # Collapsible
        card = InfoCard(title="Details", collapsible=True)
    """

    collapsed_changed = Signal(bool)

    def __init__(
        self,
        title: str = "",
        icon: str = None,
        collapsible: bool = False,
        collapsed: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._collapsible = collapsible
        self._collapsed = collapsed
        self._icon_name = icon

        self.setStyleSheet(f"""
            InfoCard {{
                background-color: transparent;
                border: none;
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        self._main_layout.setSpacing(SPACING.md)

        # Header
        self._header = QFrame()
        self._header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING.sm)

        if icon:
            from .icons import Icon
            self._icon_widget = Icon(icon, size=16, color=self._colors.primary, colors=self._colors)
            header_layout.addWidget(self._icon_widget)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        if collapsible:
            from .icons import Icon
            self._collapse_icon = Icon(
                "mdi6.chevron-down" if not collapsed else "mdi6.chevron-right",
                size=16,
                color=self._colors.text_secondary,
                colors=self._colors
            )
            header_layout.addWidget(self._collapse_icon)
            self._header.setCursor(Qt.CursorShape.PointingHandCursor)
            self._header.mousePressEvent = self._toggle_collapse

        self._main_layout.addWidget(self._header)

        # Content container
        self._content_container = QFrame()
        self._content_container.setStyleSheet("background: transparent; border: none;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content_container)

        if collapsed:
            self._content_container.hide()

    def _toggle_collapse(self, event=None):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._content_container.hide()
            if hasattr(self, '_collapse_icon'):
                self._collapse_icon._name = "mdi6.chevron-right"
                self._collapse_icon._setup_icon()
        else:
            self._content_container.show()
            if hasattr(self, '_collapse_icon'):
                self._collapse_icon._name = "mdi6.chevron-down"
                self._collapse_icon._setup_icon()
        self.collapsed_changed.emit(self._collapsed)

    def set_content(self, widget: QWidget):
        """Set the content widget (slot-based)"""
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._content_layout.addWidget(widget)

    def set_text(self, text: str):
        """Set simple text content"""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            line-height: 1.6;
        """)
        self.set_content(label)

    def set_title(self, title: str):
        """Update the title"""
        self._title_label.setText(title)

    def is_collapsed(self) -> bool:
        return self._collapsed


class CodeDetailCard(QFrame):
    """
    Displays details of a selected code.

    Shows code color, name, memo, and optional example text.

    Usage:
        detail = CodeDetailCard(
            color="#FFC107",
            name="soccer playing",
            memo="Code for references to playing soccer...",
            example="I have not studied much before..."
        )
    """

    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(
        self,
        color: str = "#009688",
        name: str = "",
        memo: str = "",
        example: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._code_color = color

        self.setStyleSheet(f"""
            CodeDetailCard {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        # Header: color dot + name
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        self._color_dot = QFrame()
        self._color_dot.setFixedSize(16, 16)
        self._color_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: {RADIUS.xs}px;
        """)
        header.addWidget(self._color_dot)

        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header.addWidget(self._name_label)
        header.addStretch()

        layout.addLayout(header)

        # Memo
        if memo:
            self._memo_label = QLabel(memo)
            self._memo_label.setWordWrap(True)
            self._memo_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                line-height: 1.6;
            """)
            layout.addWidget(self._memo_label)

        # Example text
        if example:
            example_frame = QFrame()
            example_frame.setStyleSheet(f"""
                background-color: {self._colors.surface_lighter};
                border-radius: {RADIUS.sm}px;
                border-left: 3px solid {color};
            """)
            example_layout = QVBoxLayout(example_frame)
            example_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.sm, SPACING.sm)

            example_label = QLabel(f'"{example}"')
            example_label.setWordWrap(True)
            example_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-style: italic;
            """)
            example_layout.addWidget(example_label)
            layout.addWidget(example_frame)

    def set_code(self, color: str, name: str, memo: str = "", example: str = None):
        """Update the displayed code details"""
        self._code_color = color
        self._color_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: {RADIUS.xs}px;
        """)
        self._name_label.setText(name)
        if hasattr(self, '_memo_label'):
            self._memo_label.setText(memo)


class StatRow(QFrame):
    """
    Label + value row for statistics display.

    Usage:
        row = StatRow("Total Files", "24")
    """

    def __init__(
        self,
        label: str,
        value: str,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, SPACING.sm, 0, SPACING.sm)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(label_widget)

        layout.addStretch()

        self._value = QLabel(value)
        self._value.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(self._value)

    def setValue(self, value: str):
        self._value.setText(value)


class KeyValueList(QFrame):
    """
    List of key-value pairs.

    Usage:
        kv_list = KeyValueList()
        kv_list.add_item("Name", "Project Alpha")
        kv_list.add_item("Created", "Jan 15, 2025")
        kv_list.add_item("Files", "24")
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def add_item(self, label: str, value: str) -> StatRow:
        row = StatRow(label, value, colors=self._colors)
        self._layout.addWidget(row)
        return row

    def add_separator(self):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self._colors.border};")
        self._layout.addWidget(sep)


class EmptyState(QFrame):
    """
    Empty state placeholder with icon, message, and action.

    Usage:
        empty = EmptyState(
            icon="📂",
            title="No files yet",
            message="Import some files to get started",
            action_text="Import Files",
            on_action=self.import_files
        )
    """

    action_clicked = Signal()

    def __init__(
        self,
        icon: str = "📭",
        title: str = "No items",
        message: str = "",
        action_text: str = None,
        on_action=None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xxxl, SPACING.xxxl, SPACING.xxxl, SPACING.xxxl)
        layout.setSpacing(SPACING.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Message
        if message:
            msg_label = QLabel(message)
            msg_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

        # Action button
        if action_text:
            btn = QPushButton(action_text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.xl}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{
                    background-color: {self._colors.primary_light};
                }}
            """)
            if on_action:
                btn.clicked.connect(on_action)
            btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


class HeatMapCell(QFrame):
    """
    Heat map cell with color intensity based on value.

    Used in co-occurrence matrices and frequency tables to show
    value intensity through color.

    Usage:
        cell = HeatMapCell(value=0.75, min_value=0, max_value=1)
        cell.set_value(0.85)

    Color schemes:
        - "primary": Light to primary color
        - "sequential": White to red
        - "diverging": Blue (-) to white (0) to red (+)
    """

    clicked = Signal(float)

    def __init__(
        self,
        value: float = 0,
        min_value: float = 0,
        max_value: float = 1,
        show_value: bool = True,
        color_scheme: str = "primary",
        size: int = 40,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._value = value
        self._min_value = min_value
        self._max_value = max_value
        self._show_value = show_value
        self._color_scheme = color_scheme

        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self._update_display()

    def _normalize_value(self) -> float:
        """Normalize value to 0-1 range"""
        if self._max_value == self._min_value:
            return 0
        return (self._value - self._min_value) / (self._max_value - self._min_value)

    def _get_color(self) -> str:
        """Calculate color based on value and scheme"""
        normalized = self._normalize_value()

        if self._color_scheme == "primary":
            # Interpolate from surface to primary
            base = QColor(self._colors.surface_lighter)
            target = QColor(self._colors.primary)
            return self._interpolate_color(base, target, normalized)

        elif self._color_scheme == "sequential":
            # White to red
            base = QColor("#FFFFFF")
            target = QColor("#F44336")
            return self._interpolate_color(base, target, normalized)

        elif self._color_scheme == "diverging":
            # Blue (-) to white (0) to red (+)
            if normalized < 0.5:
                base = QColor("#2196F3")  # Blue
                target = QColor("#FFFFFF")
                return self._interpolate_color(base, target, normalized * 2)
            else:
                base = QColor("#FFFFFF")
                target = QColor("#F44336")  # Red
                return self._interpolate_color(base, target, (normalized - 0.5) * 2)

        elif self._color_scheme == "success":
            # White to success green
            base = QColor(self._colors.surface_lighter)
            target = QColor(self._colors.success)
            return self._interpolate_color(base, target, normalized)

        # Default to primary scheme
        base = QColor(self._colors.surface_lighter)
        target = QColor(self._colors.primary)
        return self._interpolate_color(base, target, normalized)

    def _interpolate_color(self, color1: QColor, color2: QColor, factor: float) -> str:
        """Interpolate between two colors"""
        factor = max(0, min(1, factor))
        r = int(color1.red() + (color2.red() - color1.red()) * factor)
        g = int(color1.green() + (color2.green() - color1.green()) * factor)
        b = int(color1.blue() + (color2.blue() - color1.blue()) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text_color(self) -> str:
        """Get appropriate text color for contrast"""
        bg_color = QColor(self._get_color())
        # Calculate luminance
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
        return self._colors.text_primary if luminance > 0.5 else "#FFFFFF"

    def _update_display(self):
        """Update the cell appearance"""
        bg_color = self._get_color()
        text_color = self._get_text_color()

        self.setStyleSheet(f"""
            HeatMapCell {{
                background-color: {bg_color};
                border-radius: {RADIUS.xs}px;
            }}
        """)

        if self._show_value:
            # Format value appropriately
            if abs(self._value) >= 100:
                text = f"{int(self._value)}"
            elif abs(self._value) >= 10:
                text = f"{self._value:.1f}"
            else:
                text = f"{self._value:.2f}"

            self._label.setText(text)
            self._label.setStyleSheet(f"""
                color: {text_color};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)

    def set_value(self, value: float):
        """Update the cell value"""
        self._value = value
        self._update_display()

    def value(self) -> float:
        """Get current value"""
        return self._value

    def set_range(self, min_value: float, max_value: float):
        """Set the value range"""
        self._min_value = min_value
        self._max_value = max_value
        self._update_display()

    def set_color_scheme(self, scheme: str):
        """Change color scheme"""
        self._color_scheme = scheme
        self._update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._value)


class HeatMapGrid(QFrame):
    """
    Grid of heat map cells for co-occurrence matrices.

    Usage:
        grid = HeatMapGrid(
            row_labels=["Code A", "Code B", "Code C"],
            col_labels=["Code A", "Code B", "Code C"],
            values=[
                [1.0, 0.5, 0.2],
                [0.5, 1.0, 0.7],
                [0.2, 0.7, 1.0],
            ]
        )
        grid.cell_clicked.connect(on_cell_click)
    """

    cell_clicked = Signal(int, int, float)  # row, col, value

    def __init__(
        self,
        row_labels: List[str],
        col_labels: List[str],
        values: List[List[float]],
        cell_size: int = 40,
        color_scheme: str = "primary",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("light")
        self._row_labels = row_labels
        self._col_labels = col_labels
        self._values = values
        self._cell_size = cell_size
        self._color_scheme = color_scheme
        self._cells: List[List[HeatMapCell]] = []

        # Calculate min/max for normalization
        flat_values = [v for row in values for v in row]
        self._min_val = min(flat_values) if flat_values else 0
        self._max_val = max(flat_values) if flat_values else 1

        self._setup_ui()

    def _setup_ui(self):
        """Build the grid UI"""
        self.setStyleSheet(f"""
            HeatMapGrid {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.md}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QGridLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(2)

        # Column headers
        for j, label in enumerate(self._col_labels):
            header = QLabel(label)
            header.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFixedWidth(self._cell_size)
            layout.addWidget(header, 0, j + 1)

        # Rows
        for i, row_label in enumerate(self._row_labels):
            # Row header
            header = QLabel(row_label)
            header.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(header, i + 1, 0)

            # Cells
            row_cells = []
            for j, value in enumerate(self._values[i]):
                cell = HeatMapCell(
                    value=value,
                    min_value=self._min_val,
                    max_value=self._max_val,
                    color_scheme=self._color_scheme,
                    size=self._cell_size,
                    colors=self._colors
                )
                cell.clicked.connect(lambda v, r=i, c=j: self.cell_clicked.emit(r, c, v))
                layout.addWidget(cell, i + 1, j + 1)
                row_cells.append(cell)

            self._cells.append(row_cells)

    def set_value(self, row: int, col: int, value: float):
        """Update a single cell value"""
        if 0 <= row < len(self._cells) and 0 <= col < len(self._cells[row]):
            self._cells[row][col].set_value(value)

    def get_value(self, row: int, col: int) -> float:
        """Get a cell value"""
        if 0 <= row < len(self._cells) and 0 <= col < len(self._cells[row]):
            return self._cells[row][col].value()
        return 0
