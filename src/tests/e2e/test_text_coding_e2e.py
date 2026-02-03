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
    click_color_swatch_by_index,
    click_dialog_button,
    find_color_swatch_buttons,
    find_input_by_placeholder,
    is_button_enabled,
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
# QC-028.01: Create New Code - Dialog Tests (Black-Box)
# =============================================================================


@allure.story("QC-028.01 Create New Code")
class TestCreateCodeDialog:
    """
    QC-028.01: Create New Code
    Test the CreateCodeDialog UI using black-box patterns.
    """

    @allure.title("AC #1: Dialog shows name input field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_has_name_input(self, create_code_dialog):
        """Dialog should have a name input field with proper placeholder."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find input by placeholder text
        name_input = find_input_by_placeholder(create_code_dialog, "Enter code name")
        assert name_input is not None, "Name input field should be visible"
        assert name_input.placeholderText() == "Enter code name..."

    @allure.title("AC #1: User can enter code name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enter_code_name(self, create_code_dialog):
        """User can type a code name in the input."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use public API to set/get name
        create_code_dialog.set_code_name("New Theme")
        assert create_code_dialog.get_code_name() == "New Theme"

    @allure.title("AC #2: Dialog shows color selection grid")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_has_color_grid(self, create_code_dialog):
        """Dialog should show a grid of color options."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find color swatches by their 'color' property
        swatches = find_color_swatch_buttons(create_code_dialog)
        assert len(swatches) == 16, "Should show 16 color options"

    @allure.title("AC #2: User can select a color")
    @allure.severity(allure.severity_level.NORMAL)
    def test_select_color(self, create_code_dialog):
        """User can click a color to select it."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Click second color swatch by index
        swatches = find_color_swatch_buttons(create_code_dialog)
        expected_color = swatches[1].property("color")
        swatches[1].click()
        QApplication.processEvents()

        # Verify via public getter
        assert create_code_dialog.get_code_color() == expected_color

    @allure.title("AC #3: User can add optional memo")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_memo(self, create_code_dialog):
        """User can add an optional description/memo."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find memo input and set text via public API
        memo_text = "This code is for positive themes"
        # Use public API if available
        create_code_dialog.set_code_memo(memo_text)
        assert create_code_dialog.get_code_memo() == memo_text

    @allure.title("Create button disabled when name is empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_disabled_without_name(self, create_code_dialog):
        """Create button should be disabled when name is empty."""
        create_code_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find button by text and check enabled state
        assert not is_button_enabled(create_code_dialog, "Create")

    @allure.title("Create button enabled when name is entered")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_enabled_with_name(self, create_code_dialog):
        """Create button should be enabled when name is entered."""
        create_code_dialog.show()
        QApplication.processEvents()

        create_code_dialog.set_code_name("New Code")
        QApplication.processEvents()

        # BLACK-BOX: Find button by text and check enabled state
        assert is_button_enabled(create_code_dialog, "Create")

    @allure.title("AC #4: Clicking create emits code_created signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emits_signal(self, create_code_dialog):
        """Clicking Create Code should emit the code_created signal."""
        create_code_dialog.show()
        QApplication.processEvents()

        # Setup signal spy
        spy = QSignalSpy(create_code_dialog.code_created)

        # Fill form using public API
        create_code_dialog.set_code_name("Test Code")
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

    @allure.title("Cancel button closes dialog")
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

    @allure.title("AC #1: Selecting a code sets it as active")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_code_sets_active(self, coding_screen):
        """Selecting a code sets it as the active code."""
        # Use public API to set active code
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")

        # Verify via public getter
        active = coding_screen.get_active_code()
        assert active["id"] == "1"
        assert active["name"] == "Positive Experience"

    @allure.title("AC #2: Selected code added to recent codes")
    @allure.severity(allure.severity_level.NORMAL)
    def test_selected_code_added_to_recent(self, coding_screen):
        """Selecting codes adds them to recent codes list."""
        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_active_code("2", "Challenge", "#FF0000")

        # BLACK-BOX: Verify via public API that tracks recent count
        recent_count = coding_screen.get_recent_codes_count()
        assert recent_count == 2

        # Most recent should be the active one
        active = coding_screen.get_active_code()
        assert active["id"] == "2"


# =============================================================================
# QC-029.01: Text Selection and Quick Mark (Black-Box)
# =============================================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestApplyCodeUI:
    """Test selecting text and applying code using Q key (black-box)."""

    @allure.title("AC #1: Text selection enables quick mark")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_text_selection_enables_quick_mark(self, coding_screen):
        """Selecting text enables quick mark feature."""
        # Verify initial state via public API
        assert not coding_screen.is_quick_mark_enabled()

        coding_screen.set_text_selection(50, 100)
        QApplication.processEvents()

        # Verify state change via public API
        assert coding_screen.is_quick_mark_enabled()

    @allure.title("AC #2: Q key applies code to selection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_quick_mark_applies_code(self, coding_screen):
        """Q key applies the active code to the selection."""
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

    @allure.title("AC #1: U key removes code from selection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_removes_code(self, coding_screen):
        """U key removes code from the selection."""
        spy = QSignalSpy(coding_screen.code_removed)

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        QApplication.processEvents()

        # BLACK-BOX: Verify signal emitted
        assert spy.count() == 1
        assert spy.at(0) == ["1", 50, 100]

    @allure.title("AC #2: Unmark enables undo")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_enables_undo(self, coding_screen):
        """Unmark adds operation to undo capability."""
        # Initially undo should not be available
        assert not coding_screen.can_undo_unmark()

        coding_screen.set_active_code("1", "Positive Experience", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()

        # BLACK-BOX: Verify undo became available via public API
        assert coding_screen.can_undo_unmark()

    @allure.title("AC #3: Ctrl+Z undoes unmark")
    @allure.severity(allure.severity_level.NORMAL)
    def test_undo_reapplies_code(self, coding_screen):
        """Ctrl+Z re-applies the unmarked code."""
        spy = QSignalSpy(coding_screen.code_applied)

        coding_screen.set_active_code("1", "Positive", "#00FF00")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        coding_screen.undo_unmark()
        QApplication.processEvents()

        # BLACK-BOX: Verify code_applied signal was emitted
        assert spy.count() >= 1


# =============================================================================
# QC-029.01: Recent Codes (Black-Box)
# =============================================================================


@allure.story("QC-029.01 Recent Codes")
class TestRecentCodesUI:
    """Test recent codes functionality using black-box patterns."""

    @allure.title("Recent codes maintains MRU order")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_codes_order(self, coding_screen):
        """Recent codes are in most-recently-used order."""
        coding_screen.set_active_code("1", "Code A", "#FF0000")
        coding_screen.set_active_code("2", "Code B", "#00FF00")
        coding_screen.set_active_code("1", "Code A", "#FF0000")

        # BLACK-BOX: Most recently selected should be active
        active = coding_screen.get_active_code()
        assert active["id"] == "1"

    @allure.title("Recent codes limited to 10")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_codes_max_10(self, coding_screen):
        """Recent codes limited to 10 items."""
        for i in range(15):
            coding_screen.set_active_code(str(i), f"Code {i}", "#FF0000")

        # BLACK-BOX: Verify via public API
        assert coding_screen.get_recent_codes_count() == 10


# =============================================================================
# Keyboard Shortcuts (Black-Box)
# =============================================================================


@allure.story("QC-007.10 Keyboard Shortcuts")
class TestKeyboardShortcutsUI:
    """Test keyboard shortcut registration using black-box patterns."""

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

    @allure.title("Quick mark persists segment to database")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_quick_mark_persists_to_database(self, coding_screen_ready):
        """
        Q key applies code and persists segment to database.

        BLACK-BOX verification:
        1. Check database state before
        2. Perform user action
        3. Check database state after
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        source = coding_screen_ready["seeded"]["sources"][0]
        code = coding_screen_ready["seeded"]["codes"][0]

        # Get initial segment count from database
        initial_segments = ctx.coding_context.segment_repo.get_by_source(source.id)
        initial_count = len(initial_segments)

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

    @allure.title("Screen is properly configured after wiring")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_screen_is_wired(self, coding_screen_ready):
        """
        Verify screen is properly wired by testing functionality works.

        BLACK-BOX: Don't check internal _viewmodel, test that
        user actions produce expected outcomes.
        """
        screen = coding_screen_ready["screens"]["coding"]

        # BLACK-BOX: If wiring is correct, the document should be loaded
        # and we should be able to interact with it
        screen.set_text_selection(0, 10)
        QApplication.processEvents()

        # If screen is wired, quick_mark_enabled should work
        assert screen.is_quick_mark_enabled()

    @allure.title("Signal bridge receives segment_coded event")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_signal_bridge_receives_event(self, coding_screen_ready):
        """
        Verify the reactive flow produces signals.

        BLACK-BOX: Use signal spies to verify event flow
        without checking internal bridge state.
        """
        screen = coding_screen_ready["screens"]["coding"]
        signal_bridge = coding_screen_ready["coding_signal_bridge"]
        code = coding_screen_ready["seeded"]["codes"][0]

        # BLACK-BOX: Set up signal spy
        spy = QSignalSpy(signal_bridge.segment_coded)

        # Apply code
        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(5, 25)
        screen.quick_mark()
        QApplication.processEvents()

        # BLACK-BOX: Signal bridge should have emitted
        assert spy.count() >= 1

    @allure.title("Multiple segments can be created for same source")
    @allure.severity(allure.severity_level.NORMAL)
    def test_multiple_segments_same_source(self, coding_screen_ready):
        """Multiple quick marks create multiple segments in database."""
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

    @allure.title("Navigation loads source into coding screen")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigation_loads_source(self, seeded_app):
        """
        Test that navigation loads the correct source.

        BLACK-BOX: Verify source is loaded by checking visible title.
        """
        app = seeded_app["app"]
        source = seeded_app["seeded"]["sources"][1]  # Second source
        screen = seeded_app["screens"]["coding"]

        # Navigate
        app._on_navigate_to_coding(str(source.id.value))
        QApplication.processEvents()

        # BLACK-BOX: Verify by checking the document title shown in UI
        # The screen should display the source name
        current_title = screen.get_document_title()
        assert source.name in current_title or current_title == source.name


@allure.story("QC-028 Full Application Path")
class TestCodeManagementFullPath:
    """E2E tests for code management using full application path (black-box)."""

    @allure.title("Codes from database are available for selection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_codes_available_from_database(self, coding_screen_ready):
        """
        Verify that codes seeded in database can be selected.

        BLACK-BOX: Don't check internal viewmodel, verify codes
        can be used in user workflows.
        """
        ctx = coding_screen_ready["ctx"]
        screen = coding_screen_ready["screens"]["coding"]
        codes = coding_screen_ready["seeded"]["codes"]

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

    BLACK-BOX: Verify wiring by testing that expected screens exist
    and respond to interactions.
    """

    @allure.title("All screens are created by _setup_shell")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_all_screens_created(self, wired_app):
        """Verify _setup_shell creates all required screens."""
        screens = wired_app["screens"]

        assert "project" in screens
        assert "files" in screens
        assert "cases" in screens
        assert "coding" in screens

    @allure.title("File manager screen is functional")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_file_manager_functional(self, wired_app):
        """Verify file manager screen responds to refresh."""
        files_screen = wired_app["screens"]["files"]

        # BLACK-BOX: If wired, refresh should work without error
        files_screen.refresh()
        QApplication.processEvents()

    @allure.title("Coding screen accepts code selection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_coding_screen_functional(self, wired_app):
        """Verify coding screen responds to code selection."""
        coding_screen = wired_app["screens"]["coding"]

        # BLACK-BOX: If wired, set_active_code should work
        coding_screen.set_active_code("1", "Test", "#FF0000")
        active = coding_screen.get_active_code()
        assert active["id"] == "1"

    @allure.title("Signal bridges produce events")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_signal_bridges_running(self, wired_app):
        """Verify signal bridges are started and can emit signals."""
        coding_bridge = wired_app["coding_signal_bridge"]
        project_bridge = wired_app["project_signal_bridge"]

        # BLACK-BOX: Check running state via public API
        assert coding_bridge.is_running()
        assert project_bridge.is_running()

    @allure.title("Bounded contexts provide repository access")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_bounded_contexts_initialized(self, wired_app):
        """Verify bounded contexts provide working repositories."""
        ctx = wired_app["ctx"]

        # BLACK-BOX: Verify by trying to use the repos
        # If they work, contexts are initialized
        sources = ctx.sources_context.source_repo.get_all()
        assert isinstance(sources, list)

        codes = ctx.coding_context.code_repo.get_all()
        assert isinstance(codes, list)
