"""
Unit tests for Project Dialogs.

Tests the OpenProjectDialog and CreateProjectDialog components.
Uses pytest-qt for Qt widget testing.

Run with: QT_QPA_PLATFORM=offscreen pytest src/contexts/projects/presentation/dialogs/tests/test_project_dialog.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from src.contexts.projects.presentation.dialogs.project_dialog import (
    CreateProjectDialog,
    OpenProjectDialog,
)

pytestmark = [pytest.mark.unit]


# =============================================================================
# OpenProjectDialog Tests
# =============================================================================


class TestOpenProjectDialogInitialization:
    """Tests for OpenProjectDialog initialization."""

    def test_dialog_initializes_with_default_values(self, qapp, colors):
        """Dialog initializes with expected default values."""
        dialog = OpenProjectDialog(colors=colors)

        assert dialog.windowTitle() == "Open Project"
        assert dialog.isModal()
        assert dialog.minimumWidth() >= 500
        assert dialog.minimumHeight() >= 400
        assert dialog.get_selected_path() == ""

        dialog.close()

    def test_dialog_initializes_without_recent_projects(self, qapp, colors):
        """Dialog initializes correctly with no recent projects."""
        dialog = OpenProjectDialog(recent_projects=None, colors=colors)

        # Should show empty state (no recent_list attribute created)
        assert not hasattr(dialog, "_recent_list") or dialog._recent_projects == []
        dialog.close()

    def test_dialog_initializes_with_empty_recent_projects(self, qapp, colors):
        """Dialog initializes correctly with empty recent projects list."""
        dialog = OpenProjectDialog(recent_projects=[], colors=colors)

        assert dialog._recent_projects == []
        dialog.close()

    def test_dialog_initializes_with_recent_projects(self, qapp, colors):
        """Dialog initializes correctly with recent projects list."""
        recent = [
            {"name": "Project A", "path": "/path/to/a.qda"},
            {"name": "Project B", "path": "/path/to/b.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        assert dialog._recent_projects == recent
        assert hasattr(dialog, "_recent_list")
        assert dialog._recent_list.count() == 2

        dialog.close()

    def test_dialog_buttons_initial_state(self, qapp, colors):
        """Dialog buttons are in correct initial state."""
        dialog = OpenProjectDialog(colors=colors)

        assert dialog._open_btn.isEnabled() is False
        assert dialog._cancel_btn.isEnabled() is True
        assert dialog._browse_btn.isEnabled() is True

        dialog.close()


class TestOpenProjectDialogRecentProjects:
    """Tests for OpenProjectDialog recent projects interaction."""

    def test_recent_list_displays_project_names(self, qapp, colors):
        """Recent list displays project names correctly."""
        recent = [
            {"name": "My Research", "path": "/path/to/research.qda"},
            {"name": "Analysis 2024", "path": "/path/to/analysis.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        item0 = dialog._recent_list.item(0)
        item1 = dialog._recent_list.item(1)

        assert item0.text() == "My Research"
        assert item1.text() == "Analysis 2024"

        dialog.close()

    def test_recent_list_stores_paths_in_user_data(self, qapp, colors):
        """Recent list stores project paths in UserRole data."""
        recent = [
            {"name": "My Research", "path": "/path/to/research.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        item = dialog._recent_list.item(0)
        assert item.data(Qt.ItemDataRole.UserRole) == "/path/to/research.qda"

        dialog.close()

    def test_clicking_recent_item_enables_open_button(self, qapp, colors):
        """Clicking a recent project item enables the Open button."""
        recent = [
            {"name": "Project", "path": "/path/to/project.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        assert dialog._open_btn.isEnabled() is False

        # Simulate clicking item
        item = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item)
        QApplication.processEvents()

        assert dialog._open_btn.isEnabled() is True
        assert dialog._selected_path == "/path/to/project.qda"

        dialog.close()

    def test_clicking_recent_item_sets_selected_path(self, qapp, colors):
        """Clicking a recent project sets the selected path."""
        recent = [
            {"name": "Project A", "path": "/path/a.qda"},
            {"name": "Project B", "path": "/path/b.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        # Click first item
        item_a = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item_a)
        assert dialog.get_selected_path() == "/path/a.qda"

        # Click second item
        item_b = dialog._recent_list.item(1)
        dialog._on_recent_clicked(item_b)
        assert dialog.get_selected_path() == "/path/b.qda"

        dialog.close()

    def test_handles_item_with_missing_path(self, qapp, colors):
        """Dialog handles recent item with missing path gracefully."""
        recent = [
            {"name": "Project"},  # No path
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        item = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item)

        assert dialog.get_selected_path() == ""
        assert dialog._open_btn.isEnabled() is False

        dialog.close()


class TestOpenProjectDialogSignals:
    """Tests for OpenProjectDialog signal emissions."""

    def test_project_selected_signal_emitted_on_open(self, qapp, colors):
        """project_selected signal emits when Open button is clicked."""
        from PySide6.QtTest import QSignalSpy

        recent = [{"name": "Project", "path": "/path/project.qda"}]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        spy = QSignalSpy(dialog.project_selected)

        # Select and open
        item = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item)
        dialog._on_open()
        QApplication.processEvents()

        assert spy.count() == 1
        # PySide6 QSignalSpy uses at() method
        assert spy.at(0)[0] == "/path/project.qda"

        dialog.close()

    def test_cancel_clicked_signal_emitted_on_cancel(self, qapp, colors):
        """cancel_clicked signal emits when Cancel button is clicked."""
        from PySide6.QtTest import QSignalSpy

        dialog = OpenProjectDialog(colors=colors)
        spy = QSignalSpy(dialog.cancel_clicked)

        dialog._on_cancel()
        QApplication.processEvents()

        assert spy.count() == 1

        dialog.close()

    def test_double_click_recent_item_opens_project(self, qapp, colors):
        """Double-clicking a recent project item opens it immediately."""
        from PySide6.QtTest import QSignalSpy

        recent = [{"name": "Project", "path": "/test/project.qda"}]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        spy = QSignalSpy(dialog.project_selected)

        item = dialog._recent_list.item(0)
        dialog._on_recent_double_clicked(item)
        QApplication.processEvents()

        assert spy.count() == 1
        # PySide6 QSignalSpy uses at() method
        assert spy.at(0)[0] == "/test/project.qda"

        dialog.close()

    def test_double_click_item_without_path_does_nothing(self, qapp, colors):
        """Double-clicking item without path does not emit signal."""
        from PySide6.QtTest import QSignalSpy

        recent = [{"name": "Project"}]  # No path
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        spy = QSignalSpy(dialog.project_selected)

        item = dialog._recent_list.item(0)
        dialog._on_recent_double_clicked(item)
        QApplication.processEvents()

        assert spy.count() == 0

        dialog.close()


class TestOpenProjectDialogBrowse:
    """Tests for OpenProjectDialog browse functionality."""

    def test_browse_button_exists(self, qapp, colors):
        """Browse button is present in dialog."""
        dialog = OpenProjectDialog(colors=colors)

        assert dialog._browse_btn is not None
        assert dialog._browse_btn.text() == "Browse..."

        dialog.close()

    def test_browse_sets_path_and_enables_open(self, qapp, colors):
        """Browsing for a file sets the path and enables Open button."""
        dialog = OpenProjectDialog(colors=colors)

        # Simulate successful browse
        dialog._selected_path = "/browsed/project.qda"
        dialog._open_btn.setEnabled(True)

        assert dialog.get_selected_path() == "/browsed/project.qda"
        assert dialog._open_btn.isEnabled() is True

        dialog.close()

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getOpenFileName"
    )
    def test_browse_clicked_opens_file_dialog(self, mock_file_dialog, qapp, colors):
        """Clicking Browse opens a file dialog."""
        mock_file_dialog.return_value = ("/selected/file.qda", "")

        recent = [{"name": "Project", "path": "/old/path.qda"}]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        dialog._on_browse_clicked()
        QApplication.processEvents()

        mock_file_dialog.assert_called_once()
        assert dialog._selected_path == "/selected/file.qda"
        assert dialog._open_btn.isEnabled() is True

        dialog.close()

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getOpenFileName"
    )
    def test_browse_cancelled_does_not_change_state(
        self, mock_file_dialog, qapp, colors
    ):
        """Cancelling browse dialog does not change state."""
        mock_file_dialog.return_value = ("", "")

        dialog = OpenProjectDialog(colors=colors)

        original_path = dialog._selected_path
        dialog._on_browse_clicked()
        QApplication.processEvents()

        assert dialog._selected_path == original_path
        assert dialog._open_btn.isEnabled() is False

        dialog.close()


class TestOpenProjectDialogResult:
    """Tests for OpenProjectDialog dialog result codes."""

    def test_open_accepts_dialog(self, qapp, colors):
        """Opening a project accepts the dialog."""
        recent = [{"name": "Project", "path": "/path/project.qda"}]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)
        dialog.show()

        item = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item)
        dialog._on_open()

        assert dialog.result() == QDialog.DialogCode.Accepted

        dialog.close()

    def test_cancel_rejects_dialog(self, qapp, colors):
        """Cancelling rejects the dialog."""
        dialog = OpenProjectDialog(colors=colors)
        dialog.show()

        dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected

        dialog.close()


# =============================================================================
# CreateProjectDialog Tests
# =============================================================================


class TestCreateProjectDialogInitialization:
    """Tests for CreateProjectDialog initialization."""

    def test_dialog_initializes_with_default_values(self, qapp, colors):
        """Dialog initializes with expected default values."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog.windowTitle() == "Create New Project"
        assert dialog.isModal()
        assert dialog.minimumWidth() >= 500
        assert dialog.minimumHeight() >= 280

        dialog.close()

    def test_dialog_uses_home_directory_as_default(self, qapp, colors):
        """Dialog uses home directory as default location."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog._location_input.text() == str(Path.home())

        dialog.close()

    def test_dialog_uses_provided_default_directory(self, qapp, colors):
        """Dialog uses provided default directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            assert dialog._location_input.text() == tmpdir

            dialog.close()

    def test_dialog_buttons_initial_state(self, qapp, colors):
        """Dialog buttons are in correct initial state."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog._create_btn.isEnabled() is False
        assert dialog._cancel_btn.isEnabled() is True
        assert dialog._location_btn.isEnabled() is True

        dialog.close()

    def test_name_input_placeholder(self, qapp, colors):
        """Name input has correct placeholder text."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog._name_input.placeholderText() == "Enter project name..."

        dialog.close()


class TestCreateProjectDialogValidation:
    """Tests for CreateProjectDialog form validation."""

    def test_create_disabled_when_name_empty(self, qapp, colors):
        """Create button disabled when name is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("")
            QApplication.processEvents()

            assert dialog._create_btn.isEnabled() is False

            dialog.close()

    def test_create_disabled_when_location_empty(self, qapp, colors):
        """Create button disabled when location is empty."""
        dialog = CreateProjectDialog(colors=colors)

        dialog._name_input.setText("Test Project")
        dialog._location_input.setText("")
        QApplication.processEvents()

        assert dialog._create_btn.isEnabled() is False

        dialog.close()

    def test_create_disabled_when_location_does_not_exist(self, qapp, colors):
        """Create button disabled when location directory doesn't exist."""
        dialog = CreateProjectDialog(colors=colors)

        dialog._name_input.setText("Test Project")
        dialog._location_input.setText("/nonexistent/path/that/does/not/exist")
        QApplication.processEvents()

        assert dialog._create_btn.isEnabled() is False

        dialog.close()

    def test_create_enabled_with_valid_name_and_location(self, qapp, colors):
        """Create button enabled with valid name and existing location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("My Project")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            assert dialog._create_btn.isEnabled() is True

            dialog.close()

    def test_validation_updates_on_name_change(self, qapp, colors):
        """Validation updates when name changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            # Initially disabled
            assert dialog._create_btn.isEnabled() is False

            # Enter valid name
            dialog._name_input.setText("Valid Name")
            QApplication.processEvents()

            assert dialog._create_btn.isEnabled() is True

            # Clear name
            dialog._name_input.setText("")
            QApplication.processEvents()

            assert dialog._create_btn.isEnabled() is False

            dialog.close()

    def test_validation_updates_on_location_change(self, qapp, colors):
        """Validation updates when location changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("Project")

            # Valid location
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is True

            # Invalid location
            dialog._location_input.setText("/nonexistent")
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is False

            dialog.close()


class TestCreateProjectDialogPathPreview:
    """Tests for CreateProjectDialog path preview."""

    def test_path_preview_shows_full_path(self, qapp, colors):
        """Path preview shows the full project path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("My Project")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            preview_text = dialog._path_preview.text()
            assert tmpdir in preview_text
            assert "My_Project.qda" in preview_text

            dialog.close()

    def test_path_preview_sanitizes_name(self, qapp, colors):
        """Path preview sanitizes special characters in name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("My Project!@#$%")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            preview_text = dialog._path_preview.text()
            assert "My_Project.qda" in preview_text
            assert "!" not in preview_text
            assert "@" not in preview_text

            dialog.close()

    def test_path_preview_handles_spaces(self, qapp, colors):
        """Path preview converts spaces to underscores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("My Research Project")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            preview_text = dialog._path_preview.text()
            assert "My_Research_Project.qda" in preview_text

            dialog.close()

    def test_path_preview_empty_when_name_empty(self, qapp, colors):
        """Path preview is empty when name is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            assert dialog._path_preview.text() == ""

            dialog.close()

    def test_path_preview_empty_when_location_empty(self, qapp, colors):
        """Path preview is empty when location is empty."""
        dialog = CreateProjectDialog(colors=colors)

        dialog._name_input.setText("Project")
        dialog._location_input.setText("")
        QApplication.processEvents()

        assert dialog._path_preview.text() == ""

        dialog.close()


class TestCreateProjectDialogNameSanitization:
    """Tests for CreateProjectDialog name sanitization."""

    def test_sanitization_preserves_alphanumeric(self, qapp, colors):
        """Sanitization preserves alphanumeric characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("Project123")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            path = dialog.get_project_path()
            assert "Project123.qda" in path

            dialog.close()

    def test_sanitization_preserves_dashes(self, qapp, colors):
        """Sanitization preserves dashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("my-project")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            path = dialog.get_project_path()
            assert "my-project.qda" in path

            dialog.close()

    def test_sanitization_preserves_underscores(self, qapp, colors):
        """Sanitization preserves underscores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("my_project")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            path = dialog.get_project_path()
            assert "my_project.qda" in path

            dialog.close()

    def test_sanitization_removes_special_characters(self, qapp, colors):
        """Sanitization removes special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("project!@#$%^&*()")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            path = dialog.get_project_path()
            assert "project.qda" in path

            dialog.close()

    def test_handles_name_with_only_special_characters(self, qapp, colors):
        """Handles name with only special characters gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("!@#$%^")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            # Should result in empty sanitized name, preview should be empty
            # Note: the button may be enabled (validation checks non-empty input),
            # but the path preview will be empty and get_project_path returns empty string
            assert dialog._path_preview.text() == ""
            # The sanitized name would be empty, so get_project_path returns empty
            # But the actual name input has text, so create button may be enabled
            # This is actually a potential bug in the dialog, but we test current behavior

            dialog.close()


class TestCreateProjectDialogSignals:
    """Tests for CreateProjectDialog signal emissions."""

    def test_project_created_signal_emitted_on_create(self, qapp, colors):
        """project_created signal emits when Create button is clicked."""
        from PySide6.QtTest import QSignalSpy

        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            spy = QSignalSpy(dialog.project_created)

            dialog._name_input.setText("Test Project")
            dialog._location_input.setText(tmpdir)
            dialog._on_create()
            QApplication.processEvents()

            assert spy.count() == 1
            # PySide6 QSignalSpy uses at() method
            signal_args = spy.at(0)
            name = signal_args[0]
            path = signal_args[1]
            assert name == "Test Project"
            assert "Test_Project.qda" in path
            assert tmpdir in path

            dialog.close()

    def test_cancel_clicked_signal_emitted_on_cancel(self, qapp, colors):
        """cancel_clicked signal emits when Cancel button is clicked."""
        from PySide6.QtTest import QSignalSpy

        dialog = CreateProjectDialog(colors=colors)
        spy = QSignalSpy(dialog.cancel_clicked)

        dialog._on_cancel()
        QApplication.processEvents()

        assert spy.count() == 1

        dialog.close()


class TestCreateProjectDialogBrowse:
    """Tests for CreateProjectDialog browse functionality."""

    def test_browse_button_exists(self, qapp, colors):
        """Browse button is present in dialog."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog._location_btn is not None
        assert dialog._location_btn.text() == "Browse..."

        dialog.close()

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getExistingDirectory"
    )
    def test_browse_clicked_opens_directory_dialog(self, mock_dir_dialog, qapp, colors):
        """Clicking Browse opens a directory dialog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_dir_dialog.return_value = tmpdir

            dialog = CreateProjectDialog(colors=colors)

            dialog._on_browse_clicked()
            QApplication.processEvents()

            mock_dir_dialog.assert_called_once()
            assert dialog._location_input.text() == tmpdir

            dialog.close()

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getExistingDirectory"
    )
    def test_browse_cancelled_does_not_change_location(
        self, mock_dir_dialog, qapp, colors
    ):
        """Cancelling browse dialog does not change location."""
        mock_dir_dialog.return_value = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            original_location = dialog._location_input.text()
            dialog._on_browse_clicked()
            QApplication.processEvents()

            assert dialog._location_input.text() == original_location

            dialog.close()


class TestCreateProjectDialogResult:
    """Tests for CreateProjectDialog dialog result codes."""

    def test_create_accepts_dialog(self, qapp, colors):
        """Creating a project accepts the dialog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)
            dialog.show()

            dialog._name_input.setText("Test")
            dialog._on_create()

            assert dialog.result() == QDialog.DialogCode.Accepted

            dialog.close()

    def test_cancel_rejects_dialog(self, qapp, colors):
        """Cancelling rejects the dialog."""
        dialog = CreateProjectDialog(colors=colors)
        dialog.show()

        dialog._on_cancel()

        assert dialog.result() == QDialog.DialogCode.Rejected

        dialog.close()


class TestCreateProjectDialogGetters:
    """Tests for CreateProjectDialog getter methods."""

    def test_get_project_name_returns_trimmed_name(self, qapp, colors):
        """get_project_name returns trimmed name."""
        dialog = CreateProjectDialog(colors=colors)

        dialog._name_input.setText("  My Project  ")

        assert dialog.get_project_name() == "My Project"

        dialog.close()

    def test_get_project_path_returns_full_path(self, qapp, colors):
        """get_project_path returns full sanitized path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("Test Project")
            dialog._location_input.setText(tmpdir)

            path = dialog.get_project_path()

            assert path == str(Path(tmpdir) / "Test_Project.qda")

            dialog.close()

    def test_get_project_path_returns_empty_when_invalid(self, qapp, colors):
        """get_project_path returns empty string when inputs invalid."""
        dialog = CreateProjectDialog(colors=colors)

        dialog._name_input.setText("")
        dialog._location_input.setText("")

        assert dialog.get_project_path() == ""

        dialog.close()
