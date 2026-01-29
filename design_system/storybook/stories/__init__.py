"""
Story registry - collects all stories from category modules
"""

from typing import List, Tuple, Callable
from PyQt6.QtWidgets import QWidget

from ...tokens import ColorPalette

from .core import get_stories as get_core_stories
from .feedback import get_stories as get_feedback_stories
from .navigation import get_stories as get_navigation_stories
from .forms import get_stories as get_forms_stories
from .data import get_stories as get_data_stories
from .media import get_stories as get_media_stories
from .chat import get_stories as get_chat_stories
from .editors import get_stories as get_editors_stories
from .overlays import get_stories as get_overlays_stories


# Story type: (key, label, page_creator)
StoryDef = Tuple[str, str, Callable]

# Section type: (section_name, stories_list)
SectionDef = Tuple[str, List[StoryDef]]


def get_all_sections(colors: ColorPalette) -> List[SectionDef]:
    """Get all story sections with their stories"""
    return [
        ("Core", get_core_stories(colors)),
        ("Feedback", get_feedback_stories(colors)),
        ("Navigation", get_navigation_stories(colors)),
        ("Forms", get_forms_stories(colors)),
        ("Data Display", get_data_stories(colors)),
        ("Media", get_media_stories(colors)),
        ("Chat / AI", get_chat_stories(colors)),
        ("Editors", get_editors_stories(colors)),
        ("Overlays", get_overlays_stories(colors)),
        ("Layout", get_overlays_stories(colors, layout_only=True)),
    ]


__all__ = ["get_all_sections", "StoryDef", "SectionDef"]
