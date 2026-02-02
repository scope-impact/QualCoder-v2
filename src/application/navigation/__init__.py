"""
Application layer for navigation operations.

Provides use cases for screen and segment navigation.
"""

from src.application.navigation.usecases import navigate_to_screen, navigate_to_segment

__all__ = [
    "navigate_to_screen",
    "navigate_to_segment",
]
