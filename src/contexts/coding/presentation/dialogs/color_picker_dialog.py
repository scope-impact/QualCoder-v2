"""
Color Picker Dialog

Implements QC-007.03 AC #15: Change code color (color picker dialog)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    ColorSwatch,
    get_colors,
)

# Preset colors for qualitative coding
PRESET_COLORS = [
    # Row 1 - Reds/Oranges
    "#F44336",
    "#E91E63",
    "#FF5722",
    "#FF9800",
    "#FFC107",
    # Row 2 - Yellows/Greens
    "#FFEB3B",
    "#CDDC39",
    "#8BC34A",
    "#4CAF50",
    "#009688",
    # Row 3 - Blues/Purples
    "#00BCD4",
    "#03A9F4",
    "#2196F3",
    "#3F51B5",
    "#673AB7",
    # Row 4 - Purples/Grays
    "#9C27B0",
    "#E040FB",
    "#795548",
    "#9E9E9E",
    "#607D8B",
]


class ColorPickerDialog(QDialog):
    """
    Color picker dialog for selecting code colors.

    Features:
    - Preset color swatches
    - Custom color input (hex)
    - Preview of selected color

    Signals:
        color_selected(str): Emitted when color is confirmed
    """

    color_selected = Signal(str)

    def __init__(
        self,
        initial_color: str = "#4CAF50",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected_color = initial_color
        self._swatches: list[ColorSwatch] = []

        self.setWindowTitle("Choose Color")
        self.setModal(True)
        self.setMinimumSize(350, 300)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Title
        title = QLabel("Select a Color")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        layout.addWidget(title)

        # Preset colors grid
        presets_label = QLabel("Preset Colors")
        presets_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(presets_label)

        grid = QGridLayout()
        grid.setSpacing(SPACING.sm)

        for i, color in enumerate(PRESET_COLORS):
            swatch = ColorSwatch(color, size=36, colors=self._colors)
            swatch.clicked.connect(self._on_swatch_clicked)
            if color.upper() == self._selected_color.upper():
                swatch.set_selected(True)
            self._swatches.append(swatch)
            grid.addWidget(swatch, i // 5, i % 5)

        layout.addLayout(grid)

        # Custom color input
        custom_label = QLabel("Custom Color (Hex)")
        custom_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(custom_label)

        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(SPACING.sm)

        self._color_input = QLineEdit()
        self._color_input.setPlaceholderText("#RRGGBB")
        self._color_input.setText(self._selected_color)
        self._color_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-family: monospace;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._color_input.textChanged.connect(self._on_input_changed)
        custom_layout.addWidget(self._color_input, 1)

        # Preview swatch
        self._preview = QFrame()
        self._preview.setFixedSize(36, 36)
        self._preview.setStyleSheet(f"""
            QFrame {{
                background-color: {self._selected_color};
                border: 1px solid rgba(0,0,0,0.2);
                border-radius: {RADIUS.sm}px;
            }}
        """)
        custom_layout.addWidget(self._preview)

        layout.addLayout(custom_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Select")
        select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def _on_swatch_clicked(self, color: str):
        """Handle swatch click."""
        self._selected_color = color
        self._color_input.setText(color)
        self._update_selection()

    def _on_input_changed(self, text: str):
        """Handle custom color input."""
        if self._is_valid_hex(text):
            self._selected_color = text
            self._update_selection()

    def _is_valid_hex(self, text: str) -> bool:
        """Check if text is a valid hex color."""
        if not text.startswith("#") or len(text) != 7:
            return False
        try:
            int(text[1:], 16)
            return True
        except ValueError:
            return False

    def _update_selection(self):
        """Update the visual selection state."""
        # Update swatches
        for swatch in self._swatches:
            swatch.set_selected(
                swatch.get_color().upper() == self._selected_color.upper()
            )

        # Update preview
        self._preview.setStyleSheet(f"""
            QFrame {{
                background-color: {self._selected_color};
                border: 1px solid rgba(0,0,0,0.2);
                border-radius: {RADIUS.sm}px;
            }}
        """)

    def _on_select(self):
        """Handle select button click."""
        self.color_selected.emit(self._selected_color)
        self.accept()

    def get_selected_color(self) -> str:
        """Get the currently selected color."""
        return self._selected_color

    def select_color(self, color: str):
        """Programmatically select a color."""
        self._selected_color = color
        self._color_input.setText(color)
        self._update_selection()
        self.color_selected.emit(color)

    def get_preset_count(self) -> int:
        """Get the number of preset colors."""
        return len(PRESET_COLORS)
