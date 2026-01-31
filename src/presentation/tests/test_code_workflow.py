"""
TDD Tests for QC-007.02 Code Application Workflow.

Integration tests for the keyboard-driven code application workflow.
Tests verify actual database persistence via CodingContext.

For signal-level unit tests, see test_code_application_workflow.py.
"""

import pytest

from src.presentation.screens.text_coding import TextCodingScreen

# Note: qapp, colors, coding_context, viewmodel fixtures come from conftest.py


@pytest.fixture
def screen_with_code(qapp, qtbot, colors, coding_context, viewmodel):  # noqa: ARG001
    """Create a screen with a code already created."""
    # Create a code
    viewmodel.create_code("TestCode", "#ff5500")
    codes = coding_context.controller.get_all_codes()
    code = codes[0]

    # Create screen
    screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
    screen.set_current_source(1)
    screen.page.set_document(
        "Test", text="The quick brown fox jumps over the lazy dog."
    )
    qtbot.addWidget(screen)

    # Set active code
    screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())

    return screen, coding_context, code


# =============================================================================
# AC #1: Q key quick mark
# =============================================================================


class TestQuickMark:
    """Test Q key quick mark functionality."""

    def test_quick_mark_applies_code_to_selection(self, screen_with_code, qapp):
        """AC #1: Q key should apply selected code to text selection."""
        screen, ctx, code = screen_with_code

        # Select text
        screen.set_text_selection(4, 9)  # "quick"

        # Quick mark (simulates Q key)
        screen.quick_mark()
        qapp.processEvents()

        # Verify segment created in database
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1
        assert segments[0].position.start == 4
        assert segments[0].position.end == 9
        assert segments[0].code_id.value == code.id.value

    def test_quick_mark_requires_active_code(self, qapp, qtbot, colors, viewmodel):
        """Quick mark should do nothing without active code."""
        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        qtbot.addWidget(screen)

        # Select text but no active code
        screen.set_text_selection(0, 5)

        # This should not crash
        screen.quick_mark()

        # No active code set, so quick_mark should have no effect

    def test_quick_mark_requires_text_selection(self, screen_with_code, qapp):
        """Quick mark should do nothing without text selection."""
        screen, ctx, _ = screen_with_code

        # No text selection
        screen.clear_text_selection()

        # Quick mark
        screen.quick_mark()
        qapp.processEvents()

        # No segment should be created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0


# =============================================================================
# AC #4: U key unmark
# =============================================================================


class TestUnmark:
    """Test U key unmark functionality."""

    def test_unmark_removes_segment(self, screen_with_code, qapp):
        """AC #4: U key should remove code at cursor position."""
        screen, ctx, code = screen_with_code

        # First apply a code
        screen.set_text_selection(4, 9)
        screen.quick_mark()
        qapp.processEvents()

        # Verify segment exists
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        # Now unmark at same position
        screen.set_text_selection(4, 9)
        screen.unmark()
        qapp.processEvents()

        # Segment should be removed
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0


# =============================================================================
# AC #5: Ctrl+Z undo unmark
# =============================================================================


class TestUndoUnmark:
    """Test Ctrl+Z undo unmark functionality."""

    def test_undo_unmark_restores_segment(self, screen_with_code, qapp):
        """AC #5: Ctrl+Z should restore last unmarked segment."""
        screen, ctx, code = screen_with_code

        # Apply a code
        screen.set_text_selection(4, 9)
        screen.quick_mark()
        qapp.processEvents()

        # Unmark it
        screen.set_text_selection(4, 9)
        screen.unmark()
        qapp.processEvents()

        assert len(ctx.controller.get_segments_for_source(1)) == 0

        # Undo unmark
        screen.undo_unmark()
        qapp.processEvents()

        # Segment should be restored
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1


# =============================================================================
# AC #8: text_selected enables quick mark
# =============================================================================


class TestTextSelectionEnablesQuickMark:
    """Test that text selection enables quick mark."""

    def test_text_selection_enables_quick_mark(self, screen_with_code, qapp):
        """AC #8: text_selected should enable quick mark."""
        screen, _, _ = screen_with_code

        # Initially no selection
        assert not screen.is_quick_mark_enabled()

        # Select text
        screen.set_text_selection(0, 5)

        # Quick mark should be enabled
        assert screen.is_quick_mark_enabled()

    def test_clearing_selection_disables_quick_mark(self, screen_with_code, qapp):
        """Clearing selection should disable quick mark."""
        screen, _, _ = screen_with_code

        # Select then clear
        screen.set_text_selection(0, 5)
        assert screen.is_quick_mark_enabled()

        screen.clear_text_selection()
        assert not screen.is_quick_mark_enabled()


# =============================================================================
# AC #10: code_applied triggers highlight update
# =============================================================================


class TestCodeAppliedTriggersHighlight:
    """Test that applying code updates highlights."""

    def test_quick_mark_adds_highlight(self, screen_with_code, qapp):
        """AC #10: code_applied should trigger highlight in editor."""
        screen, ctx, code = screen_with_code

        # Get initial highlight count
        initial_count = screen.page.editor_panel.get_highlight_count()

        # Apply code
        screen.set_text_selection(4, 9)
        screen.quick_mark()
        qapp.processEvents()

        # Highlight count should increase
        # Note: The highlight is applied via segments_changed signal from viewmodel
        # which triggers _on_viewmodel_segments_changed
        final_count = screen.page.editor_panel.get_highlight_count()
        assert final_count > initial_count


# =============================================================================
# AC #3: R key recent codes
# =============================================================================


class TestRecentCodes:
    """Test R key recent codes functionality."""

    def test_recent_codes_tracked(self, screen_with_code, qapp):
        """Recent codes should be tracked when codes are used."""
        screen, ctx, code = screen_with_code

        # Active code should be in recent
        assert len(screen._recent_codes) >= 1
        assert screen._recent_codes[0]["id"] == str(code.id.value)

    def test_apply_recent_code(self, screen_with_code, qapp):
        """AC #3: Should be able to apply code from recent list."""
        screen, ctx, code = screen_with_code

        # Select text
        screen.set_text_selection(10, 15)

        # Apply from recent
        screen.apply_recent_code(str(code.id.value))
        qapp.processEvents()

        # Segment should be created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1


# =============================================================================
# Integration: Full keyboard workflow
# =============================================================================


class TestFullKeyboardWorkflow:
    """Test complete keyboard-driven workflow."""

    def test_complete_coding_session(self, screen_with_code, qapp):
        """Test a complete coding session with keyboard shortcuts."""
        screen, ctx, code = screen_with_code

        # 1. Select text and quick mark (Q)
        screen.set_text_selection(4, 9)  # "quick"
        screen.quick_mark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        # 2. Select another range and quick mark
        screen.set_text_selection(10, 15)  # "brown"
        screen.quick_mark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 2

        # 3. Unmark the second one (U)
        screen.set_text_selection(10, 15)
        screen.unmark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        # 4. Undo unmark (Ctrl+Z)
        screen.undo_unmark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 2


# =============================================================================
# QC-007.10: Additional Keyboard Shortcuts
# =============================================================================


class TestKeyboardShortcuts:
    """Test QC-007.10 keyboard shortcuts are registered."""

    def test_all_shortcuts_registered(self, screen_with_code, qapp):
        """All required shortcuts should be registered."""
        screen, _, _ = screen_with_code

        shortcuts = screen.get_registered_shortcuts()

        # Core coding shortcuts
        assert "Q" in shortcuts  # Quick mark
        assert "U" in shortcuts  # Unmark
        assert "N" in shortcuts  # New code
        assert "V" in shortcuts  # In-vivo
        assert "M" in shortcuts  # Memo
        assert "A" in shortcuts  # Annotate
        assert "R" in shortcuts  # Recent codes
        assert "I" in shortcuts  # Important
        assert "Ctrl+Z" in shortcuts  # Undo

        # Navigation
        assert "Ctrl+F" in shortcuts  # Search
        assert "O" in shortcuts  # Cycle overlaps

        # Display
        assert "H" in shortcuts  # Toggle panels


class TestInVivoCode:
    """Test V key in-vivo coding."""

    def test_in_vivo_creates_and_applies_code(
        self, qapp, qtbot, colors, coding_context
    ):
        """AC #4: V key should create code from selection and apply it."""
        viewmodel = coding_context.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=viewmodel, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="The quick brown fox")
        qtbot.addWidget(screen)

        # Select text
        screen.set_text_selection(4, 9)  # "quick"

        # In-vivo code
        screen.in_vivo_code()
        qapp.processEvents()

        # Should have created a code
        codes = coding_context.controller.get_all_codes()
        assert len(codes) == 1
        assert codes[0].name == "quick"

        # Should have applied it
        segments = coding_context.controller.get_segments_for_source(1)
        assert len(segments) == 1


class TestTogglePanels:
    """Test H key panel toggle."""

    def test_toggle_panels_changes_visibility(self, screen_with_code, qapp):
        """AC #19: H key should toggle panel visibility."""
        screen, _, _ = screen_with_code

        # Initially visible
        assert screen.are_panels_visible()

        # Toggle off
        screen.toggle_panels()
        assert not screen.are_panels_visible()

        # Toggle on
        screen.toggle_panels()
        assert screen.are_panels_visible()
