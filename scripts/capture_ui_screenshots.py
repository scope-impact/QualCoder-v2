#!/usr/bin/env python3
"""
Capture UI screenshots for documentation after UI refactor.

Run with: QT_QPA_PLATFORM=offscreen uv run python scripts/capture_ui_screenshots.py

This script captures screenshots of the new unified navigation bar and
simplified coding toolbar for the user manual.

Screenshots to capture:
- main-window-startup.png: New unified nav bar on startup
- coding-screen-with-codes.png: Coding screen with new toolbar
- file-manager-empty.png: File manager with new nav bar
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.shared.presentation.templates import AppShell
from src.contexts.projects.presentation import ProjectScreen
from src.contexts.sources.presentation import FileManagerScreen
from src.contexts.coding.presentation import TextCodingScreen
from src.shared.presentation import create_empty_text_coding_data
from src.tests.e2e.utils.doc_screenshot import DocScreenshot


def main():
    app = QApplication(sys.argv)
    colors = get_colors()

    print("Capturing UI screenshots for documentation...")

    # 1. Main window startup (Project screen with unified nav)
    print("  - main-window-startup.png")
    shell = AppShell(colors=colors)
    project_screen = ProjectScreen(
        colors=colors,
        on_open=lambda: None,
        on_create=lambda: None,
    )
    shell.set_screen(project_screen)
    shell.set_active_navigation("project")
    shell.resize(1200, 800)
    shell.show()
    DocScreenshot.capture(shell, "main-window-startup", max_width=1000)
    shell.close()

    # 2. File manager empty (with unified nav)
    print("  - file-manager-empty.png")
    shell = AppShell(colors=colors)
    files_screen = FileManagerScreen(viewmodel=None, colors=colors)
    shell.set_screen(files_screen)
    shell.set_active_navigation("files")
    shell.resize(1200, 800)
    shell.show()
    DocScreenshot.capture(shell, "file-manager-empty", max_width=1000)
    shell.close()

    # 3. Coding screen (with simplified toolbar)
    print("  - coding-screen-with-codes.png")
    shell = AppShell(colors=colors)
    coding_screen = TextCodingScreen(
        data=create_empty_text_coding_data(),
        colors=colors,
    )
    shell.set_screen(coding_screen)
    shell.set_active_navigation("coding")
    shell.resize(1200, 800)
    shell.show()
    DocScreenshot.capture(shell, "coding-screen-with-codes", max_width=1000)
    shell.close()

    print("\nScreenshots saved to docs/user-manual/images/")
    print("Review and adjust as needed.")


if __name__ == "__main__":
    main()
