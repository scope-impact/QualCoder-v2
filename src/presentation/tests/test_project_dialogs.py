"""
Tests for QC-026 Project Dialogs

Tests the project dialog functionality:
- AC #1: Researcher can open an existing project file
- AC #2: Researcher can create a new project
"""

from pathlib import Path

import pytest

# Conditionally import Qt - allows running tests to check for collection issues
try:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QSignalSpy

    HAS_QT = True
except ImportError:
    HAS_QT = False
    Qt = None
    QSignalSpy = None

# Skip all tests in this module if Qt is not available
pytestmark = pytest.mark.skipif(not HAS_QT, reason="PySide6 not available")


class TestOpenProjectDialog:
    """Tests for the OpenProjectDialog component."""

    def test_open_project_dialog_creates(self, qapp, colors):
        """OpenProjectDialog creates with default settings."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        dialog = OpenProjectDialog(colors=colors)
        assert dialog is not None

    def test_open_project_dialog_shows_recent_projects(self, qapp, colors):
        """OpenProjectDialog shows recent projects list."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        recent = [
            {"name": "Project A", "path": "/tmp/projectA.qda"},
            {"name": "Project B", "path": "/tmp/projectB.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        assert dialog._recent_list.count() == 2

    def test_open_project_dialog_empty_without_recent(self, qapp, colors):
        """OpenProjectDialog shows message when no recent projects."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        dialog = OpenProjectDialog(recent_projects=[], colors=colors)

        # Should not have a recent list
        assert not hasattr(dialog, "_recent_list") or dialog._recent_list is None

    def test_open_project_dialog_select_recent(self, qapp, colors):
        """OpenProjectDialog enables open button when recent project selected."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        recent = [
            {"name": "Project A", "path": "/tmp/projectA.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        # Initially disabled
        assert not dialog._open_btn.isEnabled()

        # Click on item
        item = dialog._recent_list.item(0)
        dialog._recent_list.setCurrentItem(item)
        dialog._on_recent_clicked(item)

        # Now enabled
        assert dialog._open_btn.isEnabled()
        assert dialog.get_selected_path() == "/tmp/projectA.qda"

    def test_open_project_dialog_emits_project_selected(self, qapp, colors):
        """OpenProjectDialog emits project_selected signal."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        recent = [
            {"name": "Project A", "path": "/tmp/projectA.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)
        spy = QSignalSpy(dialog.project_selected)

        # Select and open
        item = dialog._recent_list.item(0)
        dialog._recent_list.setCurrentItem(item)
        dialog._on_recent_clicked(item)
        dialog._open_btn.click()

        assert spy.count() == 1
        assert spy[0][0] == "/tmp/projectA.qda"

    def test_open_project_dialog_emits_cancel_signal(self, qapp, colors):
        """OpenProjectDialog emits cancel_clicked signal."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        dialog = OpenProjectDialog(colors=colors)
        spy = QSignalSpy(dialog.cancel_clicked)

        dialog._cancel_btn.click()

        assert spy.count() == 1

    def test_open_project_dialog_double_click_opens(self, qapp, colors):
        """OpenProjectDialog opens on double-click."""
        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        recent = [
            {"name": "Project A", "path": "/tmp/projectA.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)
        spy = QSignalSpy(dialog.project_selected)

        # Double-click on item
        item = dialog._recent_list.item(0)
        dialog._on_recent_double_clicked(item)

        assert spy.count() == 1


class TestCreateProjectDialog:
    """Tests for the CreateProjectDialog component."""

    def test_create_project_dialog_creates(self, qapp, colors):
        """CreateProjectDialog creates with default settings."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(colors=colors)
        assert dialog is not None

    def test_create_project_dialog_shows_default_directory(
        self, qapp, colors, tmp_path
    ):
        """CreateProjectDialog shows specified default directory."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        assert dialog._location_input.text() == str(tmp_path)

    def test_create_project_dialog_disabled_without_name(self, qapp, colors, tmp_path):
        """CreateProjectDialog disables create button without name."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        # Create button initially disabled
        assert not dialog._create_btn.isEnabled()

    def test_create_project_dialog_enabled_with_name_and_location(
        self, qapp, colors, tmp_path
    ):
        """CreateProjectDialog enables create button with valid input."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        # Enter name
        dialog._name_input.setText("My Research Project")

        # Should now be enabled
        assert dialog._create_btn.isEnabled()

    def test_create_project_dialog_generates_path(self, qapp, colors, tmp_path):
        """CreateProjectDialog generates correct project path."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        dialog._name_input.setText("My Project")

        expected_path = str(tmp_path / "My_Project.qda")
        assert dialog.get_project_path() == expected_path

    def test_create_project_dialog_sanitizes_name(self, qapp, colors, tmp_path):
        """CreateProjectDialog sanitizes project name for filename."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        # Name with special characters
        dialog._name_input.setText("My Project: Test/Data")

        # Should sanitize to safe filename
        path = dialog.get_project_path()
        assert ":" not in path
        assert (
            "/" not in Path(path).name or Path(path).name == dialog.get_project_name()
        )

    def test_create_project_dialog_emits_project_created(self, qapp, colors, tmp_path):
        """CreateProjectDialog emits project_created signal."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )
        spy = QSignalSpy(dialog.project_created)

        dialog._name_input.setText("New Project")
        dialog._create_btn.click()

        assert spy.count() == 1
        assert spy[0][0] == "New Project"  # name
        assert str(tmp_path) in spy[0][1]  # path

    def test_create_project_dialog_emits_cancel_signal(self, qapp, colors):
        """CreateProjectDialog emits cancel_clicked signal."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(colors=colors)
        spy = QSignalSpy(dialog.cancel_clicked)

        dialog._cancel_btn.click()

        assert spy.count() == 1

    def test_create_project_dialog_updates_path_preview(self, qapp, colors, tmp_path):
        """CreateProjectDialog updates path preview on input change."""
        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        dialog = CreateProjectDialog(
            default_directory=str(tmp_path),
            colors=colors,
        )

        dialog._name_input.setText("Test Project")

        preview_text = dialog._path_preview.text()
        assert "Test_Project.qda" in preview_text
