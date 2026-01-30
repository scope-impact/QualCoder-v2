# Media Components

Media playback and visualization components.

## VideoContainer

Video player container.

```python
from design_system import VideoContainer

video = VideoContainer()
video.set_source("/path/to/video.mp4")
```

---

## WaveformVisualization

Audio waveform display.

```python
from design_system import WaveformVisualization

waveform = WaveformVisualization()
waveform.set_position(0.5)  # 50% through
waveform.add_segment(start=10.0, end=25.0, color="#009688")

waveform.position_changed.connect(lambda pos: print(f"Position: {pos}"))
```

### WaveformVisualization Methods

| Method | Description |
|--------|-------------|
| `set_position(pos)` | Set playback position (0-1) |
| `add_segment(start, end, color)` | Add highlighted segment |
| `clear_segments()` | Remove all segments |

### WaveformVisualization Signals

| Signal | Description |
|--------|-------------|
| `position_changed(pos)` | Position updated |

---

## Timeline

Playback timeline.

![Timeline](../../../design_system/assets/screenshots/timeline_with_segments.png)

```python
from design_system import Timeline

timeline = Timeline()
timeline.set_duration(300)  # 5 minutes in seconds
timeline.set_position(60)   # 1 minute in seconds
```

### Timeline Methods

| Method | Description |
|--------|-------------|
| `set_duration(seconds)` | Set total duration |
| `set_position(seconds)` | Set current position |
| `get_position()` | Get current position |

---

## PlayerControls

Media player controls.

![Player Controls](../../../design_system/assets/screenshots/player_controls.png)

```python
from design_system import PlayerControls

controls = PlayerControls()
controls.play_clicked.connect(play_handler)
controls.pause_clicked.connect(pause_handler)
```

### PlayerControls Signals

| Signal | Description |
|--------|-------------|
| `play_clicked` | Play button clicked |
| `pause_clicked` | Pause button clicked |
| `stop_clicked` | Stop button clicked |
| `seek_requested(position)` | Seek requested |

---

## Thumbnail / ThumbnailStrip

Image thumbnails.

```python
from design_system import Thumbnail, ThumbnailStrip

# Individual Thumbnail widget
thumb = Thumbnail(image_path="/path/to/image.jpg", size=100)
thumb.clicked.connect(lambda: open_image())

# ThumbnailStrip displays multiple thumbnails in a row
strip = ThumbnailStrip()
strip.add_thumbnail("/path/to/img1.jpg")
strip.add_thumbnail("/path/to/img2.jpg")
strip.thumbnail_clicked.connect(lambda index: select_image(index))
```

### Thumbnail Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `image_path` | str | required | Path to image |
| `size` | int | `80` | Thumbnail size |

### ThumbnailStrip Signals

| Signal | Description |
|--------|-------------|
| `thumbnail_clicked(index)` | Thumbnail clicked |

---

## Media Player Example

Complete audio/video player:

```python
from design_system import (
    Panel, PanelHeader, VideoContainer, Timeline,
    PlayerControls, WaveformVisualization
)

class MediaPlayer(Panel):
    def __init__(self):
        super().__init__()

        self.add_widget(PanelHeader(title="Media Player"))

        # Video display
        self.video = VideoContainer()
        self.add_widget(self.video)

        # Waveform (for audio)
        self.waveform = WaveformVisualization()
        self.waveform.position_changed.connect(self.seek_to)
        self.add_widget(self.waveform)

        # Timeline
        self.timeline = Timeline()
        self.add_widget(self.timeline)

        # Controls
        self.controls = PlayerControls()
        self.controls.play_clicked.connect(self.play)
        self.controls.pause_clicked.connect(self.pause)
        self.add_widget(self.controls)

        self.duration = 0
        self.position = 0

    def load_media(self, path):
        self.video.set_source(path)
        # Set duration after loading
        self.timeline.set_duration(self.duration)

    def play(self):
        # Start playback
        pass

    def pause(self):
        # Pause playback
        pass

    def seek_to(self, position):
        self.position = position * self.duration
        self.timeline.set_position(self.position)
```
