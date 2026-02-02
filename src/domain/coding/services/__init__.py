"""
DEPRECATED: Use src.contexts.coding.core.services instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.core.services import (
    MatchScope,
    MatchType,
    TextMatch,
    TextMatcher,
)

__all__ = [
    "MatchScope",
    "MatchType",
    "TextMatch",
    "TextMatcher",
]
