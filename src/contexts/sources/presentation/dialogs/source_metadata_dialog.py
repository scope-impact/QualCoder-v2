"""
Source Metadata Dialog

Implements QC-027.06 View Source Metadata:
- AC #1: Display file name, type, size, and date
- AC #2: Edit memo/notes for a source
- AC #3: Display coding statistics
- AC #4: Edit source properties
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
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


@dataclass(frozen=True)
class SourceMetadata:
    """Data for source metadata dialog."""

    id: str
    name: str
    source_type: str
    status: str
    file_size: int
    code_count: int
    memo: str | None = None
    origin: str | None = None
    modified_at: str | None = None


class SourceMetadataDialog(QDialog):
    """
    Dialog for viewing and editing source metadata.

    Displays source information and allows editing memo and origin fields.

    Signals:
        save_clicked(SourceMetadata): Emitted with updated metadata on save
        cancel_clicked(): Emitted when dialog is cancelled
    """

    save_clicked = Signal(object)  # SourceMetadata
    cancel_clicked = Signal()

    def __init__(
        self,
        metadata: SourceMetadata,
        colors: ColorPalette | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._metadata = metadata

        self.setWindowTitle(f"Source: {metadata.name}")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self._setup_ui()
        self._connect_signals()

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

        # Content
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
        content_layout.setSpacing(SPACING.md)

        # File info section (AC #1)
        self._setup_file_info(content_layout)

        # Coding stats section (AC #3)
        self._setup_coding_stats(content_layout)

        # Editable fields (AC #2, #4)
        self._setup_editable_fields(content_layout)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, parent_layout: QVBoxLayout):
        """Create dialog header with title and close button."""
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, 0, SPACING.md, 0)

        # Icon based on source type
        icon_name = self._get_type_icon()
        icon_color = self._get_type_color()
        icon = Icon(icon_name, size=24, color=icon_color)

        # Title
        title = QLabel(self._metadata.name)
        title.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_lg}px;
                font-weight: {TYPOGRAPHY.weight_bold};
            }}
        """)

        # Type badge
        type_badge = QLabel(self._metadata.source_type.upper())
        type_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {icon_color}20;
                color: {icon_color};
                padding: 4px 8px;
                border-radius: {RADIUS.sm}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
        """)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(type_badge)

        parent_layout.addWidget(header)

    def _setup_file_info(self, parent_layout: QVBoxLayout):
        """Create file information section (AC #1)."""
        section = self._create_section("File Information")

        form = QFormLayout()
        form.setSpacing(SPACING.sm)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # File size
        size_label = self._create_value_label(
            self._format_size(self._metadata.file_size)
        )
        form.addRow(self._create_field_label("Size:"), size_label)

        # Type
        type_label = self._create_value_label(self._metadata.source_type.capitalize())
        form.addRow(self._create_field_label("Type:"), type_label)

        # Status
        status_label = self._create_value_label(
            self._metadata.status.replace("_", " ").title()
        )
        form.addRow(self._create_field_label("Status:"), status_label)

        # Modified date
        modified = self._metadata.modified_at or "Unknown"
        modified_label = self._create_value_label(modified)
        form.addRow(self._create_field_label("Modified:"), modified_label)

        section.layout().addLayout(form)
        parent_layout.addWidget(section)

    def _setup_coding_stats(self, parent_layout: QVBoxLayout):
        """Create coding statistics section (AC #3)."""
        section = self._create_section("Coding Statistics")

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(SPACING.lg)

        # Code count stat
        code_stat = self._create_stat_card(
            str(self._metadata.code_count),
            "Coded Segments",
            self._colors.primary,
        )
        stats_layout.addWidget(code_stat)

        # Status indicator
        status_color = self._get_status_color()
        status_stat = self._create_stat_card(
            self._metadata.status.replace("_", " ").title(),
            "Current Status",
            status_color,
        )
        stats_layout.addWidget(status_stat)

        section.layout().addLayout(stats_layout)
        parent_layout.addWidget(section)

    def _setup_editable_fields(self, parent_layout: QVBoxLayout):
        """Create editable fields section (AC #2, #4)."""
        section = self._create_section("Properties")

        form = QFormLayout()
        form.setSpacing(SPACING.sm)

        # Origin field (AC #4)
        self._origin_input = QLineEdit()
        self._origin_input.setText(self._metadata.origin or "")
        self._origin_input.setPlaceholderText("e.g., Interview, Survey, Document")
        self._origin_input.setStyleSheet(self._input_style())
        form.addRow(self._create_field_label("Origin:"), self._origin_input)

        section.layout().addLayout(form)

        # Memo field (AC #2)
        memo_label = self._create_field_label("Memo / Notes:")
        section.layout().addWidget(memo_label)

        self._memo_input = QTextEdit()
        self._memo_input.setText(self._metadata.memo or "")
        self._memo_input.setPlaceholderText("Add notes about this source...")
        self._memo_input.setMinimumHeight(100)
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
        section.layout().addWidget(self._memo_input)

        parent_layout.addWidget(section, 1)

    def _setup_footer(self, parent_layout: QVBoxLayout):
        """Create footer with action buttons."""
        footer = QFrame()
        footer.setFixedHeight(64)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)

        footer_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._button_style(secondary=True))
        cancel_btn.clicked.connect(self._on_cancel)
        footer_layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet(self._button_style())
        save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(save_btn)

        parent_layout.addWidget(footer)

    def _connect_signals(self):
        """Connect internal signals."""
        pass

    def _on_save(self):
        """Handle save button click."""
        updated = SourceMetadata(
            id=self._metadata.id,
            name=self._metadata.name,
            source_type=self._metadata.source_type,
            status=self._metadata.status,
            file_size=self._metadata.file_size,
            code_count=self._metadata.code_count,
            memo=self._memo_input.toPlainText() or None,
            origin=self._origin_input.text() or None,
            modified_at=self._metadata.modified_at,
        )
        self.save_clicked.emit(updated)
        self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_clicked.emit()
        self.reject()

    # Helper methods

    def _create_section(self, title: str) -> QFrame:
        """Create a styled section with title."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_bold};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """)
        layout.addWidget(title_label)

        return section

    def _create_field_label(self, text: str) -> QLabel:
        """Create a field label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        return label

    def _create_value_label(self, text: str) -> QLabel:
        """Create a value label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
        """)
        return label

    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """Create a statistics card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}10;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.md}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {TYPOGRAPHY.text_xl}px;
                font-weight: {TYPOGRAPHY.weight_bold};
            }}
        """)

        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_widget.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
        """)

        layout.addWidget(value_label)
        layout.addWidget(label_widget)

        return card

    def _input_style(self) -> str:
        """Return stylesheet for input fields."""
        return f"""
            QLineEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """

    def _button_style(self, secondary: bool = False) -> str:
        """Return stylesheet for buttons."""
        if secondary:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: white;
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """

    def _get_type_icon(self) -> str:
        """Get icon name for source type."""
        icons = {
            "text": "mdi6.file-document-outline",
            "audio": "mdi6.file-music-outline",
            "video": "mdi6.file-video-outline",
            "image": "mdi6.file-image-outline",
            "pdf": "mdi6.file-pdf-box",
        }
        return icons.get(self._metadata.source_type, "mdi6.file-outline")

    def _get_type_color(self) -> str:
        """Get color for source type."""
        colors = {
            "text": self._colors.file_text,
            "audio": self._colors.file_audio,
            "video": self._colors.file_video,
            "image": self._colors.file_image,
            "pdf": self._colors.file_pdf,
        }
        return colors.get(self._metadata.source_type, self._colors.text_secondary)

    def _get_status_color(self) -> str:
        """Get color for status."""
        status_colors = {
            "imported": self._colors.info,
            "ready": self._colors.success,
            "in_progress": self._colors.warning,
            "coded": self._colors.success,
            "transcribing": self._colors.info,
            "error": self._colors.error,
        }
        return status_colors.get(self._metadata.status, self._colors.text_secondary)

    def _format_size(self, size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
