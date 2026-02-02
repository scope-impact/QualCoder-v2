"""
Navigation Use Cases - Functional 5-Step Pattern

Use cases for navigation operations:
- navigate_to_screen: Navigate to a different screen
- navigate_to_segment: Navigate to a specific segment in a source
"""

from src.application.navigation.usecases.navigate_to_screen import navigate_to_screen
from src.application.navigation.usecases.navigate_to_segment import navigate_to_segment

__all__ = [
    "navigate_to_screen",
    "navigate_to_segment",
]
