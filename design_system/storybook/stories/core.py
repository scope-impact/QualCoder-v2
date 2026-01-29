"""
Core component stories: buttons, inputs, cards, badges
"""

from typing import List, Tuple, Callable
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ...tokens import SPACING, ColorPalette
from ...components import Button, Input, Card, Badge, Chip, FileIcon
from ...forms import SearchBox, Textarea, NumberInput
from ...data_display import InfoCard
from ..page import StoryPage


def create_buttons_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Primary buttons
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.md)
    for variant in ["primary", "secondary", "outline", "ghost", "danger"]:
        btn = Button(variant.capitalize(), variant=variant, colors=colors)
        layout.addWidget(btn)
    layout.addStretch()
    examples.append((
        "Button Variants",
        container,
        'Button("Primary", variant="primary")\nButton("Secondary", variant="secondary")'
    ))

    # Sizes
    container2 = QWidget()
    layout2 = QHBoxLayout(container2)
    layout2.setSpacing(SPACING.md)
    for size in ["sm", "md", "lg"]:
        btn = Button(f"Size {size}", size=size, colors=colors)
        layout2.addWidget(btn)
    layout2.addStretch()
    examples.append((
        "Button Sizes",
        container2,
        'Button("Small", size="sm")\nButton("Large", size="lg")'
    ))

    return StoryPage(
        "Buttons",
        "Buttons trigger actions or events. Use different variants to indicate importance and context.",
        examples,
        colors=colors
    )


def create_inputs_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Basic input
    inp = Input(placeholder="Enter text...", colors=colors)
    examples.append((
        "Basic Input",
        inp,
        'Input(placeholder="Enter text...")'
    ))

    # Search box
    search = SearchBox(placeholder="Search files...", colors=colors)
    examples.append((
        "Search Box",
        search,
        'SearchBox(placeholder="Search files...")'
    ))

    # Textarea
    textarea = Textarea(placeholder="Enter description...", min_height=100, colors=colors)
    examples.append((
        "Textarea",
        textarea,
        'Textarea(placeholder="Enter description...", min_height=100)'
    ))

    # Number input
    number = NumberInput(min_val=0, max_val=100, step=1, colors=colors)
    number.setValue(50)
    examples.append((
        "Number Input",
        number,
        'number = NumberInput(min_val=0, max_val=100)\nnumber.setValue(50)'
    ))

    return StoryPage(
        "Inputs",
        "Form inputs for collecting user data. Various types for different data formats.",
        examples,
        colors=colors
    )


def create_cards_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Basic card
    card = Card(colors=colors)
    card.setFixedSize(300, 150)
    content_label = QLabel("Card Content")
    content_label.setStyleSheet(f"color: {colors.text_primary}; padding: 20px;")
    card.layout().addWidget(content_label)
    examples.append((
        "Basic Card",
        card,
        'card = Card()\ncard.layout().addWidget(content)'
    ))

    # Info card
    info = InfoCard(
        title="Project Statistics",
        icon="mdi6.chart-bar",
        colors=colors
    )
    info.set_text("This project contains 24 files, 156 codes, and 42 memos.")
    examples.append((
        "Info Card",
        info,
        'InfoCard(title="Stats", icon="mdi6.chart-bar")\ninfo.set_text("...")'
    ))

    return StoryPage(
        "Cards",
        "Cards group related content and actions. Use them to create visual hierarchy.",
        examples,
        colors=colors
    )


def create_badges_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Badges
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(SPACING.md)
    for variant in ["default", "success", "warning", "error", "info"]:
        badge = Badge(variant.capitalize(), variant=variant, colors=colors)
        layout.addWidget(badge)
    layout.addStretch()
    examples.append((
        "Badge Variants",
        container,
        'Badge("Success", variant="success")'
    ))

    # Chips
    container2 = QWidget()
    layout2 = QHBoxLayout(container2)
    layout2.setSpacing(SPACING.md)
    chip1 = Chip("Learning", colors=colors)
    chip2 = Chip("Experience", closable=True, colors=colors)
    chip3 = Chip("Emotion", colors=colors)
    layout2.addWidget(chip1)
    layout2.addWidget(chip2)
    layout2.addWidget(chip3)
    layout2.addStretch()
    examples.append((
        "Chips",
        container2,
        'Chip("Learning")\nChip("Experience", closable=True)'
    ))

    # File icons
    container3 = QWidget()
    layout3 = QHBoxLayout(container3)
    layout3.setSpacing(SPACING.lg)
    for ftype in ["text", "audio", "video", "image", "pdf"]:
        icon = FileIcon(ftype, colors=colors)
        layout3.addWidget(icon)
    layout3.addStretch()
    examples.append((
        "File Icons",
        container3,
        'FileIcon("audio")'
    ))

    return StoryPage(
        "Badges & Chips",
        "Badges show status or counts. Chips represent tags, codes, or categories.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all core stories"""
    return [
        ("buttons", "Buttons", create_buttons_story(colors)),
        ("inputs", "Inputs", create_inputs_story(colors)),
        ("cards", "Cards", create_cards_story(colors)),
        ("badges", "Badges & Chips", create_badges_story(colors)),
    ]
