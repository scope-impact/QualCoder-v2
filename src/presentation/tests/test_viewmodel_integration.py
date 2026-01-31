"""
TDD Tests for QC-007.21 ViewModel Integration.

Tests the wiring between Presentation layer and Application layer:
- Text selection signals from TextEditorPanel
- ViewModel command methods
- Screen-to-ViewModel signal routing
- ViewModel-to-Screen signal routing
- Source document tracking

Note: qapp, colors, coding_context, viewmodel fixtures from root conftest.py.
"""

import pytest

from src.presentation.organisms.text_editor_panel import TextEditorPanel
from src.presentation.screens.text_coding import TextCodingScreen

pytestmark = pytest.mark.integration  # All tests in this module are integration tests


# =============================================================================
# AC #1: TextEditorPanel emits text_selected(start, end, text)
# =============================================================================


class TestTextSelectionCapture:
    """Test that TextEditorPanel captures and emits text selection."""

    def test_text_editor_panel_has_text_selected_signal(self, qapp, colors):
        """AC #1: TextEditorPanel should have text_selected signal."""
        panel = TextEditorPanel(colors=colors)
        assert hasattr(panel, "text_selected")

    def test_text_selected_emitted_on_selection(self, qapp, qtbot, colors):
        """AC #1: text_selected should emit when user selects text."""
        panel = TextEditorPanel(colors=colors)
        qtbot.addWidget(panel)
        panel.set_document("Test", text="Hello World Test Document")

        # Track signal emissions
        received = []
        panel.text_selected.connect(lambda t, s, e: received.append((t, s, e)))

        # Simulate selection by setting cursor range
        panel.select_range(0, 5)

        # Should have emitted
        assert len(received) >= 1
        text, start, end = received[-1]
        assert start == 0
        assert end == 5
        assert "Hello" in text


# =============================================================================
# AC #3: Clearing selection emits text_deselected
# =============================================================================


class TestTextDeselection:
    """Test text deselection signal."""

    def test_text_editor_panel_has_text_deselected_signal(self, qapp, colors):
        """AC #3: TextEditorPanel should have text_deselected signal."""
        panel = TextEditorPanel(colors=colors)
        assert hasattr(panel, "text_deselected")

    def test_text_deselected_emitted_on_clear(self, qapp, qtbot, colors):
        """AC #3: text_deselected should emit when selection is cleared."""
        panel = TextEditorPanel(colors=colors)
        qtbot.addWidget(panel)
        panel.set_document("Test", text="Hello World")

        # Track deselection
        deselected = []
        panel.text_deselected.connect(lambda: deselected.append(True))

        # Select then clear
        panel.select_range(0, 5)
        panel.clear_selection()

        assert len(deselected) >= 1


# =============================================================================
# AC #4-7: ViewModel Command Methods
# =============================================================================


class TestViewModelCommands:
    """Test ViewModel command methods call controller correctly."""

    def test_apply_code_to_selection_creates_segment(
        self, qapp, coding_context, viewmodel
    ):
        """AC #4: apply_code_to_selection should call controller.apply_code."""
        # Create a code first
        viewmodel.create_code("TestCode", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        assert len(codes) == 1
        code_id = codes[0].id.value

        # Apply code to selection
        result = viewmodel.apply_code_to_selection(
            code_id=code_id,
            source_id=1,
            start=0,
            end=10,
        )

        assert result is True

        # Verify segment was created
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].position.start == 0
        assert segments[0].position.end == 10

    def test_remove_segment_deletes_segment(self, qapp, coding_context, viewmodel):
        """AC #5: remove_segment should call controller.remove_code."""
        # Create code and segment
        viewmodel.create_code("TestCode", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value
        viewmodel.apply_code_to_selection(code_id, 1, 0, 10)

        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        segment_id = segments[0].id.value

        # Remove the segment
        result = viewmodel.remove_segment(segment_id)
        assert result is True

        # Verify segment was removed
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 0

    def test_create_code_creates_in_database(self, qapp, coding_context, viewmodel):
        """AC #6: create_code should call controller.create_code."""
        result = viewmodel.create_code("NewCode", "#00ff00")
        assert result is True

        codes = coding_context.controller.get_all_codes()
        assert len(codes) == 1
        assert codes[0].name == "NewCode"

    def test_commands_return_false_on_failure(self, qapp, coding_context, viewmodel):
        """AC #7: Commands should return False on failure."""
        # Try to apply non-existent code
        result = viewmodel.apply_code_to_selection(
            code_id=99999,  # Non-existent
            source_id=1,
            start=0,
            end=10,
        )
        assert result is False


# =============================================================================
# AC #8-10: Screen-to-ViewModel Wiring
# =============================================================================


class TestScreenToViewModelWiring:
    """Test screen signals route to viewmodel methods."""

    def test_screen_accepts_viewmodel(self, qapp, qtbot, colors, viewmodel):
        """Screen should accept viewmodel parameter."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        qtbot.addWidget(screen)
        assert screen._viewmodel is viewmodel

    def test_code_applied_routes_to_viewmodel(
        self, qapp, qtbot, colors, coding_context, viewmodel
    ):
        """AC #8: code_applied signal should route to viewmodel."""
        # Create a code
        viewmodel.create_code("Marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        # Create screen with viewmodel
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        qtbot.addWidget(screen)

        # Emit code_applied signal
        screen.code_applied.emit(str(code_id), 0, 10)

        # Wait for signal processing
        qapp.processEvents()

        # Verify segment was created in database
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1

    def test_code_removed_routes_to_viewmodel(
        self, qapp, qtbot, colors, coding_context, viewmodel
    ):
        """AC #9: code_removed signal should route to viewmodel."""
        # Create code and segment
        viewmodel.create_code("Marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value
        viewmodel.apply_code_to_selection(code_id, 1, 5, 15)

        # Create screen
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        qtbot.addWidget(screen)

        # Emit code_removed signal (with position that overlaps the segment)
        screen.code_removed.emit(str(code_id), 5, 15)

        qapp.processEvents()

        # Verify segment was removed
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 0


# =============================================================================
# AC #11-13: ViewModel-to-Screen Wiring
# =============================================================================


class TestViewModelToScreenWiring:
    """Test viewmodel signals update screen."""

    def test_codes_changed_updates_screen(self, qapp, qtbot, colors, viewmodel):
        """AC #11: codes_changed should update CodesPanel."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        qtbot.addWidget(screen)

        # Track codes_changed emissions
        received = []
        viewmodel.codes_changed.connect(lambda cats: received.append(cats))

        # Create a code (triggers codes_changed via SignalBridge)
        viewmodel.create_code("NewCode", "#00ff00")

        qapp.processEvents()

        # Should have received codes_changed
        assert len(received) >= 1

    def test_segments_changed_updates_highlights(
        self, qapp, qtbot, colors, coding_context, viewmodel
    ):
        """AC #12: segments_changed should update TextEditorPanel highlights."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World Test Document")
        qtbot.addWidget(screen)

        # Track segments_changed
        received = []
        viewmodel.segments_changed.connect(lambda segs: received.append(segs))

        # Create code and apply it
        viewmodel.create_code("Marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value
        viewmodel.apply_code_to_selection(code_id, 1, 0, 5)

        qapp.processEvents()

        # Should have received segments_changed
        assert len(received) >= 1

    def test_error_occurred_emits_on_failure(self, qapp, qtbot, colors, viewmodel):
        """AC #13: operation_failed should be emitted on error."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        qtbot.addWidget(screen)

        # Track error signal
        errors = []
        viewmodel.error_occurred.connect(lambda msg: errors.append(msg))

        # Try to apply non-existent code
        viewmodel.apply_code_to_selection(99999, 1, 0, 10)

        qapp.processEvents()

        # Should have received error
        assert len(errors) >= 1


# =============================================================================
# AC #14-16: Source Document Tracking
# =============================================================================


class TestSourceTracking:
    """Test source document tracking."""

    def test_set_current_source_on_screen(self, qapp, qtbot, colors, viewmodel):
        """AC #14: Screen should track _source_id."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        qtbot.addWidget(screen)

        screen.set_current_source(42)
        assert screen._source_id == 42

    def test_set_current_source_propagates_to_viewmodel(
        self, qapp, qtbot, colors, viewmodel
    ):
        """AC #15: set_current_source should update viewmodel."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        qtbot.addWidget(screen)

        screen.set_current_source(42)

        # Viewmodel should also have updated
        assert viewmodel._current_source_id == 42

    def test_source_id_used_in_apply_code(
        self, qapp, qtbot, colors, coding_context, viewmodel
    ):
        """AC #16: source_id should be passed with operations."""
        viewmodel.create_code("Marker", "#ff0000")
        codes = coding_context.controller.get_all_codes()
        code_id = codes[0].id.value

        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(99)  # Specific source ID
        qtbot.addWidget(screen)

        # Emit code_applied
        screen.code_applied.emit(str(code_id), 0, 10)
        qapp.processEvents()

        # Segment should be in source 99
        segments = coding_context.controller.get_segments_for_source(99)
        assert len(segments) == 1


# =============================================================================
# Integration: Full Flow Test
# =============================================================================


class TestFullIntegrationFlow:
    """Test complete end-to-end flow."""

    def test_full_coding_flow(self, qapp, qtbot, colors, coding_context, viewmodel):
        """
        Test complete flow:
        1. Create code
        2. Set up screen with viewmodel
        3. Select text
        4. Apply code via signal
        5. Verify highlight appears
        6. Remove code
        7. Verify highlight removed
        """
        # 1. Create code
        viewmodel.create_code("TestCode", "#ff5500")
        codes = coding_context.controller.get_all_codes()
        code = codes[0]

        # 2. Create screen
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document(
            "Test Doc", text="The quick brown fox jumps over the lazy dog."
        )
        qtbot.addWidget(screen)

        # 3. Set active code and selection
        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(4, 9)  # "quick"

        # 4. Apply code via quick_mark
        screen.quick_mark()
        qapp.processEvents()

        # 5. Verify segment created
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].position.start == 4
        assert segments[0].position.end == 9

        # 6. Find and remove the segment
        segment_id = viewmodel.find_segment_at_position(1, 4, 9)
        assert segment_id is not None
        viewmodel.remove_segment(segment_id)
        qapp.processEvents()

        # 7. Verify segment removed
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 0
