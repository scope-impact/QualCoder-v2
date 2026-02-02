"""
Settings Use Cases - Functional 5-Step Pattern

Each use case is a pure function that follows the pattern:
1. Load current state from repository
2. Derive event using domain deriver (pure)
3. Persist changes
4. Publish event
5. Return result

These are global use cases - they don't require an open project.
"""

from src.application.settings.usecases.change_font import change_font
from src.application.settings.usecases.change_language import change_language
from src.application.settings.usecases.change_theme import change_theme
from src.application.settings.usecases.configure_av_coding import configure_av_coding
from src.application.settings.usecases.configure_backup import configure_backup

__all__ = [
    "change_theme",
    "change_font",
    "change_language",
    "configure_backup",
    "configure_av_coding",
]
