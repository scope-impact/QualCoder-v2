"""
Image Viewer Component

Implements QC-027.03 Import Image Files:
- AC #2: Images are displayed in the viewer
- Supports zoom, pan, and fit-to-window

Also supports QC-027.04 for image metadata display.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)


class ImageViewer(QWidget):
    """
    Widget for viewing image files with zoom and pan support.

    Features:
    - Fit to window or actual size display
    - Zoom in/out with mouse wheel
    - Pan with click and drag
    - Image metadata display

    Signals:
        image_loaded(str): Emitted when an image is successfully loaded
        load_failed(str): Emitted when image loading fails
    """

    image_loaded = Signal(str)  # file path
    load_failed = Signal(str)  # error message

    MIN_ZOOM = 0.1
    MAX_ZOOM = 5.0
    ZOOM_STEP = 0.1

    def __init__(
        self,
        colors: ColorPalette | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_path: Path | None = None
        self._zoom_level = 1.0
        self._fit_mode = True  # True = fit to window, False = actual size

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the viewer UI."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self._setup_toolbar(layout)

        # Image display area
        self._setup_image_area(layout)

        # Info bar
        self._setup_info_bar(layout)

    def _setup_toolbar(self, parent_layout: QVBoxLayout):
        """Create the toolbar with zoom controls."""
        toolbar = QFrame()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(SPACING.md, 0, SPACING.md, 0)
        toolbar_layout.setSpacing(SPACING.sm)

        # Fit to window button
        self._fit_btn = self._create_toolbar_button(
            "mdi6.fit-to-screen", "Fit to window"
        )
        self._fit_btn.setCheckable(True)
        self._fit_btn.setChecked(True)
        self._fit_btn.clicked.connect(self._on_fit_clicked)
        toolbar_layout.addWidget(self._fit_btn)

        # Actual size button
        self._actual_btn = self._create_toolbar_button(
            "mdi6.image-size-select-actual", "Actual size"
        )
        self._actual_btn.clicked.connect(self._on_actual_size_clicked)
        toolbar_layout.addWidget(self._actual_btn)

        toolbar_layout.addSpacing(SPACING.md)

        # Zoom out
        zoom_out_btn = self._create_toolbar_button("mdi6.minus", "Zoom out")
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)

        # Zoom level display
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(60)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
        """)
        toolbar_layout.addWidget(self._zoom_label)

        # Zoom in
        zoom_in_btn = self._create_toolbar_button("mdi6.plus", "Zoom in")
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)

        toolbar_layout.addStretch()

        parent_layout.addWidget(toolbar)

    def _setup_image_area(self, parent_layout: QVBoxLayout):
        """Create the scrollable image display area."""
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors.surface};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self._colors.surface};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self._colors.border};
                border-radius: 4px;
            }}
            QScrollBar:horizontal {{
                background-color: {self._colors.surface};
                height: 8px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {self._colors.border};
                border-radius: 4px;
            }}
        """)

        # Image label
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)

        self._scroll_area.setWidget(self._image_label)
        parent_layout.addWidget(self._scroll_area, 1)

    def _setup_info_bar(self, parent_layout: QVBoxLayout):
        """Create the info bar showing image metadata."""
        self._info_bar = QFrame()
        self._info_bar.setFixedHeight(32)
        self._info_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        info_layout = QHBoxLayout(self._info_bar)
        info_layout.setContentsMargins(SPACING.md, 0, SPACING.md, 0)

        self._info_label = QLabel("No image loaded")
        self._info_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
        """)
        info_layout.addWidget(self._info_label)

        info_layout.addStretch()

        parent_layout.addWidget(self._info_bar)

    def _create_toolbar_button(self, icon_name: str, tooltip: str) -> QPushButton:
        """Create a toolbar button."""
        btn = QPushButton()
        btn.setFixedSize(32, 32)
        btn.setToolTip(tooltip)
        btn.setIcon(Icon(icon_name, size=18, color=self._colors.text_secondary))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface};
            }}
            QPushButton:checked {{
                background-color: {self._colors.primary}20;
            }}
        """)
        return btn

    def _connect_signals(self):
        """Connect internal signals."""
        pass

    # Public API

    def load_image(self, path: str | Path):
        """
        Load and display an image file.

        Args:
            path: Path to the image file
        """
        path = Path(path)
        if not path.exists():
            self.load_failed.emit(f"File not found: {path}")
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.load_failed.emit(f"Failed to load image: {path}")
            return

        self._current_path = path
        self._original_pixmap = pixmap
        self._zoom_level = 1.0

        if self._fit_mode:
            self._fit_to_window()
        else:
            self._show_actual_size()

        # Update info bar (AC #4 metadata)
        self._update_info(pixmap)
        self.image_loaded.emit(str(path))

    def clear(self):
        """Clear the current image."""
        self._image_label.clear()
        self._current_path = None
        self._info_label.setText("No image loaded")

    def get_current_path(self) -> Path | None:
        """Get the path of the currently displayed image."""
        return self._current_path

    # Internal methods

    def _fit_to_window(self):
        """Scale image to fit the viewport."""
        if not hasattr(self, "_original_pixmap"):
            return

        viewport_size = self._scroll_area.viewport().size()
        scaled = self._original_pixmap.scaled(
            viewport_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._zoom_level = scaled.width() / self._original_pixmap.width()
        self._update_zoom_label()

    def _show_actual_size(self):
        """Show image at actual size (100%)."""
        if not hasattr(self, "_original_pixmap"):
            return

        self._image_label.setPixmap(self._original_pixmap)
        self._zoom_level = 1.0
        self._update_zoom_label()

    def _apply_zoom(self):
        """Apply the current zoom level."""
        if not hasattr(self, "_original_pixmap"):
            return

        new_size = self._original_pixmap.size() * self._zoom_level
        scaled = self._original_pixmap.scaled(
            new_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._update_zoom_label()

    def _update_zoom_label(self):
        """Update the zoom level display."""
        percent = int(self._zoom_level * 100)
        self._zoom_label.setText(f"{percent}%")

    def _update_info(self, pixmap: QPixmap):
        """Update the info bar with image metadata."""
        if self._current_path:
            size = self._current_path.stat().st_size
            size_str = self._format_size(size)
            dims = f"{pixmap.width()} x {pixmap.height()}"
            self._info_label.setText(f"{self._current_path.name} | {dims} | {size_str}")

    def _format_size(self, size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    # Event handlers

    def _on_fit_clicked(self):
        """Handle fit to window button click."""
        self._fit_mode = True
        self._fit_btn.setChecked(True)
        self._fit_to_window()

    def _on_actual_size_clicked(self):
        """Handle actual size button click."""
        self._fit_mode = False
        self._fit_btn.setChecked(False)
        self._show_actual_size()

    def _on_zoom_in(self):
        """Handle zoom in button click."""
        self._fit_mode = False
        self._fit_btn.setChecked(False)
        self._zoom_level = min(self.MAX_ZOOM, self._zoom_level + self.ZOOM_STEP)
        self._apply_zoom()

    def _on_zoom_out(self):
        """Handle zoom out button click."""
        self._fit_mode = False
        self._fit_btn.setChecked(False)
        self._zoom_level = max(self.MIN_ZOOM, self._zoom_level - self.ZOOM_STEP)
        self._apply_zoom()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._fit_mode = False
            self._fit_btn.setChecked(False)

            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_level = min(self.MAX_ZOOM, self._zoom_level + self.ZOOM_STEP)
            else:
                self._zoom_level = max(self.MIN_ZOOM, self._zoom_level - self.ZOOM_STEP)

            self._apply_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        """Handle resize to refit image if in fit mode."""
        super().resizeEvent(event)
        if self._fit_mode and hasattr(self, "_original_pixmap"):
            self._fit_to_window()
