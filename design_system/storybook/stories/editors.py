"""
Editor component stories: codeeditor, richtext
"""

from ...editors import CodeEditor, MemoEditor, RichTextEditor
from ...tokens import ColorPalette
from ..page import StoryPage


def create_codeeditor_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Code editor
    editor = CodeEditor(language="python", colors=colors)
    editor.set_code(
        "def analyze_text(text):\n    codes = find_codes(text)\n    return codes"
    )
    editor.setFixedHeight(150)
    examples.append(
        (
            "Code Editor",
            editor,
            'editor = CodeEditor(language="python")\neditor.set_code("def hello():...")',
        )
    )

    # Memo editor
    memo = MemoEditor(title="Research Notes", colors=colors)
    memo.set_content("Important observation about participant responses...")
    memo.setFixedHeight(200)
    examples.append(("Memo Editor", memo, 'MemoEditor(title="Research Notes")'))

    return StoryPage(
        "Code Editor",
        "Code editors with syntax highlighting and line numbers.",
        examples,
        colors=colors,
    )


def create_richtext_story(colors: ColorPalette) -> StoryPage:
    examples = []

    # Rich text editor
    editor = RichTextEditor(colors=colors)
    editor.setFixedHeight(200)
    examples.append(("Rich Text Editor", editor, "RichTextEditor(show_toolbar=True)"))

    return StoryPage(
        "Rich Text", "Rich text editing components.", examples, colors=colors
    )


def get_stories(colors: ColorPalette) -> list[tuple[str, str, StoryPage]]:
    """Return all editor stories"""
    return [
        ("codeeditor", "Code Editor", create_codeeditor_story(colors)),
        ("richtext", "Rich Text", create_richtext_story(colors)),
    ]
