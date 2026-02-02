"""
Application layer for navigation operations.

Provides use cases for screen and segment navigation, plus a stateful
NavigationService for managing screen connections and UI integration.
"""

from src.application.navigation.service import NavigationService
from src.application.navigation.usecases import navigate_to_screen, navigate_to_segment

__all__ = [
    "NavigationService",
    "navigate_to_screen",
    "navigate_to_segment",
]
