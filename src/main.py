"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.application.coordinator import get_coordinator
from src.presentation.screens import (
    CaseManagerScreen,
    FileManagerScreen,
    ProjectScreen,
    TextCodingScreen,
)
from src.presentation.templates.app_shell import AppShell


class QualCoderApp:
    """
    Main application class.

    Wires together all layers:
    - Infrastructure (repositories, database)
    - Application (controllers, event bus)
    - Presentation (screens, viewmodels)
    """

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._colors = get_colors()
        self._coordinator = get_coordinator()
        self._shell: AppShell | None = None
        self._screens: dict = {}
        self._current_project_path: Path | None = None

    def _setup_shell(self):
        """Create and configure the main application shell."""
        self._shell = AppShell(colors=self._colors)

        # Create screens
        self._screens = {
            "project": ProjectScreen(
                colors=self._colors,
                on_open=self._on_open_project,
                on_create=self._on_create_project,
            ),
            "files": FileManagerScreen(colors=self._colors),
            "cases": CaseManagerScreen(colors=self._colors),
            "coding": TextCodingScreen(colors=self._colors),
        }

        # Set initial screen (project selection)
        self._shell.set_screen(self._screens["project"])
        self._shell.set_active_menu("project")

        # Connect navigation
        self._shell.menu_clicked.connect(self._on_menu_click)
        self._shell.tab_clicked.connect(self._on_tab_click)

        # Connect settings button
        self._shell.settings_clicked.connect(
            lambda: self._coordinator.show_settings_dialog(
                parent=self._shell, colors=self._colors
            )
        )

    def _on_menu_click(self, menu_id: str):
        """Handle menu item clicks."""
        if menu_id in self._screens:
            self._shell.set_screen(self._screens[menu_id])
            self._shell.set_active_menu(menu_id)

    def _on_tab_click(self, tab_id: str):
        """Handle tab clicks."""
        tab_to_menu = {
            "coding": "coding",
            "reports": "reports",
            "manage": "files",
            "action_log": "project",
        }
        menu_id = tab_to_menu.get(tab_id, tab_id)
        if menu_id in self._screens:
            self._shell.set_screen(self._screens[menu_id])
            self._shell.set_active_tab(tab_id)

    def _on_open_project(self):
        """Handle open project request."""
        result = self._coordinator.show_open_project_dialog(parent=self._shell)
        if result:
            # Project opened successfully - switch to files view
            self._shell.set_screen(self._screens["files"])
            self._shell.set_active_menu("files")

    def _on_create_project(self):
        """Handle create project request."""
        result = self._coordinator.show_create_project_dialog(parent=self._shell)
        if result:
            # Project created successfully - switch to files view
            self._shell.set_screen(self._screens["files"])
            self._shell.set_active_menu("files")

    def run(self) -> int:
        """Run the application."""
        self._coordinator.start()
        self._setup_shell()
        self._shell.show()

        exit_code = self._app.exec()

        self._coordinator.stop()
        return exit_code


def main():
    """Application entry point."""
    app = QualCoderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
