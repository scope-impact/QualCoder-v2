"""
Create Category Dialog

Dialog for creating a new code category.

Implements QC-028.02 Organize Codes into Categories:
- AC #1: Enter category name
- AC #2: Select parent category (optional)
- AC #3: Add description/memo (optional)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
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


class CreateCategoryDialog(QDialog):
    """
    Dialog for creating a new code category.

    Provides input for category name, parent selection, and optional memo.

    Signals:
        category_created(str, int | None, str): Emitted when category is created
            (name, parent_id, memo)
    """

    category_created = Signal(str, object, str)  # name, parent_id (int|None), memo

    def __init__(
        self,
        existing_categories: list[dict] | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            existing_categories: List of existing categories for parent selection.
                Each dict should have 'id' and 'name' keys.
            colors: Color palette for styling
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._categories = existing_categories or []

        self.setWindowTitle("Create New Category")
        self.setModal(True)
        self.setMinimumSize(400, 320)
        self.setMaximumSize(500, 450)

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

        # Category name input
        name_label = QLabel("Category Name")
        name_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(name_label)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter category name...")
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

        # Parent category selection
        parent_label = QLabel("Parent Category (optional)")
        parent_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(parent_label)

        self._parent_combo = QComboBox()
        self._parent_combo.addItem("None (Top Level)", None)
        for cat in self._categories:
            self._parent_combo.addItem(cat["name"], cat["id"])
        self._parent_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QComboBox:focus {{
                border-color: {self._colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        content_layout.addWidget(self._parent_combo)

        # Memo input (optional)
        memo_label = QLabel("Description (optional)")
        memo_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(memo_label)

        self._memo_input = QTextEdit()
        self._memo_input.setPlaceholderText("Add a description for this category...")
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
            "mdi6.folder-plus-outline",
            size=20,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(icon)

        # Title
        title_label = QLabel("Create New Category")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

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
        self._create_btn = QPushButton("Create Category")
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
        parent_id = self._parent_combo.currentData()
        memo = self._memo_input.toPlainText().strip()

        if name:
            self.category_created.emit(name, parent_id, memo)
            self.accept()

    # =========================================================================
    # Public API for black-box testing
    # =========================================================================

    def get_category_name(self) -> str:
        """Get the entered category name."""
        return self._name_input.text().strip()

    def set_category_name(self, name: str) -> None:
        """Set the category name."""
        self._name_input.setText(name)
        self._validate()

    def get_parent_id(self) -> int | None:
        """Get the selected parent category ID."""
        return self._parent_combo.currentData()

    def set_parent_id(self, parent_id: int | None) -> None:
        """Set the parent category by ID."""
        for i in range(self._parent_combo.count()):
            if self._parent_combo.itemData(i) == parent_id:
                self._parent_combo.setCurrentIndex(i)
                return

    def get_category_memo(self) -> str:
        """Get the entered memo."""
        return self._memo_input.toPlainText().strip()

    def set_category_memo(self, memo: str) -> None:
        """Set the memo text."""
        self._memo_input.setPlainText(memo)

    def get_parent_options_count(self) -> int:
        """Get the number of parent category options."""
        return self._parent_combo.count()
