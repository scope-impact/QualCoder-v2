"""
Create Code Dialog

Dialog for creating a new code with name and color selection.

Implements QC-028.01 Create New Code:
- AC #1: Enter code name
- AC #2: Select color for the code
- AC #3: Add description/memo (optional)
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
    QTextEdit,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)

# Preset colors for quick selection
PRESET_COLORS = [
    # Row 1: Reds and oranges
    "#F44336",
    "#E91E63",
    "#FF5722",
    "#FF9800",
    # Row 2: Yellows and greens
    "#FFEB3B",
    "#CDDC39",
    "#8BC34A",
    "#4CAF50",
    # Row 3: Blues and teals
    "#009688",
    "#00BCD4",
    "#03A9F4",
    "#2196F3",
    # Row 4: Purples and grays
    "#3F51B5",
    "#673AB7",
    "#9C27B0",
    "#607D8B",
]


class CreateCodeDialog(QDialog):
    """
    Dialog for creating a new code.

    Provides input for code name, color selection, and optional memo.

    Signals:
        code_created(str, str, str): Emitted when code is created (name, color, memo)
    """

    code_created = Signal(str, str, str)  # name, color, memo

    def __init__(
        self,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected_color = PRESET_COLORS[0]

        self.setWindowTitle("Create New Code")
        self.setModal(True)
        self.setMinimumSize(400, 380)
        self.setMaximumSize(500, 500)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg
        )
        content_layout.setSpacing(SPACING.lg)

        # Code name input
        name_label = QLabel("Code Name")
        name_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(name_label)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter code name...")
        self._name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_base}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._name_input.textChanged.connect(self._validate)
        content_layout.addWidget(self._name_input)

        # Color selection
        color_label = QLabel("Color")
        color_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(color_label)

        self._setup_color_grid(content_layout)

        # Memo input (optional)
        memo_label = QLabel("Description (optional)")
        memo_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(memo_label)

        self._memo_input = QTextEdit()
        self._memo_input.setPlaceholderText("Add a description for this code...")
        self._memo_input.setMaximumHeight(80)
        self._memo_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QTextEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        content_layout.addWidget(self._memo_input)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the dialog header."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Icon
        icon = Icon(
            "mdi6.label-outline",
            size=20,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(icon)

        # Title
        title_label = QLabel("Create New Code")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def _setup_color_grid(self, layout: QVBoxLayout):
        """Setup the color selection grid."""
        grid_frame = QFrame()
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(SPACING.xs)

        self._color_buttons: list[QPushButton] = []

        for i, color in enumerate(PRESET_COLORS):
            row = i // 4
            col = i % 4

            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("color", color)
            btn.setStyleSheet(self._get_color_button_style(color, selected=i == 0))
            btn.clicked.connect(
                lambda _checked, c=color, b=btn: self._on_color_click(c, b)
            )

            self._color_buttons.append(btn)
            grid_layout.addWidget(btn, row, col)

        layout.addWidget(grid_frame)

    def _get_color_button_style(self, color: str, selected: bool = False) -> str:
        """Get stylesheet for a color button."""
        border = (
            f"3px solid {self._colors.primary}" if selected else "2px solid transparent"
        )
        return f"""
            QPushButton {{
                background-color: {color};
                border: {border};
                border-radius: {RADIUS.md}px;
            }}
            QPushButton:hover {{
                border: 2px solid {self._colors.text_secondary};
            }}
        """

    def _on_color_click(self, color: str, button: QPushButton):
        """Handle color button click."""
        self._selected_color = color

        # Update button styles
        for btn in self._color_buttons:
            btn_color = btn.property("color")
            btn.setStyleSheet(
                self._get_color_button_style(btn_color, selected=btn == button)
            )

    def _setup_footer(self, layout: QVBoxLayout):
        """Setup the dialog footer with buttons."""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        footer_layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self._cancel_btn)

        # Create button
        self._create_btn = QPushButton("Create Code")
        self._create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._create_btn.setEnabled(False)
        self._create_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
            }}
        """)
        self._create_btn.clicked.connect(self._on_create)
        footer_layout.addWidget(self._create_btn)

        layout.addWidget(footer)

    def _validate(self):
        """Validate inputs and enable/disable create button."""
        name = self._name_input.text().strip()
        self._create_btn.setEnabled(len(name) > 0)

    def _on_create(self):
        """Handle create button click."""
        name = self._name_input.text().strip()
        memo = self._memo_input.toPlainText().strip()

        if name:
            self.code_created.emit(name, self._selected_color, memo)
            self.accept()

    def get_code_name(self) -> str:
        """Get the entered code name."""
        return self._name_input.text().strip()

    def get_code_color(self) -> str:
        """Get the selected color."""
        return self._selected_color

    def get_code_memo(self) -> str:
        """Get the entered memo."""
        return self._memo_input.toPlainText().strip()

    def set_code_name(self, name: str):
        """Pre-fill the code name (e.g., for in-vivo coding)."""
        self._name_input.setText(name)
        self._validate()

    def set_code_memo(self, memo: str):
        """
        Set the memo text.

        BLACK-BOX API: Allows setting memo without accessing private _memo_input.
        """
        self._memo_input.setPlainText(memo)
