"""
Media component stories: player, upload, calendar
"""

from typing import List, Tuple

from ...qt_compat import QWidget

from ...tokens import ColorPalette
from ...media import VideoContainer, Timeline, PlayerControls, ThumbnailStrip
from ...upload import DropZone, UploadProgress
from ...calendar import CalendarMini, DateRangePicker, QuickDateSelect
from ..page import StoryPage


def create_player_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Video container
    video = VideoContainer(colors=colors)
    video.setFixedHeight(200)
    examples.append((
        "Video Container",
        video,
        'VideoContainer(aspect_ratio=16/9)'
    ))

    # Timeline
    timeline = Timeline(duration=180.0, colors=colors)
    timeline.set_position(45.0)
    timeline.add_segment(10.0, 30.0, "#FFC107", "Segment 1")
    timeline.add_segment(60.0, 90.0, "#4CAF50", "Segment 2")
    examples.append((
        "Timeline",
        timeline,
        'timeline = Timeline(duration=180.0)\ntimeline.add_segment(10, 30, "#FFC107")'
    ))

    # Player controls
    controls = PlayerControls(colors=colors)
    examples.append((
        "Player Controls",
        controls,
        'PlayerControls(show_volume=True, show_rate=True)'
    ))

    # Thumbnail strip
    strip = ThumbnailStrip(colors=colors)
    strip.add_thumbnail("", "Page 1")
    strip.add_thumbnail("", "Page 2")
    strip.add_thumbnail("", "Page 3")
    strip.add_thumbnail("", "Page 4")
    examples.append((
        "Thumbnail Strip",
        strip,
        'strip = ThumbnailStrip()\nstrip.add_thumbnail("path.png", "Page 1")'
    ))

    return StoryPage(
        "Media Player",
        "Components for audio/video playback and media navigation.",
        examples,
        colors=colors
    )


def create_upload_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Drop zone
    drop = DropZone(
        accepted_types=["text", "audio", "video"],
        max_files=10,
        max_size_mb=100,
        colors=colors
    )
    examples.append((
        "Drop Zone",
        drop,
        'DropZone(accepted_types=["text", "audio"], max_files=10)'
    ))

    # Upload progress
    progress = UploadProgress("document.txt", "12.4 KB", colors=colors)
    progress.set_progress(65)
    examples.append((
        "Upload Progress",
        progress,
        'progress = UploadProgress("file.txt", "12 KB")\nprogress.set_progress(65)'
    ))

    return StoryPage(
        "Upload",
        "File upload components with drag-and-drop support.",
        examples,
        colors=colors
    )


def create_calendar_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Mini calendar
    calendar = CalendarMini(colors=colors)
    examples.append((
        "Mini Calendar",
        calendar,
        'CalendarMini()'
    ))

    # Date range picker
    date_range = DateRangePicker(colors=colors)
    examples.append((
        "Date Range Picker",
        date_range,
        'DateRangePicker()'
    ))

    # Quick date select
    quick = QuickDateSelect(colors=colors)
    examples.append((
        "Quick Date Select",
        quick,
        'QuickDateSelect()'
    ))

    return StoryPage(
        "Calendar",
        "Date selection and calendar components.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all media stories"""
    return [
        ("player", "Media Player", create_player_story(colors)),
        ("upload", "Upload", create_upload_story(colors)),
        ("calendar", "Calendar", create_calendar_story(colors)),
    ]
