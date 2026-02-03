"""
QC-028/QC-029: Text Coding Screen UI E2E Tests

Tests for the text coding interface through the UI layer.

These tests use NO MOCKS:
1. Real Qt widgets
2. Real dialogs (CreateCodeDialog, etc.)
3. Simulated user interactions

Test Categories:
- Create Code Dialog: Test code creation through the dialog
- Code Selection: Select codes from the codes panel
- Text Selection: Select text in the editor
- Code Application: Apply codes to text (Q key)
- Keyboard Shortcuts: Test coding shortcuts
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtWidgets import QApplication, QLineEdit

from design_system import get_colors
from src.contexts.coding.presentation.dialogs import CreateCodeDialog
from src.contexts.coding.presentation.screens.text_coding import TextCodingScreen
from src.shared.presentation.dto import (
    CodeCategoryDTO,
    CodeDTO,
    DocumentDTO,
    FileDTO,
    TextCodingDataDTO,
)

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028/QC-029 Text Coding"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def colors():
    """Get color palette for UI."""
    return get_colors()


@pytest.fixture
def sample_data():
    """Create sample data for the coding screen."""
    return TextCodingDataDTO(
        files=[
            FileDTO(id="1", name="interview_01.txt", file_type="text", meta="2.5 KB"),
            FileDTO(id="2", name="interview_02.txt", file_type="text", meta="3.1 KB"),
        ],
        categories=[
            CodeCategoryDTO(
                id="cat-1",
                name="Themes",
                codes=[
                    CodeDTO(
                        id="1", name="Positive Experience", color="#00FF00", count=5
                    ),
                    CodeDTO(id="2", name="Challenge", color="#FF0000", count=3),
                ],
            ),
        ],
        document=DocumentDTO(
            id="1",
            title="interview_01.txt",
            badge="File 1",
            content="""INTERVIEWER: Can you tell me about your experience?

PARTICIPANT: I really enjoyed the learning process. The course materials were comprehensive and the instructors were helpful. However, I found some topics quite challenging.

INTERVIEWER: What topics were most challenging?

PARTICIPANT: Data analysis was difficult at first. But with practice, I improved significantly.""",
        ),
        document_stats=None,
        selected_code=None,
        overlapping_segments=[],
        file_memo=None,
        navigation=None,
        coders=["default"],
        selected_coder="default",
    )


@pytest.fixture
def coding_screen(qapp, colors, sample_data):
    """Create a TextCodingScreen with sample data."""
    screen = TextCodingScreen(
        data=sample_data,
        viewmodel=None,
        colors=colors,
    )
    screen.show()
    QApplication.processEvents()
    yield screen
    screen.close()


@pytest.fixture
def create_code_dialog(qapp, colors):
    """Create a CreateCodeDialog for testing."""
    dialog = CreateCodeDialog(colors=colors)
    yield dialog
    dialog.close()


# =============================================================================
# QC-028.01: Create New Code - Dialog Tests
# =============================================================================


@allure.story("QC-028.01 Create New Code")
class TestCreateCodeDialog:
    """
    QC-028.01: Create New Code
    Test the CreateCodeDialog UI.
    """

    @allure.title("AC #1: Dialog shows name input field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_has_name_input(self, create_code_dialog):
        """Dialog should have a name input field."""
        create_code_dialog.show()
        QApplication.processEvents()

        name_input = create_code_dialog.findChild(QLineEdit)
        assert name_input is not None
        assert name_input.placeholderText() == "Enter code name..."

    @allure.title("AC #1: User can enter code name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enter_code_name(self, create_code_dialog):
        """User can type a code name in the input."""
        create_code_dialog.show()
        QApplication.processEvents()

        create_code_dialog.set_code_name("New Theme")
        assert create_code_dialog.get_code_name() == "New Theme"

    @allure.title("AC #2: Dialog shows color selection grid")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_has_color_grid(self, create_code_dialog):
        """Dialog should show a grid of color options."""
        create_code_dialog.show()
        QApplication.processEvents()

        assert len(create_code_dialog._color_buttons) == 16

    @allure.title("AC #2: User can select a color")
    @allure.severity(allure.severity_level.NORMAL)
    def test_select_color(self, create_code_dialog):
        """User can click a color to select it."""
        create_code_dialog.show()
        QApplication.processEvents()

        second_color_btn = create_code_dialog._color_buttons[1]
        second_color_btn.click()
        QApplication.processEvents()

        expected_color = second_color_btn.property("color")
        assert create_code_dialog.get_code_color() == expected_color

    @allure.title("AC #3: User can add optional memo")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_memo(self, create_code_dialog):
        """User can add an optional description/memo."""
        create_code_dialog.show()
        QApplication.processEvents()

        create_code_dialog._memo_input.setPlainText("This code is for positive themes")
        assert create_code_dialog.get_code_memo() == "This code is for positive themes"

    @allure.title("Create button disabled when name is empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_disabled_without_name(self, create_code_dialog):
        """Create button should be disabled when name is empty."""
        create_code_dialog.show()
        QApplication.processEvents()

        assert not create_code_dialog._create_btn.isEnabled()

    @allure.title("Create button enabled when name is entered")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_enabled_with_name(self, create_code_dialog):
        """Create button should be enabled when name is entered."""
        create_code_dialog.show()
        QApplication.processEvents()

        create_code_dialog.set_code_name("New Code")
        assert create_code_dialog._create_btn.isEnabled()

    @allure.title("AC #4: Clicking create emits code_created signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emits_signal(self, create_code_dialog):
        """Clicking Create Code should emit the code_created signal."""
        create_code_dialog.show()
        QApplication.processEvents()

        signals = []
        create_code_dialog.code_created.connect(
            lambda name, color, memo: signals.append((name, color, memo))
        )

        create_code_dialog.set_code_name("Test Code")
        create_code_dialog._color_buttons[2].click()
        create_code_dialog._memo_input.setPlainText("Test memo")
        QApplication.processEvents()

        create_code_dialog._create_btn.click()
        QApplication.processEvents()

        assert len(signals) == 1
        name, color, memo = signals[0]
        assert name == "Test Code"
        assert color == "#FF5722"
        assert memo == "Test memo"

    @allure.title("Cancel button closes dialog")
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_closes_dialog(self, create_code_dialog):
        """Clicking Cancel should close the dialog."""
        create_code_dialog.show()
        QApplication.processEvents()

        create_code_dialog._cancel_btn.click()
        QApplication.processEvents()

        assert create_code_dialog.result() == 0


# =============================================================================
# QC-028.03: Code Selection
# =============================================================================


@allure.story("QC-028.03 Code Selection")
class TestCodeSelectionUI:
    """Test selecting codes from the codes panel."""

    @allure.title("AC #1: Selecting a code sets it as active")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_code_sets_active(self, coding_screen):
        """Selecting a code sets it as the active code."""
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")

        active = coding_screen.get_active_code()
        assert active["id"] == "1"
        assert active["name"] == "Positive Experience"

    @allure.title("AC #2: Selected code added to recent codes")
    @allure.severity(allure.severity_level.NORMAL)
    def test_selected_code_added_to_recent(self, coding_screen):
        """Selecting codes adds them to recent codes list."""
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_active_code("2", "Challenge", "#FF0000")

        assert len(coding_screen._recent_codes) == 2
        assert coding_screen._recent_codes[0]["id"] == "2"


# =============================================================================
# QC-029.01: Text Selection and Quick Mark
# =============================================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestApplyCodeUI:
    """Test selecting text and applying code using Q key."""

    @allure.title("AC #1: Text selection enables quick mark")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_text_selection_enables_quick_mark(self, coding_screen):
        """Selecting text enables quick mark feature."""
        assert not coding_screen.is_quick_mark_enabled()

        coding_screen.set_text_selection(50, 100)
        QApplication.processEvents()

        assert coding_screen.is_quick_mark_enabled()

    @allure.title("AC #2: Q key applies code to selection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_quick_mark_applies_code(self, coding_screen):
        """Q key applies the active code to the selection."""
        signals = []
        coding_screen.code_applied.connect(
            lambda code_id, start, end: signals.append((code_id, start, end))
        )

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        QApplication.processEvents()

        coding_screen.quick_mark()
        QApplication.processEvents()

        assert len(signals) == 1
        assert signals[0] == ("1", 50, 100)

    @allure.title("AC #3: Quick mark without code does nothing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_quick_mark_requires_code(self, coding_screen):
        """Quick mark without active code does not apply."""
        signals = []
        coding_screen.code_applied.connect(
            lambda code_id, start, end: signals.append((code_id, start, end))
        )

        coding_screen.set_text_selection(50, 100)
        coding_screen.quick_mark()
        QApplication.processEvents()

        assert len(signals) == 0


# =============================================================================
# QC-029.05: Unmark and Undo
# =============================================================================


@allure.story("QC-029.05 Unmark")
class TestUnmarkUI:
    """Test removing codes from text."""

    @allure.title("AC #1: U key removes code from selection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_removes_code(self, coding_screen):
        """U key removes code from the selection."""
        signals = []
        coding_screen.code_removed.connect(
            lambda code_id, start, end: signals.append((code_id, start, end))
        )

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        QApplication.processEvents()

        assert len(signals) == 1
        assert signals[0] == ("1", 50, 100)

    @allure.title("AC #2: Unmark adds to undo history")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_adds_to_history(self, coding_screen):
        """Unmark adds operation to undo history."""
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()

        assert len(coding_screen._unmark_history) == 1

    @allure.title("AC #3: Ctrl+Z undoes unmark")
    @allure.severity(allure.severity_level.NORMAL)
    def test_undo_reapplies_code(self, coding_screen):
        """Ctrl+Z re-applies the unmarked code."""
        applied = []
        coding_screen.code_applied.connect(
            lambda code_id, start, end: applied.append((code_id, start, end))
        )

        coding_screen.set_active_code("1", "Positive", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        coding_screen.undo_unmark()
        QApplication.processEvents()

        assert len(applied) == 1


# =============================================================================
# QC-029.01: Recent Codes
# =============================================================================


@allure.story("QC-029.01 Recent Codes")
class TestRecentCodesUI:
    """Test recent codes functionality."""

    @allure.title("Recent codes maintains MRU order")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_codes_order(self, coding_screen):
        """Recent codes are in most-recently-used order."""
        coding_screen.set_active_code("1", "Code A", "#FF0000")
        coding_screen.set_active_code("2", "Code B", "#00FF00")
        coding_screen.set_active_code("1", "Code A", "#FF0000")

        assert coding_screen._recent_codes[0]["id"] == "1"

    @allure.title("Recent codes limited to 10")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_codes_max_10(self, coding_screen):
        """Recent codes limited to 10 items."""
        for i in range(15):
            coding_screen.set_active_code(str(i), f"Code {i}", "#FF0000")

        assert len(coding_screen._recent_codes) == 10


# =============================================================================
# Keyboard Shortcuts
# =============================================================================


@allure.story("QC-007.10 Keyboard Shortcuts")
class TestKeyboardShortcutsUI:
    """Test keyboard shortcut registration."""

    @allure.title("All coding shortcuts are registered")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shortcuts_registered(self, coding_screen):
        """All coding shortcuts are registered."""
        shortcuts = coding_screen.get_registered_shortcuts()

        assert "Q" in shortcuts
        assert "U" in shortcuts
        assert "V" in shortcuts
        assert "N" in shortcuts
        assert "R" in shortcuts
        assert "H" in shortcuts


# =============================================================================
# Integration Workflow
# =============================================================================


@allure.story("QC-028/QC-029 Integration")
class TestCodingWorkflowUI:
    """Integration test for complete coding workflow."""

    @allure.title("Full workflow: Create code via dialog, select, apply")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_workflow_with_dialog(self, qapp, colors):
        """Test complete workflow from dialog to application."""
        with allure.step("Open CreateCodeDialog and create code"):
            dialog = CreateCodeDialog(colors=colors)
            dialog.show()
            QApplication.processEvents()

            created = []
            dialog.code_created.connect(
                lambda n, c, m: created.append({"name": n, "color": c, "memo": m})
            )

            dialog.set_code_name("Interview Theme")
            dialog._color_buttons[4].click()
            dialog._memo_input.setPlainText("Key themes from interviews")
            dialog._create_btn.click()
            QApplication.processEvents()

            assert len(created) == 1
            assert created[0]["name"] == "Interview Theme"
            dialog.close()

        with allure.step("Apply code to text in coding screen"):
            sample_data = TextCodingDataDTO(
                files=[FileDTO(id="1", name="test.txt", file_type="text")],
                categories=[
                    CodeCategoryDTO(
                        id="cat-1",
                        name="Themes",
                        codes=[
                            CodeDTO(
                                id="1",
                                name=created[0]["name"],
                                color=created[0]["color"],
                                count=0,
                            )
                        ],
                    )
                ],
                document=DocumentDTO(
                    id="1", title="test.txt", content="Sample interview text"
                ),
                document_stats=None,
                selected_code=None,
                overlapping_segments=[],
                file_memo=None,
                navigation=None,
                coders=["default"],
                selected_coder="default",
            )

            screen = TextCodingScreen(data=sample_data, viewmodel=None, colors=colors)
            screen.show()
            QApplication.processEvents()

            applied = []
            screen.code_applied.connect(lambda cid, s, e: applied.append((cid, s, e)))

            screen.set_active_code("1", "Interview Theme", created[0]["color"])
            screen.set_text_selection(0, 15)
            screen.quick_mark()
            QApplication.processEvents()

            assert len(applied) == 1
            assert applied[0][0] == "1"

            screen.close()
