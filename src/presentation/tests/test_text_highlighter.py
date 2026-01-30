"""
Tests for QualCoder-specific text highlighting components.

These components implement qualitative coding functionality and are
specific to the QualCoder application (not part of the generic design system).
"""

import pytest
from design_system.qt_compat import Qt

from src.presentation.organisms.text_highlighter import (
    TextHighlighter,
    CodeSegment,
    Annotation,
    CodedTextHighlight,
    OverlapIndicator,
    AnnotationIndicator,
)


class TestCodeSegment:
    """Tests for CodeSegment dataclass"""

    def test_default_values(self):
        """CodeSegment should have sensible defaults"""
        segment = CodeSegment()
        assert segment.segment_id == ""
        assert segment.code_color == "#777777"
        assert segment.pos0 == 0
        assert segment.pos1 == 0
        assert segment.important is False

    def test_custom_values(self):
        """CodeSegment should accept custom values"""
        segment = CodeSegment(
            segment_id="seg-1",
            code_id=101,
            code_name="Learning",
            code_color="#FFC107",
            pos0=10,
            pos1=25,
            text="important passage",
            memo="This is a key insight",
            important=True,
            owner="researcher1"
        )
        assert segment.segment_id == "seg-1"
        assert segment.code_id == 101
        assert segment.code_name == "Learning"
        assert segment.code_color == "#FFC107"
        assert segment.pos0 == 10
        assert segment.pos1 == 25
        assert segment.important is True


class TestTextHighlighter:
    """Tests for TextHighlighter component"""

    def test_creation(self, qtbot):
        """TextHighlighter should be created"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)
        assert highlighter is not None

    def test_set_text(self, qtbot):
        """TextHighlighter should display text"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello, this is a test document.")
        assert highlighter.get_text() == "Hello, this is a test document."

    def test_with_header(self, qtbot):
        """TextHighlighter should show header when enabled"""
        highlighter = TextHighlighter(
            title="Test Document",
            show_header=True
        )
        qtbot.addWidget(highlighter)
        assert hasattr(highlighter, '_header')
        assert hasattr(highlighter, '_title_label')

    def test_add_segment(self, qtbot):
        """TextHighlighter should store segments"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        segment = CodeSegment(
            segment_id="1",
            code_color="#FFC107",
            pos0=0,
            pos1=5
        )
        highlighter.add_segment(segment)

        assert highlighter.get_segment_count() == 1

    def test_add_multiple_segments(self, qtbot):
        """TextHighlighter should handle multiple segments"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        segments = [
            CodeSegment(segment_id="1", pos0=0, pos1=5),
            CodeSegment(segment_id="2", pos0=10, pos1=15),
            CodeSegment(segment_id="3", pos0=20, pos1=25),
        ]
        highlighter.add_segments(segments)

        assert highlighter.get_segment_count() == 3

    def test_clear_segments(self, qtbot):
        """TextHighlighter should clear segments"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.add_segment(CodeSegment(segment_id="1", pos0=0, pos1=5))
        highlighter.add_segment(CodeSegment(segment_id="2", pos0=10, pos1=15))
        assert highlighter.get_segment_count() == 2

        highlighter.clear_segments()
        assert highlighter.get_segment_count() == 0

    def test_remove_segment(self, qtbot):
        """TextHighlighter should remove specific segment"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.add_segment(CodeSegment(segment_id="keep", pos0=0, pos1=5))
        highlighter.add_segment(CodeSegment(segment_id="remove", pos0=10, pos1=15))
        highlighter.remove_segment("remove")

        segments = highlighter.get_segments()
        assert len(segments) == 1
        assert segments[0].segment_id == "keep"

    def test_highlight_applies_formatting(self, qtbot):
        """TextHighlighter.highlight() should apply formatting"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello World Test Document")
        highlighter.add_segment(CodeSegment(
            segment_id="1",
            code_color="#FFC107",
            pos0=0,
            pos1=5
        ))

        # Should not raise
        highlighter.highlight()

    def test_unlight_removes_formatting(self, qtbot):
        """TextHighlighter.unlight() should remove formatting"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello World")
        highlighter.add_segment(CodeSegment(pos0=0, pos1=5, code_color="#FFC107"))
        highlighter.highlight()

        # Should not raise
        highlighter.unlight()

    def test_overlap_detection(self, qtbot):
        """TextHighlighter should detect overlapping segments"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("This is overlapping text here")
        # Overlapping segments: 0-15 and 10-20
        highlighter.add_segment(CodeSegment(segment_id="1", pos0=0, pos1=15))
        highlighter.add_segment(CodeSegment(segment_id="2", pos0=10, pos1=20))

        assert highlighter.get_overlap_count() == 1

    def test_no_overlaps(self, qtbot):
        """TextHighlighter should report 0 overlaps for non-overlapping segments"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("This is a test document with segments")
        highlighter.add_segment(CodeSegment(segment_id="1", pos0=0, pos1=5))
        highlighter.add_segment(CodeSegment(segment_id="2", pos0=10, pos1=15))

        assert highlighter.get_overlap_count() == 0

    def test_get_codes_at_position(self, qtbot):
        """TextHighlighter should return codes at position"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello World Test")
        highlighter.add_segment(CodeSegment(segment_id="1", pos0=0, pos1=5))
        highlighter.add_segment(CodeSegment(segment_id="2", pos0=0, pos1=11))

        # Position 3 is in both segments
        codes = highlighter.get_codes_at_position(3)
        assert len(codes) == 2

        # Position 8 is only in segment 2
        codes = highlighter.get_codes_at_position(8)
        assert len(codes) == 1
        assert codes[0].segment_id == "2"

    def test_scroll_to_position(self, qtbot):
        """TextHighlighter should scroll to position"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        long_text = "Line\n" * 100
        highlighter.set_text(long_text)

        # Should not raise
        highlighter.scroll_to_position(200)

    def test_selection_signal(self, qtbot):
        """TextHighlighter should emit text_selected signal"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello World")

        # Signal should exist
        assert hasattr(highlighter, 'text_selected')

    def test_segment_clicked_signal(self, qtbot):
        """TextHighlighter should have segment_clicked signal"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        assert hasattr(highlighter, 'segment_clicked')

    def test_file_offset(self, qtbot):
        """TextHighlighter should handle file offset"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        # Text is a portion of a larger file starting at position 100
        highlighter.set_text("This is partial text", file_start=100)

        # Segment positions are in absolute file coordinates
        highlighter.add_segment(CodeSegment(
            segment_id="1",
            pos0=100,  # Absolute position
            pos1=104   # Absolute position
        ))

        # Should apply correctly (positions 0-4 in the displayed text)
        highlighter.highlight()

    def test_annotations(self, qtbot):
        """TextHighlighter should handle annotations"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        highlighter.set_text("Hello World with annotations")
        highlighter.add_annotation(Annotation(
            annotation_id="ann-1",
            pos0=6,
            pos1=11,
            text="A note about World"
        ))

        # Should highlight as bold without error
        highlighter.highlight()

    def test_popup_disabled(self, qtbot):
        """TextHighlighter should work without popup"""
        highlighter = TextHighlighter(show_selection_popup=False)
        qtbot.addWidget(highlighter)

        assert highlighter._popup is None

    def test_set_popup_actions(self, qtbot):
        """TextHighlighter should allow custom popup actions"""
        highlighter = TextHighlighter()
        qtbot.addWidget(highlighter)

        custom_actions = [
            ("mdi6.tag", "Custom Action", "custom", True),
        ]
        highlighter.set_popup_actions(custom_actions)

        assert highlighter._popup is not None


class TestCodedTextHighlight:
    """Tests for CodedTextHighlight component"""

    def test_creation(self, qtbot):
        """CodedTextHighlight should be created"""
        highlight = CodedTextHighlight(
            text="Test text",
            code_name="Test Code",
            code_color="#FFC107"
        )
        qtbot.addWidget(highlight)
        assert highlight is not None

    def test_inline_mode(self, qtbot):
        """CodedTextHighlight should support inline mode"""
        highlight = CodedTextHighlight(
            text="Inline text",
            code_color="#FFC107",
            inline=True
        )
        qtbot.addWidget(highlight)
        assert highlight is not None

    def test_overlap_indicator(self, qtbot):
        """CodedTextHighlight should show overlap indicator"""
        highlight = CodedTextHighlight(
            text="Overlapping text",
            code_name="Test",
            code_color="#FFC107",
            overlap_count=3
        )
        qtbot.addWidget(highlight)
        assert highlight._overlap_count == 3


class TestOverlapIndicator:
    """Tests for OverlapIndicator component"""

    def test_creation(self, qtbot):
        """OverlapIndicator should be created"""
        indicator = OverlapIndicator(count=3)
        qtbot.addWidget(indicator)

        assert indicator is not None
        assert indicator._count == 3

    def test_size(self, qtbot):
        """OverlapIndicator should have fixed size"""
        indicator = OverlapIndicator()
        qtbot.addWidget(indicator)

        assert indicator.width() == 18
        assert indicator.height() == 18


class TestAnnotationIndicator:
    """Tests for AnnotationIndicator component"""

    def test_creation(self, qtbot):
        """AnnotationIndicator should be created"""
        indicator = AnnotationIndicator(annotation_type="memo")
        qtbot.addWidget(indicator)
        assert indicator is not None

    def test_different_types(self, qtbot):
        """AnnotationIndicator should support different types"""
        for ann_type in ["memo", "comment", "link"]:
            indicator = AnnotationIndicator(annotation_type=ann_type)
            qtbot.addWidget(indicator)
            assert indicator is not None

    def test_click_signal(self, qtbot):
        """AnnotationIndicator should have clicked signal"""
        indicator = AnnotationIndicator()
        qtbot.addWidget(indicator)
        assert hasattr(indicator, 'clicked')
