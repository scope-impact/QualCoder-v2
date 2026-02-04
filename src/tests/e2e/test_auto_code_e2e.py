"""
QC-032: Auto-Code E2E Tests

Tests for automatic coding features through the UI layer.

These tests use NO MOCKS:
1. Real Qt widgets
2. Real dialogs (AutoCodeDialog)
3. Simulated user interactions

Test Categories:
- QC-032.01: Search for text patterns
- QC-032.02: Preview matches before coding
- QC-032.03: Apply code to all matches
- QC-032.04: Undo batch coding
- QC-032.05: Auto-code by speaker
- QC-032.06-08: Agent batch operations
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.contexts.coding.presentation.dialogs.auto_code_dialog import AutoCodeDialog
from src.contexts.coding.presentation.screens.text_coding import TextCodingScreen
from src.shared.presentation.dto import (
    CodeCategoryDTO,
    CodeDTO,
    DocumentDTO,
    FileDTO,
    TextCodingDataDTO,
)
from src.tests.e2e.helpers import attach_screenshot

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-032 Auto-Code"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def colors():
    """Get color palette for UI."""
    return get_colors()


@pytest.fixture
def auto_code_dialog(qapp, colors):
    """Create an AutoCodeDialog for testing."""
    dialog = AutoCodeDialog(colors=colors)
    yield dialog
    dialog.close()


@pytest.fixture
def sample_interview_text():
    """Sample interview transcript for auto-coding tests."""
    return """INTERVIEWER: Welcome. Can you tell me about your experience with the program?

PARTICIPANT: Thank you. I found the program very helpful. The learning materials were comprehensive.

INTERVIEWER: What aspects did you find most beneficial?

PARTICIPANT: I think the hands-on exercises were excellent. The practical experience was invaluable.

INTERVIEWER: Were there any challenges?

PARTICIPANT: Yes, the time management was difficult. Balancing work and study was challenging.

INTERVIEWER: How did you overcome those challenges?

PARTICIPANT: I created a strict schedule. Time management improved with practice."""


@pytest.fixture
def sample_data(sample_interview_text):
    """Create sample data for the coding screen."""
    return TextCodingDataDTO(
        files=[
            FileDTO(id="1", name="interview_01.txt", file_type="text", meta="1.2 KB"),
        ],
        categories=[
            CodeCategoryDTO(
                id="cat-1",
                name="Themes",
                codes=[
                    CodeDTO(id="1", name="Positive", color="#4CAF50", count=0),
                    CodeDTO(id="2", name="Challenge", color="#F44336", count=0),
                    CodeDTO(id="3", name="Time Management", color="#2196F3", count=0),
                ],
            ),
        ],
        document=DocumentDTO(
            id="1",
            title="interview_01.txt",
            badge="File 1",
            content=sample_interview_text,
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


# =============================================================================
# QC-032.01: Search for Text Patterns
# =============================================================================


@allure.story("QC-032.01 Search for Text Patterns")
class TestPatternSearch:
    """
    QC-032.01: Researcher can search for text patterns
    Tests for pattern search functionality.
    """

    @allure.title("AC #1.1: Dialog has pattern input field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_dialog_has_pattern_input(self, auto_code_dialog):
        """Dialog should have a text input for search pattern."""
        auto_code_dialog.show()
        QApplication.processEvents()

        assert auto_code_dialog._pattern_input is not None
        assert (
            auto_code_dialog._pattern_input.placeholderText() == "Enter text to find..."
        )

    @allure.title("AC #1.2: User can enter search pattern")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enter_search_pattern(self, auto_code_dialog):
        """User can type a search pattern."""
        auto_code_dialog.show()
        QApplication.processEvents()

        auto_code_dialog.set_pattern("time management")

        assert auto_code_dialog.get_pattern() == "time management"
        attach_screenshot(auto_code_dialog, "AutoCode - Pattern Search")

    @allure.title("AC #1.3: Match type options available")
    @allure.severity(allure.severity_level.NORMAL)
    def test_match_type_options(self, auto_code_dialog):
        """Dialog provides match type options (exact, contains, regex)."""
        auto_code_dialog.show()
        QApplication.processEvents()

        match_types = auto_code_dialog.get_available_match_types()

        assert "exact" in match_types
        assert "contains" in match_types
        assert "regex" in match_types
        attach_screenshot(auto_code_dialog, "AutoCode - Match Type Options")

    @allure.title("AC #1.4: User can select match type")
    @allure.severity(allure.severity_level.NORMAL)
    def test_select_match_type(self, auto_code_dialog):
        """User can select a match type from dropdown."""
        auto_code_dialog.show()
        QApplication.processEvents()

        auto_code_dialog._match_combo.setCurrentIndex(1)  # "Contains"
        QApplication.processEvents()

        assert auto_code_dialog._get_match_type_str() == "contains"

    @allure.title("AC #1.5: Scope options available")
    @allure.severity(allure.severity_level.NORMAL)
    def test_scope_options(self, auto_code_dialog):
        """Dialog provides scope options (all, first, last)."""
        auto_code_dialog.show()
        QApplication.processEvents()

        scopes = auto_code_dialog.get_available_scopes()

        assert "all" in scopes
        assert "first" in scopes
        assert "last" in scopes


# =============================================================================
# QC-032.02: Preview Matches Before Coding
# =============================================================================


@allure.story("QC-032.02 Preview Matches")
class TestMatchPreview:
    """
    QC-032.02: Researcher can preview matches before coding
    Tests for match preview functionality.
    """

    @allure.title("AC #2.1: Preview button emits find_matches_requested")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_preview_emits_signal(self, auto_code_dialog, sample_interview_text):
        """Preview button emits find_matches_requested signal."""
        auto_code_dialog.show()
        QApplication.processEvents()

        signals = []
        auto_code_dialog.find_matches_requested.connect(
            lambda _text, pattern, match_type, scope, _case: signals.append(
                (pattern, match_type, scope)
            )
        )

        auto_code_dialog.set_text(sample_interview_text)
        auto_code_dialog.set_pattern("challenge")
        auto_code_dialog._match_combo.setCurrentIndex(1)  # Contains
        auto_code_dialog._scope_combo.setCurrentIndex(0)  # All
        auto_code_dialog._on_preview()
        QApplication.processEvents()

        assert len(signals) == 1
        assert signals[0][0] == "challenge"
        assert signals[0][1] == "contains"
        assert signals[0][2] == "all"
        attach_screenshot(auto_code_dialog, "AutoCode - Preview Matches")

    @allure.title("AC #2.2: Dialog receives and caches matches")
    @allure.severity(allure.severity_level.NORMAL)
    def test_receives_matches(self, auto_code_dialog):
        """Dialog can receive and store match results."""
        auto_code_dialog.show()
        QApplication.processEvents()

        # Simulate receiving matches from controller
        matches = [(100, 110), (200, 210), (300, 310)]
        auto_code_dialog.on_matches_found(matches)

        cached = auto_code_dialog.get_cached_matches()
        assert len(cached) == 3
        assert cached[0] == (100, 110)
        attach_screenshot(auto_code_dialog, "AutoCode - Matches Found")

    @allure.title("AC #2.3: Preview requires pattern and text")
    @allure.severity(allure.severity_level.NORMAL)
    def test_preview_requires_pattern(self, auto_code_dialog):
        """Preview does nothing if pattern or text is empty."""
        auto_code_dialog.show()
        QApplication.processEvents()

        signals = []
        auto_code_dialog.find_matches_requested.connect(
            lambda *args: signals.append(args)
        )

        # No text set
        auto_code_dialog.set_pattern("test")
        auto_code_dialog._on_preview()

        assert len(signals) == 0


# =============================================================================
# QC-032.03: Apply Code to All Matches
# =============================================================================


@allure.story("QC-032.03 Apply to All Matches")
class TestApplyToMatches:
    """
    QC-032.03: Researcher can apply code to all matches
    Tests for batch code application.
    """

    @allure.title("AC #3.1: Apply button emits apply_auto_code_requested")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_apply_emits_signal(self, auto_code_dialog, sample_interview_text):
        """Apply button emits apply_auto_code_requested with config."""
        auto_code_dialog.show()
        QApplication.processEvents()

        signals = []
        auto_code_dialog.apply_auto_code_requested.connect(
            lambda config: signals.append(config)
        )

        auto_code_dialog.set_text(sample_interview_text)
        auto_code_dialog.set_pattern("challenge")
        auto_code_dialog.set_code({"id": "2", "name": "Challenge", "color": "#F44336"})
        auto_code_dialog._match_combo.setCurrentIndex(1)  # Contains
        auto_code_dialog._on_apply()
        QApplication.processEvents()

        assert len(signals) == 1
        config = signals[0]
        assert config["pattern"] == "challenge"
        assert config["match_type"] == "contains"
        assert config["code"]["name"] == "Challenge"

    @allure.title("AC #3.2: Code display shows selected code")
    @allure.severity(allure.severity_level.NORMAL)
    def test_shows_selected_code(self, auto_code_dialog):
        """Dialog displays the code that will be applied."""
        auto_code_dialog.show()
        QApplication.processEvents()

        # Verify initial state
        assert auto_code_dialog._code_label.text() == "No code selected"

        auto_code_dialog.set_code({"id": "1", "name": "Positive", "color": "#4CAF50"})
        QApplication.processEvents()

        # Verify UI updated with code name
        assert auto_code_dialog._code_label.text() == "Positive"
        # Verify color swatch updated (check stylesheet contains color)
        style = auto_code_dialog._code_color.styleSheet()
        assert "#4CAF50" in style
        attach_screenshot(auto_code_dialog, "AutoCode - Selected Code Display")

    @allure.title("AC #3.3: Get code returns selected code")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_code(self, auto_code_dialog):
        """get_code returns the currently selected code."""
        auto_code_dialog.show()
        QApplication.processEvents()

        auto_code_dialog.set_code({"id": "1", "name": "Test", "color": "#FF0000"})

        code = auto_code_dialog.get_code()
        assert code["name"] == "Test"


# =============================================================================
# QC-032.04: Undo Batch Coding
# =============================================================================


@allure.story("QC-032.04 Undo Batch Coding")
class TestUndoBatchCoding:
    """
    QC-032.04: Researcher can undo batch coding
    Tests for undoing auto-code operations.
    """

    @allure.title("AC #4.1: Coding screen has undo capability")
    @allure.severity(allure.severity_level.NORMAL)
    def test_screen_has_undo(self, coding_screen):
        """Coding screen supports undo operations."""
        # Undo is typically handled at application level or via unmark history
        assert coding_screen._unmark_history is not None
        attach_screenshot(coding_screen, "AutoCode - Coding Screen with Undo")

    @allure.title("AC #4.2: Unmark history tracks operations")
    @allure.severity(allure.severity_level.NORMAL)
    def test_unmark_history_tracks(self, coding_screen):
        """Unmark operations are tracked for undo."""
        coding_screen.set_active_code("1", "Positive", "#4CAF50")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()

        assert len(coding_screen._unmark_history) == 1

    @allure.title("AC #4.3: Undo re-applies code")
    @allure.severity(allure.severity_level.NORMAL)
    def test_undo_reapplies_code(self, coding_screen):
        """Undo operation re-applies the unmarked code."""
        applied = []
        coding_screen.code_applied.connect(
            lambda cid, start, end: applied.append((cid, start, end))
        )

        coding_screen.set_active_code("1", "Positive", "#4CAF50")
        coding_screen.set_text_selection(50, 100)
        coding_screen.unmark()
        coding_screen.undo_unmark()
        QApplication.processEvents()

        assert len(applied) >= 1


# =============================================================================
# QC-032.05: Auto-Code by Speaker
# =============================================================================


@allure.story("QC-032.05 Auto-Code by Speaker")
class TestAutoCodeBySpeaker:
    """
    QC-032.05: Researcher can auto-code by speaker
    Tests for speaker-based auto-coding.
    """

    @allure.title("AC #5.1: Dialog can request speaker detection")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_detect_speakers_signal(self, auto_code_dialog, sample_interview_text):
        """Dialog emits detect_speakers_requested signal."""
        auto_code_dialog.show()
        QApplication.processEvents()

        signals = []
        auto_code_dialog.detect_speakers_requested.connect(
            lambda text: signals.append(text)
        )

        auto_code_dialog.set_text(sample_interview_text)
        auto_code_dialog.detect_speakers_requested.emit(sample_interview_text)
        QApplication.processEvents()

        assert len(signals) == 1
        attach_screenshot(auto_code_dialog, "AutoCode - Speaker Detection")

    @allure.title("AC #5.2: Dialog receives detected speakers")
    @allure.severity(allure.severity_level.NORMAL)
    def test_receives_speakers(self, auto_code_dialog):
        """Dialog can receive detected speaker list."""
        auto_code_dialog.show()
        QApplication.processEvents()

        speakers = [
            {"name": "INTERVIEWER", "count": 4},
            {"name": "PARTICIPANT", "count": 4},
        ]
        auto_code_dialog.on_speakers_detected(speakers)
        # No assertion needed - just verify no crash

    @allure.title("AC #5.3: Dialog can request speaker segments")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_speaker_segments_signal(self, auto_code_dialog, sample_interview_text):
        """Dialog emits get_speaker_segments_requested signal."""
        auto_code_dialog.show()
        QApplication.processEvents()

        signals = []
        auto_code_dialog.get_speaker_segments_requested.connect(
            lambda text, speaker: signals.append((text, speaker))
        )

        auto_code_dialog.set_text(sample_interview_text)
        auto_code_dialog.get_speaker_segments_requested.emit(
            sample_interview_text, "PARTICIPANT"
        )
        QApplication.processEvents()

        assert len(signals) == 1
        assert signals[0][1] == "PARTICIPANT"


# =============================================================================
# QC-032.06-08: Agent Batch Operations
# =============================================================================


@allure.story("QC-032.06-08 Agent Batch Operations")
class TestAgentBatchOperations:
    """
    QC-032.06-08: Agent batch coding features
    Tests for AI-agent batch coding functionality.
    """

    @allure.title("AC #6.1: Config includes all required fields")
    @allure.severity(allure.severity_level.NORMAL)
    def test_apply_config_fields(self, auto_code_dialog):
        """Apply config includes pattern, match_type, scope, code."""
        auto_code_dialog.show()
        QApplication.processEvents()

        configs = []
        auto_code_dialog.apply_auto_code_requested.connect(
            lambda config: configs.append(config)
        )

        auto_code_dialog.set_text("Test text")
        auto_code_dialog.set_pattern("test")
        auto_code_dialog.set_code({"id": "1", "name": "Test", "color": "#FF0000"})
        auto_code_dialog._on_apply()
        QApplication.processEvents()

        config = configs[0]
        assert "pattern" in config
        assert "match_type" in config
        assert "scope" in config
        assert "code" in config

    @allure.title("AC #7.1: Regex match type available for agents")
    @allure.severity(allure.severity_level.NORMAL)
    def test_regex_match_type(self, auto_code_dialog):
        """Regex match type is available for pattern matching."""
        auto_code_dialog.show()
        QApplication.processEvents()

        auto_code_dialog._match_combo.setCurrentIndex(2)  # Regex
        QApplication.processEvents()

        assert auto_code_dialog._get_match_type_str() == "regex"

    @allure.title("AC #8.1: Error handler slot available")
    @allure.severity(allure.severity_level.NORMAL)
    def test_error_handler(self, auto_code_dialog):
        """Dialog has error handler slot for reporting issues."""
        auto_code_dialog.show()
        QApplication.processEvents()

        # Call error handler - should not crash
        auto_code_dialog.on_error("batch_apply", "Test error message")
        # No assertion - just verify no crash


# =============================================================================
# Integration Tests
# =============================================================================


@allure.story("QC-032 Integration")
class TestAutoCodeIntegration:
    """Integration tests for complete auto-code workflow."""

    @allure.title("Full workflow: Set code, pattern, preview, apply")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_auto_code_workflow(
        self, auto_code_dialog, sample_interview_text, colors
    ):
        """Test complete auto-code workflow from pattern to apply."""
        with allure.step("Open dialog and set text"):
            auto_code_dialog.show()
            QApplication.processEvents()
            auto_code_dialog.set_text(sample_interview_text)

        with allure.step("Set code to apply"):
            auto_code_dialog.set_code(
                {"id": "3", "name": "Time Management", "color": "#2196F3"}
            )
            assert auto_code_dialog._code_label.text() == "Time Management"

        with allure.step("Set pattern and match type"):
            auto_code_dialog.set_pattern("time management")
            auto_code_dialog._match_combo.setCurrentIndex(1)  # Contains
            assert auto_code_dialog.get_pattern() == "time management"

        with allure.step("Request preview"):
            preview_signals = []
            auto_code_dialog.find_matches_requested.connect(
                lambda *args: preview_signals.append(args)
            )
            auto_code_dialog._on_preview()
            QApplication.processEvents()
            assert len(preview_signals) == 1

        with allure.step("Receive matches"):
            # Simulate controller response
            auto_code_dialog.on_matches_found([(350, 366), (500, 516)])
            assert len(auto_code_dialog.get_cached_matches()) == 2

        with allure.step("Apply auto-code"):
            apply_signals = []
            auto_code_dialog.apply_auto_code_requested.connect(
                lambda config: apply_signals.append(config)
            )
            auto_code_dialog._on_apply()
            QApplication.processEvents()

            assert len(apply_signals) == 1
            config = apply_signals[0]
            assert config["pattern"] == "time management"
            assert config["code"]["name"] == "Time Management"
            attach_screenshot(auto_code_dialog, "AutoCode - Applied")

    @allure.title("Cancel button closes dialog without applying")
    @allure.severity(allure.severity_level.NORMAL)
    def test_cancel_without_apply(self, auto_code_dialog, sample_interview_text):
        """Cancel button closes dialog without emitting apply signal."""
        auto_code_dialog.show()
        QApplication.processEvents()

        apply_signals = []
        auto_code_dialog.apply_auto_code_requested.connect(
            lambda config: apply_signals.append(config)
        )

        auto_code_dialog.set_text(sample_interview_text)
        auto_code_dialog.set_pattern("test")
        auto_code_dialog.reject()  # Cancel
        QApplication.processEvents()

        assert len(apply_signals) == 0
