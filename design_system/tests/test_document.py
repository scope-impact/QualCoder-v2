"""
Tests for document components: TextPanel, SelectionPopup, TranscriptPanel, etc.
"""

import pytest

from design_system.document import (
    TextColor,
    TextPanel,
    SelectionPopup,
    TranscriptPanel,
)


class TestTextColor:
    """Tests for TextColor contrast helper"""

    def test_light_background_gets_dark_text(self):
        """Light colors should get black text"""
        color = TextColor("#FFC107")  # Yellow
        assert color.recommendation == "#000000"

    def test_dark_background_gets_light_text(self):
        """Dark colors should get white text"""
        color = TextColor("#1B5E20")  # Dark green
        assert color.recommendation == "#EEEEEE"

    def test_known_dark_colors(self):
        """Known dark colors should return white text"""
        dark_colors = ["#B71C1C", "#0D47A1", "#4646D1", "#880E4F"]
        for hex_color in dark_colors:
            color = TextColor(hex_color)
            assert color.recommendation == "#EEEEEE", f"Failed for {hex_color}"

    def test_invalid_color_defaults_to_black(self):
        """Invalid colors should default to black text"""
        color = TextColor("invalid")
        assert color.recommendation == "#000000"

    def test_case_insensitive(self):
        """Color matching should be case insensitive"""
        color1 = TextColor("#ffc107")
        color2 = TextColor("#FFC107")
        assert color1.recommendation == color2.recommendation


class TestTextPanel:
    """Tests for TextPanel component"""

    def test_creation(self, qtbot):
        """TextPanel should be created"""
        panel = TextPanel()
        qtbot.addWidget(panel)
        assert panel is not None

    def test_set_text(self, qtbot):
        """TextPanel should display text"""
        panel = TextPanel()
        qtbot.addWidget(panel)

        panel.set_text("Hello, this is a test document.")
        assert panel.get_text() == "Hello, this is a test document."

    def test_with_header(self, qtbot):
        """TextPanel should show header when enabled"""
        panel = TextPanel(
            title="Test Document",
            show_header=True
        )
        qtbot.addWidget(panel)
        assert hasattr(panel, '_header')
        assert hasattr(panel, '_title_label')

    def test_text_selected_signal(self, qtbot):
        """TextPanel should have text_selected signal"""
        panel = TextPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'text_selected')


class TestSelectionPopup:
    """Tests for SelectionPopup component"""

    def test_creation(self, qtbot):
        """SelectionPopup should be created"""
        popup = SelectionPopup()
        qtbot.addWidget(popup)
        assert popup is not None

    def test_default_actions(self, qtbot):
        """SelectionPopup should have default actions"""
        popup = SelectionPopup()
        qtbot.addWidget(popup)

        # Should have layout with buttons
        assert popup.layout().count() == 4  # 4 default actions

    def test_custom_actions(self, qtbot):
        """SelectionPopup should accept custom actions"""
        actions = [
            ("mdi6.label", "Action 1", "act1"),
            ("mdi6.plus", "Action 2", "act2"),
        ]
        popup = SelectionPopup(actions=actions)
        qtbot.addWidget(popup)

        assert popup.layout().count() == 2

    def test_action_signal(self, qtbot):
        """SelectionPopup should emit action_clicked signal"""
        popup = SelectionPopup()
        qtbot.addWidget(popup)

        assert hasattr(popup, 'action_clicked')


class TestTranscriptPanel:
    """Tests for TranscriptPanel component"""

    def test_creation(self, qtbot):
        """TranscriptPanel should be created"""
        panel = TranscriptPanel()
        qtbot.addWidget(panel)
        assert panel is not None

    def test_add_segment(self, qtbot):
        """TranscriptPanel should add segments"""
        panel = TranscriptPanel()
        qtbot.addWidget(panel)

        panel.add_segment(0.0, 5.5, "Speaker 1", "Hello")
        panel.add_segment(5.5, 10.0, "Speaker 2", "Hi there")

        assert len(panel._segments) == 2

    def test_clear(self, qtbot):
        """TranscriptPanel should clear segments"""
        panel = TranscriptPanel()
        qtbot.addWidget(panel)

        panel.add_segment(0.0, 5.0, "Speaker", "Text")
        panel.clear()

        assert len(panel._segments) == 0

    def test_highlight_time(self, qtbot):
        """TranscriptPanel should highlight by time"""
        panel = TranscriptPanel()
        qtbot.addWidget(panel)

        panel.add_segment(0.0, 5.0, "Speaker 1", "First")
        panel.add_segment(5.0, 10.0, "Speaker 2", "Second")

        # Should not raise
        panel.highlight_time(3.0)

        # First segment should be highlighted
        assert panel._segments[0]._highlighted is True
        assert panel._segments[1]._highlighted is False

    def test_timestamp_signal(self, qtbot):
        """TranscriptPanel should have timestamp_clicked signal"""
        panel = TranscriptPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, 'timestamp_clicked')
