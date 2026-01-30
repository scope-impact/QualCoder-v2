"""
Forms component stories: search, select, toggle, pickers
"""

from PySide6.QtWidgets import QHBoxLayout, QWidget

from ...filters import FilterChip, SearchInput, ViewToggle
from ...forms import ColorPicker, RangeSlider, Select
from ...pickers import ChartTypeSelector, RadioCardGroup, TypeSelector
from ...toggle import LabeledToggle, Toggle
from ...tokens import SPACING, ColorPalette
from ..page import StoryPage


def create_search_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Search input
    search = SearchInput(placeholder="Search files...", colors=colors)
    examples.append(
        ("Search Input", search, 'SearchInput(placeholder="Search files...")')
    )

    # View toggle
    toggle = ViewToggle(["grid", "list", "table"], colors=colors)
    examples.append(("View Toggle", toggle, 'ViewToggle(["grid", "list", "table"])'))

    # Filter chips
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.sm)
    layout.addWidget(FilterChip("Status: Active", colors=colors))
    layout.addWidget(FilterChip("Type: Audio", colors=colors))
    layout.addStretch()
    examples.append(("Filter Chips", container, 'FilterChip("Status: Active")'))

    return StoryPage(
        "Search & Filters",
        "Search and filter components for finding and narrowing down content.",
        examples,
        colors=colors,
    )


def create_select_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Select
    select = Select(placeholder="Select an option...", colors=colors)
    select.add_items(["Option 1", "Option 2", "Option 3"])
    examples.append(
        (
            "Select",
            select,
            'select = Select(placeholder="Select...")\nselect.add_items(["Option 1", "Option 2"])',
        )
    )

    # Range slider
    slider = RangeSlider(min_val=0, max_val=100, value=50, colors=colors)
    examples.append(
        ("Range Slider", slider, "RangeSlider(min_val=0, max_val=100, value=50)")
    )

    # Color picker
    picker = ColorPicker(colors=colors)
    examples.append(("Color Picker", picker, "ColorPicker()"))

    return StoryPage(
        "Select & Pickers",
        "Selection components for choosing from predefined options.",
        examples,
        colors=colors,
    )


def create_toggle_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Basic toggle
    toggle = Toggle(colors=colors)
    examples.append(("Toggle", toggle, "Toggle()"))

    # Labeled toggle
    labeled = LabeledToggle("Enable notifications", colors=colors)
    examples.append(
        ("Labeled Toggle", labeled, 'LabeledToggle("Enable notifications")')
    )

    return StoryPage(
        "Toggle", "Toggle switches for binary on/off states.", examples, colors=colors
    )


def create_pickers_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Type selector
    selector = TypeSelector(columns=3, colors=colors)
    selector.add_option("text", "📄", "Text", "Plain text files")
    selector.add_option("audio", "🎵", "Audio", "MP3, WAV files")
    selector.add_option("video", "🎬", "Video", "MP4, MOV files")
    examples.append(
        (
            "Type Selector",
            selector,
            'selector = TypeSelector()\nselector.add_option("text", "📄", "Text")',
        )
    )

    # Chart type
    chart = ChartTypeSelector(colors=colors)
    examples.append(("Chart Type Selector", chart, "ChartTypeSelector()"))

    # Radio cards
    radio = RadioCardGroup(colors=colors)
    radio.add_card("opt1", "Standard Import", "Import files with default settings")
    radio.add_card("opt2", "Custom Import", "Configure import options manually")
    examples.append(
        (
            "Radio Card Group",
            radio,
            'group = RadioCardGroup()\ngroup.add_card("opt1", "Title", "Description")',
        )
    )

    return StoryPage(
        "Pickers",
        "Picker components for selecting types, colors, and configurations.",
        examples,
        colors=colors,
    )


def get_stories(colors: ColorPalette) -> list[tuple[str, str, StoryPage]]:
    """Return all forms stories"""
    return [
        ("search", "Search", create_search_story(colors)),
        ("select", "Select", create_select_story(colors)),
        ("toggle", "Toggle", create_toggle_story(colors)),
        ("pickers", "Pickers", create_pickers_story(colors)),
    ]
