"""
Tests for media components: VideoContainer, Timeline, PlayerControls, etc.
"""

import pytest
from PyQt6.QtCore import Qt

from design_system.media import (
    VideoContainer, WaveformVisualization, Timeline,
    PlayerControls, Thumbnail, ThumbnailStrip
)


class TestVideoContainer:
    """Tests for VideoContainer component"""

    def test_video_creation(self, qtbot):
        """VideoContainer should be created"""
        video = VideoContainer()
        qtbot.addWidget(video)

        assert video is not None

    def test_video_aspect_ratio(self, qtbot):
        """VideoContainer should respect aspect ratio"""
        video = VideoContainer(aspect_ratio=16/9)
        qtbot.addWidget(video)

        assert video._aspect_ratio == 16/9


class TestWaveformVisualization:
    """Tests for WaveformVisualization component"""

    def test_waveform_creation(self, qtbot):
        """WaveformVisualization should be created"""
        waveform = WaveformVisualization()
        qtbot.addWidget(waveform)

        assert waveform is not None

    def test_waveform_position(self, qtbot):
        """WaveformVisualization should set position"""
        waveform = WaveformVisualization()
        qtbot.addWidget(waveform)

        waveform.set_position(0.5)
        assert waveform._position == 0.5

    def test_waveform_bounds(self, qtbot):
        """WaveformVisualization should clamp position"""
        waveform = WaveformVisualization()
        qtbot.addWidget(waveform)

        waveform.set_position(1.5)  # Above 1
        assert waveform._position <= 1.0

        waveform.set_position(-0.5)  # Below 0
        assert waveform._position >= 0.0

    def test_waveform_signal(self, qtbot):
        """WaveformVisualization should emit position_changed signal"""
        waveform = WaveformVisualization()
        qtbot.addWidget(waveform)

        # Signal should exist
        assert hasattr(waveform, 'position_changed')


class TestTimeline:
    """Tests for Timeline component"""

    def test_timeline_creation(self, qtbot):
        """Timeline should be created"""
        timeline = Timeline(duration=120.0)
        qtbot.addWidget(timeline)

        assert timeline is not None
        assert timeline._duration == 120.0

    def test_timeline_position(self, qtbot):
        """Timeline should set position"""
        timeline = Timeline(duration=100.0)
        qtbot.addWidget(timeline)

        timeline.set_position(50.0)
        assert timeline._position == 50.0

    def test_timeline_duration(self, qtbot):
        """Timeline should update duration"""
        timeline = Timeline(duration=100.0)
        qtbot.addWidget(timeline)

        timeline.set_duration(200.0)
        assert timeline._duration == 200.0

    def test_timeline_segments(self, qtbot):
        """Timeline should add segments"""
        timeline = Timeline(duration=100.0)
        qtbot.addWidget(timeline)

        timeline.add_segment(10.0, 30.0, "#FFC107", "test")

        assert len(timeline._segments) == 1


class TestPlayerControls:
    """Tests for PlayerControls component"""

    def test_controls_creation(self, qtbot):
        """PlayerControls should be created"""
        controls = PlayerControls()
        qtbot.addWidget(controls)

        assert controls is not None

    def test_controls_play_signal(self, qtbot):
        """PlayerControls should emit play_clicked signal"""
        controls = PlayerControls()
        qtbot.addWidget(controls)

        with qtbot.waitSignal(controls.play_clicked, timeout=1000):
            qtbot.mouseClick(controls._play_btn, Qt.MouseButton.LeftButton)

    def test_controls_toggle_play(self, qtbot):
        """PlayerControls should toggle play state"""
        controls = PlayerControls()
        qtbot.addWidget(controls)

        assert controls._playing is False

        # Click play
        qtbot.mouseClick(controls._play_btn, Qt.MouseButton.LeftButton)
        assert controls._playing is True

        # Click again to pause
        qtbot.mouseClick(controls._play_btn, Qt.MouseButton.LeftButton)
        assert controls._playing is False

    def test_controls_set_playing(self, qtbot):
        """PlayerControls should set playing state"""
        controls = PlayerControls()
        qtbot.addWidget(controls)

        controls.set_playing(True)
        assert controls._playing is True

        controls.set_playing(False)
        assert controls._playing is False


class TestThumbnail:
    """Tests for Thumbnail component"""

    def test_thumbnail_creation(self, qtbot):
        """Thumbnail should be created"""
        thumb = Thumbnail(label="Page 1")
        qtbot.addWidget(thumb)

        assert thumb is not None

    def test_thumbnail_selection(self, qtbot):
        """Thumbnail should support selection"""
        thumb = Thumbnail(selected=False)
        qtbot.addWidget(thumb)

        thumb.setSelected(True)
        assert thumb._selected is True

    def test_thumbnail_click_signal(self, qtbot):
        """Thumbnail should emit clicked signal"""
        thumb = Thumbnail()
        qtbot.addWidget(thumb)

        with qtbot.waitSignal(thumb.clicked, timeout=1000):
            qtbot.mouseClick(thumb, Qt.MouseButton.LeftButton)


class TestThumbnailStrip:
    """Tests for ThumbnailStrip component"""

    def test_strip_creation(self, qtbot):
        """ThumbnailStrip should be created"""
        strip = ThumbnailStrip()
        qtbot.addWidget(strip)

        assert strip is not None

    def test_strip_add_thumbnails(self, qtbot):
        """ThumbnailStrip should add thumbnails"""
        strip = ThumbnailStrip()
        qtbot.addWidget(strip)

        strip.add_thumbnail("", "Page 1")
        strip.add_thumbnail("", "Page 2")
        strip.add_thumbnail("", "Page 3")

        assert len(strip._thumbnails) == 3

    def test_strip_selection_signal(self, qtbot):
        """ThumbnailStrip should emit thumbnail_selected signal"""
        strip = ThumbnailStrip()
        qtbot.addWidget(strip)

        strip.add_thumbnail("", "Page 1")
        strip.add_thumbnail("", "Page 2")

        with qtbot.waitSignal(strip.thumbnail_selected, timeout=1000):
            thumb = strip._thumbnails[1]
            qtbot.mouseClick(thumb, Qt.MouseButton.LeftButton)
