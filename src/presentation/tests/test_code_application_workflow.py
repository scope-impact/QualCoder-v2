"""
TDD Tests for Code Application Workflow (QC-007.02)

Tests for the complete code application workflow including:
- AC #1: Apply selected code via Q key (quick mark)
- AC #2: In-vivo coding: create new code from selected text (V key)
- AC #3: Apply code from recent codes submenu (R key)
- AC #4: Remove code at cursor position (U key - unmark)
- AC #5: Undo last unmark operation (Ctrl+Z)
- AC #6: Visual feedback (flash/highlight) on code application
- AC #7: Code counts update in tree after apply/remove
- AC #8: text_selected signal enables code application buttons
- AC #9: code_selected signal sets active code for quick-mark
- AC #10: code_applied signal triggers highlight update
"""

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.presentation.screens.text_coding import TextCodingScreen

_colors = get_colors()


class TestQuickMark:
    """AC #1: Apply selected code to text selection via Q key."""

    def test_q_key_applies_selected_code(self, qtbot):
        """Q key should apply the currently selected code to text selection."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: select a code and text
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)

        # Action: press Q key
        spy = QSignalSpy(screen.code_applied)
        screen.quick_mark()

        # Verify: code_applied signal emitted
        assert spy.count() == 1
        emitted = spy.at(0)
        assert emitted[0] == "1"  # code_id
        assert emitted[1] == 0  # start
        assert emitted[2] == 10  # end

    def test_q_key_no_code_selected_shows_warning(self, qtbot):
        """Q key without code selected should show warning."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: text selected but no code
        screen.set_text_selection(start=0, end=10)

        # Action & Verify: should not crash, no signal
        spy = QSignalSpy(screen.code_applied)
        screen.quick_mark()
        assert spy.count() == 0

    def test_q_key_no_text_selected_shows_warning(self, qtbot):
        """Q key without text selected should show warning."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: code selected but no text
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")

        # Action & Verify: should not crash, no signal
        spy = QSignalSpy(screen.code_applied)
        screen.quick_mark()
        assert spy.count() == 0


class TestInVivoCoding:
    """AC #2: In-vivo coding - create new code from selected text (V key)."""

    def test_v_key_creates_code_from_selection(self, qtbot):
        """V key should create new code with selected text as name."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: select text "important concept"
        screen.page.set_document("Test", text="This is an important concept here")
        screen.set_text_selection(start=11, end=28)

        # Action: in-vivo code
        spy = QSignalSpy(screen.code_created)
        screen.in_vivo_code()

        # Verify: code_created signal with text as name
        assert spy.count() == 1
        emitted = spy.at(0)
        assert "important concept" in emitted[0]  # code name from selection

    def test_v_key_no_selection_shows_warning(self, qtbot):
        """V key without selection should show warning."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.code_created)
        screen.in_vivo_code()
        assert spy.count() == 0


class TestRecentCodes:
    """AC #3: Apply code from recent codes submenu (R key)."""

    def test_r_key_shows_recent_codes_menu(self, qtbot):
        """R key should show recent codes popup."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: have some recent codes
        screen.add_to_recent_codes("1", "Code A", "#FFC107")
        screen.add_to_recent_codes("2", "Code B", "#4CAF50")

        # Action: show recent
        screen.show_recent_codes()

        # Verify: recent codes menu visible
        assert screen.has_recent_codes_menu()

    def test_recent_codes_apply_on_select(self, qtbot):
        """Selecting from recent codes should apply that code."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup
        screen.add_to_recent_codes("1", "Code A", "#FFC107")
        screen.set_text_selection(start=0, end=10)

        # Action: apply recent code
        spy = QSignalSpy(screen.code_applied)
        screen.apply_recent_code("1")

        # Verify
        assert spy.count() == 1


class TestUnmark:
    """AC #4: Remove code at cursor position (U key)."""

    def test_u_key_removes_code_at_cursor(self, qtbot):
        """U key should remove code at current cursor position."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: apply a code first
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)
        screen.quick_mark()

        # Move cursor into coded region
        screen.set_cursor_position(5)

        # Action: unmark
        spy = QSignalSpy(screen.code_removed)
        screen.unmark()

        # Verify: code removed
        assert spy.count() == 1

    def test_u_key_no_code_at_cursor_shows_warning(self, qtbot):
        """U key at position without code should show warning."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.code_removed)
        screen.unmark()
        assert spy.count() == 0


class TestUndoUnmark:
    """AC #5: Undo last unmark operation (Ctrl+Z)."""

    def test_ctrl_z_restores_last_unmarked(self, qtbot):
        """Ctrl+Z should restore the last unmarked code."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: apply then unmark
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)
        screen.quick_mark()
        screen.set_cursor_position(5)
        screen.unmark()

        # Action: undo
        spy = QSignalSpy(screen.code_applied)
        screen.undo_unmark()

        # Verify: code restored
        assert spy.count() == 1

    def test_ctrl_z_no_unmark_history_does_nothing(self, qtbot):
        """Ctrl+Z without unmark history should do nothing."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        spy = QSignalSpy(screen.code_applied)
        screen.undo_unmark()
        assert spy.count() == 0


class TestVisualFeedback:
    """AC #6: Visual feedback (flash/highlight) on code application."""

    def test_flash_on_code_apply(self, qtbot):
        """Code application should trigger visual flash."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)

        # Action: apply code
        spy = QSignalSpy(screen.highlight_flashed)
        screen.quick_mark()

        # Verify: flash signal emitted
        assert spy.count() == 1

    def test_flash_on_code_remove(self, qtbot):
        """Code removal should trigger visual flash."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup: have a code to remove
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)
        screen.quick_mark()
        screen.set_cursor_position(5)

        # Action: unmark
        spy = QSignalSpy(screen.highlight_flashed)
        screen.unmark()

        # Verify: flash signal
        assert spy.count() >= 1


class TestCodeCountUpdates:
    """AC #7: Code counts update in tree after apply/remove."""

    def test_count_increases_on_apply(self, qtbot):
        """Code count should increase when code is applied."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup codes with initial count
        screen.set_codes(
            [
                {
                    "name": "Category",
                    "codes": [
                        {"id": "1", "name": "Test", "color": "#FFC107", "count": 5}
                    ],
                }
            ]
        )

        # Apply code
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)
        screen.quick_mark()

        # Verify count updated
        count = screen.get_code_count("1")
        assert count == 6

    def test_count_decreases_on_remove(self, qtbot):
        """Code count should decrease when code is removed."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup
        screen.set_codes(
            [
                {
                    "name": "Category",
                    "codes": [
                        {"id": "1", "name": "Test", "color": "#FFC107", "count": 5}
                    ],
                }
            ]
        )
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=10)
        screen.quick_mark()
        screen.set_cursor_position(5)

        # Remove
        screen.unmark()

        # Verify count
        count = screen.get_code_count("1")
        assert count == 5  # Back to original


class TestTextSelectionSignal:
    """AC #8: text_selected signal enables code application buttons."""

    def test_text_selection_enables_quick_mark(self, qtbot):
        """Text selection should enable quick mark action."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Initially disabled
        assert not screen.is_quick_mark_enabled()

        # Select text
        screen.page.editor_panel.text_selected.emit("test", 0, 4)
        QApplication.processEvents()

        # Now enabled
        assert screen.is_quick_mark_enabled()

    def test_clear_selection_disables_quick_mark(self, qtbot):
        """Clearing selection should disable quick mark action."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Select then clear
        screen.page.editor_panel.text_selected.emit("test", 0, 4)
        QApplication.processEvents()
        screen.clear_text_selection()

        # Disabled again
        assert not screen.is_quick_mark_enabled()


class TestCodeSelectionSignal:
    """AC #9: code_selected signal sets active code for quick-mark."""

    def test_code_selection_sets_active_code(self, qtbot):
        """Selecting a code should set it as active for quick mark."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        # Setup codes
        screen.set_codes(
            [
                {
                    "name": "Category",
                    "codes": [
                        {"id": "1", "name": "Test", "color": "#FFC107", "count": 0}
                    ],
                }
            ]
        )

        # Select code via signal
        screen.page.codes_panel.code_selected.emit({"id": "1"})
        QApplication.processEvents()

        # Verify active code set
        active = screen.get_active_code()
        assert active["id"] == "1"


class TestCodeAppliedSignal:
    """AC #10: code_applied signal triggers highlight update."""

    def test_code_applied_updates_highlight(self, qtbot):
        """code_applied signal should trigger highlight in editor."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        screen.page.set_document("Test", text="Hello World Test")

        # Apply code
        screen.set_active_code(code_id="1", code_name="Test", code_color="#FFC107")
        screen.set_text_selection(start=0, end=5)
        screen.quick_mark()

        # Verify highlight exists
        highlight_count = screen.page.editor_panel.get_highlight_count()
        assert highlight_count >= 1


class TestKeyboardShortcuts:
    """Integration tests for keyboard shortcuts."""

    def test_keyboard_shortcuts_registered(self, qtbot):
        """Screen should have keyboard shortcuts registered."""
        screen = TextCodingScreen(colors=_colors)
        qtbot.addWidget(screen)

        shortcuts = screen.get_registered_shortcuts()
        assert "Q" in shortcuts  # Quick mark
        assert "V" in shortcuts  # In-vivo
        assert "R" in shortcuts  # Recent
        assert "U" in shortcuts  # Unmark
