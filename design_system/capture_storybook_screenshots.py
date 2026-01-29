#!/usr/bin/env python3
"""
Capture screenshots of all Storybook pages.
Saves to: design_system/assets/screenshots/storybook/
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from design_system.storybook import Storybook


# All storybook page keys
PAGES = [
    "buttons", "inputs", "cards", "badges",
    "alerts", "progress", "spinners",
    "tabs", "breadcrumbs", "steps", "pagination",
    "search", "select", "toggle", "pickers",
    "tables", "lists", "stats", "codetree",
    "player", "upload", "calendar",
    "messages", "chatinput",
    "codeeditor", "richtext",
    "modals", "toasts", "contextmenu",
    "panels", "toolbar",
    # Visualization components
    "charts", "network", "wordcloud", "annotation",
    "pdf", "heatmap", "scores",
]


def capture_screenshots():
    """Capture screenshots of all pages"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Output directory
    output_dir = Path(__file__).parent / "assets" / "screenshots" / "storybook"
    output_dir.mkdir(parents=True, exist_ok=True)

    screenshots_taken = []

    def take_screenshot(window, page_key):
        """Take a screenshot of the current page"""
        # Ensure the page is rendered
        app.processEvents()

        # Grab the window content
        pixmap = window.grab()

        # Save the screenshot
        filename = f"{page_key}.png"
        filepath = output_dir / filename
        pixmap.save(str(filepath))

        screenshots_taken.append(str(filepath))
        print(f"Saved: {filepath}")

    def capture_all():
        """Capture all pages"""
        print("\n=== Capturing screenshots ===")

        # Create storybook
        window = Storybook()
        window.resize(1400, 900)
        window.show()
        app.processEvents()

        # Wait for initial render
        QTimer.singleShot(200, lambda: None)
        app.processEvents()

        for page_key in PAGES:
            # Navigate to page
            window._on_page_select(page_key)
            app.processEvents()

            # Wait for render
            QTimer.singleShot(100, lambda: None)
            app.processEvents()

            # Take screenshot
            take_screenshot(window, page_key)

        window.close()

        print(f"\n=== Done! Captured {len(screenshots_taken)} screenshots ===")
        print(f"Output directory: {output_dir}")
        app.quit()

    # Start capturing after a short delay to ensure everything is initialized
    QTimer.singleShot(100, capture_all)

    return app.exec()


if __name__ == "__main__":
    sys.exit(capture_screenshots())
