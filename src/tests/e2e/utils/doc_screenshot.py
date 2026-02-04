"""Screenshot capture utility for documentation.

Provides consistent screenshot capture during E2E tests for use in
user documentation at docs/user-manual/images/.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

# Documentation images directory
DOCS_IMAGES_DIR = Path(__file__).parents[4] / "docs" / "user-manual" / "images"


class DocScreenshot:
    """Utility for capturing screenshots for documentation."""

    @staticmethod
    def capture(
        widget: QWidget,
        name: str,
        *,
        attach_to_allure: bool = False,
        max_width: int | None = 800,
    ) -> Path:
        """Capture a widget screenshot for documentation.

        Args:
            widget: The widget to capture.
            name: Screenshot name (without extension).
            attach_to_allure: Whether to attach to Allure report.
            max_width: Maximum width for scaling (None to disable).

        Returns:
            Path to the saved screenshot.

        Example:
            DocScreenshot.capture(dialog, "create-code-dialog")
        """
        # Ensure pending events are processed for accurate capture
        QApplication.processEvents()

        # Grab the widget
        pixmap = widget.grab()

        # Scale if needed
        if max_width and pixmap.width() > max_width:
            pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

        # Ensure directory exists
        DOCS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Save screenshot
        path = DOCS_IMAGES_DIR / f"{name}.png"
        pixmap.save(str(path))

        # Optionally attach to Allure
        if attach_to_allure:
            try:
                import allure

                allure.attach.file(
                    str(path),
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
            except ImportError:
                pass  # Allure not available

        return path

    @staticmethod
    def capture_if_missing(
        widget: QWidget,
        name: str,
        *,
        attach_to_allure: bool = False,
        max_width: int | None = 800,
    ) -> Path | None:
        """Capture screenshot only if it doesn't already exist.

        Useful for avoiding accidental overwrites of manually edited screenshots.

        Args:
            widget: The widget to capture.
            name: Screenshot name (without extension).
            attach_to_allure: Whether to attach to Allure report.
            max_width: Maximum width for scaling (None to disable).

        Returns:
            Path to screenshot if captured, None if already exists.
        """
        path = DOCS_IMAGES_DIR / f"{name}.png"
        if path.exists():
            return None
        return DocScreenshot.capture(
            widget,
            name,
            attach_to_allure=attach_to_allure,
            max_width=max_width,
        )

    @staticmethod
    def capture_with_highlight(
        widget: QWidget,
        name: str,
        highlight_region: tuple[int, int, int, int] | None = None,
        *,
        attach_to_allure: bool = False,
        max_width: int | None = 800,
    ) -> Path:
        """Capture screenshot with optional highlight region.

        Args:
            widget: The widget to capture.
            name: Screenshot name (without extension).
            highlight_region: (x, y, width, height) to highlight, or None.
            attach_to_allure: Whether to attach to Allure report.
            max_width: Maximum width for scaling (None to disable).

        Returns:
            Path to the saved screenshot.
        """
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QColor, QPainter, QPen

        # Ensure pending events are processed
        QApplication.processEvents()

        # Grab the widget
        pixmap = widget.grab()

        # Draw highlight if specified
        if highlight_region:
            painter = QPainter(pixmap)
            pen = QPen(QColor("#FF6B6B"))
            pen.setWidth(3)
            painter.setPen(pen)
            x, y, w, h = highlight_region
            painter.drawRect(QRect(x, y, w, h))
            painter.end()

        # Scale if needed
        if max_width and pixmap.width() > max_width:
            pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

        # Ensure directory exists
        DOCS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Save screenshot
        path = DOCS_IMAGES_DIR / f"{name}.png"
        pixmap.save(str(path))

        # Optionally attach to Allure
        if attach_to_allure:
            try:
                import allure

                allure.attach.file(
                    str(path),
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
            except ImportError:
                pass

        return path

    @staticmethod
    def list_missing_images() -> list[str]:
        """Check docs for missing image references.

        Returns:
            List of missing image filenames.
        """
        import re

        docs_dir = DOCS_IMAGES_DIR.parent
        missing = []

        for doc_file in docs_dir.glob("*.md"):
            content = doc_file.read_text()
            # Find all image references
            for match in re.finditer(r"images/([^)\s]+)", content):
                image_name = match.group(1)
                image_path = DOCS_IMAGES_DIR / image_name
                if not image_path.exists():
                    missing.append(image_name)

        return list(set(missing))
