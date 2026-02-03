"""
Delete Code Dialog

Confirmation dialog for deleting a code from the codebook.

Implements QC-028.06 Delete Codes:
- AC #1: Show confirmation with code details
- AC #2: Option to delete associated segments
- AC #3: Warn about segment count
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
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


class DeleteCodeDialog(QDialog):
    """
    Confirmation dialog for deleting a code.

    Shows code details and offers option to delete associated segments.

    Signals:
        delete_confirmed(int, bool): Emitted when deletion is confirmed
            (code_id, delete_segments)
    """

    delete_confirmed = Signal(int, bool)  # code_id, delete_segments

    def __init__(
        self,
        code_id: int,
        code_name: str,
        code_color: str,
        segment_count: int,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            code_id: ID of the code to delete
            code_name: Name of the code
            code_color: Hex color of the code
            segment_count: Number of segments using this code
            colors: Color palette for styling
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._code_id = code_id
        self._code_name = code_name
        self._code_color = code_color
        self._segment_count = segment_count

        self.setWindowTitle("Delete Code")
        self.setModal(True)
        self.setMinimumSize(400, 280)
        self.setMaximumSize(500, 400)

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

        # Warning message
        warning_label = QLabel(
            f"Are you sure you want to delete the code <b>{self._code_name}</b>?"
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_base}px;
        """)
        content_layout.addWidget(warning_label)

        # Code preview
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)
        preview_layout = QHBoxLayout(preview_frame)
        preview_layout.setContentsMargins(
            SPACING.md, SPACING.md, SPACING.md, SPACING.md
        )

        # Color swatch
        swatch = QFrame()
        swatch.setFixedSize(24, 24)
        swatch.setStyleSheet(f"""
            QFrame {{
                background-color: {self._code_color};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        preview_layout.addWidget(swatch)

        # Code name
        name_label = QLabel(self._code_name)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        preview_layout.addWidget(name_label, 1)

        content_layout.addWidget(preview_frame)

        # Segment warning
        if self._segment_count > 0:
            warning_box = QFrame()
            warning_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.warning}15;
                    border: 1px solid {self._colors.warning};
                    border-radius: {RADIUS.md}px;
                }}
            """)
            warning_box_layout = QVBoxLayout(warning_box)
            warning_box_layout.setContentsMargins(
                SPACING.md, SPACING.md, SPACING.md, SPACING.md
            )

            segment_warning = QLabel(
                f"⚠️ This code has <b>{self._segment_count}</b> "
                f"segment{'s' if self._segment_count != 1 else ''} attached."
            )
            segment_warning.setWordWrap(True)
            segment_warning.setStyleSheet(f"""
                color: {self._colors.warning};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            warning_box_layout.addWidget(segment_warning)

            # Delete segments checkbox
            self._delete_segments_checkbox = QCheckBox("Also delete all segments")
            self._delete_segments_checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
            """)
            warning_box_layout.addWidget(self._delete_segments_checkbox)

            content_layout.addWidget(warning_box)
        else:
            self._delete_segments_checkbox = None
            no_segments = QLabel("This code has no segments attached.")
            no_segments.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            content_layout.addWidget(no_segments)

        content_layout.addStretch()

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the dialog header."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.error}15;
                border-bottom: 1px solid {self._colors.error};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Icon
        icon = Icon(
            "mdi6.delete-outline",
            size=20,
            color=self._colors.error,
            colors=self._colors,
        )
        header_layout.addWidget(icon)

        # Title
        title_label = QLabel("Delete Code")
        title_label.setStyleSheet(f"""
            color: {self._colors.error};
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

        # Delete button
        self._delete_btn = QPushButton("Delete Code")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.error};
                color: white;
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.error}dd;
            }}
        """)
        self._delete_btn.clicked.connect(self._on_delete)
        footer_layout.addWidget(self._delete_btn)

        layout.addWidget(footer)

    def _on_delete(self):
        """Handle delete button click."""
        delete_segments = (
            self._delete_segments_checkbox.isChecked()
            if self._delete_segments_checkbox
            else False
        )
        self.delete_confirmed.emit(self._code_id, delete_segments)
        self.accept()

    # =========================================================================
    # Public API for black-box testing
    # =========================================================================

    def get_code_id(self) -> int:
        """Get the ID of the code being deleted."""
        return self._code_id

    def get_code_name(self) -> str:
        """Get the name of the code being deleted."""
        return self._code_name

    def get_segment_count(self) -> int:
        """Get the segment count displayed in the dialog."""
        return self._segment_count

    def is_delete_segments_checked(self) -> bool:
        """Check if the 'delete segments' checkbox is checked."""
        if self._delete_segments_checkbox:
            return self._delete_segments_checkbox.isChecked()
        return False

    def set_delete_segments(self, checked: bool) -> None:
        """Set the 'delete segments' checkbox state."""
        if self._delete_segments_checkbox:
            self._delete_segments_checkbox.setChecked(checked)

    def confirm_delete(self) -> None:
        """
        Programmatically confirm deletion.

        BLACK-BOX API: Triggers deletion as if user clicked the delete button.
        """
        self._on_delete()

    def has_segment_warning(self) -> bool:
        """Check if the dialog shows a segment warning."""
        return self._delete_segments_checkbox is not None
