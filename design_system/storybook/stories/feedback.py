"""
Feedback component stories: alerts, progress, spinners
"""

from typing import List, Tuple
from PyQt6.QtWidgets import QWidget

from ...tokens import ColorPalette
from ...components import Alert
from ...progress_bar import ProgressBar
from ...spinner import Spinner, LoadingIndicator, SkeletonLoader
from ...chat import TypingIndicator, ConfidenceScore
from ..page import StoryPage


def create_alerts_story(colors: ColorPalette) -> StoryPage:
    examples = []

    variant_map = {
        "default": "default",
        "success": "success",
        "warning": "warning",
        "destructive": "destructive",
    }

    for label, variant in variant_map.items():
        alert = Alert(
            title=label.capitalize(),
            description=f"This is a {label} alert message.",
            variant=variant,
            colors=colors
        )
        examples.append((
            f"{label.capitalize()} Alert",
            alert,
            f'Alert(title="{label.capitalize()}", description="...", variant="{variant}")'
        ))

    return StoryPage(
        "Alerts",
        "Alerts communicate important information to users. Use appropriate variants for context.",
        examples,
        colors=colors
    )


def create_progress_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Basic progress
    progress = ProgressBar(value=65, colors=colors)
    examples.append((
        "Basic Progress",
        progress,
        'ProgressBar(value=65)'
    ))

    # With label
    progress2 = ProgressBar(value=40, label="Uploading...", show_percentage=True, colors=colors)
    examples.append((
        "Progress with Label",
        progress2,
        'ProgressBar(value=40, label="Uploading...", show_percentage=True)'
    ))

    # Confidence score
    conf = ConfidenceScore(0.85, label="Match confidence", colors=colors)
    examples.append((
        "Confidence Score",
        conf,
        'ConfidenceScore(0.85, label="Match confidence")'
    ))

    return StoryPage(
        "Progress",
        "Progress indicators show completion status of operations.",
        examples,
        colors=colors
    )


def create_spinners_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Spinner
    spinner = Spinner(size=32, colors=colors)
    examples.append((
        "Spinner",
        spinner,
        'Spinner(size=32)'
    ))

    # Loading indicator
    loading = LoadingIndicator(text="Loading data...", colors=colors)
    examples.append((
        "Loading Indicator",
        loading,
        'LoadingIndicator(text="Loading data...")'
    ))

    # Typing indicator
    typing = TypingIndicator(colors=colors)
    typing.start()
    examples.append((
        "Typing Indicator",
        typing,
        'indicator = TypingIndicator()\nindicator.start()'
    ))

    # Skeleton
    skeleton = SkeletonLoader(width=200, height=20, colors=colors)
    examples.append((
        "Skeleton Loader",
        skeleton,
        'SkeletonLoader(width=200, height=20)'
    ))

    return StoryPage(
        "Spinners & Loaders",
        "Loading indicators show that content is being fetched or processed.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all feedback stories"""
    return [
        ("alerts", "Alerts", create_alerts_story(colors)),
        ("progress", "Progress", create_progress_story(colors)),
        ("spinners", "Spinners", create_spinners_story(colors)),
    ]
