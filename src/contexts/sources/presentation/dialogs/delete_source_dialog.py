"""
Delete Source Confirmation Dialog

Implements QC-027.07 Delete Source:
- AC #2: Warn about losing coded segments
- AC #3: Confirm deletion intent
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class DeleteSourceInfo:
    """Information about source to be deleted."""

    id: str
    name: str
    source_type: str
    code_count: int


class DeleteSourceDialog(QDialog):
    """
    Confirmation dialog for deleting sources.

    Shows warning about coded segments that will be lost.

    Signals:
        delete_confirmed(list[str]): Emitted with source IDs when deletion is confirmed
        cancel_clicked(): Emitted when dialog is cancelled
    """

    delete_confirmed = Signal(list)  # list of source IDs
    cancel_clicked = Signal()

    def __init__(
        self,
        sources: list[DeleteSourceInfo],
        colors: ColorPalette | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._sources = sources

        self.setWindowTitle("Delete Sources")
        self.setModal(True)
        self.setMinimumWidth(450)

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

        # Header with warning icon
        self._setup_header(layout)

        # Content
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg
        )
        content_layout.setSpacing(SPACING.md)

        # Warning message
        self._setup_warning(content_layout)

        # Source list
        self._setup_source_list(content_layout)

        # Confirmation checkbox
        self._setup_confirmation(content_layout)

        layout.addWidget(content_frame)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, parent_layout: QVBoxLayout):
        """Create dialog header with warning icon."""
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.error}15;
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)

        # Warning icon
        icon = Icon("mdi6.alert-circle", size=32, color=self._colors.error)

        # Title
        count = len(self._sources)
        title_text = f"Delete {count} source{'s' if count != 1 else ''}?"
        title = QLabel(title_text)
        title.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.error};
                font-size: {TYPOGRAPHY.text_lg}px;
                font-weight: {TYPOGRAPHY.weight_bold};
            }}
        """)

        header_layout.addWidget(icon)
        header_layout.addSpacing(SPACING.sm)
        header_layout.addWidget(title)
        header_layout.addStretch()

        parent_layout.addWidget(header)

    def _setup_warning(self, parent_layout: QVBoxLayout):
        """Create warning message about coded segments (AC #2)."""
        total_codes = sum(s.code_count for s in self._sources)

        if total_codes > 0:
            warning_frame = QFrame()
            warning_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.warning}15;
                    border: 1px solid {self._colors.warning}50;
                    border-radius: {RADIUS.md}px;
                }}
            """)

            warning_layout = QHBoxLayout(warning_frame)
            warning_layout.setContentsMargins(
                SPACING.md, SPACING.sm, SPACING.md, SPACING.sm
            )

            icon = Icon("mdi6.alert", size=20, color=self._colors.warning)

            text = QLabel(
                f"Warning: This will permanently delete {total_codes} coded segment{'s' if total_codes != 1 else ''}."
            )
            text.setWordWrap(True)
            text.setStyleSheet(f"""
                QLabel {{
                    color: {self._colors.text_primary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
            """)

            warning_layout.addWidget(icon)
            warning_layout.addSpacing(SPACING.sm)
            warning_layout.addWidget(text, 1)

            parent_layout.addWidget(warning_frame)

    def _setup_source_list(self, parent_layout: QVBoxLayout):
        """Create list of sources to be deleted."""
        label = QLabel("The following sources will be deleted:")
        label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        parent_layout.addWidget(label)

        list_frame = QFrame()
        list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        list_layout.setSpacing(4)

        # Show up to 5 sources, then summarize
        display_sources = self._sources[:5]
        for source in display_sources:
            row = self._create_source_row(source)
            list_layout.addWidget(row)

        if len(self._sources) > 5:
            more_label = QLabel(f"... and {len(self._sources) - 5} more")
            more_label.setStyleSheet(f"""
                QLabel {{
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_xs}px;
                    padding: 4px 8px;
                }}
            """)
            list_layout.addWidget(more_label)

        parent_layout.addWidget(list_frame)

    def _create_source_row(self, source: DeleteSourceInfo) -> QFrame:
        """Create a row showing source info."""
        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(SPACING.sm, 4, SPACING.sm, 4)
        row_layout.setSpacing(SPACING.sm)

        # Type icon
        icon_name = self._get_type_icon(source.source_type)
        icon_color = self._get_type_color(source.source_type)
        icon = Icon(icon_name, size=16, color=icon_color)
        row_layout.addWidget(icon)

        # Name
        name = QLabel(source.name)
        name.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        row_layout.addWidget(name, 1)

        # Code count badge
        if source.code_count > 0:
            badge = QLabel(f"{source.code_count} codes")
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {self._colors.warning}20;
                    color: {self._colors.warning};
                    padding: 2px 6px;
                    border-radius: {RADIUS.sm}px;
                    font-size: {TYPOGRAPHY.text_xs}px;
                }}
            """)
            row_layout.addWidget(badge)

        return row

    def _setup_confirmation(self, parent_layout: QVBoxLayout):
        """Create confirmation checkbox."""
        self._confirm_checkbox = QCheckBox("I understand this action cannot be undone")
        self._confirm_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                spacing: {SPACING.sm}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        self._confirm_checkbox.stateChanged.connect(self._on_confirm_changed)

        parent_layout.addWidget(self._confirm_checkbox)

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

        # Delete button
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)  # Disabled until confirmed
        self._delete_btn.setStyleSheet(self._delete_button_style())
        self._delete_btn.clicked.connect(self._on_delete)
        footer_layout.addWidget(self._delete_btn)

        parent_layout.addWidget(footer)

    def _on_confirm_changed(self, state: int):
        """Handle confirmation checkbox change."""
        self._delete_btn.setEnabled(state == Qt.CheckState.Checked.value)

    def _on_delete(self):
        """Handle delete button click."""
        source_ids = [s.id for s in self._sources]
        self.delete_confirmed.emit(source_ids)
        self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_clicked.emit()
        self.reject()

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

    def _delete_button_style(self) -> str:
        """Return stylesheet for delete button."""
        return f"""
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
                background-color: {self._colors.error};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {self._colors.border};
                color: {self._colors.text_secondary};
            }}
        """

    def _get_type_icon(self, source_type: str) -> str:
        """Get icon name for source type."""
        icons = {
            "text": "mdi6.file-document-outline",
            "audio": "mdi6.file-music-outline",
            "video": "mdi6.file-video-outline",
            "image": "mdi6.file-image-outline",
            "pdf": "mdi6.file-pdf-box",
        }
        return icons.get(source_type, "mdi6.file-outline")

    def _get_type_color(self, source_type: str) -> str:
        """Get color for source type."""
        colors = {
            "text": self._colors.file_text,
            "audio": self._colors.file_audio,
            "video": self._colors.file_video,
            "image": self._colors.file_image,
            "pdf": self._colors.file_pdf,
        }
        return colors.get(source_type, self._colors.text_secondary)
