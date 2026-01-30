"""
Selection/Picker components
Type selectors, color pickers, and option cards
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors, hex_to_rgba


class TypeSelector(QFrame):
    """
    Type/category selector with icon cards.

    Usage:
        selector = TypeSelector()
        selector.add_option("text", "mdi6.file-document", "Text", "Plain text files")
        selector.add_option("audio", "mdi6.music-note", "Audio", "MP3, WAV files")
        selector.selection_changed.connect(self.on_type_select)
    """

    selection_changed = Signal(str)  # type_id

    def __init__(
        self,
        columns: int = 3,
        multi_select: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._columns = columns
        self._multi_select = multi_select
        self._options = {}
        self._selected = set() if multi_select else None

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.md)

        self._row = 0
        self._col = 0

    def add_option(self, type_id: str, icon: str, title: str, description: str = ""):
        card = TypeOptionCard(
            icon=icon, title=title, description=description, colors=self._colors
        )
        card.clicked.connect(lambda: self._select(type_id))
        self._options[type_id] = card

        self._layout.addWidget(card, self._row, self._col)
        self._col += 1
        if self._col >= self._columns:
            self._col = 0
            self._row += 1

    def _select(self, type_id: str):
        if self._multi_select:
            if type_id in self._selected:
                self._selected.remove(type_id)
            else:
                self._selected.add(type_id)
        else:
            self._selected = type_id

        self._update_styles()
        self.selection_changed.emit(type_id)

    def _update_styles(self):
        for tid, card in self._options.items():
            if self._multi_select:
                card.setSelected(tid in self._selected)
            else:
                card.setSelected(tid == self._selected)

    def get_selected(self):
        if self._multi_select:
            return list(self._selected)
        return self._selected

    def set_selected(self, type_id):
        if self._multi_select:
            if isinstance(type_id, list):
                self._selected = set(type_id)
            else:
                self._selected.add(type_id)
        else:
            self._selected = type_id
        self._update_styles()


class TypeOptionCard(QFrame):
    """
    Individual type option card.

    Usage:
        card = TypeOptionCard("mdi6.file-document", "Text Files", "Import plain text")
        card.clicked.connect(self.select_type)
    """

    clicked = Signal()

    def __init__(
        self,
        icon: str,
        title: str,
        description: str = "",
        selected: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected = selected

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon - support both mdi6 icons and emoji fallback
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon.startswith("mdi6."):
            icon_label.setPixmap(
                qta.icon(icon, color=self._colors.primary).pixmap(32, 32)
            )
        else:
            icon_label.setText(icon)
            icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(title_label)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(desc_label)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {hex_to_rgba(self._colors.primary, 0.08)};
                    border: 2px solid {self._colors.primary};
                    border-radius: {RADIUS.lg}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border: 2px solid transparent;
                    border-radius: {RADIUS.lg}px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_lighter};
                    border-color: {self._colors.border};
                }}
            """)

    def setSelected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ColorSchemeSelector(QFrame):
    """
    Color scheme/palette selector.

    Usage:
        selector = ColorSchemeSelector()
        selector.add_scheme("warm", ["#C84B31", "#E9C46A", "#E76F51"])  # Vermilion palette
        selector.add_scheme("cool", ["#2A6F97", "#468FAF", "#1E3A5F"])  # Prussian ink palette
        selector.scheme_changed.connect(self.apply_scheme)
    """

    scheme_changed = Signal(str)  # scheme_id

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._schemes = {}
        self._selected = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.md)

    def add_scheme(self, scheme_id: str, color_list: list[str], name: str = ""):
        scheme = ColorSchemeOption(
            colors_list=color_list, name=name, palette=self._colors
        )
        scheme.clicked.connect(lambda: self._select(scheme_id))
        self._schemes[scheme_id] = scheme
        self._layout.addWidget(scheme)

    def _select(self, scheme_id: str):
        self._selected = scheme_id
        for sid, scheme in self._schemes.items():
            scheme.setSelected(sid == scheme_id)
        self.scheme_changed.emit(scheme_id)

    def get_selected(self) -> str | None:
        return self._selected

    def set_selected(self, scheme_id: str):
        if scheme_id in self._schemes:
            self._select(scheme_id)


class ColorSchemeOption(QFrame):
    """Individual color scheme option"""

    clicked = Signal()

    def __init__(
        self,
        colors_list: list[str],
        name: str = "",
        selected: bool = False,
        palette: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._palette = palette or get_colors()
        self._selected = selected

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Color swatches
        swatches = QHBoxLayout()
        swatches.setSpacing(2)
        for color in colors_list:
            swatch = QFrame()
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(f"""
                background-color: {color};
                border-radius: 4px;
            """)
            swatches.addWidget(swatch)
        layout.addLayout(swatches)

        # Name
        if name:
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet(f"""
                color: {self._palette.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(name_label)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._palette.surface_light};
                    border: 2px solid {self._palette.primary};
                    border-radius: {RADIUS.md}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: 2px solid transparent;
                    border-radius: {RADIUS.md}px;
                }}
                QFrame:hover {{
                    background-color: {self._palette.surface_light};
                }}
            """)

    def setSelected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ChartTypeSelector(QFrame):
    """
    Chart type selector for reports.

    Usage:
        selector = ChartTypeSelector()
        selector.chart_changed.connect(self.update_chart)
    """

    chart_changed = Signal(str)

    CHART_TYPES = [
        ("bar", "mdi6.chart-bar", "Bar Chart"),
        ("line", "mdi6.chart-line", "Line Chart"),
        ("pie", "mdi6.chart-pie", "Pie Chart"),
        ("scatter", "mdi6.chart-scatter-plot", "Scatter Plot"),
        ("area", "mdi6.chart-areaspline", "Area Chart"),
        ("heatmap", "mdi6.grid", "Heat Map"),
    ]

    def __init__(
        self,
        available: list[str] = None,
        current: str = "bar",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._available = available or [t[0] for t in self.CHART_TYPES]
        self._current = current
        self._buttons = {}

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        for chart_id, icon_name, tooltip in self.CHART_TYPES:
            if chart_id in self._available:
                btn = QPushButton()
                btn.setIcon(qta.icon(icon_name, color=self._colors.text_secondary))
                btn.setIconSize(btn.sizeHint())
                btn.setFixedSize(36, 36)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip(tooltip)
                btn.clicked.connect(lambda _checked, c=chart_id: self._select(c))
                self._buttons[chart_id] = (btn, icon_name)
                layout.addWidget(btn)

        self._update_styles()

    def _select(self, chart_type: str):
        if chart_type != self._current:
            self._current = chart_type
            self._update_styles()
            self.chart_changed.emit(chart_type)

    def _update_styles(self):
        for chart_id, (btn, icon_name) in self._buttons.items():
            if chart_id == self._current:
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

    def set_chart_type(self, chart_type: str):
        if chart_type in self._available:
            self._current = chart_type
            self._update_styles()

    def current_type(self) -> str:
        return self._current


class RadioCardGroup(QFrame):
    """
    Radio-style selection with cards.

    Usage:
        group = RadioCardGroup()
        group.add_card("opt1", "Option 1", "Description for option 1")
        group.add_card("opt2", "Option 2", "Description for option 2")
        group.selection_changed.connect(self.on_select)
    """

    selection_changed = Signal(str)

    def __init__(
        self,
        orientation: str = "vertical",  # "vertical" or "horizontal"
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._cards = {}
        self._selected = None

        if orientation == "horizontal":
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.sm)

    def add_card(
        self, card_id: str, title: str, description: str = "", icon: str = None
    ):
        card = RadioCard(
            title=title, description=description, icon=icon, colors=self._colors
        )
        card.clicked.connect(lambda: self._select(card_id))
        self._cards[card_id] = card
        self._layout.addWidget(card)

    def _select(self, card_id: str):
        self._selected = card_id
        for cid, card in self._cards.items():
            card.setSelected(cid == card_id)
        self.selection_changed.emit(card_id)

    def get_selected(self) -> str | None:
        return self._selected

    def set_selected(self, card_id: str):
        if card_id in self._cards:
            self._select(card_id)


class RadioCard(QFrame):
    """Individual radio card option"""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        description: str = "",
        icon: str = None,
        selected: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected = selected

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.md)

        # Radio indicator
        self._indicator = QFrame()
        self._indicator.setFixedSize(20, 20)
        self._update_indicator()
        layout.addWidget(self._indicator)

        # Content
        content = QVBoxLayout()
        content.setSpacing(SPACING.xs)

        header = QHBoxLayout()
        if icon:
            icon_label = QLabel()
            if icon.startswith("mdi6."):
                icon_label.setPixmap(
                    qta.icon(icon, color=self._colors.text_primary).pixmap(16, 16)
                )
            else:
                icon_label.setText(icon)
                icon_label.setStyleSheet("font-size: 16px;")
            header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header.addWidget(title_label)
        header.addStretch()
        content.addLayout(header)

        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            content.addWidget(desc_label)

        layout.addLayout(content, 1)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {hex_to_rgba(self._colors.primary, 0.08)};
                    border: 2px solid {self._colors.primary};
                    border-radius: {RADIUS.md}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border: 2px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                }}
                QFrame:hover {{
                    border-color: {self._colors.primary};
                }}
            """)

    def _update_indicator(self):
        if self._selected:
            self._indicator.setStyleSheet(f"""
                background-color: {self._colors.primary};
                border: 2px solid {self._colors.primary};
                border-radius: 10px;
            """)
        else:
            self._indicator.setStyleSheet(f"""
                background-color: transparent;
                border: 2px solid {self._colors.border};
                border-radius: 10px;
            """)

    def setSelected(self, selected: bool):
        self._selected = selected
        self._update_style()
        self._update_indicator()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
