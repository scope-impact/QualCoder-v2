"""
Media components
Video, audio, and timeline widgets
"""

from typing import List, Optional

from .qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QSizePolicy,
    Qt, Signal, QTimer,
)

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class VideoContainer(QFrame):
    """
    Video player container with placeholder.

    Usage:
        video = VideoContainer()
        video.set_source("path/to/video.mp4")
    """

    def __init__(
        self,
        aspect_ratio: float = 16/9,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._aspect_ratio = aspect_ratio

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #000000;
                border-radius: {RADIUS.md}px;
            }}
        """)

        self.setMinimumHeight(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Placeholder
        self._placeholder = QLabel("🎬")
        self._placeholder.setStyleSheet(f"font-size: 48px; color: {self._colors.text_secondary};")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._placeholder)

    def set_source(self, path: str):
        # In a real implementation, this would load the video
        self._placeholder.setText("▶")


class WaveformVisualization(QFrame):
    """
    Audio waveform display with playhead.

    Usage:
        waveform = WaveformVisualization()
        waveform.set_position(0.5)  # 50% through
        waveform.position_changed.connect(self.seek)
    """

    position_changed = Signal(float)  # 0.0 to 1.0

    def __init__(
        self,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._position = 0.0
        self._segments = []

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Waveform placeholder (would be replaced with actual waveform rendering)
        self._waveform = QLabel("〰️ 〰️ 〰️ 〰️ 〰️ 〰️")
        self._waveform.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._waveform.setStyleSheet(f"color: {self._colors.primary}; font-size: 20px;")
        layout.addWidget(self._waveform)

    def set_position(self, position: float):
        self._position = max(0.0, min(1.0, position))
        self.update()

    def add_segment(self, start: float, end: float, color: str):
        self._segments.append((start, end, color))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().x() / self.width()
            self.position_changed.emit(pos)


class Timeline(QFrame):
    """
    Media timeline with position indicator and segments.

    Usage:
        timeline = Timeline(duration=120.0)
        timeline.set_position(30.5)
        timeline.add_segment(10.0, 25.0, "#FFC107", "Learning")
    """

    position_changed = Signal(float)  # seconds
    segment_clicked = Signal(str)  # segment_id

    def __init__(
        self,
        duration: float = 100.0,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._duration = duration
        self._position = 0.0
        self._segments = []

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        self.setFixedHeight(40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Track
        self._track = QFrame()
        self._track.setFixedHeight(8)
        self._track.setStyleSheet(f"""
            background-color: {self._colors.surface_lighter};
            border-radius: 4px;
        """)
        self._track.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._track)

        # Time labels
        time_layout = QHBoxLayout()
        self._current_time = QLabel("0:00")
        self._current_time.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
        time_layout.addWidget(self._current_time)
        time_layout.addStretch()
        self._total_time = QLabel(self._format_time(duration))
        self._total_time.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
        time_layout.addWidget(self._total_time)
        layout.addLayout(time_layout)

    def set_position(self, seconds: float):
        self._position = max(0.0, min(seconds, self._duration))
        self._current_time.setText(self._format_time(self._position))
        self.update()

    def set_duration(self, seconds: float):
        self._duration = seconds
        self._total_time.setText(self._format_time(seconds))

    def add_segment(self, start: float, end: float, color: str, id: str = ""):
        self._segments.append({
            "start": start,
            "end": end,
            "color": color,
            "id": id
        })
        self.update()

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"


class PlayerControls(QFrame):
    """
    Media player controls (play, pause, volume, etc.).

    Usage:
        controls = PlayerControls()
        controls.play_clicked.connect(self.play)
        controls.volume_changed.connect(self.set_volume)
    """

    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    rewind_clicked = Signal()
    forward_clicked = Signal()
    volume_changed = Signal(int)
    rate_changed = Signal(float)

    def __init__(
        self,
        show_volume: bool = True,
        show_rate: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._playing = False

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Main controls
        controls = QHBoxLayout()
        controls.setSpacing(SPACING.sm)

        # Rewind
        rewind = self._create_btn("⏪")
        rewind.clicked.connect(self.rewind_clicked.emit)
        controls.addWidget(rewind)

        # Play/Pause
        self._play_btn = self._create_btn("▶", primary=True)
        self._play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self._play_btn)

        # Forward
        forward = self._create_btn("⏩")
        forward.clicked.connect(self.forward_clicked.emit)
        controls.addWidget(forward)

        # Stop
        stop = self._create_btn("⏹")
        stop.clicked.connect(self.stop_clicked.emit)
        controls.addWidget(stop)

        layout.addLayout(controls)
        layout.addStretch()

        # Volume
        if show_volume:
            volume_layout = QHBoxLayout()
            volume_layout.setSpacing(SPACING.sm)

            vol_icon = QLabel("🔊")
            vol_icon.setStyleSheet(f"font-size: 16px;")
            volume_layout.addWidget(vol_icon)

            vol_slider = QSlider(Qt.Orientation.Horizontal)
            vol_slider.setFixedWidth(80)
            vol_slider.setMinimum(0)
            vol_slider.setMaximum(100)
            vol_slider.setValue(100)
            vol_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    background-color: {self._colors.surface_lighter};
                    height: 4px;
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    background-color: {self._colors.primary};
                    width: 12px;
                    height: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }}
            """)
            vol_slider.valueChanged.connect(self.volume_changed.emit)
            volume_layout.addWidget(vol_slider)

            layout.addLayout(volume_layout)

        # Playback rate
        if show_rate:
            rate_btn = QPushButton("1.0x")
            rate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rate_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.sm}px;
                    padding: 4px 8px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)
            layout.addWidget(rate_btn)

    def _create_btn(self, icon: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: 18px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.primary_light};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: 18px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
            """)

        return btn

    def _toggle_play(self):
        self._playing = not self._playing
        self._play_btn.setText("⏸" if self._playing else "▶")
        if self._playing:
            self.play_clicked.emit()
        else:
            self.pause_clicked.emit()

    def set_playing(self, playing: bool):
        self._playing = playing
        self._play_btn.setText("⏸" if playing else "▶")


class Thumbnail(QFrame):
    """
    Image/page thumbnail with selection.

    Usage:
        thumb = Thumbnail("page_1.png", label="Page 1")
        thumb.clicked.connect(self.select_page)
    """

    clicked = Signal()

    def __init__(
        self,
        image_path: str = "",
        label: str = "",
        selected: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._selected = selected

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        # Image placeholder
        img = QFrame()
        img.setFixedSize(80, 100)
        img.setStyleSheet(f"""
            background-color: {self._colors.surface_light};
            border-radius: {RADIUS.sm}px;
        """)
        img_layout = QVBoxLayout(img)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_label = QLabel("🖼️")
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet(f"font-size: 24px; color: {self._colors.text_secondary};")
        img_layout.addWidget(img_label)
        layout.addWidget(img)

        # Label
        if label:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {self._colors.text_secondary}; font-size: {TYPOGRAPHY.text_xs}px;")
            layout.addWidget(lbl)

    def _update_style(self):
        border = f"2px solid {self._colors.primary}" if self._selected else "2px solid transparent"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: {border};
                border-radius: {RADIUS.md}px;
            }}
        """)

    def setSelected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ThumbnailStrip(QFrame):
    """
    Horizontal strip of thumbnails.

    Usage:
        strip = ThumbnailStrip()
        strip.add_thumbnail("page1.png", "Page 1")
        strip.add_thumbnail("page2.png", "Page 2")
        strip.thumbnail_selected.connect(self.on_select)
    """

    thumbnail_selected = Signal(int)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._thumbnails = []
        self._selected = 0

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(SPACING.sm)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def add_thumbnail(self, image_path: str = "", label: str = "") -> Thumbnail:
        idx = len(self._thumbnails)
        thumb = Thumbnail(image_path, label, selected=(idx == self._selected), colors=self._colors)
        thumb.clicked.connect(lambda i=idx: self._select(i))
        self._thumbnails.append(thumb)
        self._layout.addWidget(thumb)
        return thumb

    def _select(self, index: int):
        for i, thumb in enumerate(self._thumbnails):
            thumb.setSelected(i == index)
        self._selected = index
        self.thumbnail_selected.emit(index)
