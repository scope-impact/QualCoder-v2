"""
Signal-Level Unit Tests for Code Application Workflow (QC-007.02)

These tests verify signal emission behavior WITHOUT database overhead.
For integration tests with database persistence, see test_code_workflow.py.

Tests unique signal behaviors:
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
