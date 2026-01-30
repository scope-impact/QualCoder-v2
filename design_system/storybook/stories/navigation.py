"""
Navigation component stories: tabs, breadcrumbs, steps, pagination
"""

from typing import List, Tuple

from PySide6.QtWidgets import QWidget

from ...tokens import ColorPalette
from ...navigation import TabGroup, Breadcrumb, StepIndicator
from ...pagination import Pagination, SimplePagination
from ..page import StoryPage


def create_tabs_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Tab group
    tabs = TabGroup(colors=colors)
    tabs.add_tab("Coding", icon="🏷️", active=True)
    tabs.add_tab("Reports", icon="📊")
    tabs.add_tab("Settings", icon="⚙️")
    examples.append((
        "Tab Group",
        tabs,
        'tabs = TabGroup()\ntabs.add_tab("Coding", icon="🏷️", active=True)'
    ))

    return StoryPage(
        "Tabs",
        "Tabs organize content into separate views within the same context.",
        examples,
        colors=colors
    )


def create_breadcrumbs_story(colors: ColorPalette) -> StoryPage:
    examples = []

    breadcrumb = Breadcrumb(colors=colors)
    breadcrumb.set_path(["Home", "Projects", "QualCoder", "Settings"])
    examples.append((
        "Breadcrumb Navigation",
        breadcrumb,
        'breadcrumb = Breadcrumb()\nbreadcrumb.set_path(["Home", "Projects", "QualCoder"])'
    ))

    return StoryPage(
        "Breadcrumbs",
        "Breadcrumbs show the current location within a navigational hierarchy.",
        examples,
        colors=colors
    )


def create_steps_story(colors: ColorPalette) -> StoryPage:
    examples = []

    steps = StepIndicator(
        ["Select Files", "Configure", "Process", "Review"],
        current=2,
        colors=colors
    )
    examples.append((
        "Step Indicator",
        steps,
        'StepIndicator(["Step 1", "Step 2", "Step 3"], current=1)'
    ))

    return StoryPage(
        "Step Indicator",
        "Step indicators show progress through a multi-step process.",
        examples,
        colors=colors
    )


def create_pagination_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Full pagination
    pagination = Pagination(total_pages=10, current_page=3, colors=colors)
    examples.append((
        "Pagination",
        pagination,
        'Pagination(total_pages=10, current_page=3)'
    ))

    # Simple pagination
    simple = SimplePagination(current=5, total=20, colors=colors)
    examples.append((
        "Simple Pagination",
        simple,
        'SimplePagination(current=5, total=20)'
    ))

    return StoryPage(
        "Pagination",
        "Pagination controls for navigating through paged content.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all navigation stories"""
    return [
        ("tabs", "Tabs", create_tabs_story(colors)),
        ("breadcrumbs", "Breadcrumbs", create_breadcrumbs_story(colors)),
        ("steps", "Step Indicator", create_steps_story(colors)),
        ("pagination", "Pagination", create_pagination_story(colors)),
    ]
