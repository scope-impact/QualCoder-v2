"""
Chat / AI component stories: messages, chatinput
"""

from typing import List, Tuple

from ...qt_compat import QWidget

from ...tokens import ColorPalette
from ...chat import MessageBubble, QuickPrompts, ChatInput
from ..page import StoryPage


def create_messages_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # User message
    user_msg = MessageBubble("How can I code this passage?", role="user", colors=colors)
    examples.append((
        "User Message",
        user_msg,
        'MessageBubble("Hello!", role="user")'
    ))

    # Assistant message
    ai_msg = MessageBubble(
        "Based on the content, I suggest the code 'Learning' with high confidence.",
        role="assistant",
        timestamp="2:34 PM",
        colors=colors
    )
    examples.append((
        "Assistant Message",
        ai_msg,
        'MessageBubble("Response...", role="assistant")'
    ))

    # Quick prompts
    prompts = QuickPrompts([
        "Suggest codes",
        "Summarize text",
        "Find similar"
    ], colors=colors)
    examples.append((
        "Quick Prompts",
        prompts,
        'QuickPrompts(["Suggest codes", "Summarize text"])'
    ))

    return StoryPage(
        "Messages",
        "Chat message bubbles and conversation components.",
        examples,
        colors=colors
    )


def create_chatinput_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Chat input
    chat = ChatInput(placeholder="Ask AI assistant...", colors=colors)
    examples.append((
        "Chat Input",
        chat,
        'ChatInput(placeholder="Ask AI assistant...")'
    ))

    return StoryPage(
        "Chat Input",
        "Input component for chat interfaces.",
        examples,
        colors=colors
    )


def get_stories(colors: ColorPalette) -> List[Tuple[str, str, StoryPage]]:
    """Return all chat stories"""
    return [
        ("messages", "Messages", create_messages_story(colors)),
        ("chatinput", "Chat Input", create_chatinput_story(colors)),
    ]
