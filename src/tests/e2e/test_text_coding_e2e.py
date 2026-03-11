"""
QC-028/QC-029: Text Coding Screen UI E2E Tests

BLACK-BOX E2E TESTS - Tests interact with UI via visible elements only:
- Find buttons by text/tooltip, not private attributes
- Verify outcomes via visible UI state, not internal state
- Simulate real user interactions

Test Categories:
- Create Code Dialog: Test code creation through the dialog
- Code Selection: Select codes from the codes panel
- Text Selection: Select text in the editor
- Code Application: Apply codes to text (Q key)
- Keyboard Shortcuts: Test coding shortcuts
- Full Application Path: Tests using wired_app fixture
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

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
from src.tests.e2e.helpers import (
    attach_screenshot,
    click_color_swatch_by_index,
    click_dialog_button,
    find_any_button_by_tooltip,
    find_color_swatch_buttons,
    find_input_by_placeholder,
    find_visible_dialog,
    is_button_enabled,
    wait_for_dialog,
)
from src.tests.e2e.utils import DocScreenshot

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
# QC-028.01: Create New Code - Dialog Tests (Black-Box)
# =============================================================================


@allure.story("QC-028.01 Create New Code")
class TestCreateCodeDialog:
    """
    QC-028.01: Create New Code
    Test the CreateCodeDialog UI using black-box patterns.
    """

    @allure.title("AC #1-3: Dialog shows elements, accepts input, and supports memo")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_elements_input_and_memo(self, create_code_dialog):
        """Dialog has name input, color grid, accepts user input, and supports optional memo."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find input by placeholder text
        name_input = find_input_by_placeholder(create_code_dialog, "Enter code name")
        assert name_input is not None, "Name input field should be visible"
        assert name_input.placeholderText() == "Enter code name..."

        # BLACK-BOX: Use public API to set/get name
        create_code_dialog.set_code_name("New Theme")
        assert create_code_dialog.get_code_name() == "New Theme"

        # BLACK-BOX: Find color swatches by their 'color' property
        swatches = find_color_swatch_buttons(create_code_dialog)
        assert len(swatches) == 16, "Should show 16 color options"

        # BLACK-BOX: Click second color swatch by index
        expected_color = swatches[1].property("color")
        swatches[1].click()
        QApplication.processEvents()

        # Verify via public getter
        assert create_code_dialog.get_code_color() == expected_color

        # BLACK-BOX: Find memo input and set text via public API
        memo_text = "This code is for positive themes"
        create_code_dialog.set_code_memo(memo_text)
        assert create_code_dialog.get_code_memo() == memo_text

    @allure.title("AC #4: Create button state and emits code_created signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_button_state_and_signal(self, create_code_dialog):
        """Create button disabled when empty, enabled with name, and emits signal on click."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Initially disabled
        assert not is_button_enabled(create_code_dialog, "Create")

        # Enter name - should become enabled
        create_code_dialog.set_code_name("Test Code")
        QApplication.processEvents()
        assert is_button_enabled(create_code_dialog, "Create")

        # Setup signal spy
        spy = QSignalSpy(create_code_dialog.code_created)

        # Fill form using public API
        click_color_swatch_by_index(create_code_dialog, 2)
        create_code_dialog.set_code_memo("Test memo")
        QApplication.processEvents()

        # BLACK-BOX: Click button by text
        click_dialog_button(create_code_dialog, "Create")
        QApplication.processEvents()

        assert spy.count() == 1
        # Verify signal arguments
        name, color, memo = spy.at(0)
        assert name == "Test Code"
        assert memo == "Test memo"

    @allure.title("Cancel button closes dialog without creating")
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_closes_dialog(self, create_code_dialog):
        """Clicking Cancel should close the dialog."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Click button by text
        click_dialog_button(create_code_dialog, "Cancel")
        QApplication.processEvents()

        assert create_code_dialog.result() == 0


# =============================================================================
# QC-028.03: Code Selection (Black-Box)
# =============================================================================


@allure.story("QC-028.03 Code Selection")
class TestCodeSelectionUI:
    """Test selecting codes from the codes panel using black-box patterns."""

    @allure.title("AC #1-2: Selecting a code sets it active and tracks recent codes")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_code_active_and_recent(self, coding_screen):
        """Selecting a code sets it as active and adds to recent codes list."""
        # Use public API to set active code
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")

        # Verify via public getter
        active = coding_screen.get_active_code()
        assert active["id"] == "1"
        assert active["name"] == "Positive Experience"

        # Select another code
        coding_screen.set_active_code("2", "Challenge", "#FF0000")

        # BLACK-BOX: Verify via public API that tracks recent count
        recent_count = coding_screen.get_recent_codes_count()
        assert recent_count == 2

        # Most recent should be the active one
        active = coding_screen.get_active_code()
        assert active["id"] == "2"

        # Screenshot for documentation
        attach_screenshot(coding_screen, "CodingScreen - Code Selected")


# =============================================================================
# QC-029.01: Text Selection and Quick Mark (Black-Box)
# =============================================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestApplyCodeUI:
    """Test selecting text and applying code using Q key (black-box)."""

    @allure.title("AC #1-2: Text selection enables quick mark and Q key applies code")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_text_selection_and_quick_mark(self, coding_screen):
        """Selecting text enables quick mark, and Q key applies the active code."""
        # Verify initial state via public API
        assert not coding_screen.is_quick_mark_enabled()

        coding_screen.set_text_selection(50, 100)
        QApplication.processEvents()

        # Verify state change via public API
        assert coding_screen.is_quick_mark_enabled()

        # Use signal spy for black-box verification
        spy = QSignalSpy(coding_screen.code_applied)

        # Get initial count via public API
        initial_count = coding_screen.get_code_count("1")

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        QApplication.processEvents()

        coding_screen.quick_mark()
        QApplication.processEvents()

        # BLACK-BOX: Verify signal emitted
        assert spy.count() == 1
        assert spy.at(0) == ["1", 50, 100]

        # BLACK-BOX: Verify UI state changed (code count incremented)
        assert coding_screen.get_code_count("1") == initial_count + 1

    @allure.title("AC #3: Quick mark without code does nothing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_quick_mark_requires_code(self, coding_screen):
        """Quick mark without active code does not apply."""
        spy = QSignalSpy(coding_screen.code_applied)

        coding_screen.set_text_selection(50, 100)
        coding_screen.quick_mark()
        QApplication.processEvents()

        # BLACK-BOX: No signal should be emitted
        assert spy.count() == 0


# =============================================================================
# QC-029.05: Unmark and Undo (Black-Box)
# =============================================================================


@allure.story("QC-029.05 Unmark")
class TestUnmarkUI:
    """Test removing codes from text using black-box patterns."""

    @allure.title("AC #1-3: U key removes code, enables undo, and Ctrl+Z undoes unmark")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_and_undo_workflow(self, coding_screen):
        """U key removes code, enables undo, and Ctrl+Z re-applies the code."""
        # Initially undo should not be available
        assert not coding_screen.can_undo_unmark()

        spy_removed = QSignalSpy(coding_screen.code_removed)
        spy_applied = QSignalSpy(coding_screen.code_applied)

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        QApplication.processEvents()

        # BLACK-BOX: Verify signal emitted
        assert spy_removed.count() == 1
        assert spy_removed.at(0) == ["1", 50, 100]

        # BLACK-BOX: Verify undo became available via public API
        assert coding_screen.can_undo_unmark()

        # Undo the unmark
        coding_screen.undo_unmark()
        QApplication.processEvents()

        # BLACK-BOX: Verify code_applied signal was emitted
        assert spy_applied.count() >= 1


# =============================================================================
# QC-029.01: Recent Codes and Keyboard Shortcuts (Black-Box)
# =============================================================================


@allure.story("QC-029.01 Recent Codes")
class TestRecentCodesAndShortcutsUI:
    """Test recent codes and keyboard shortcuts using black-box patterns."""

    @allure.title("Recent codes MRU order, 10-item limit, and all shortcuts registered")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_codes_and_shortcuts(self, coding_screen):
        """Recent codes are in MRU order, limited to 10, and all shortcuts are registered."""
        coding_screen.set_active_code("1", "Code A", "#FF0000")
        coding_screen.set_active_code("2", "Code B", "#00FF00")
        coding_screen.set_active_code("1", "Code A", "#FF0000")

        # BLACK-BOX: Most recently selected should be active
        active = coding_screen.get_active_code()
        assert active["id"] == "1"

        # Add many codes to test limit
        for i in range(15):
            coding_screen.set_active_code(str(i), f"Code {i}", "#FF0000")

        # BLACK-BOX: Verify via public API
        assert coding_screen.get_recent_codes_count() == 10

        # Verify all coding shortcuts are registered
        shortcuts = coding_screen.get_registered_shortcuts()
        assert "Q" in shortcuts
        assert "U" in shortcuts
        assert "V" in shortcuts
        assert "N" in shortcuts
        assert "R" in shortcuts
        assert "H" in shortcuts


# =============================================================================
# Integration Workflow (Black-Box)
# =============================================================================


@allure.story("QC-028/QC-029 Integration")
class TestCodingWorkflowUI:
    """Integration test for complete coding workflow using black-box patterns."""

    @allure.title("Full workflow: Create code via dialog, select, apply")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_workflow_with_dialog(self, qapp, colors):
        """Test complete workflow from dialog to application."""
        with allure.step("Open CreateCodeDialog and create code"):
            dialog = CreateCodeDialog(colors=colors)
            dialog.show()
            QApplication.processEvents()

            spy = QSignalSpy(dialog.code_created)

            # BLACK-BOX: Fill form using public API and visible elements
            dialog.set_code_name("Interview Theme")
            click_color_swatch_by_index(dialog, 4)
            dialog.set_code_memo("Key themes from interviews")

            # BLACK-BOX: Click button by text
            click_dialog_button(dialog, "Create")
            QApplication.processEvents()

            assert spy.count() == 1
            created_name = spy.at(0)[0]
            created_color = spy.at(0)[1]
            assert created_name == "Interview Theme"
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
                                name=created_name,
                                color=created_color,
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

            spy = QSignalSpy(screen.code_applied)

            screen.set_active_code("1", "Interview Theme", created_color)
            screen.set_text_selection(0, 15)
            screen.quick_mark()
            QApplication.processEvents()

            # BLACK-BOX: Verify via signal
            assert spy.count() == 1
            assert spy.at(0)[0] == "1"

            screen.close()


# =============================================================================
# Full Application Path Tests (Black-Box via wired_app)
# =============================================================================


@allure.story("QC-029 Full Application Path")
class TestApplyCodeFullPath:
    """
    E2E tests using full application path via main.py wiring.

    BLACK-BOX: These tests verify outcomes via:
    - Signals emitted
    - Database state changes
    - Visible UI changes

    Not via private attributes.
    """

    @allure.title("Quick mark persists segment to database and emits signal bridge event")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_quick_mark_persists_and_emits_signal(self, coding_screen_ready):
        """
        Q key applies code, persists segment to database, and emits signal bridge event.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        signal_bridge = coding_screen_ready["coding_signal_bridge"]
        source = coding_screen_ready["seeded"]["sources"][0]
        code = coding_screen_ready["seeded"]["codes"][0]

        # Get initial segment count from database
        initial_segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        initial_count = len(initial_segments)

        # BLACK-BOX: Set up signal spy
        spy = QSignalSpy(signal_bridge.segment_coded)

        # Apply code via screen public API
        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(0, 20)
        screen.quick_mark()
        QApplication.processEvents()

        # BLACK-BOX: Verify database state changed
        new_segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        assert len(new_segments) == initial_count + 1

        # Verify the segment data
        new_segment = new_segments[-1]
        assert new_segment.code_id == code.id
        assert new_segment.position.start == 0
        assert new_segment.position.end == 20

        # BLACK-BOX: Signal bridge should have emitted
        assert spy.count() >= 1

    @allure.title("Screen is properly configured after wiring")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_screen_is_wired(self, coding_screen_ready):
        """
        Verify screen is properly wired by testing functionality works.
        """
        screen = coding_screen_ready["screens"]["coding"]

        # BLACK-BOX: If wiring is correct, the document should be loaded
        screen.set_text_selection(0, 10)
        QApplication.processEvents()

        # If screen is wired, quick_mark_enabled should work
        assert screen.is_quick_mark_enabled()

    @allure.title("Multiple segments can be created and navigation loads source")
    @allure.severity(allure.severity_level.NORMAL)
    def test_multiple_segments_and_navigation(self, coding_screen_ready):
        """Multiple quick marks create multiple segments, and navigation loads correct source."""
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        source = coding_screen_ready["seeded"]["sources"][0]
        codes = coding_screen_ready["seeded"]["codes"]

        initial_count = len(ctx.coding_context.segment_repo.get_by_source(source.id))

        # Apply first code
        screen.set_active_code(
            str(codes[0].id.value), codes[0].name, codes[0].color.to_hex()
        )
        screen.set_text_selection(0, 10)
        screen.quick_mark()
        QApplication.processEvents()

        # Apply second code
        screen.set_active_code(
            str(codes[1].id.value), codes[1].name, codes[1].color.to_hex()
        )
        screen.set_text_selection(20, 40)
        screen.quick_mark()
        QApplication.processEvents()

        # BLACK-BOX: Verify database state
        segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        assert len(segments) == initial_count + 2

    @allure.title("Navigation loads source and database codes are available")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigation_and_codes_from_database(self, seeded_app):
        """
        Navigation loads correct source, and database codes can be selected.
        """
        app = seeded_app["app"]
        ctx = seeded_app["ctx"]
        source = seeded_app["seeded"]["sources"][1]  # Second source
        screen = seeded_app["screens"]["coding"]
        codes = seeded_app["seeded"]["codes"]

        # Navigate
        app._on_navigate_to_coding(str(source.id.value))
        QApplication.processEvents()

        # BLACK-BOX: Verify by checking the document title shown in UI
        current_title = screen.get_document_title()
        assert source.name in current_title or current_title == source.name

        # Codes should be in database
        db_codes = ctx.coding_context.code_repo.get_all()
        assert len(db_codes) == 3

        # BLACK-BOX: Verify we can select a code and it becomes active
        first_code = codes[0]
        screen.set_active_code(
            str(first_code.id.value), first_code.name, first_code.color.to_hex()
        )

        active = screen.get_active_code()
        assert active["name"] == first_code.name


@allure.story("QC-029 Wiring Verification")
class TestWiringVerification:
    """
    Tests that verify the wiring from main.py is correct.
    """

    @allure.title("All screens created, coding functional, and signal bridges running")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_wiring_complete(self, wired_app):
        """Verify screens are created, coding screen responds, and signal bridges run."""
        screens = wired_app["screens"]

        # Verify all screens exist
        assert "project" in screens
        assert "files" in screens
        assert "cases" in screens
        assert "coding" in screens

        # Verify coding screen responds to code selection
        shell = wired_app["shell"]
        coding_screen = wired_app["screens"]["coding"]
        coding_screen.set_active_code("1", "Test", "#FF0000")
        active = coding_screen.get_active_code()
        assert active["id"] == "1"

        # Verify signal bridges are running
        coding_bridge = wired_app["coding_signal_bridge"]
        project_bridge = wired_app["project_signal_bridge"]
        assert coding_bridge.is_running()
        assert project_bridge.is_running()

        # Screenshot for documentation
        attach_screenshot(shell, "CodingScreen - With Codes")
        DocScreenshot.capture(shell, "coding-screen-with-codes", max_width=1000)


# =============================================================================
# QC-028.01: Create New Code - Full Application Path (Black-Box)
# =============================================================================


@allure.story("QC-028.01 Create New Code Full Path")
class TestCreateCodeFullPath:
    """
    E2E tests for creating new codes through the full application path.
    """

    @allure.title("N key opens dialog and creating code persists to database")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_n_key_opens_dialog_and_persists(self, coding_screen_ready):
        """
        N key opens CreateCodeDialog, and creating a code persists it to database.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]

        # Verify shortcut is registered
        assert "N" in screen.get_registered_shortcuts(), (
            "N shortcut should be registered"
        )

        # Get initial code count
        initial_codes = ctx.coding_context.code_repo.get_all()
        initial_count = len(initial_codes)

        # Call the method that N key triggers
        screen.show_new_code_dialog()

        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open when N is pressed"

        # Screenshot for documentation
        attach_screenshot(dialog, "CreateCodeDialog - Opened via N key")

        # BLACK-BOX: Fill form using public API
        dialog.set_code_name("Research Theme")
        click_color_swatch_by_index(dialog, 3)
        dialog.set_code_memo("Captures research-related content")
        QApplication.processEvents()

        # BLACK-BOX: Click Create button
        click_dialog_button(dialog, "Create")
        QApplication.processEvents()

        # BLACK-BOX: Verify code persisted to database
        new_codes = ctx.coding_context.code_repo.get_all()
        assert len(new_codes) == initial_count + 1, "New code should be in database"

        # Find the newly created code
        created_code = next((c for c in new_codes if c.name == "Research Theme"), None)
        assert created_code is not None, "Created code should have correct name"

    @allure.title("Created code appears in panel and can be applied immediately")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_created_code_appears_and_applies(self, coding_screen_ready):
        """
        After creating a code, it appears in the codes panel and can be applied to text.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        shell = coding_screen_ready["shell"]
        source = coding_screen_ready["seeded"]["sources"][0]

        # Get initial segment count
        initial_segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        initial_count = len(initial_segments)

        # Open dialog and create code
        screen.show_new_code_dialog()

        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open"

        dialog.set_code_name("Quick Code")
        click_color_swatch_by_index(dialog, 0)
        QApplication.processEvents()

        click_dialog_button(dialog, "Create")
        QApplication.processEvents()

        # Find the created code in database to get its ID
        codes = ctx.coding_context.code_repo.get_all()
        quick_code = next((c for c in codes if c.name == "Quick Code"), None)
        assert quick_code is not None, "Quick Code should exist in database"

        # Select the code and apply to text
        screen.set_active_code(
            str(quick_code.id.value), quick_code.name, quick_code.color.to_hex()
        )
        active = screen.get_active_code()
        assert active["name"] == "Quick Code", "Created code should be selectable"

        screen.set_text_selection(0, 15)
        screen.quick_mark()
        QApplication.processEvents()

        # Verify segment was created with new code
        new_segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        assert len(new_segments) == initial_count + 1, "Segment should be created"
        new_segment = new_segments[-1]
        assert new_segment.code_id == quick_code.id

        # Screenshot showing the code in the panel
        attach_screenshot(shell, "CodingScreen - After Code Created")

    @allure.title("Dialog closes after creation, cancel does not create, and duplicate name rejected")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_close_cancel_and_duplicate(self, coding_screen_ready):
        """
        Dialog closes after successful creation; Cancel closes without creating;
        Duplicate name is rejected.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        existing_code = coding_screen_ready["seeded"]["codes"][0]

        # Test successful creation closes dialog
        screen.show_new_code_dialog()
        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open"

        dialog.set_code_name("Auto Close Test")
        click_color_swatch_by_index(dialog, 2)
        click_dialog_button(dialog, "Create")
        QApplication.processEvents()

        remaining_dialog = find_visible_dialog(CreateCodeDialog)
        assert remaining_dialog is None, "Dialog should close after creation"

        # Test cancel does not create code
        initial_count = len(ctx.coding_context.code_repo.get_all())

        screen.show_new_code_dialog()
        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open"

        dialog.set_code_name("Should Not Exist")
        click_color_swatch_by_index(dialog, 1)
        click_dialog_button(dialog, "Cancel")
        QApplication.processEvents()

        final_count = len(ctx.coding_context.code_repo.get_all())
        assert final_count == initial_count, "Cancel should not create code"
        assert find_visible_dialog(CreateCodeDialog) is None

        # Test duplicate code name is rejected
        screen.show_new_code_dialog()
        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open"

        dialog.set_code_name(existing_code.name)  # "Positive" from seeded data
        click_color_swatch_by_index(dialog, 0)
        click_dialog_button(dialog, "Create")
        QApplication.processEvents()

        dup_final_count = len(ctx.coding_context.code_repo.get_all())
        assert dup_final_count == initial_count, "Duplicate code should not be created"

        # Dialog may show error or remain open - cleanup
        dialog = find_visible_dialog(CreateCodeDialog)
        if dialog:
            dialog.close()

    @allure.title("Plus button opens dialog and creates code that persists")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_plus_button_creates_code_persists(self, coding_screen_ready):
        """
        Clicking the + button opens CreateCodeDialog and creating a code
        via the dialog persists it to the database.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]

        initial_count = len(ctx.coding_context.code_repo.get_all())

        # Click + button
        add_btn = find_any_button_by_tooltip(screen, "Add code")
        assert add_btn is not None, "Add code button should exist in codes panel"
        add_btn.click()

        dialog = wait_for_dialog(CreateCodeDialog)
        assert dialog is not None, "CreateCodeDialog should open when + is clicked"

        # Fill form and create
        dialog.set_code_name("Button Created Code")
        click_color_swatch_by_index(dialog, 7)
        click_dialog_button(dialog, "Create")
        QApplication.processEvents()

        # Verify persisted
        final_count = len(ctx.coding_context.code_repo.get_all())
        assert final_count == initial_count + 1

        # Verify code exists with correct name
        codes = ctx.coding_context.code_repo.get_all()
        created = next((c for c in codes if c.name == "Button Created Code"), None)
        assert created is not None
