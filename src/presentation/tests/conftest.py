"""
Pytest fixtures for presentation layer tests.

Note: Core fixtures are inherited from root conftest.py:
- qapp, colors: Qt application and theme
- coding_context, viewmodel: Database and business logic

This file contains presentation-specific fixtures for screenshots
and UI testing utilities.
"""

from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QWidget

# =============================================================================
# Screenshot Fixtures
# =============================================================================

# Screenshot directory
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


@pytest.fixture(scope="session")
def screenshot_dir():
    """Create and return screenshot directory"""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    return SCREENSHOT_DIR


@pytest.fixture
def take_screenshot(screenshot_dir, request):
    """Fixture to take screenshots of widgets"""

    def _take_screenshot(widget: QWidget, name: str = None, delay_ms: int = 100):
        if name is None:
            name = request.node.name

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = screenshot_dir / filename

        widget.show()
        widget.raise_()
        widget.activateWindow()

        QApplication.processEvents()

        if delay_ms > 0:
            from PySide6.QtCore import QEventLoop

            loop = QEventLoop()
            QTimer.singleShot(delay_ms, loop.quit)
            loop.exec()

        pixmap = widget.grab()
        pixmap.save(str(filepath))

        print(f"\nScreenshot saved: {filepath}")
        return filepath

    return _take_screenshot


@pytest.fixture
def placeholder_widget(colors):
    """Create a simple placeholder widget for testing layouts"""
    from design_system import RADIUS

    def _create(text: str = "Placeholder", min_height: int = 100):
        widget = QWidget()
        widget.setMinimumHeight(min_height)
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.surface_light};
                border-radius: {RADIUS.xs}px;
            }}
        """)
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {colors.text_secondary};")
        layout.addWidget(label)
        return widget

    return _create
