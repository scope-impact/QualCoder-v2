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

import allure
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from src.contexts.projects.presentation.dialogs.project_dialog import (
    CreateProjectDialog,
    OpenProjectDialog,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-026 Open & Navigate Project"),
]


# =============================================================================
# OpenProjectDialog Tests
# =============================================================================


@allure.story("QC-026.01 Open Project Dialog")
class TestOpenProjectDialogInitialization:
    """Tests for OpenProjectDialog initialization."""

    def test_dialog_initializes_with_default_values_and_buttons(self, qapp, colors):
        """Dialog initializes with expected default values and button states."""
        dialog = OpenProjectDialog(colors=colors)

        assert dialog.windowTitle() == "Open Project"
        assert dialog.isModal()
        assert dialog.minimumWidth() >= 500
        assert dialog.minimumHeight() >= 400
        assert dialog.get_selected_path() == ""
        assert dialog._open_btn.isEnabled() is False
        assert dialog._cancel_btn.isEnabled() is True
        assert dialog._browse_btn.isEnabled() is True

        dialog.close()

    @pytest.mark.parametrize(
        "recent_projects, expected_count",
        [
            (None, 0),
            ([], 0),
            (
                [
                    {"name": "Project A", "path": "/path/to/a.qda"},
                    {"name": "Project B", "path": "/path/to/b.qda"},
                ],
                2,
            ),
        ],
        ids=["none", "empty", "two-projects"],
    )
    def test_dialog_initializes_with_recent_projects(
        self, qapp, colors, recent_projects, expected_count
    ):
        """Dialog initializes correctly with various recent project inputs."""
        dialog = OpenProjectDialog(recent_projects=recent_projects, colors=colors)

        effective_projects = recent_projects or []
        if not hasattr(dialog, "_recent_list") or effective_projects == []:
            assert dialog._recent_projects == effective_projects
        else:
            assert dialog._recent_projects == recent_projects
            assert dialog._recent_list.count() == expected_count

        dialog.close()


@allure.story("QC-026.01 Open Project Dialog")
class TestOpenProjectDialogRecentProjects:
    """Tests for OpenProjectDialog recent projects interaction."""

    def test_recent_list_displays_and_stores_data_and_enables_open(self, qapp, colors):
        """Recent list displays names, stores paths, and clicking enables Open."""
        recent = [
            {"name": "My Research", "path": "/path/to/research.qda"},
            {"name": "Analysis 2024", "path": "/path/to/analysis.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        # Verify display names
        item0 = dialog._recent_list.item(0)
        item1 = dialog._recent_list.item(1)
        assert item0.text() == "My Research"
        assert item1.text() == "Analysis 2024"

        # Verify stored paths in UserRole data
        assert item0.data(Qt.ItemDataRole.UserRole) == "/path/to/research.qda"
        assert item1.data(Qt.ItemDataRole.UserRole) == "/path/to/analysis.qda"

        # Initially Open is disabled
        assert dialog._open_btn.isEnabled() is False

        # Click first item -> enables Open and sets path
        dialog._on_recent_clicked(item0)
        QApplication.processEvents()
        assert dialog._open_btn.isEnabled() is True
        assert dialog.get_selected_path() == "/path/to/research.qda"

        # Click second item -> changes path
        dialog._on_recent_clicked(item1)
        assert dialog.get_selected_path() == "/path/to/analysis.qda"

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


@allure.story("QC-026.01 Open Project Dialog")
class TestOpenProjectDialogSignals:
    """Tests for OpenProjectDialog signal emissions."""

    def test_open_and_double_click_emit_project_selected(self, qapp, colors):
        """project_selected signal emits on Open click and double-click."""
        from PySide6.QtTest import QSignalSpy

        recent = [
            {"name": "Project", "path": "/path/project.qda"},
            {"name": "Project2", "path": "/test/project.qda"},
        ]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        spy = QSignalSpy(dialog.project_selected)

        # Open via button click
        item = dialog._recent_list.item(0)
        dialog._on_recent_clicked(item)
        dialog._on_open()
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "/path/project.qda"

        # Also verify dialog result code (re-create to reset state)
        dialog.close()

        dialog2 = OpenProjectDialog(recent_projects=recent, colors=colors)
        dialog2.show()
        spy2 = QSignalSpy(dialog2.project_selected)

        # Open via double-click
        item2 = dialog2._recent_list.item(1)
        dialog2._on_recent_double_clicked(item2)
        QApplication.processEvents()

        assert spy2.count() == 1
        assert spy2.at(0)[0] == "/test/project.qda"
        assert dialog2.result() == QDialog.DialogCode.Accepted

        dialog2.close()

    def test_cancel_signal_and_no_signal_on_missing_path(self, qapp, colors):
        """cancel_clicked signal emits on Cancel; no signal on missing-path double-click."""
        from PySide6.QtTest import QSignalSpy

        # Cancel signal
        dialog = OpenProjectDialog(colors=colors)
        cancel_spy = QSignalSpy(dialog.cancel_clicked)

        dialog.show()
        dialog._on_cancel()
        QApplication.processEvents()

        assert cancel_spy.count() == 1
        assert dialog.result() == QDialog.DialogCode.Rejected

        dialog.close()

        # Double-click with no path does nothing
        recent = [{"name": "Project"}]  # No path
        dialog2 = OpenProjectDialog(recent_projects=recent, colors=colors)
        spy = QSignalSpy(dialog2.project_selected)

        item = dialog2._recent_list.item(0)
        dialog2._on_recent_double_clicked(item)
        QApplication.processEvents()

        assert spy.count() == 0

        dialog2.close()


@allure.story("QC-026.01 Open Project Dialog")
class TestOpenProjectDialogBrowse:
    """Tests for OpenProjectDialog browse functionality."""

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getOpenFileName"
    )
    def test_browse_opens_file_dialog_and_sets_path(
        self, mock_file_dialog, qapp, colors
    ):
        """Browse button exists, opens file dialog, and sets path on selection."""
        mock_file_dialog.return_value = ("/selected/file.qda", "")

        recent = [{"name": "Project", "path": "/old/path.qda"}]
        dialog = OpenProjectDialog(recent_projects=recent, colors=colors)

        # Button exists
        assert dialog._browse_btn is not None
        assert dialog._browse_btn.text() == "Browse..."

        dialog._on_browse_clicked()
        QApplication.processEvents()

        mock_file_dialog.assert_called_once()
        assert dialog._selected_path == "/selected/file.qda"
        assert dialog._open_btn.isEnabled() is True
        assert dialog.get_selected_path() == "/selected/file.qda"

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


# =============================================================================
# CreateProjectDialog Tests
# =============================================================================


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogInitialization:
    """Tests for CreateProjectDialog initialization."""

    def test_dialog_initializes_with_defaults_and_buttons(self, qapp, colors):
        """Dialog initializes with expected default values, buttons, and placeholder."""
        dialog = CreateProjectDialog(colors=colors)

        assert dialog.windowTitle() == "Create New Project"
        assert dialog.isModal()
        assert dialog.minimumWidth() >= 500
        assert dialog.minimumHeight() >= 280
        assert dialog._location_input.text() == str(Path.home())
        assert dialog._create_btn.isEnabled() is False
        assert dialog._cancel_btn.isEnabled() is True
        assert dialog._location_btn.isEnabled() is True
        assert dialog._name_input.placeholderText() == "Enter project name..."

        dialog.close()

    def test_dialog_uses_provided_default_directory(self, qapp, colors):
        """Dialog uses provided default directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            assert dialog._location_input.text() == tmpdir

            dialog.close()


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogValidation:
    """Tests for CreateProjectDialog form validation."""

    @pytest.mark.parametrize(
        "name, location, expected_enabled",
        [
            ("", "VALID_DIR", False),
            ("Test Project", "", False),
            ("Test Project", "/nonexistent/path/that/does/not/exist", False),
        ],
        ids=["empty-name", "empty-location", "nonexistent-location"],
    )
    def test_create_disabled_for_invalid_inputs(
        self, qapp, colors, name, location, expected_enabled
    ):
        """Create button disabled when name or location is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText(name)
            actual_location = tmpdir if location == "VALID_DIR" else location
            dialog._location_input.setText(actual_location)
            QApplication.processEvents()

            assert dialog._create_btn.isEnabled() is expected_enabled

            dialog.close()

    def test_create_enabled_with_valid_inputs_and_reacts_to_changes(self, qapp, colors):
        """Create button enabled with valid inputs and updates on name/location changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            # Initially disabled
            assert dialog._create_btn.isEnabled() is False

            # Enter valid name -> enabled
            dialog._name_input.setText("My Project")
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is True

            # Clear name -> disabled
            dialog._name_input.setText("")
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is False

            # Re-enter name
            dialog._name_input.setText("Project")
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is True

            # Invalid location -> disabled
            dialog._location_input.setText("/nonexistent")
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is False

            # Valid location -> enabled
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()
            assert dialog._create_btn.isEnabled() is True

            dialog.close()


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogPathPreview:
    """Tests for CreateProjectDialog path preview."""

    @pytest.mark.parametrize(
        "name, expected_filename, not_in_preview",
        [
            ("My Project", "My_Project.qda", []),
            ("My Project!@#$%", "My_Project.qda", ["!", "@"]),
            ("My Research Project", "My_Research_Project.qda", []),
        ],
        ids=["spaces-to-underscores", "sanitizes-specials", "multi-word"],
    )
    def test_path_preview_shows_sanitized_path(
        self, qapp, colors, name, expected_filename, not_in_preview
    ):
        """Path preview shows full path with sanitized name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText(name)
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            preview_text = dialog._path_preview.text()
            assert tmpdir in preview_text
            assert expected_filename in preview_text
            for char in not_in_preview:
                assert char not in preview_text

            dialog.close()

    @pytest.mark.parametrize(
        "name, location_is_empty",
        [
            ("", False),
            ("Project", True),
        ],
        ids=["empty-name", "empty-location"],
    )
    def test_path_preview_empty_when_input_missing(
        self, qapp, colors, name, location_is_empty
    ):
        """Path preview is empty when name or location is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText(name)
            dialog._location_input.setText("" if location_is_empty else tmpdir)
            QApplication.processEvents()

            assert dialog._path_preview.text() == ""

            dialog.close()


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogNameSanitization:
    """Tests for CreateProjectDialog name sanitization."""

    @pytest.mark.parametrize(
        "input_name, expected_in_path",
        [
            ("Project123", "Project123.qda"),
            ("my-project", "my-project.qda"),
            ("my_project", "my_project.qda"),
            ("project!@#$%^&*()", "project.qda"),
        ],
        ids=["alphanumeric", "dashes", "underscores", "special-chars-removed"],
    )
    def test_sanitization_rules(self, qapp, colors, input_name, expected_in_path):
        """Sanitization preserves alphanumeric, dashes, underscores and removes specials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText(input_name)
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            path = dialog.get_project_path()
            assert expected_in_path in path

            dialog.close()

    def test_handles_name_with_only_special_characters(self, qapp, colors):
        """Handles name with only special characters gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)

            dialog._name_input.setText("!@#$%^")
            dialog._location_input.setText(tmpdir)
            QApplication.processEvents()

            assert dialog._path_preview.text() == ""

            dialog.close()


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogSignals:
    """Tests for CreateProjectDialog signal emissions."""

    def test_create_and_cancel_signals(self, qapp, colors):
        """project_created emits on Create; cancel_clicked emits on Cancel."""
        from PySide6.QtTest import QSignalSpy

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test create signal
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)
            create_spy = QSignalSpy(dialog.project_created)

            dialog._name_input.setText("Test Project")
            dialog._location_input.setText(tmpdir)
            dialog._on_create()
            QApplication.processEvents()

            assert create_spy.count() == 1
            signal_args = create_spy.at(0)
            name = signal_args[0]
            path = signal_args[1]
            assert name == "Test Project"
            assert "Test_Project.qda" in path
            assert tmpdir in path

            dialog.close()

        # Test cancel signal
        dialog2 = CreateProjectDialog(colors=colors)
        cancel_spy = QSignalSpy(dialog2.cancel_clicked)

        dialog2._on_cancel()
        QApplication.processEvents()

        assert cancel_spy.count() == 1

        dialog2.close()


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogBrowse:
    """Tests for CreateProjectDialog browse functionality."""

    @patch(
        "src.contexts.projects.presentation.dialogs.project_dialog.QFileDialog.getExistingDirectory"
    )
    def test_browse_opens_directory_dialog_and_sets_location(
        self, mock_dir_dialog, qapp, colors
    ):
        """Browse button exists, opens directory dialog, and updates location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_dir_dialog.return_value = tmpdir

            dialog = CreateProjectDialog(colors=colors)

            # Button exists
            assert dialog._location_btn is not None
            assert dialog._location_btn.text() == "Browse..."

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


@allure.story("QC-026.02 Create Project Dialog")
class TestCreateProjectDialogResultAndGetters:
    """Tests for CreateProjectDialog result codes and getter methods."""

    def test_accept_reject_and_getters(self, qapp, colors):
        """Create accepts dialog, cancel rejects; getters return correct values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test create -> accepted
            dialog = CreateProjectDialog(default_directory=tmpdir, colors=colors)
            dialog.show()

            dialog._name_input.setText("  Test Project  ")
            dialog._location_input.setText(tmpdir)
            dialog._on_create()

            assert dialog.result() == QDialog.DialogCode.Accepted
            assert dialog.get_project_name() == "Test Project"
            assert dialog.get_project_path() == str(Path(tmpdir) / "Test_Project.qda")

            dialog.close()

        # Test cancel -> rejected
        dialog2 = CreateProjectDialog(colors=colors)
        dialog2.show()

        dialog2._on_cancel()

        assert dialog2.result() == QDialog.DialogCode.Rejected

        dialog2.close()

        # Test getters with invalid inputs
        dialog3 = CreateProjectDialog(colors=colors)

        dialog3._name_input.setText("")
        dialog3._location_input.setText("")

        assert dialog3.get_project_path() == ""

        dialog3.close()
