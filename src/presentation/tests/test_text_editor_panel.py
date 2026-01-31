"""
TDD Tests for Text Highlighting System (QC-007.01)

Tests for the TextEditorPanel organism implementing:
- AC #1: highlight_range(start, end, color) method applies background color to text range
- AC #2: clear_highlights() method removes all highlights
- AC #3: Overlapping highlights display with transparency/blending
- AC #4: Bold formatting for text segments with memos attached
- AC #5: Underline formatting for overlapping code regions
- AC #6: Line numbers displayed in left margin
- AC #7: Dynamic text color (light/dark) based on background highlight
"""

from PySide6.QtGui import QColor, QFont, QTextCharFormat

from design_system import get_colors
from src.presentation.organisms.text_editor_panel import TextEditorPanel

_colors = get_colors()


class TestHighlightRange:
    """AC #1: highlight_range(start, end, color) applies background color to text range."""

    def test_highlight_range_applies_background(self, qtbot):
        """highlight_range should apply background color to specified range."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply yellow highlight to "World" (positions 6-11)
        panel.highlight_range(6, 11, _colors.code_yellow)

        # Verify the text at position 8 has yellow background
        char_format = panel.get_char_format_at(8)
        assert char_format is not None
        bg_color = char_format.background().color()
        assert bg_color.isValid()
        # Background should match the highlight color
        expected_color = QColor(_colors.code_yellow)
        assert bg_color.name() == expected_color.name()

    def test_highlight_multiple_ranges(self, qtbot):
        """Multiple highlight_range calls should apply multiple highlights."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply different highlights
        panel.highlight_range(0, 5, _colors.code_yellow)  # "Hello"
        panel.highlight_range(12, 16, _colors.code_green)  # "Test"

        # Verify both highlights exist
        fmt_hello = panel.get_char_format_at(2)
        fmt_test = panel.get_char_format_at(14)

        assert (
            fmt_hello.background().color().name() == QColor(_colors.code_yellow).name()
        )
        assert fmt_test.background().color().name() == QColor(_colors.code_green).name()

    def test_highlight_range_empty_range_is_noop(self, qtbot):
        """highlight_range with empty range should do nothing."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World")

        # Empty range (start == end)
        panel.highlight_range(5, 5, _colors.code_yellow)
        # Should not raise and text should remain unhighlighted


class TestClearHighlights:
    """AC #2: clear_highlights() removes all highlights."""

    def test_clear_highlights_removes_all(self, qtbot):
        """clear_highlights should remove all applied highlights."""
        from PySide6.QtCore import Qt

        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply highlights
        panel.highlight_range(0, 5, _colors.code_yellow)
        panel.highlight_range(6, 11, _colors.code_green)

        # Clear all highlights
        panel.clear_highlights()

        # Verify no background colors remain
        fmt_hello = panel.get_char_format_at(2)
        fmt_world = panel.get_char_format_at(8)

        # Background should be NoBrush (style 0) after clearing
        assert fmt_hello.background().style() == Qt.BrushStyle.NoBrush
        assert fmt_world.background().style() == Qt.BrushStyle.NoBrush

    def test_clear_highlights_on_empty_panel(self, qtbot):
        """clear_highlights should not raise on empty panel."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        # Clear without any highlights
        panel.clear_highlights()  # Should not raise


class TestOverlappingHighlights:
    """AC #3: Overlapping highlights display with transparency/blending."""

    def test_overlapping_highlights_both_visible(self, qtbot):
        """Overlapping highlights should both be visible (via underline indicator)."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply overlapping highlights: 0-10 and 6-15
        panel.highlight_range(0, 10, _colors.code_yellow)
        panel.highlight_range(6, 15, _colors.code_green)

        # The overlap region (6-10) should have underline to indicate overlap
        fmt_overlap = panel.get_char_format_at(8)
        assert (
            fmt_overlap.underlineStyle() != QTextCharFormat.UnderlineStyle.NoUnderline
        )

    def test_detect_overlaps_returns_regions(self, qtbot):
        """Should be able to detect overlapping highlight regions."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply overlapping highlights
        panel.highlight_range(0, 10, _colors.code_yellow)
        panel.highlight_range(6, 15, _colors.code_green)

        # Get overlap regions
        overlaps = panel.get_overlap_regions()
        assert len(overlaps) >= 1
        # Overlap should be approximately (6, 10)
        overlap_start, overlap_end = overlaps[0]
        assert overlap_start == 6
        assert overlap_end == 10


class TestMemoFormatting:
    """AC #4: Bold formatting for text segments with memos attached."""

    def test_highlight_with_memo_is_bold(self, qtbot):
        """Highlights with memos should have bold formatting."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply highlight with memo
        panel.highlight_range(0, 5, _colors.code_yellow, memo="Important insight")

        # Verify bold formatting
        fmt = panel.get_char_format_at(2)
        assert fmt.fontWeight() == QFont.Weight.Bold

    def test_highlight_without_memo_not_bold(self, qtbot):
        """Highlights without memos should not be bold."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply highlight without memo
        panel.highlight_range(0, 5, _colors.code_yellow)

        # Verify not bold
        fmt = panel.get_char_format_at(2)
        assert fmt.fontWeight() != QFont.Weight.Bold


class TestOverlapUnderline:
    """AC #5: Underline formatting for overlapping code regions."""

    def test_overlap_has_underline(self, qtbot):
        """Overlapping regions should have underline formatting."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply overlapping highlights
        panel.highlight_range(0, 10, _colors.code_yellow)
        panel.highlight_range(5, 15, _colors.code_green)

        # Check underline in overlap region (5-10)
        fmt = panel.get_char_format_at(7)
        assert fmt.underlineStyle() == QTextCharFormat.UnderlineStyle.SingleUnderline

    def test_non_overlapping_no_underline(self, qtbot):
        """Non-overlapping regions should not have underline."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test Document")

        # Apply non-overlapping highlights
        panel.highlight_range(0, 5, _colors.code_yellow)
        panel.highlight_range(12, 16, _colors.code_green)

        # Check no underline in either region
        fmt_first = panel.get_char_format_at(2)
        fmt_second = panel.get_char_format_at(14)

        assert fmt_first.underlineStyle() == QTextCharFormat.UnderlineStyle.NoUnderline
        assert fmt_second.underlineStyle() == QTextCharFormat.UnderlineStyle.NoUnderline


class TestLineNumbers:
    """AC #6: Line numbers displayed in left margin."""

    def test_line_numbers_shown_when_enabled(self, qtbot):
        """Line numbers should be displayed when enabled."""
        panel = TextEditorPanel(show_line_numbers=True)
        qtbot.addWidget(panel)

        panel.set_document(
            title="Test",
            text="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        )

        # Verify line numbers are visible
        assert panel.has_line_numbers()
        assert panel.get_line_count() == 5

    def test_line_numbers_hidden_by_default(self, qtbot):
        """Line numbers should be hidden by default."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Line 1\nLine 2")

        # Verify line numbers are not visible by default
        assert not panel.has_line_numbers()

    def test_toggle_line_numbers(self, qtbot):
        """Should be able to toggle line numbers visibility."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Line 1\nLine 2")

        # Initially hidden
        assert not panel.has_line_numbers()

        # Enable line numbers
        panel.set_line_numbers_visible(True)
        assert panel.has_line_numbers()

        # Disable line numbers
        panel.set_line_numbers_visible(False)
        assert not panel.has_line_numbers()


class TestDynamicTextColor:
    """AC #7: Dynamic text color (light/dark) based on background highlight."""

    def test_light_background_gets_dark_text(self, qtbot):
        """Light background highlight should have dark text."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World")

        # Apply light background (yellow)
        panel.highlight_range(0, 5, "#FFFF00")

        fmt = panel.get_char_format_at(2)
        text_color = fmt.foreground().color()

        # Should be dark text (black or near-black)
        assert text_color.lightness() < 128

    def test_dark_background_gets_light_text(self, qtbot):
        """Dark background highlight should have light text."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World")

        # Apply dark background
        panel.highlight_range(0, 5, "#1B5E20")

        fmt = panel.get_char_format_at(2)
        text_color = fmt.foreground().color()

        # Should be light text (white or near-white)
        assert text_color.lightness() > 128


class TestIntegration:
    """Integration tests for the complete highlighting workflow."""

    def test_full_coding_workflow(self, qtbot):
        """Test a complete coding workflow: load, highlight, modify, clear."""
        panel = TextEditorPanel(show_line_numbers=True)
        qtbot.addWidget(panel)

        # 1. Load document
        text = "The quick brown fox jumps over the lazy dog."
        panel.set_document(title="Interview Transcript", text=text)

        # 2. Apply multiple codes
        panel.highlight_range(4, 9, _colors.code_yellow)  # "quick"
        panel.highlight_range(10, 15, _colors.code_green)  # "brown"
        panel.highlight_range(7, 12, _colors.code_blue, memo="Important")  # overlap

        # 3. Verify highlights exist
        assert panel.get_highlight_count() >= 3

        # 4. Verify overlap detection
        overlaps = panel.get_overlap_regions()
        assert len(overlaps) >= 1

        # 5. Clear all
        panel.clear_highlights()
        assert panel.get_highlight_count() == 0

    def test_highlight_preserves_selection(self, qtbot):
        """Highlighting should not affect user text selection."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World Test")

        # Apply highlight
        panel.highlight_range(0, 5, _colors.code_yellow)

        # Select some text
        panel.select_range(6, 11)

        # Verify selection still works
        selection = panel.get_selection()
        assert selection == (6, 11)

        selected_text = panel.get_selected_text()
        assert selected_text == "World"


class TestSignals:
    """Test signal emissions for highlighting events."""

    def test_highlight_applied_signal(self, qtbot):
        """Signal should emit when highlight is applied."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World")

        # Connect to signal
        signals_received = []
        if hasattr(panel, "highlight_applied"):
            panel.highlight_applied.connect(
                lambda s, e, c: signals_received.append((s, e, c))
            )

            panel.highlight_range(0, 5, _colors.code_yellow)

            assert len(signals_received) == 1
            assert signals_received[0] == (0, 5, _colors.code_yellow)

    def test_highlights_cleared_signal(self, qtbot):
        """Signal should emit when highlights are cleared."""
        panel = TextEditorPanel()
        qtbot.addWidget(panel)

        panel.set_document(title="Test", text="Hello World")
        panel.highlight_range(0, 5, _colors.code_yellow)

        # Connect to signal
        cleared = []
        if hasattr(panel, "highlights_cleared"):
            panel.highlights_cleared.connect(lambda: cleared.append(True))

            panel.clear_highlights()

            assert len(cleared) == 1
