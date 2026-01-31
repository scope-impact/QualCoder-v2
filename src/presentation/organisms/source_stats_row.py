"""
Source Stats Row Organism

Displays a row of clickable stat cards showing source counts by type.
Clicking a card filters the source table to that type.

Based on UX-003 from UX_TECH_DEBT.md:
- Cards are actionable (clicking filters table)
- Visual feedback when filter active
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from design_system import ColorPalette, get_colors
from design_system.icons import Icon
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY


class SourceStatCard(QFrame):
    """
    Clickable stat card for a source type.

    Displays count and label with type-specific icon and color.
    Clicking emits a signal for filtering.

    Signals:
        clicked(str): Emitted when card is clicked, with source_type
    """

    clicked = Signal(str)

    # Type-specific styling
    TYPE_CONFIG = {
        "text": {
            "icon": "mdi6.file-document-outline",
            "label": "Text Documents",
            "color_attr": "file_text",
        },
        "audio": {
            "icon": "mdi6.music-note",
            "label": "Audio Files",
            "color_attr": "file_audio",
        },
        "video": {
            "icon": "mdi6.video-outline",
            "label": "Video Files",
            "color_attr": "file_video",
        },
        "image": {
            "icon": "mdi6.image-outline",
            "label": "Images",
            "color_attr": "file_image",
        },
        "pdf": {
            "icon": "mdi6.file-pdf-box",
            "label": "PDF Documents",
            "color_attr": "file_pdf",
        },
    }

    def __init__(
        self,
        source_type: str,
        count: int = 0,
        active: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._source_type = source_type
        self._count = count
        self._active = active

        config = self.TYPE_CONFIG.get(source_type, self.TYPE_CONFIG["text"])
        self._icon_name = config["icon"]
        self._label_text = config["label"]
        self._accent_color = getattr(self._colors, config["color_attr"])

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        """Build the card UI."""
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Icon container with colored background
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            background-color: {self._hex_with_alpha(self._accent_color, 0.2)};
            border-radius: {RADIUS.md}px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = Icon(
            self._icon_name, size=24, color=self._accent_color, colors=self._colors
        )
        icon_layout.addWidget(self._icon)
        layout.addWidget(icon_frame)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self._count_label = QLabel(str(self._count))
        self._count_label.setStyleSheet(f"""
            font-family: {TYPOGRAPHY.font_family_display};
            color: {self._colors.text_primary};
            font-size: 24px;
            font-weight: {TYPOGRAPHY.weight_bold};
        """)
        info_layout.addWidget(self._count_label)

        self._type_label = QLabel(self._label_text)
        self._type_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        info_layout.addWidget(self._type_label)

        layout.addLayout(info_layout)
        layout.addStretch()

    def _hex_with_alpha(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string."""
        color = QColor(hex_color)
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"

    def _update_style(self):
        """Update card styling based on active state."""
        if self._active:
            border = f"2px solid {self._accent_color}"
            bg = self._hex_with_alpha(self._accent_color, 0.05)
        else:
            border = f"1px solid {self._colors.border}"
            bg = self._colors.surface

        self.setStyleSheet(f"""
            SourceStatCard {{
                background-color: {bg};
                border-radius: {RADIUS.lg}px;
                border: {border};
            }}
            SourceStatCard:hover {{
                background-color: {self._hex_with_alpha(self._accent_color, 0.08)};
            }}
        """)

    def set_count(self, count: int):
        """Update the count display."""
        self._count = count
        self._count_label.setText(str(count))

    def set_active(self, active: bool):
        """Set the active/filter state."""
        self._active = active
        self._update_style()

    def is_active(self) -> bool:
        """Check if card is in active/filter state."""
        return self._active

    def source_type(self) -> str:
        """Get the source type this card represents."""
        return self._source_type

    def mousePressEvent(self, event):
        """Handle click to emit filter signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._source_type)


class SourceStatsRow(QFrame):
    """
    Row of source stat cards for filtering by type.

    Displays counts for each source type and allows filtering
    by clicking cards. Only one filter can be active at a time.

    Signals:
        filter_changed(str | None): Emitted when filter changes.
            None means no filter (show all).
    """

    filter_changed = Signal(object)  # str | None

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._cards: dict[str, SourceStatCard] = {}
        self._active_filter: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        """Build the stats row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.lg)

        # Create cards for each type
        for source_type in ["text", "audio", "video", "image", "pdf"]:
            card = SourceStatCard(source_type=source_type, count=0, colors=self._colors)
            card.clicked.connect(self._on_card_clicked)
            self._cards[source_type] = card
            layout.addWidget(card)

    def _on_card_clicked(self, source_type: str):
        """Handle card click - toggle filter."""
        if self._active_filter == source_type:
            # Clear filter
            self._active_filter = None
            self._cards[source_type].set_active(False)
        else:
            # Set new filter
            if self._active_filter:
                self._cards[self._active_filter].set_active(False)
            self._active_filter = source_type
            self._cards[source_type].set_active(True)

        self.filter_changed.emit(self._active_filter)

    def set_counts(
        self,
        text_count: int = 0,
        audio_count: int = 0,
        video_count: int = 0,
        image_count: int = 0,
        pdf_count: int = 0,
    ):
        """Set all counts at once."""
        self._cards["text"].set_count(text_count)
        self._cards["audio"].set_count(audio_count)
        self._cards["video"].set_count(video_count)
        self._cards["image"].set_count(image_count)
        self._cards["pdf"].set_count(pdf_count)

    def set_count(self, source_type: str, count: int):
        """Set count for a specific type."""
        if source_type in self._cards:
            self._cards[source_type].set_count(count)

    def clear_filter(self):
        """Clear any active filter."""
        if self._active_filter:
            self._cards[self._active_filter].set_active(False)
            self._active_filter = None
            self.filter_changed.emit(None)

    def active_filter(self) -> str | None:
        """Get the currently active filter type."""
        return self._active_filter
