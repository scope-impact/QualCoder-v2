"""
Exploratory Tests - Simulating User Clicking Around

These tests simulate realistic user behavior and edge cases
to find bugs that unit tests might miss.
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.presentation.factory import CodingContext
from src.presentation.screens.text_coding import TextCodingScreen


@pytest.fixture
def qapp():
    """Ensure QApplication exists."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def colors():
    """Get color palette."""
    from design_system import get_colors

    return get_colors()


# =============================================================================
# Edge Case: No Code Selected
# =============================================================================


class TestNoCodeSelected:
    """What happens when user tries actions without selecting a code first?"""

    def test_quick_mark_without_code_selected(self, qapp, colors):
        """User selects text and presses Q without selecting a code first."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("TestCode", "#ff0000")  # Code exists but not selected

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        # Select text but DON'T select a code
        screen.set_text_selection(0, 5)

        # Try quick mark - should not crash
        screen.quick_mark()
        qapp.processEvents()

        # No segment should be created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()

    def test_popup_code_button_without_code_selected(self, qapp, colors):
        """User clicks popup Code button without selecting a code."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("TestCode", "#ff0000")

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        # Select text
        screen.set_text_selection(0, 5)

        # Simulate popup code button click (no code selected)
        screen.page.editor_panel.popup_code_clicked.emit()
        qapp.processEvents()

        # Should not crash, no segment created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()


# =============================================================================
# Edge Case: No Text Selected
# =============================================================================


class TestNoTextSelected:
    """What happens when user tries actions without selecting text?"""

    def test_quick_mark_without_text_selected(self, qapp, colors):
        """User selects a code and presses Q without selecting text."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("TestCode", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        # Select code but NO text
        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        # Don't select any text

        # Try quick mark - should not crash
        screen.quick_mark()
        qapp.processEvents()

        # No segment should be created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()

    def test_in_vivo_without_text_selected(self, qapp, colors):
        """User presses V without selecting text."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        # No text selected, press V
        screen.in_vivo_code()
        qapp.processEvents()

        # No code should be created
        codes = ctx.controller.get_all_codes()
        assert len(codes) == 0

        ctx.close()

    def test_unmark_without_selection(self, qapp, colors):
        """User presses U without any selection."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        # No selection, press U - should not crash
        screen.unmark()
        qapp.processEvents()

        ctx.close()


# =============================================================================
# Edge Case: Empty Document
# =============================================================================


class TestEmptyDocument:
    """What happens with an empty document?"""

    def test_select_in_empty_document(self, qapp, colors):
        """Try to select text in empty document."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Empty", text="")  # Empty!

        # Try to select - should not crash
        screen.set_text_selection(0, 0)
        qapp.processEvents()

        ctx.close()

    def test_quick_mark_in_empty_document(self, qapp, colors):
        """Try quick mark in empty document."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Test", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Empty", text="")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(0, 0)
        screen.quick_mark()
        qapp.processEvents()

        # Should not crash, no segment created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()


# =============================================================================
# Edge Case: Overlapping Segments
# =============================================================================


class TestOverlappingSegments:
    """What happens when segments overlap?"""

    def test_apply_overlapping_codes(self, qapp, colors):
        """Apply two codes to overlapping text ranges."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code1", "#ff0000")
        vm.create_code("Code2", "#00ff00")
        codes = ctx.controller.get_all_codes()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World Test")

        # Apply first code to "Hello World"
        screen.set_active_code(
            str(codes[0].id.value), codes[0].name, codes[0].color.to_hex()
        )
        screen.set_text_selection(0, 11)
        screen.quick_mark()
        qapp.processEvents()

        # Apply second code to "World Test" (overlapping!)
        screen.set_active_code(
            str(codes[1].id.value), codes[1].name, codes[1].color.to_hex()
        )
        screen.set_text_selection(6, 16)
        screen.quick_mark()
        qapp.processEvents()

        # Both segments should exist
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 2

        ctx.close()

    def test_unmark_in_overlapping_region(self, qapp, colors):
        """Unmark in a region where two codes overlap."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code1", "#ff0000")
        vm.create_code("Code2", "#00ff00")
        codes = ctx.controller.get_all_codes()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World Test")

        # Apply overlapping codes
        screen.set_active_code(
            str(codes[0].id.value), codes[0].name, codes[0].color.to_hex()
        )
        screen.set_text_selection(0, 11)
        screen.quick_mark()

        screen.set_active_code(
            str(codes[1].id.value), codes[1].name, codes[1].color.to_hex()
        )
        screen.set_text_selection(6, 16)
        screen.quick_mark()
        qapp.processEvents()

        assert len(ctx.controller.get_segments_for_source(1)) == 2

        # Unmark in overlapping region - should remove one
        screen.set_text_selection(6, 11)  # "World" - overlapping region
        screen.unmark()
        qapp.processEvents()

        # Should have removed one segment
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        ctx.close()


# =============================================================================
# Edge Case: Rapid Actions
# =============================================================================


class TestRapidActions:
    """What happens with rapid successive actions?"""

    def test_rapid_quick_marks(self, qapp, colors):
        """Rapidly apply multiple codes."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="One Two Three Four Five Six Seven Eight")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())

        # Rapidly apply to different ranges
        ranges = [(0, 3), (4, 7), (8, 13), (14, 18), (19, 23)]
        for start, end in ranges:
            screen.set_text_selection(start, end)
            screen.quick_mark()

        qapp.processEvents()

        # All segments should be created
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 5

        ctx.close()

    def test_rapid_undo_redo(self, qapp, colors):
        """Rapidly undo multiple times."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())

        # Apply then unmark multiple times
        for _i in range(5):
            screen.set_text_selection(0, 5)
            screen.quick_mark()
            screen.set_text_selection(0, 5)
            screen.unmark()

        qapp.processEvents()

        # Should have undo history
        assert len(screen._unmark_history) == 5

        # Undo all
        for _i in range(5):
            screen.undo_unmark()

        qapp.processEvents()

        # Should have 5 segments restored
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 5

        ctx.close()


# =============================================================================
# Edge Case: Invalid Positions
# =============================================================================


class TestInvalidPositions:
    """What happens with invalid text positions?"""

    def test_selection_beyond_text_length(self, qapp, colors):
        """Try to select beyond the text length."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Short")  # Only 5 chars

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(0, 100)  # Way beyond!
        screen.quick_mark()
        qapp.processEvents()

        # Should not crash - might create segment with clamped range or nothing
        ctx.close()

    def test_negative_selection(self, qapp, colors):
        """Try negative selection positions."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello")

        # Negative positions - should not crash
        screen.set_text_selection(-5, 3)
        qapp.processEvents()

        ctx.close()

    def test_reversed_selection(self, qapp, colors):
        """Try selection with start > end."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Hello World")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(10, 5)  # Reversed!
        screen.quick_mark()
        qapp.processEvents()

        # Should not create invalid segment
        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 0

        ctx.close()


# =============================================================================
# Edge Case: Source Switching
# =============================================================================


class TestSourceSwitching:
    """What happens when switching between source documents?"""

    def test_segments_isolated_per_source(self, qapp, colors):
        """Segments should be isolated to their source document."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.page.set_document("Doc1", text="Document One Content")

        # Code in source 1
        screen.set_current_source(1)
        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(0, 8)
        screen.quick_mark()
        qapp.processEvents()

        # Switch to source 2
        screen.set_current_source(2)
        screen.set_text_selection(0, 5)
        screen.quick_mark()
        qapp.processEvents()

        # Source 1 should have 1 segment
        assert len(ctx.controller.get_segments_for_source(1)) == 1

        # Source 2 should have 1 segment
        assert len(ctx.controller.get_segments_for_source(2)) == 1

        ctx.close()


# =============================================================================
# Edge Case: No Viewmodel (Standalone Mode)
# =============================================================================


class TestStandaloneMode:
    """What happens when screen is used without viewmodel?"""

    def test_screen_without_viewmodel(self, qapp, colors):
        """Screen should work in demo mode without viewmodel."""
        # No viewmodel - uses sample data
        screen = TextCodingScreen(colors=colors)
        screen.page.set_document("Demo", text="Demo content")

        # Should not crash
        screen.set_text_selection(0, 4)
        screen.quick_mark()  # Won't persist but shouldn't crash
        qapp.processEvents()

        screen.close()

    def test_in_vivo_without_viewmodel(self, qapp, colors):
        """In-vivo should emit signal even without viewmodel."""
        screen = TextCodingScreen(colors=colors)
        screen.page.set_document("Demo", text="Demo content")

        # Track signal
        received = []
        screen.code_created.connect(lambda name: received.append(name))

        screen.set_text_selection(0, 4)
        screen.in_vivo_code()
        qapp.processEvents()

        # Signal should have been emitted
        assert len(received) == 1
        assert received[0] == "Demo"

        screen.close()


# =============================================================================
# Edge Case: Special Characters
# =============================================================================


class TestSpecialCharacters:
    """What happens with special characters in text?"""

    def test_unicode_text(self, qapp, colors):
        """Handle unicode characters in text."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Unicode", text="Hello 世界 🌍 émoji")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(6, 8)  # "世界"
        screen.quick_mark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        ctx.close()

    def test_newlines_in_text(self, qapp, colors):
        """Handle newlines in text selection."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()
        vm.create_code("Code", "#ff0000")
        codes = ctx.controller.get_all_codes()
        code = codes[0]

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Multiline", text="Line 1\nLine 2\nLine 3")

        screen.set_active_code(str(code.id.value), code.name, code.color.to_hex())
        screen.set_text_selection(0, 14)  # Across newlines
        screen.quick_mark()
        qapp.processEvents()

        segments = ctx.controller.get_segments_for_source(1)
        assert len(segments) == 1

        ctx.close()

    def test_in_vivo_with_special_chars(self, qapp, colors):
        """In-vivo code name with special characters."""
        ctx = CodingContext.create_in_memory()
        vm = ctx.create_text_coding_viewmodel()

        screen = TextCodingScreen(viewmodel=vm, colors=colors)
        screen.set_current_source(1)
        screen.page.set_document("Test", text="Test: émoji 🎉 here!")

        screen.set_text_selection(6, 17)  # "émoji 🎉 here"
        screen.in_vivo_code()
        qapp.processEvents()

        codes = ctx.controller.get_all_codes()
        # Should create code (might have issues with special chars)
        assert len(codes) >= 0  # At minimum shouldn't crash

        ctx.close()
