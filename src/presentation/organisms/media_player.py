"""
Media Player Component

Implements QC-027.04 Import Audio/Video Files:
- AC #3: Media duration is displayed
- AC #4: Playback controls are available

Uses python-vlc for media playback (excellent codec support via libVLC).
"""

from __future__ import annotations

import sys
from pathlib import Path

import vlc
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)


class MediaPlayer(QWidget):
    """
    Widget for playing audio and video files using VLC.

    Features:
    - Play/pause toggle
    - Seek slider
    - Volume control
    - Duration display (AC #3)
    - Playback controls (AC #4)
    - Excellent codec support via libVLC

    Signals:
        media_loaded(str): Emitted when media is successfully loaded
        load_failed(str): Emitted when media loading fails
        playback_started(): Emitted when playback starts
        playback_stopped(): Emitted when playback stops
        position_changed(int): Emitted when playback position changes (ms)
    """

    media_loaded = Signal(str)
    load_failed = Signal(str)
    playback_started = Signal()
    playback_stopped = Signal()
    position_changed = Signal(int)

    def __init__(
        self,
        colors: ColorPalette | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_path: Path | None = None
        self._is_video = False
        self._duration_ms = 0

        self._setup_vlc()
        self._setup_ui()
        self._setup_timer()

    def _setup_vlc(self):
        """Initialize VLC player instance."""
        # Create VLC instance with minimal output
        self._vlc_instance = vlc.Instance("--no-xlib", "--quiet")
        self._player = self._vlc_instance.media_player_new()

    def _setup_ui(self):
        """Build the player UI."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video display area
        self._video_container = QFrame()
        self._video_container.setStyleSheet("""
            QFrame {
                background-color: #000000;
            }
        """)
        video_layout = QVBoxLayout(self._video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        # Video frame for VLC output
        self._video_frame = QFrame()
        self._video_frame.setStyleSheet("background-color: #000000;")
        video_layout.addWidget(self._video_frame)
        layout.addWidget(self._video_container, 1)

        # Audio placeholder (shown for audio files)
        self._audio_placeholder = QFrame()
        self._audio_placeholder.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
            }}
        """)
        audio_layout = QVBoxLayout(self._audio_placeholder)
        audio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        audio_icon = Icon("mdi6.music", size=64, color=self._colors.file_audio)
        audio_layout.addWidget(audio_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._audio_name_label = QLabel("No audio loaded")
        self._audio_name_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
        """)
        self._audio_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_layout.addWidget(self._audio_name_label)

        layout.addWidget(self._audio_placeholder, 1)
        self._audio_placeholder.hide()

        # Controls bar
        self._setup_controls(layout)

    def _setup_controls(self, parent_layout: QVBoxLayout):
        """Create the playback controls bar."""
        controls = QFrame()
        controls.setFixedHeight(80)
        controls.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(
            SPACING.md, SPACING.sm, SPACING.md, SPACING.sm
        )
        controls_layout.setSpacing(SPACING.sm)

        # Progress slider
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 1000)  # Use 1000 for smooth seeking
        self._progress_slider.setStyleSheet(self._slider_style())
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        self._progress_slider.sliderMoved.connect(self._on_seek)
        controls_layout.addWidget(self._progress_slider)

        self._slider_being_dragged = False

        # Bottom controls row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(SPACING.md)

        # Time display (AC #3)
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setStyleSheet(f"""
            QLabel {{
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-family: monospace;
            }}
        """)
        bottom_row.addWidget(self._time_label)

        bottom_row.addStretch()

        # Playback controls (AC #4)
        # Previous
        prev_btn = self._create_control_button("mdi6.skip-previous", "Previous")
        prev_btn.clicked.connect(self._on_previous)
        bottom_row.addWidget(prev_btn)

        # Play/Pause
        self._play_btn = self._create_control_button("mdi6.play", "Play", primary=True)
        self._play_btn.clicked.connect(self._on_play_pause)
        bottom_row.addWidget(self._play_btn)

        # Next
        next_btn = self._create_control_button("mdi6.skip-next", "Next")
        next_btn.clicked.connect(self._on_next)
        bottom_row.addWidget(next_btn)

        bottom_row.addStretch()

        # Volume control
        volume_icon = Icon(
            "mdi6.volume-high", size=18, color=self._colors.text_secondary
        )
        volume_label = QLabel()
        volume_label.setPixmap(volume_icon.pixmap(18, 18))
        bottom_row.addWidget(volume_label)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(70)
        self._volume_slider.setFixedWidth(80)
        self._volume_slider.setStyleSheet(self._slider_style())
        self._volume_slider.valueChanged.connect(self._on_volume_change)
        bottom_row.addWidget(self._volume_slider)

        # Apply initial volume
        self._player.audio_set_volume(70)

        controls_layout.addLayout(bottom_row)
        parent_layout.addWidget(controls)

    def _create_control_button(
        self, icon_name: str, tooltip: str, primary: bool = False
    ) -> QPushButton:
        """Create a playback control button."""
        btn = QPushButton()
        size = 40 if primary else 32
        btn.setFixedSize(size, size)
        btn.setToolTip(tooltip)

        icon_size = 24 if primary else 18
        color = self._colors.primary if primary else self._colors.text_secondary
        btn.setIcon(Icon(icon_name, size=icon_size, color=color))

        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    border: none;
                    border-radius: {size // 2}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.primary_hover};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {RADIUS.sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface};
                }}
            """)

        return btn

    def _slider_style(self) -> str:
        """Return stylesheet for sliders."""
        return f"""
            QSlider::groove:horizontal {{
                background-color: {self._colors.border};
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
            QSlider::sub-page:horizontal {{
                background-color: {self._colors.primary};
                border-radius: 2px;
            }}
        """

    def _setup_timer(self):
        """Set up timer for updating UI during playback."""
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)  # Update every 100ms
        self._update_timer.timeout.connect(self._on_timer_tick)

    def _attach_vlc_to_widget(self):
        """Attach VLC video output to the video frame widget."""
        # Get the window handle for VLC
        if sys.platform.startswith("linux"):
            self._player.set_xwindow(int(self._video_frame.winId()))
        elif sys.platform == "win32":
            self._player.set_hwnd(int(self._video_frame.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self._video_frame.winId()))

    # Public API

    def load_media(self, path: str | Path):
        """
        Load and prepare a media file for playback.

        Args:
            path: Path to the audio or video file
        """
        path = Path(path)
        if not path.exists():
            self.load_failed.emit(f"File not found: {path}")
            return

        self._current_path = path
        self._is_video = path.suffix.lower() in {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".wmv",
            ".flv",
            ".m4v",
        }

        # Show appropriate view
        if self._is_video:
            self._video_container.show()
            self._audio_placeholder.hide()
        else:
            self._video_container.hide()
            self._audio_placeholder.show()
            self._audio_name_label.setText(path.name)

        # Create VLC media and load
        try:
            media = self._vlc_instance.media_new(str(path))
            self._player.set_media(media)

            # Attach to video widget if video
            if self._is_video:
                self._attach_vlc_to_widget()

            # Parse media to get duration
            media.parse_with_options(vlc.MediaParseFlag.local, 0)

            # Reset UI
            self._progress_slider.setValue(0)
            self._update_time_display()

            self.media_loaded.emit(str(path))

        except Exception as e:
            self.load_failed.emit(f"Failed to load media: {e}")

    def play(self):
        """Start or resume playback."""
        self._player.play()
        self._update_timer.start()
        self._play_btn.setIcon(Icon("mdi6.pause", size=24, color="#ffffff"))
        self.playback_started.emit()

    def pause(self):
        """Pause playback."""
        self._player.pause()
        self._play_btn.setIcon(Icon("mdi6.play", size=24, color="#ffffff"))

    def stop(self):
        """Stop playback and reset to beginning."""
        self._player.stop()
        self._update_timer.stop()
        self._progress_slider.setValue(0)
        self._play_btn.setIcon(Icon("mdi6.play", size=24, color="#ffffff"))
        self._update_time_display()
        self.playback_stopped.emit()

    def seek(self, position_ms: int):
        """
        Seek to a specific position.

        Args:
            position_ms: Position in milliseconds
        """
        self._player.set_time(position_ms)

    def get_position(self) -> int:
        """Get current playback position in milliseconds."""
        pos = self._player.get_time()
        return pos if pos >= 0 else 0

    def get_duration(self) -> int:
        """Get total duration in milliseconds."""
        duration = self._player.get_length()
        return duration if duration >= 0 else 0

    def is_playing(self) -> bool:
        """Check if media is currently playing."""
        return self._player.is_playing() == 1

    def clear(self):
        """Clear the current media."""
        self.stop()
        self._player.set_media(None)
        self._current_path = None
        self._time_label.setText("0:00 / 0:00")
        self._progress_slider.setValue(0)

    # Internal methods

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as M:SS or H:MM:SS."""
        if ms < 0:
            ms = 0
        seconds = ms // 1000
        minutes = seconds // 60
        hours = minutes // 60

        if hours > 0:
            return f"{hours}:{minutes % 60:02d}:{seconds % 60:02d}"
        return f"{minutes}:{seconds % 60:02d}"

    def _update_time_display(self):
        """Update the time display label."""
        current = self._format_time(self.get_position())
        total = self._format_time(self.get_duration())
        self._time_label.setText(f"{current} / {total}")

    # Event handlers

    def _on_timer_tick(self):
        """Handle periodic UI update during playback."""
        # Check if still playing
        if not self.is_playing():
            state = self._player.get_state()
            if state == vlc.State.Ended:
                self.stop()
            return

        # Update position slider (if not being dragged)
        if not self._slider_being_dragged:
            duration = self.get_duration()
            if duration > 0:
                position = self.get_position()
                slider_pos = int(position * 1000 / duration)
                self._progress_slider.blockSignals(True)
                self._progress_slider.setValue(slider_pos)
                self._progress_slider.blockSignals(False)

        self._update_time_display()
        self.position_changed.emit(self.get_position())

    def _on_play_pause(self):
        """Handle play/pause button click."""
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def _on_previous(self):
        """Handle previous button click - seek to start."""
        self.seek(0)

    def _on_next(self):
        """Handle next button click - seek to end."""
        duration = self.get_duration()
        if duration > 0:
            self.seek(duration - 1000)  # Seek near end

    def _on_slider_pressed(self):
        """Handle slider press - pause updates."""
        self._slider_being_dragged = True

    def _on_slider_released(self):
        """Handle slider release - apply seek."""
        self._slider_being_dragged = False
        self._on_seek(self._progress_slider.value())

    def _on_seek(self, position: int):
        """Handle seek slider movement."""
        duration = self.get_duration()
        if duration > 0:
            ms_position = int(position * duration / 1000)
            self._player.set_time(ms_position)
            self._update_time_display()

    def _on_volume_change(self, value: int):
        """Handle volume slider change."""
        self._player.audio_set_volume(value)

    def showEvent(self, event):
        """Handle show event to attach VLC to widget."""
        super().showEvent(event)
        if self._is_video:
            self._attach_vlc_to_widget()

    def closeEvent(self, event):
        """Clean up VLC resources on close."""
        self._update_timer.stop()
        self._player.stop()
        self._player.release()
        self._vlc_instance.release()
        super().closeEvent(event)
