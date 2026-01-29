"""
Pytest configuration and fixtures for design system tests
"""

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
import sys
from pathlib import Path
from datetime import datetime

# Ensure we have a QApplication instance
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for the test session"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# Note: pytest-qt provides its own qtbot fixture, no need to redefine it
# The qapp fixture ensures QApplication exists before tests run


@pytest.fixture
def dark_theme():
    """Get dark theme colors"""
    from design_system.tokens import get_theme
    return get_theme("dark")


@pytest.fixture
def light_theme():
    """Get light theme colors"""
    from design_system.tokens import get_theme
    return get_theme("light")


# Screenshot directories
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
ASSETS_SCREENSHOT_DIR = Path(__file__).parent.parent / "assets" / "screenshots"


@pytest.fixture(scope="session")
def screenshot_dir():
    """Create and return screenshot directory"""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    ASSETS_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOT_DIR


@pytest.fixture
def take_screenshot(screenshot_dir, request):
    """
    Fixture to take screenshots of widgets.

    Usage:
        def test_button(qtbot, take_screenshot):
            btn = Button("Click me")
            qtbot.addWidget(btn)
            btn.show()
            take_screenshot(btn, "button_primary")
    """
    def _take_screenshot(widget: QWidget, name: str = None, delay_ms: int = 100):
        """
        Take a screenshot of a widget.

        Args:
            widget: The widget to capture
            name: Optional name for the screenshot file
            delay_ms: Delay before capture (for animations to settle)
        """
        # Generate filename
        if name is None:
            name = request.node.name

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = screenshot_dir / filename

        # Also save to assets with clean name (for API documentation)
        assets_filepath = ASSETS_SCREENSHOT_DIR / f"{name}.png"

        # Ensure widget is visible and rendered
        widget.show()
        widget.raise_()
        widget.activateWindow()

        # Process events and wait for render
        QApplication.processEvents()

        # Use QTimer for delay if needed
        if delay_ms > 0:
            loop = __import__('PyQt6.QtCore', fromlist=['QEventLoop']).QEventLoop()
            QTimer.singleShot(delay_ms, loop.quit)
            loop.exec()

        # Capture the widget
        pixmap = widget.grab()

        # Save timestamped version (for history/tracking)
        pixmap.save(str(filepath))

        # Save clean version to assets (for API docs)
        pixmap.save(str(assets_filepath))

        print(f"\nScreenshot saved: {filepath}")
        print(f"Assets copy: {assets_filepath}")
        return filepath

    return _take_screenshot


@pytest.fixture
def screenshot_comparison(screenshot_dir):
    """
    Fixture for visual regression testing.
    Compares current screenshot with a baseline.

    Usage:
        def test_button_visual(qtbot, screenshot_comparison):
            btn = Button("Click me")
            qtbot.addWidget(btn)
            btn.show()
            assert screenshot_comparison(btn, "button_baseline")
    """
    def _compare(widget: QWidget, baseline_name: str, threshold: float = 0.99):
        """
        Compare widget screenshot with baseline.

        Args:
            widget: Widget to capture
            baseline_name: Name of baseline image (without extension)
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if images match within threshold, False otherwise
        """
        baseline_path = screenshot_dir / f"{baseline_name}.png"
        current_path = screenshot_dir / f"{baseline_name}_current.png"

        # Capture current state
        widget.show()
        QApplication.processEvents()

        loop = __import__('PyQt6.QtCore', fromlist=['QEventLoop']).QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

        pixmap = widget.grab()
        pixmap.save(str(current_path))

        # If no baseline exists, create it
        if not baseline_path.exists():
            pixmap.save(str(baseline_path))
            print(f"\nBaseline created: {baseline_path}")
            return True

        # Compare images
        baseline = QPixmap(str(baseline_path))

        if baseline.size() != pixmap.size():
            print(f"\nSize mismatch: baseline={baseline.size()}, current={pixmap.size()}")
            return False

        # Simple pixel comparison
        baseline_img = baseline.toImage()
        current_img = pixmap.toImage()

        total_pixels = baseline_img.width() * baseline_img.height()
        matching_pixels = 0

        for x in range(baseline_img.width()):
            for y in range(baseline_img.height()):
                if baseline_img.pixel(x, y) == current_img.pixel(x, y):
                    matching_pixels += 1

        similarity = matching_pixels / total_pixels

        if similarity >= threshold:
            # Clean up current if matches
            current_path.unlink(missing_ok=True)
            return True
        else:
            print(f"\nVisual difference detected: {similarity:.2%} similarity (threshold: {threshold:.0%})")
            diff_path = screenshot_dir / f"{baseline_name}_diff.png"
            print(f"Current saved to: {current_path}")
            return False

    return _compare
