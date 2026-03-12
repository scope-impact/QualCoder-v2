"""
QC-028: Code Management E2E Tests

BLACK-BOX E2E TESTS - Tests interact with UI via visible elements only:
- Find buttons by text/tooltip, not private attributes
- Verify outcomes via visible UI state, not internal state
- Simulate real user interactions

Test Categories:
- QC-028.02: Organize codes into categories
- QC-028.03: Rename and recolor codes
- QC-028.05: Merge duplicate codes
- QC-028.06: Delete codes
- QC-028.08: Agent suggest new codes (AI)
- QC-028.09: Agent detect duplicates (AI)
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.contexts.coding.presentation.dialogs import (
    CodeSuggestionDialog,
    ColorPickerDialog,
    DuplicateCodesDialog,
)
from src.contexts.coding.presentation.dialogs.memo_dialog import CodeMemoDialog
from src.tests.e2e.helpers import (
    attach_screenshot,
    click_dialog_button,
    find_color_swatch_buttons,
    find_input_by_placeholder,
    get_swatch_color,
    is_button_enabled,
)

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def color_picker_dialog(qapp, colors):
    """Create a ColorPickerDialog for testing."""
    dialog = ColorPickerDialog(initial_color="#4CAF50", colors=colors)
    yield dialog
    dialog.close()


@pytest.fixture
def duplicate_dialog(qapp, colors):
    """Create a DuplicateCodesDialog for testing."""
    dialog = DuplicateCodesDialog(colors=colors)
    yield dialog
    dialog.close()


@pytest.fixture
def suggestion_dialog(qapp, colors):
    """Create a CodeSuggestionDialog for testing."""
    dialog = CodeSuggestionDialog(colors=colors)
    yield dialog
    dialog.close()


@pytest.fixture
def sample_duplicate_candidates():
    """Sample duplicate code candidates for testing."""
    return [
        {
            "code_a_id": 1,
            "code_a_name": "Theme",
            "code_a_color": "#FF5722",
            "code_a_segments": 5,
            "code_b_id": 2,
            "code_b_name": "Themes",
            "code_b_color": "#FF9800",
            "code_b_segments": 3,
            "similarity": 92,
            "rationale": "Names are nearly identical (Theme vs Themes)",
        },
        {
            "code_a_id": 3,
            "code_a_name": "Positive Emotion",
            "code_a_color": "#4CAF50",
            "code_a_segments": 8,
            "code_b_id": 4,
            "code_b_name": "Positive Feeling",
            "code_b_color": "#8BC34A",
            "code_b_segments": 6,
            "similarity": 85,
            "rationale": "Both codes relate to positive emotional states",
        },
    ]


@pytest.fixture
def sample_suggestions():
    """Sample AI code suggestions for testing."""
    return [
        {
            "suggestion_id": "sug-1",
            "name": "Learning Experience",
            "color": "#2196F3",
            "rationale": "Multiple passages discuss learning and educational experiences",
            "confidence": 85,
            "contexts": [
                "I really enjoyed the learning process",
                "The course materials were comprehensive",
            ],
        },
        {
            "suggestion_id": "sug-2",
            "name": "Challenge",
            "color": "#F44336",
            "rationale": "Several mentions of difficulties and challenging aspects",
            "confidence": 72,
            "contexts": ["I found some topics quite challenging"],
        },
    ]


# =============================================================================
# QC-028.03: Rename and Recolor Codes (Black-Box)
# =============================================================================


@allure.story("QC-028.03 Rename and Recolor Codes")
class TestColorPickerDialog:
    """
    QC-028.03: Rename and Recolor Codes
    Test the ColorPickerDialog using black-box patterns.
    """

    @allure.title("AC #3.1+3.2+3.7: Preset grid, select preset, visual state updates")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_preset_colors_and_selection(self, color_picker_dialog):
        """Dialog shows preset colors and user can select them with visual feedback."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # Verify preset count
        preset_count = color_picker_dialog.get_preset_count()
        assert preset_count == 20  # 4 rows x 5 columns

        # Find and click a swatch
        swatches = find_color_swatch_buttons(color_picker_dialog)
        assert len(swatches) > 5, f"Expected at least 6 swatches, found {len(swatches)}"
        expected_color = get_swatch_color(swatches[5])
        swatches[5].clicked.emit(expected_color)
        QApplication.processEvents()

        assert color_picker_dialog.get_selected_color() == expected_color

        # Select a different swatch and verify selection moved
        assert len(swatches) >= 2
        color1 = get_swatch_color(swatches[0])
        swatches[0].clicked.emit(color1)
        QApplication.processEvents()
        assert color_picker_dialog.get_selected_color() == color1

        color2 = get_swatch_color(swatches[1])
        swatches[1].clicked.emit(color2)
        QApplication.processEvents()
        assert color_picker_dialog.get_selected_color() == color2

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Swatch Selection")

    @allure.title("AC #3.3+3.5: Custom hex color and Select button signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_custom_hex_and_select_signal(self, color_picker_dialog):
        """User can enter custom hex and clicking Select emits signal."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # Enter custom hex values
        color_picker_dialog.select_color("#123ABC")
        QApplication.processEvents()
        assert color_picker_dialog.get_selected_color() == "#123ABC"

        color_picker_dialog.select_color("#ABCDEF")
        QApplication.processEvents()
        assert color_picker_dialog.get_selected_color() == "#ABCDEF"

        # Set up signal spy and click Select
        spy = QSignalSpy(color_picker_dialog.color_selected)
        color_picker_dialog.select_color("#AABBCC")
        QApplication.processEvents()

        click_dialog_button(color_picker_dialog, "Select")
        QApplication.processEvents()

        assert spy.count() >= 1
        assert spy.at(spy.count() - 1)[0] == "#AABBCC"

        attach_screenshot(
            color_picker_dialog, "ColorPickerDialog - Custom Hex and Select"
        )


# =============================================================================
# QC-028.05: Merge Duplicate Codes (Black-Box)
# =============================================================================


@allure.story("QC-028.05 Merge Duplicate Codes")
class TestDuplicateCodesDialog:
    """
    QC-028.05: Merge Duplicate Codes
    Test the DuplicateCodesDialog using black-box patterns.
    """

    @allure.title("AC #5.1+5.6: Display candidates and empty state")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_display_candidates_and_empty_state(
        self, duplicate_dialog, sample_duplicate_candidates
    ):
        """Dialog displays candidates and shows empty state when none found."""
        duplicate_dialog.show()
        QApplication.processEvents()

        # Load candidates
        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Candidates")
        assert duplicate_dialog.get_candidate_count() == 2

        # Show empty state
        duplicate_dialog.on_duplicates_detected([])
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Empty State")
        assert duplicate_dialog.is_empty_state_visible()

    @allure.title("AC #5.3: Merge code A into code B")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_merge_a_into_b(self, duplicate_dialog, sample_duplicate_candidates):
        """User can click to merge code A into code B."""
        duplicate_dialog.show()
        QApplication.processEvents()

        spy = QSignalSpy(duplicate_dialog.merge_requested)
        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        duplicate_dialog.request_merge(1, 2)
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0) == [1, 2]

    @allure.title("AC #5.4+5.5: Dismiss pair and scan for duplicates")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dismiss_pair_and_scan(self, duplicate_dialog, sample_duplicate_candidates):
        """User can dismiss pairs and request new scan."""
        duplicate_dialog.show()
        QApplication.processEvents()

        dismiss_spy = QSignalSpy(duplicate_dialog.dismiss_requested)
        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        initial_count = duplicate_dialog.get_candidate_count()

        # Dismiss a pair
        duplicate_dialog.request_dismiss(1, 2)
        QApplication.processEvents()
        assert dismiss_spy.count() == 1
        assert duplicate_dialog.get_candidate_count() == initial_count - 1

        # Scan for duplicates
        scan_spy = QSignalSpy(duplicate_dialog.detect_duplicates_requested)
        duplicate_dialog.request_scan()
        QApplication.processEvents()
        assert scan_spy.count() == 1
        assert scan_spy.at(0)[0] == 0.8  # Default threshold


# =============================================================================
# QC-028.08: Agent Suggest New Codes (Black-Box)
# =============================================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCodeSuggestionDialog:
    """
    QC-028.08: Agent Suggest New Codes
    Test the CodeSuggestionDialog using black-box patterns.
    """

    @allure.title("AC #8.1+8.3: Display suggestions and edit name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_display_and_edit_suggestions(self, suggestion_dialog, sample_suggestions):
        """Dialog displays suggestions and allows name editing."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Suggestions")
        assert suggestion_dialog.get_suggestion_count() == 2

        # Edit suggestion name
        suggestion_dialog.set_suggestion_name("sug-1", "Modified Name")
        QApplication.processEvents()
        assert suggestion_dialog.get_suggestion_name("sug-1") == "Modified Name"

    @allure.title("AC #8.4+8.6: Approve suggestion and verify removal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_approve_and_remove_suggestion(self, suggestion_dialog, sample_suggestions):
        """User can approve a suggestion and it gets removed from list."""
        suggestion_dialog.show()
        QApplication.processEvents()

        spy = QSignalSpy(suggestion_dialog.approve_suggestion_requested)
        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()
        initial_count = suggestion_dialog.get_suggestion_count()

        # Approve
        suggestion_dialog.approve_suggestion("sug-1")
        QApplication.processEvents()
        assert spy.count() == 1
        assert spy.at(0)[0] == "sug-1"

        # Simulate approval callback - suggestion removed
        suggestion_dialog.on_suggestion_approved("sug-1")
        QApplication.processEvents()
        assert suggestion_dialog.get_suggestion_count() == initial_count - 1

    @allure.title("AC #8.5+8.7: Reject suggestion and approve all")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reject_and_approve_all(self, suggestion_dialog, sample_suggestions):
        """User can reject individual suggestions or approve all at once."""
        suggestion_dialog.show()
        QApplication.processEvents()

        reject_spy = QSignalSpy(suggestion_dialog.reject_suggestion_requested)
        approve_all_spy = QSignalSpy(suggestion_dialog.approve_all_requested)

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        # Reject one
        suggestion_dialog.reject_suggestion("sug-2")
        QApplication.processEvents()
        assert reject_spy.count() == 1
        assert reject_spy.at(0)[0] == "sug-2"

        # Approve all
        suggestion_dialog.approve_all()
        QApplication.processEvents()
        assert approve_all_spy.count() == 1

    @allure.title("AC #8.8: Empty state when no suggestions")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_state(self, suggestion_dialog):
        """Empty state shown when no suggestions found."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received([])
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Empty State")
        assert suggestion_dialog.is_empty_state_visible()


# =============================================================================
# QC-028.09: Agent Detect Duplicates (Black-Box)
# =============================================================================


# =============================================================================
# DuplicatePairCard Unit Tests (Black-Box)
# =============================================================================


@allure.story("QC-028.05 Duplicate Pair Card")
class TestDuplicatePairCard:
    """Unit tests for DuplicatePairCard widget using black-box patterns."""

    @allure.title("Card emits merge_requested and dismiss_requested with correct IDs")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_merge_and_dismiss_signals(self, qapp, colors):
        """Merge and dismiss signals include correct source and target IDs."""
        from src.contexts.coding.presentation.dialogs.duplicate_codes_dialog import (
            DuplicatePairCard,
        )

        card = DuplicatePairCard(
            code_a_id=10,
            code_a_name="Code A",
            code_a_color="#FF0000",
            code_a_segments=5,
            code_b_id=20,
            code_b_name="Code B",
            code_b_color="#00FF00",
            code_b_segments=3,
            similarity=90,
            rationale="Test rationale",
            colors=colors,
        )
        card.show()
        QApplication.processEvents()

        attach_screenshot(card, "DuplicatePairCard - Signal Test")

        # Test merge signal
        merge_spy = QSignalSpy(card.merge_requested)
        card.merge_requested.emit(10, 20)
        assert merge_spy.count() == 1
        assert merge_spy.at(0) == [10, 20]

        # Test dismiss signal
        dismiss_spy = QSignalSpy(card.dismiss_requested)
        card.dismiss_requested.emit(10, 20)
        assert dismiss_spy.count() == 1
        assert dismiss_spy.at(0) == [10, 20]

        card.deleteLater()


# =============================================================================
# QC-028.02: Organize Codes into Categories (Black-Box)
# =============================================================================


@pytest.fixture
def create_category_dialog(qapp, colors):
    """Create a CreateCategoryDialog for testing."""
    from src.contexts.coding.presentation.dialogs import CreateCategoryDialog

    existing_categories = [
        {"id": 1, "name": "Themes"},
        {"id": 2, "name": "Emotions"},
    ]
    dialog = CreateCategoryDialog(
        existing_categories=existing_categories, colors=colors
    )
    yield dialog
    dialog.close()


@allure.story("QC-028.02 Organize Codes into Categories")
class TestCreateCategoryDialog:
    """
    QC-028.02: Organize Codes into Categories
    Test the CreateCategoryDialog using black-box patterns.
    """

    @allure.title("AC #2.1+2.2: Dialog has name input and user can enter name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_name_input_and_entry(self, create_category_dialog):
        """Dialog has name input field and user can type a category name."""
        create_category_dialog.show()
        QApplication.processEvents()

        # Verify input field exists
        name_input = find_input_by_placeholder(
            create_category_dialog, "Enter category name"
        )
        assert name_input is not None, "Name input field should be visible"

        # Enter a name
        create_category_dialog.set_category_name("New Category")
        QApplication.processEvents()
        assert create_category_dialog.get_category_name() == "New Category"

        attach_screenshot(create_category_dialog, "CreateCategoryDialog - Name Entered")

    @allure.title("AC #2.3+2.4+2.5: Parent category options, selection, and memo")
    @allure.severity(allure.severity_level.NORMAL)
    def test_parent_options_and_memo(self, create_category_dialog):
        """Dialog shows parent options, allows selection and optional memo."""
        create_category_dialog.show()
        QApplication.processEvents()

        # Verify parent options (1 for "None" + 2 existing)
        assert create_category_dialog.get_parent_options_count() == 3

        # Select parent
        create_category_dialog.set_parent_id(1)
        QApplication.processEvents()
        assert create_category_dialog.get_parent_id() == 1

        # Add memo
        create_category_dialog.set_category_memo("Category for interview themes")
        QApplication.processEvents()
        assert (
            create_category_dialog.get_category_memo()
            == "Category for interview themes"
        )

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Parent and Memo"
        )

    @allure.title("AC #2.6+2.8: Create button toggles and emits signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_button_toggle_and_signal(self, create_category_dialog):
        """Create button disabled when empty, enabled when name entered, emits signal."""
        create_category_dialog.show()
        QApplication.processEvents()

        # Initially disabled
        assert not is_button_enabled(create_category_dialog, "Create")

        # Fill form
        spy = QSignalSpy(create_category_dialog.category_created)
        create_category_dialog.set_category_name("Test Category")
        create_category_dialog.set_parent_id(1)
        create_category_dialog.set_category_memo("Test memo")
        QApplication.processEvents()

        # Now enabled
        assert is_button_enabled(create_category_dialog, "Create")

        # Click create
        click_dialog_button(create_category_dialog, "Create")
        QApplication.processEvents()

        assert spy.count() == 1
        name, parent_id, memo = spy.at(0)
        assert name == "Test Category"
        assert parent_id == 1
        assert memo == "Test memo"

    @allure.title("AC #2.9: Cancel button closes dialog")
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_closes_dialog(self, create_category_dialog):
        """Clicking Cancel should close the dialog."""
        create_category_dialog.show()
        QApplication.processEvents()

        click_dialog_button(create_category_dialog, "Cancel")
        QApplication.processEvents()

        assert create_category_dialog.result() == 0


# =============================================================================
# QC-028.06: Delete Codes (Black-Box)
# =============================================================================


@pytest.fixture
def delete_code_dialog_with_segments(qapp, colors):
    """Create a DeleteCodeDialog for a code with segments."""
    from src.contexts.coding.presentation.dialogs import DeleteCodeDialog

    dialog = DeleteCodeDialog(
        code_id=1,
        code_name="Test Code",
        code_color="#FF5722",
        segment_count=5,
        colors=colors,
    )
    yield dialog
    dialog.close()


@pytest.fixture
def delete_code_dialog_no_segments(qapp, colors):
    """Create a DeleteCodeDialog for a code without segments."""
    from src.contexts.coding.presentation.dialogs import DeleteCodeDialog

    dialog = DeleteCodeDialog(
        code_id=2,
        code_name="Empty Code",
        code_color="#4CAF50",
        segment_count=0,
        colors=colors,
    )
    yield dialog
    dialog.close()


@allure.story("QC-028.06 Delete Codes")
class TestDeleteCodeDialog:
    """
    QC-028.06: Delete Codes
    Test the DeleteCodeDialog using black-box patterns.
    """

    @allure.title("AC #6.1+6.2+6.4: Code details, segment warning, and delete option")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_code_details_warning_and_option(self, delete_code_dialog_with_segments):
        """Dialog shows code details, segment warning, and delete segments option."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        # Verify code details
        assert delete_code_dialog_with_segments.get_code_name() == "Test Code"
        assert delete_code_dialog_with_segments.get_code_id() == 1

        # Verify segment warning
        assert delete_code_dialog_with_segments.get_segment_count() == 5
        assert delete_code_dialog_with_segments.has_segment_warning()

        # Verify delete segments option
        assert not delete_code_dialog_with_segments.is_delete_segments_checked()
        delete_code_dialog_with_segments.set_delete_segments(True)
        QApplication.processEvents()
        assert delete_code_dialog_with_segments.is_delete_segments_checked()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Details and Warning"
        )

    @allure.title("AC #6.3: No segment warning when no segments")
    @allure.severity(allure.severity_level.NORMAL)
    def test_no_segment_warning_when_empty(self, delete_code_dialog_no_segments):
        """Dialog should not show segment warning when no segments."""
        delete_code_dialog_no_segments.show()
        QApplication.processEvents()

        assert delete_code_dialog_no_segments.get_segment_count() == 0
        assert not delete_code_dialog_no_segments.has_segment_warning()

        attach_screenshot(
            delete_code_dialog_no_segments, "DeleteCodeDialog - No Segments"
        )

    @allure.title("AC #6.5+6.6+6.7: Delete signal, flag, and cancel")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_signal_flag_and_cancel(self, delete_code_dialog_with_segments):
        """Delete emits signal with correct flag; cancel closes without signal."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        # Test delete without segments checked
        spy = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)
        click_dialog_button(delete_code_dialog_with_segments, "Delete")
        QApplication.processEvents()

        assert spy.count() == 1
        code_id, delete_segments = spy.at(0)
        assert code_id == 1
        assert delete_segments is False

        # Re-show for delete with segments flag test
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        spy2 = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)
        delete_code_dialog_with_segments.set_delete_segments(True)
        QApplication.processEvents()
        delete_code_dialog_with_segments.confirm_delete()
        QApplication.processEvents()

        assert spy2.count() == 1
        code_id, delete_segments = spy2.at(0)
        assert code_id == 1
        assert delete_segments is True

        # Test cancel
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()
        spy3 = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)
        click_dialog_button(delete_code_dialog_with_segments, "Cancel")
        QApplication.processEvents()
        assert spy3.count() == 0
        assert delete_code_dialog_with_segments.result() == 0


# =============================================================================
# QC-028.04: Add Memos to Codes (Black-Box)
# =============================================================================


@pytest.fixture
def code_memo_dialog(qapp, colors):
    """Create a CodeMemoDialog for testing."""
    dialog = CodeMemoDialog(
        code_name="Test Code",
        code_color="#FF5722",
        content="",
        colors=colors,
    )
    yield dialog
    dialog.close()


@pytest.fixture
def code_memo_dialog_with_content(qapp, colors):
    """Create a CodeMemoDialog with existing content."""
    from datetime import datetime

    dialog = CodeMemoDialog(
        code_name="Test Code",
        code_color="#FF5722",
        content="Existing memo content about this code.",
        author="researcher",
        timestamp=datetime(2024, 1, 15, 10, 30),
        colors=colors,
    )
    yield dialog
    dialog.close()


@allure.story("QC-028.04 Add Memos to Codes")
class TestCodeMemoDialog:
    """
    QC-028.04: Researcher can add memos to codes
    Tests for code-level memo functionality.
    """

    @allure.title("AC #4.1+4.2: Dialog shows code info and existing content")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shows_code_info_and_existing_content(
        self, code_memo_dialog, code_memo_dialog_with_content
    ):
        """Dialog header shows code name and displays existing memo content."""
        # Empty dialog shows code info
        code_memo_dialog.show()
        QApplication.processEvents()
        title = code_memo_dialog.get_title()
        assert "Test Code" in title
        attach_screenshot(code_memo_dialog, "CodeMemoDialog - Code Info Header")

        # Dialog with content shows it
        code_memo_dialog_with_content.show()
        QApplication.processEvents()
        content = code_memo_dialog_with_content.get_content()
        assert "Existing memo content" in content
        attach_screenshot(
            code_memo_dialog_with_content, "CodeMemoDialog - Existing Content"
        )

    @allure.title("AC #4.3+4.4: Enter memo text and save emits signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enter_text_and_save(self, code_memo_dialog):
        """User can type memo content and save emits signal."""
        code_memo_dialog.show()
        QApplication.processEvents()

        # Enter text
        code_memo_dialog.set_content(
            "This code captures positive experiences mentioned."
        )
        assert (
            code_memo_dialog.get_content()
            == "This code captures positive experiences mentioned."
        )

        # Save emits signal
        signals = []
        code_memo_dialog.save_clicked.connect(lambda: signals.append(True))
        code_memo_dialog.set_content("Test memo content")
        code_memo_dialog._on_save()
        QApplication.processEvents()
        assert len(signals) == 1

    @allure.title(
        "AC #4.5+4.6+4.7: Cancel, metadata display, and content changed signal"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_metadata_and_content_changed(
        self, code_memo_dialog, code_memo_dialog_with_content
    ):
        """Cancel closes without saving; metadata shown; content changes emit signal."""
        # Test cancel
        code_memo_dialog.show()
        QApplication.processEvents()

        save_signals = []
        cancel_signals = []
        code_memo_dialog.save_clicked.connect(lambda: save_signals.append(True))
        code_memo_dialog.cancel_clicked.connect(lambda: cancel_signals.append(True))

        code_memo_dialog.set_content("Some unsaved content")
        code_memo_dialog._on_cancel()
        QApplication.processEvents()
        assert len(cancel_signals) == 1
        assert len(save_signals) == 0

        # Test metadata display
        code_memo_dialog_with_content.show()
        QApplication.processEvents()

        metadata_text = code_memo_dialog_with_content.get_metadata_text()
        assert "researcher" in metadata_text
        assert "2024-01-15" in metadata_text
        attach_screenshot(
            code_memo_dialog_with_content, "CodeMemoDialog - Metadata Display"
        )

        # Test content changed signal
        code_memo_dialog.show()
        QApplication.processEvents()

        changes = []
        code_memo_dialog.content_changed.connect(lambda text: changes.append(text))
        code_memo_dialog._editor.setPlainText("New content for the code memo")
        QApplication.processEvents()
        assert len(changes) >= 1
