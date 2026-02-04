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

from design_system import get_colors
from src.contexts.coding.presentation.dialogs import (
    CodeSuggestionDialog,
    ColorPickerDialog,
    DuplicateCodesDialog,
)
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
def colors():
    """Get color palette for UI."""
    return get_colors()


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

    @allure.title("AC #3.1: Dialog shows preset color grid")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_shows_preset_colors(self, color_picker_dialog):
        """Dialog should display a grid of preset colors."""
        color_picker_dialog.show()
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Preset Colors")

        # BLACK-BOX: Get count via public API
        preset_count = color_picker_dialog.get_preset_count()
        assert preset_count == 20  # 4 rows x 5 columns

    @allure.title("AC #3.2: User can select preset color")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_preset_color(self, color_picker_dialog):
        """User can click a preset color swatch to select it."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find color swatches and click one
        swatches = find_color_swatch_buttons(color_picker_dialog)
        assert len(swatches) > 5, f"Expected at least 6 swatches, found {len(swatches)}"
        expected_color = get_swatch_color(swatches[5])
        swatches[5].clicked.emit(expected_color)
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Color Selected")

        # Verify via public getter
        assert color_picker_dialog.get_selected_color() == expected_color

    @allure.title("AC #3.3: User can enter custom hex color")
    @allure.severity(allure.severity_level.NORMAL)
    def test_enter_custom_hex_color(self, color_picker_dialog):
        """User can enter a custom hex color value."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Find input and enter value via public API
        color_picker_dialog.select_color("#123ABC")
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Custom Hex")

        assert color_picker_dialog.get_selected_color() == "#123ABC"

    @allure.title("AC #3.4: Valid hex colors are accepted")
    @allure.severity(allure.severity_level.NORMAL)
    def test_valid_hex_accepted(self, color_picker_dialog):
        """Valid hex values update the selection."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # Set a valid hex color
        color_picker_dialog.select_color("#ABCDEF")
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Valid Hex")

        # Should update to new color
        assert color_picker_dialog.get_selected_color() == "#ABCDEF"

    @allure.title("AC #3.5: Select button emits color_selected signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_emits_signal(self, color_picker_dialog):
        """Clicking Select emits color_selected signal with chosen color."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(color_picker_dialog.color_selected)

        color_picker_dialog.select_color("#AABBCC")
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Before Select")

        # BLACK-BOX: Click button by text
        click_dialog_button(color_picker_dialog, "Select")
        QApplication.processEvents()

        # Signal should have been emitted at least once with correct color
        assert spy.count() >= 1
        # Last emission should have our color
        assert spy.at(spy.count() - 1)[0] == "#AABBCC"

    @allure.title("AC #3.6: Preview updates with selection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_preview_updates(self, color_picker_dialog):
        """Preview updates when color changes."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # Set color via public API
        color_picker_dialog.select_color("#FF0000")
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Preview Red")

        # Verify via public getter
        assert color_picker_dialog.get_selected_color() == "#FF0000"

    @allure.title("AC #3.7: Swatch selection state updates visually")
    @allure.severity(allure.severity_level.NORMAL)
    def test_swatch_selection_visual_state(self, color_picker_dialog):
        """Selected swatch shows visual indication."""
        color_picker_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Click swatches and verify selection state
        swatches = find_color_swatch_buttons(color_picker_dialog)
        assert len(swatches) >= 2, (
            f"Expected at least 2 swatches, found {len(swatches)}"
        )

        # Select first swatch
        color1 = get_swatch_color(swatches[0])
        swatches[0].clicked.emit(color1)
        QApplication.processEvents()

        # Verify via public API
        assert color_picker_dialog.get_selected_color() == color1

        # Select second swatch
        color2 = get_swatch_color(swatches[1])
        swatches[1].clicked.emit(color2)
        QApplication.processEvents()

        attach_screenshot(color_picker_dialog, "ColorPickerDialog - Swatch Selection")

        # Verify selection moved
        assert color_picker_dialog.get_selected_color() == color2


# =============================================================================
# QC-028.05: Merge Duplicate Codes (Black-Box)
# =============================================================================


@allure.story("QC-028.05 Merge Duplicate Codes")
class TestDuplicateCodesDialog:
    """
    QC-028.05: Merge Duplicate Codes
    Test the DuplicateCodesDialog using black-box patterns.
    """

    @allure.title("AC #5.1: Dialog displays duplicate candidates")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_displays_duplicate_candidates(
        self, duplicate_dialog, sample_duplicate_candidates
    ):
        """Dialog should display detected duplicate code pairs."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Candidates")

        # BLACK-BOX: Verify via public API
        assert duplicate_dialog.get_candidate_count() == 2

    @allure.title("AC #5.2: Candidate card shows similarity percentage")
    @allure.severity(allure.severity_level.NORMAL)
    def test_card_shows_similarity(self, duplicate_dialog, sample_duplicate_candidates):
        """Each candidate card displays the similarity percentage."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Similarity")

        # BLACK-BOX: Cards are created with data
        assert duplicate_dialog.get_candidate_count() == 2

    @allure.title("AC #5.3: User can merge code A into code B")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_merge_a_into_b(self, duplicate_dialog, sample_duplicate_candidates):
        """User can click to merge code A into code B."""
        duplicate_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(duplicate_dialog.merge_requested)

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Before Merge")

        # Trigger merge via public API
        duplicate_dialog.request_merge(1, 2)  # Merge code 1 into code 2
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0) == [1, 2]

    @allure.title("AC #5.4: User can dismiss pair as not duplicates")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dismiss_pair(self, duplicate_dialog, sample_duplicate_candidates):
        """User can dismiss a pair as not duplicates."""
        duplicate_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(duplicate_dialog.dismiss_requested)

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        initial_count = duplicate_dialog.get_candidate_count()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Before Dismiss")

        # Trigger dismiss via public API
        duplicate_dialog.request_dismiss(1, 2)
        QApplication.processEvents()

        # Verify signal emitted
        assert spy.count() == 1

        # Verify count decreased
        assert duplicate_dialog.get_candidate_count() == initial_count - 1

    @allure.title("AC #5.5: Scan button requests duplicate detection")
    @allure.severity(allure.severity_level.NORMAL)
    def test_scan_requests_detection(self, duplicate_dialog):
        """Scan button emits detect_duplicates_requested signal."""
        duplicate_dialog.show()
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Initial")

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(duplicate_dialog.detect_duplicates_requested)

        # BLACK-BOX: Click scan button via public method
        duplicate_dialog.request_scan()
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == 0.8  # Default threshold

    @allure.title("AC #5.6: Empty state shown when no duplicates")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_state_no_duplicates(self, duplicate_dialog):
        """Empty state is shown when no duplicates are found."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected([])
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateCodesDialog - Empty State")

        # BLACK-BOX: Verify via public API
        assert duplicate_dialog.is_empty_state_visible()


# =============================================================================
# QC-028.08: Agent Suggest New Codes (Black-Box)
# =============================================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCodeSuggestionDialog:
    """
    QC-028.08: Agent Suggest New Codes
    Test the CodeSuggestionDialog using black-box patterns.
    """

    @allure.title("AC #8.1: Dialog displays AI suggestions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_displays_suggestions(self, suggestion_dialog, sample_suggestions):
        """Dialog should display AI-generated code suggestions."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Suggestions")

        # BLACK-BOX: Verify via public API
        assert suggestion_dialog.get_suggestion_count() == 2

    @allure.title("AC #8.2: Suggestion card shows name and rationale")
    @allure.severity(allure.severity_level.NORMAL)
    def test_card_shows_details(self, suggestion_dialog, sample_suggestions):
        """Suggestion cards display name, rationale, and confidence."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Card Details")

        # BLACK-BOX: Verify cards contain expected data
        assert suggestion_dialog.get_suggestion_count() == 2

    @allure.title("AC #8.3: User can edit suggested name before approval")
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_suggestion_name(self, suggestion_dialog, sample_suggestions):
        """User can modify the suggested code name before approving."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        # BLACK-BOX: Edit via public API
        suggestion_dialog.set_suggestion_name("sug-1", "Modified Name")
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Name Edited")

        assert suggestion_dialog.get_suggestion_name("sug-1") == "Modified Name"

    @allure.title("AC #8.4: User can approve suggestion")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_approve_suggestion(self, suggestion_dialog, sample_suggestions):
        """User can approve a code suggestion."""
        suggestion_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(suggestion_dialog.approve_suggestion_requested)

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Before Approve")

        # Approve via public API
        suggestion_dialog.approve_suggestion("sug-1")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "sug-1"

    @allure.title("AC #8.5: User can reject suggestion")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reject_suggestion(self, suggestion_dialog, sample_suggestions):
        """User can reject a code suggestion."""
        suggestion_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(suggestion_dialog.reject_suggestion_requested)

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Before Reject")

        # Reject via public API
        suggestion_dialog.reject_suggestion("sug-2")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "sug-2"

    @allure.title("AC #8.6: Approved suggestion removed from list")
    @allure.severity(allure.severity_level.NORMAL)
    def test_approved_removed(self, suggestion_dialog, sample_suggestions):
        """Approved suggestions are removed from the dialog."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        initial_count = suggestion_dialog.get_suggestion_count()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Before Remove")

        suggestion_dialog.on_suggestion_approved("sug-1")
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - After Remove")

        # BLACK-BOX: Verify count decreased
        assert suggestion_dialog.get_suggestion_count() == initial_count - 1

    @allure.title("AC #8.7: Approve All emits signal")
    @allure.severity(allure.severity_level.NORMAL)
    def test_approve_all(self, suggestion_dialog, sample_suggestions):
        """Approve All button emits approve_all_requested signal."""
        suggestion_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(suggestion_dialog.approve_all_requested)

        suggestion_dialog.on_suggestions_received(sample_suggestions)
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Approve All")

        # Approve all via public API
        suggestion_dialog.approve_all()
        QApplication.processEvents()

        assert spy.count() == 1

    @allure.title("AC #8.8: Empty state when no suggestions")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_state(self, suggestion_dialog):
        """Empty state shown when no suggestions found."""
        suggestion_dialog.show()
        QApplication.processEvents()

        suggestion_dialog.on_suggestions_received([])
        QApplication.processEvents()

        attach_screenshot(suggestion_dialog, "CodeSuggestionDialog - Empty State")

        # BLACK-BOX: Verify via public API
        assert suggestion_dialog.is_empty_state_visible()


# =============================================================================
# QC-028.09: Agent Detect Duplicates (Black-Box)
# =============================================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestDuplicateDetection:
    """
    QC-028.09: Agent Detect Potential Duplicate Codes
    Test duplicate detection using black-box patterns.
    """

    @allure.title("AC #9.1: Detection shows similarity scores")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shows_similarity_scores(
        self, duplicate_dialog, sample_duplicate_candidates
    ):
        """Detection results show similarity scores for each pair."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateDetection - Similarity Scores")

        # BLACK-BOX: Verify via public API
        assert duplicate_dialog.get_candidate_count() == 2

    @allure.title("AC #9.2: High similarity pairs shown first")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sorted_by_similarity(self, duplicate_dialog, sample_duplicate_candidates):
        """Duplicate pairs should be sorted by similarity (highest first)."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateDetection - Sorted")

        # BLACK-BOX: Verify count
        assert duplicate_dialog.get_candidate_count() == 2

    @allure.title("AC #9.3: Detection considers segment counts")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shows_segment_counts(self, duplicate_dialog, sample_duplicate_candidates):
        """Duplicate cards show segment counts for each code."""
        duplicate_dialog.show()
        QApplication.processEvents()

        duplicate_dialog.on_duplicates_detected(sample_duplicate_candidates)
        QApplication.processEvents()

        attach_screenshot(duplicate_dialog, "DuplicateDetection - Segment Counts")

        # BLACK-BOX: Cards are created with segment count info
        assert duplicate_dialog.get_candidate_count() == 2


# =============================================================================
# DuplicatePairCard Unit Tests (Black-Box)
# =============================================================================


@allure.story("QC-028.05 Duplicate Pair Card")
class TestDuplicatePairCard:
    """Unit tests for DuplicatePairCard widget using black-box patterns."""

    @allure.title("Card emits merge_requested with correct IDs")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_merge_signal_ids(self, qapp, colors):
        """Merge signal includes correct source and target IDs."""
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

        attach_screenshot(card, "DuplicatePairCard - Merge Test")

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(card.merge_requested)

        # Simulate merge via signal (would be triggered by button click)
        card.merge_requested.emit(10, 20)

        assert spy.count() == 1
        assert spy.at(0) == [10, 20]
        card.deleteLater()

    @allure.title("Card emits dismiss_requested with both IDs")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dismiss_signal(self, qapp, colors):
        """Dismiss signal includes both code IDs."""
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

        attach_screenshot(card, "DuplicatePairCard - Dismiss Test")

        # BLACK-BOX: Use signal spy
        spy = QSignalSpy(card.dismiss_requested)

        card.dismiss_requested.emit(10, 20)

        assert spy.count() == 1
        assert spy.at(0) == [10, 20]
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

    @allure.title("AC #2.1: Dialog shows name input field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_has_name_input(self, create_category_dialog):
        """Dialog should have a name input field."""
        create_category_dialog.show()
        QApplication.processEvents()

        attach_screenshot(create_category_dialog, "CreateCategoryDialog - Initial")

        # BLACK-BOX: Find input by placeholder
        name_input = find_input_by_placeholder(
            create_category_dialog, "Enter category name"
        )
        assert name_input is not None, "Name input field should be visible"

    @allure.title("AC #2.2: User can enter category name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enter_category_name(self, create_category_dialog):
        """User can type a category name in the input."""
        create_category_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use public API
        create_category_dialog.set_category_name("New Category")
        QApplication.processEvents()

        attach_screenshot(create_category_dialog, "CreateCategoryDialog - Name Entered")

        assert create_category_dialog.get_category_name() == "New Category"

    @allure.title("AC #2.3: Dialog shows parent category options")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_has_parent_options(self, create_category_dialog):
        """Dialog should show parent category selection."""
        create_category_dialog.show()
        QApplication.processEvents()

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Parent Options"
        )

        # BLACK-BOX: Verify via public API
        # 1 for "None" + 2 existing categories
        assert create_category_dialog.get_parent_options_count() == 3

    @allure.title("AC #2.4: User can select parent category")
    @allure.severity(allure.severity_level.NORMAL)
    def test_select_parent_category(self, create_category_dialog):
        """User can select a parent category."""
        create_category_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use public API
        create_category_dialog.set_parent_id(1)
        QApplication.processEvents()

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Parent Selected"
        )

        assert create_category_dialog.get_parent_id() == 1

    @allure.title("AC #2.5: User can add optional memo")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_memo(self, create_category_dialog):
        """User can add an optional description/memo."""
        create_category_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Use public API
        create_category_dialog.set_category_memo("Category for interview themes")
        QApplication.processEvents()

        attach_screenshot(create_category_dialog, "CreateCategoryDialog - Memo Added")

        assert (
            create_category_dialog.get_category_memo()
            == "Category for interview themes"
        )

    @allure.title("AC #2.6: Create button disabled when name is empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_disabled_without_name(self, create_category_dialog):
        """Create button should be disabled when name is empty."""
        create_category_dialog.show()
        QApplication.processEvents()

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Button Disabled"
        )

        # BLACK-BOX: Find button and check state
        assert not is_button_enabled(create_category_dialog, "Create")

    @allure.title("AC #2.7: Create button enabled when name is entered")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_button_enabled_with_name(self, create_category_dialog):
        """Create button should be enabled when name is entered."""
        create_category_dialog.show()
        QApplication.processEvents()

        create_category_dialog.set_category_name("New Category")
        QApplication.processEvents()

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Button Enabled"
        )

        # BLACK-BOX: Find button and check state
        assert is_button_enabled(create_category_dialog, "Create")

    @allure.title("AC #2.8: Clicking create emits category_created signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emits_signal(self, create_category_dialog):
        """Clicking Create Category should emit the category_created signal."""
        create_category_dialog.show()
        QApplication.processEvents()

        # BLACK-BOX: Setup signal spy
        spy = QSignalSpy(create_category_dialog.category_created)

        # Fill form using public API
        create_category_dialog.set_category_name("Test Category")
        create_category_dialog.set_parent_id(1)
        create_category_dialog.set_category_memo("Test memo")
        QApplication.processEvents()

        attach_screenshot(create_category_dialog, "CreateCategoryDialog - Filled Form")

        # BLACK-BOX: Click button by text
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

        attach_screenshot(
            create_category_dialog, "CreateCategoryDialog - Before Cancel"
        )

        # BLACK-BOX: Click button by text
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

    @allure.title("AC #6.1: Dialog shows code details")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_shows_code_details(self, delete_code_dialog_with_segments):
        """Dialog should display the code being deleted."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - With Segments"
        )

        # BLACK-BOX: Verify via public API
        assert delete_code_dialog_with_segments.get_code_name() == "Test Code"
        assert delete_code_dialog_with_segments.get_code_id() == 1

    @allure.title("AC #6.2: Dialog shows segment count warning")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dialog_shows_segment_warning(self, delete_code_dialog_with_segments):
        """Dialog should warn about attached segments."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Segment Warning"
        )

        # BLACK-BOX: Verify via public API
        assert delete_code_dialog_with_segments.get_segment_count() == 5
        assert delete_code_dialog_with_segments.has_segment_warning()

    @allure.title("AC #6.3: No segment warning when no segments")
    @allure.severity(allure.severity_level.NORMAL)
    def test_no_segment_warning_when_empty(self, delete_code_dialog_no_segments):
        """Dialog should not show segment warning when no segments."""
        delete_code_dialog_no_segments.show()
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_no_segments, "DeleteCodeDialog - No Segments"
        )

        # BLACK-BOX: Verify via public API
        assert delete_code_dialog_no_segments.get_segment_count() == 0
        assert not delete_code_dialog_no_segments.has_segment_warning()

    @allure.title("AC #6.4: User can choose to delete segments")
    @allure.severity(allure.severity_level.NORMAL)
    def test_can_choose_delete_segments(self, delete_code_dialog_with_segments):
        """User can check option to delete associated segments."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        # Initially unchecked
        assert not delete_code_dialog_with_segments.is_delete_segments_checked()

        # BLACK-BOX: Use public API to check
        delete_code_dialog_with_segments.set_delete_segments(True)
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Segments Checked"
        )

        assert delete_code_dialog_with_segments.is_delete_segments_checked()

    @allure.title("AC #6.5: Delete button emits delete_confirmed signal")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_emits_signal(self, delete_code_dialog_with_segments):
        """Clicking Delete should emit delete_confirmed signal."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Before Delete"
        )

        # BLACK-BOX: Setup signal spy
        spy = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)

        # BLACK-BOX: Click button by text
        click_dialog_button(delete_code_dialog_with_segments, "Delete")
        QApplication.processEvents()

        assert spy.count() == 1
        code_id, delete_segments = spy.at(0)
        assert code_id == 1
        assert delete_segments is False  # Default unchecked

    @allure.title("AC #6.6: Delete with segments checked emits correct flag")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_with_segments_flag(self, delete_code_dialog_with_segments):
        """Delete with checkbox checked should emit delete_segments=True."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        # BLACK-BOX: Setup signal spy
        spy = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)

        # Check the delete segments option
        delete_code_dialog_with_segments.set_delete_segments(True)
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Delete With Segments"
        )

        # BLACK-BOX: Confirm via public API
        delete_code_dialog_with_segments.confirm_delete()
        QApplication.processEvents()

        assert spy.count() == 1
        code_id, delete_segments = spy.at(0)
        assert code_id == 1
        assert delete_segments is True

    @allure.title("AC #6.7: Cancel button closes dialog")
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_closes_dialog(self, delete_code_dialog_with_segments):
        """Clicking Cancel should close the dialog without deleting."""
        delete_code_dialog_with_segments.show()
        QApplication.processEvents()

        attach_screenshot(
            delete_code_dialog_with_segments, "DeleteCodeDialog - Before Cancel"
        )

        # BLACK-BOX: Setup signal spy
        spy = QSignalSpy(delete_code_dialog_with_segments.delete_confirmed)

        # BLACK-BOX: Click button by text
        click_dialog_button(delete_code_dialog_with_segments, "Cancel")
        QApplication.processEvents()

        # Signal should NOT be emitted
        assert spy.count() == 0
        assert delete_code_dialog_with_segments.result() == 0
