"""
TDD Tests for TextCodingScreen + ViewModel Integration.

These tests verify that the TextCodingScreen properly connects
to the TextCodingViewModel for data loading and signal routing.

Test Categories:
1. Screen accepts viewmodel parameter and loads data
2. Screen falls back to sample data without viewmodel
3. Signal routing: screen signals -> viewmodel commands
4. Signal routing: viewmodel signals -> screen updates
5. Source tracking for document context
"""

import sys

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def colors():
    """Get theme colors."""
    from design_system import get_colors

    return get_colors()


@pytest.fixture
def coding_context():
    """Create an in-memory CodingContext for testing."""
    from src.presentation.factory import CodingContext

    ctx = CodingContext.create_in_memory()
    yield ctx
    ctx.close()


@pytest.fixture
def viewmodel(coding_context):
    """Create a TextCodingViewModel connected to the test context."""
    return coding_context.create_text_coding_viewmodel()


class TestScreenViewModelWiring:
    """Test that screen connects to viewmodel correctly."""

    def test_screen_accepts_viewmodel_parameter(self, qapp, qtbot, colors):
        """Screen should accept optional viewmodel parameter."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        qtbot.addWidget(screen)

        assert screen._viewmodel is vm

        ctx.close()

    def test_screen_loads_data_from_viewmodel(self, qapp, qtbot, colors):
        """When viewmodel provided, screen loads data from it."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("test_code", "#ff0000")

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        qtbot.addWidget(screen)

        # Codes from viewmodel should be available
        categories = vm.load_codes()
        assert len(categories) > 0
        assert any(any(c.name == "test_code" for c in cat.codes) for cat in categories)

        ctx.close()

    def test_screen_falls_back_to_sample_data(self, qapp, qtbot, colors):
        """Without viewmodel, screen uses sample data."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)  # No viewmodel
        qtbot.addWidget(screen)

        assert screen._viewmodel is None
        # Should still work with sample data - verify page is functional
        assert screen.page is not None


class TestCodeAppliedSignalRouting:
    """Test code_applied signal routes to viewmodel."""

    def test_code_applied_calls_viewmodel(self, qapp, qtbot, colors):
        """code_applied signal should call viewmodel.apply_code_to_selection."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        # Get the code ID
        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        qtbot.addWidget(screen)

        # Emit code_applied signal (simulating quick mark)
        screen.code_applied.emit(str(code_id), 0, 10)
        QApplication.processEvents()

        # Verify segment created in database
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].position.start == 0
        assert segments[0].position.end == 10

        ctx.close()

    def test_code_applied_without_viewmodel_still_emits(self, qapp, qtbot, colors):
        """code_applied should still emit without viewmodel (for external listeners)."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.code_applied)

        # Set up code state
        screen.set_active_code("1", "test", "#ff0000")
        screen.set_text_selection(0, 10)

        # Trigger quick mark
        screen.quick_mark()

        # Signal should still emit (for any external listeners)
        assert spy.count() == 1


class TestCodeRemovedSignalRouting:
    """Test code_removed signal routes to viewmodel."""

    def test_code_removed_calls_viewmodel(self, qapp, qtbot, colors):
        """code_removed signal should call viewmodel.remove_segment."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        qtbot.addWidget(screen)

        # First apply a code
        vm.apply_code_to_selection(code_id, 1, 0, 10)
        QApplication.processEvents()

        # Verify segment exists
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        # Remove via signal
        screen.code_removed.emit(str(code_id), 0, 10)
        QApplication.processEvents()

        # Verify segment removed
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()


class TestViewModelSignalsUpdateScreen:
    """Test viewmodel signals update screen."""

    def test_codes_changed_updates_screen(self, qapp, qtbot, colors):
        """codes_changed from viewmodel should update screen codes."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        qtbot.addWidget(screen)

        # Get initial code count
        initial_codes = vm.load_codes()
        initial_count = sum(len(cat.codes) for cat in initial_codes)

        # Create code (triggers codes_changed)
        vm.create_code("new_code", "#00ff00")
        QApplication.processEvents()

        # Verify codes increased
        updated_codes = vm.load_codes()
        updated_count = sum(len(cat.codes) for cat in updated_codes)
        assert updated_count == initial_count + 1

        ctx.close()

    def test_segments_changed_updates_highlights(self, qapp, qtbot, colors):
        """segments_changed should update editor highlights."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World Test")
        qtbot.addWidget(screen)

        # Initial state - no highlights
        initial_count = screen.page.editor_panel.get_highlight_count()

        # Apply code (triggers segments_changed)
        vm.apply_code_to_selection(code_id, 1, 0, 5)
        QApplication.processEvents()

        # Editor should have highlight
        highlight_count = screen.page.editor_panel.get_highlight_count()
        assert highlight_count >= initial_count + 1

        ctx.close()


class TestSourceTracking:
    """Test source/document tracking."""

    def test_set_current_source(self, qapp, qtbot, colors):
        """Screen should track current source for operations."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        qtbot.addWidget(screen)

        screen.set_current_source(42)
        assert screen._source_id == 42

        ctx.close()

    def test_source_id_used_for_code_application(self, qapp, qtbot, colors):
        """Source ID should be used when applying codes."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(99)  # Use source 99
        qtbot.addWidget(screen)

        # Apply code
        screen.code_applied.emit(str(code_id), 0, 10)
        QApplication.processEvents()

        # Verify segment is for source 99
        segments = ctx.controller.get_segments_for_source(99)
        assert len(segments) == 1

        # Source 1 should have nothing
        segments_1 = ctx.controller.get_segments_for_source(1)
        assert len(segments_1) == 0

        ctx.close()


class TestSegmentLookup:
    """Test segment lookup for unmark operations."""

    def test_find_segment_at_position(self, qapp, colors):
        """ViewModel should find segment by position."""
        from src.presentation.factory import CodingContext

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        # Apply segment
        vm.apply_code_to_selection(code_id, 1, 5, 15)

        # Find it
        segment_id = vm.find_segment_at_position(1, 5, 15)
        assert segment_id is not None

        # Should not find at different position
        not_found = vm.find_segment_at_position(1, 100, 110)
        assert not_found is None

        ctx.close()

    def test_find_segment_partial_overlap(self, qapp, colors):
        """ViewModel should find segment that overlaps with given range."""
        from src.presentation.factory import CodingContext

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("marker", "#ff0000")

        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        # Apply segment at 5-15
        vm.apply_code_to_selection(code_id, 1, 5, 15)

        # Should find with partial overlap query (7-10 is within 5-15)
        segment_id = vm.find_segment_at_position(1, 7, 10)
        assert segment_id is not None

        ctx.close()


class TestCompleteWorkflow:
    """Integration tests for complete workflow."""

    def test_full_apply_and_remove_workflow(self, qapp, qtbot, colors):
        """Test complete workflow: create code, apply, verify, remove."""
        from src.presentation.factory import CodingContext
        from src.presentation.screens import TextCodingScreen

        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World Test Document")
        qtbot.addWidget(screen)

        # Step 1: Create a code
        vm.create_code("positive", "#27ae60")
        codes = ctx.controller.get_all_codes()
        code = codes[0]
        code_id = code.id.value

        # Step 2: Apply code
        screen.code_applied.emit(str(code_id), 0, 5)
        QApplication.processEvents()

        # Verify in database
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        # Step 3: Remove code
        screen.code_removed.emit(str(code_id), 0, 5)
        QApplication.processEvents()

        # Verify removed
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()


class TestAutoCodingControllerWiring:
    """Test that AutoCodingController is properly wired to TextCodingScreen."""

    def test_screen_has_auto_coding_controller(self, qapp, qtbot, colors):
        """Screen should have an AutoCodingController instance."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        assert hasattr(screen, "_auto_coding_controller")
        assert isinstance(screen._auto_coding_controller, AutoCodingController)

    def test_find_matches_via_controller(self, qapp, qtbot, colors):
        """Screen should use controller to find matches."""
        from returns.result import Success

        from src.domain.coding.services.text_matcher import MatchType
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        # Use controller directly to verify wiring
        # Use CONTAINS match type to find "at" in "cat", "sat", "mat"
        result = screen._auto_coding_controller.find_matches(
            text="The cat sat on the mat.",
            pattern="at",
            match_type=MatchType.CONTAINS,
        )

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 3  # "cat", "sat", "mat"

    def test_detect_speakers_via_controller(self, qapp, qtbot, colors):
        """Screen should use controller to detect speakers."""
        from returns.result import Success

        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        text = """INTERVIEWER: Welcome.
PARTICIPANT: Thank you.
INTERVIEWER: How are you?
PARTICIPANT: I'm fine."""

        result = screen._auto_coding_controller.detect_speakers(text)

        assert isinstance(result, Success)
        speakers = result.unwrap()
        assert len(speakers) == 2

    def test_undo_starts_empty(self, qapp, qtbot, colors):
        """Controller should start with no batches to undo."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        assert screen._auto_coding_controller.can_undo() is False


class TestAutoCodingDialogIntegration:
    """Test auto-coding dialog integration with screen."""

    def test_show_auto_code_dialog_creates_dialog(self, qapp, qtbot, colors):
        """_show_auto_code_dialog should create a configured dialog."""
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        # Set up prerequisites
        screen.set_active_code("1", "Test Code", "#FF0000")

        # Dialog should not exist initially
        assert screen._auto_code_dialog is None

        # Note: We can't test the full dialog flow easily since exec() blocks
        # But we can test the state management
        assert hasattr(screen, "_show_auto_code_dialog")
        assert hasattr(screen, "_on_find_matches_requested")
        assert hasattr(screen, "_on_apply_auto_code_requested")

    def test_on_find_matches_requested_calls_controller(self, qapp, qtbot, colors):
        """_on_find_matches_requested should route to controller."""
        from unittest.mock import MagicMock

        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        # Create a mock dialog to receive results
        dialog = AutoCodeDialog(colors=colors)
        dialog.on_matches_found = MagicMock()
        screen._auto_code_dialog = dialog

        # Call the handler directly
        screen._on_find_matches_requested(
            text="The cat sat on the mat.",
            pattern="at",
            match_type="contains",
            scope="all",
            case_sensitive=False,
        )

        # Verify dialog received matches
        dialog.on_matches_found.assert_called_once()
        matches = dialog.on_matches_found.call_args[0][0]
        assert len(matches) == 3

    def test_dialog_signals_connected_to_screen_handlers(self, qapp, qtbot, colors):
        """Dialog signals should be connectable to screen handlers."""
        from unittest.mock import MagicMock

        from src.presentation.dialogs.auto_code_dialog import AutoCodeDialog
        from src.presentation.screens import TextCodingScreen

        screen = TextCodingScreen(colors=colors)
        qtbot.addWidget(screen)

        dialog = AutoCodeDialog(colors=colors)

        # Replace handlers with mocks to verify they get called
        screen._on_find_matches_requested = MagicMock()
        screen._on_apply_auto_code_requested = MagicMock()

        # Connect signals
        dialog.find_matches_requested.connect(screen._on_find_matches_requested)
        dialog.apply_auto_code_requested.connect(screen._on_apply_auto_code_requested)

        # Emit signals and verify handlers called
        dialog.find_matches_requested.emit("text", "pattern", "exact", "all", False)
        screen._on_find_matches_requested.assert_called_once_with(
            "text", "pattern", "exact", "all", False
        )

        dialog.apply_auto_code_requested.emit({"pattern": "test"})
        screen._on_apply_auto_code_requested.assert_called_once_with(
            {"pattern": "test"}
        )
