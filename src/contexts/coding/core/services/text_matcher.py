"""
Text Matcher Domain Service

Pure domain service for text pattern matching in qualitative coding.
Extracted from presentation layer to maintain proper DDD boundaries.

This service provides text matching functionality for:
- Auto-coding text matches (exact, contains, regex)
- Scope filtering (all, first, last)
- Case-sensitive/insensitive matching

Usage:
    matcher = TextMatcher(text)
    matches = matcher.find_matches("pattern", MatchType.EXACT, scope=MatchScope.ALL)
    for match in matches:
        print(f"Found at {match.start}-{match.end}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class MatchType(Enum):
    """Type of text matching to perform."""

    EXACT = auto()  # Word boundary matching
    CONTAINS = auto()  # Substring matching
    REGEX = auto()  # Regular expression matching


class MatchScope(Enum):
    """Scope of matches to return."""

    ALL = auto()  # Return all matches
    FIRST = auto()  # Return only the first match
    LAST = auto()  # Return only the last match


@dataclass(frozen=True)
class TextMatch:
    """
    Immutable value object representing a text match.

    Attributes:
        start: Start position in the text (0-indexed)
        end: End position in the text (exclusive)
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")

    @property
    def length(self) -> int:
        """Length of the matched text."""
        return self.end - self.start


class TextMatcher:
    """
    Pure domain service for text pattern matching.

    This is a stateless service that performs text matching operations.
    All methods are pure functions that don't modify any state.

    Example:
        matcher = TextMatcher("The cat sat on the mat")
        matches = matcher.find_matches("cat", MatchType.EXACT)
        # Returns [TextMatch(start=4, end=7)]
    """

    def __init__(self, text: str) -> None:
        """
        Initialize the matcher with text to search.

        Args:
            text: The text content to search within
        """
        self._text = text

    def find_matches(
        self,
        pattern: str,
        match_type: MatchType = MatchType.EXACT,
        scope: MatchScope = MatchScope.ALL,
        case_sensitive: bool = False,
    ) -> list[TextMatch]:
        """
        Find all matches of pattern in text.

        Args:
            pattern: The pattern to search for
            match_type: Type of matching (EXACT, CONTAINS, REGEX)
            scope: Scope of matches to return (ALL, FIRST, LAST)
            case_sensitive: Whether to match case exactly

        Returns:
            List of TextMatch objects for each match found.
            Empty list if no matches or invalid pattern.
        """
        if not pattern:
            return []

        if not self._text:
            return []

        matches = self._find_all_matches(pattern, match_type, case_sensitive)

        return self._apply_scope(matches, scope)

    def _find_all_matches(
        self,
        pattern: str,
        match_type: MatchType,
        case_sensitive: bool,
    ) -> list[TextMatch]:
        """Find all matches based on match type."""
        if match_type == MatchType.REGEX:
            return self._find_regex_matches(pattern, case_sensitive)
        if match_type == MatchType.EXACT:
            return self._find_exact_matches(pattern, case_sensitive)
        # CONTAINS
        return self._find_contains_matches(pattern, case_sensitive)

    def _find_regex_matches(
        self,
        pattern: str,
        case_sensitive: bool,
    ) -> list[TextMatch]:
        """Find matches using regex pattern."""
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled = re.compile(pattern, flags)
            return [
                TextMatch(start=m.start(), end=m.end())
                for m in compiled.finditer(self._text)
            ]
        except re.error:
            # Invalid regex - return empty list gracefully
            return []

    def _find_exact_matches(
        self,
        pattern: str,
        case_sensitive: bool,
    ) -> list[TextMatch]:
        """Find exact word boundary matches."""
        # Escape special regex characters in the pattern
        escaped_pattern = re.escape(pattern)
        # Use word boundaries for exact matching
        word_pattern = rf"\b{escaped_pattern}\b"

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            compiled = re.compile(word_pattern, flags)
            return [
                TextMatch(start=m.start(), end=m.end())
                for m in compiled.finditer(self._text)
            ]
        except re.error:
            return []

    def _find_contains_matches(
        self,
        pattern: str,
        case_sensitive: bool,
    ) -> list[TextMatch]:
        """Find substring matches."""
        matches: list[TextMatch] = []

        search_text = self._text if case_sensitive else self._text.lower()
        search_pattern = pattern if case_sensitive else pattern.lower()

        start = 0
        while True:
            pos = search_text.find(search_pattern, start)
            if pos == -1:
                break
            matches.append(TextMatch(start=pos, end=pos + len(pattern)))
            start = pos + 1

        return matches

    def _apply_scope(
        self,
        matches: list[TextMatch],
        scope: MatchScope,
    ) -> list[TextMatch]:
        """Apply scope filter to matches."""
        if not matches:
            return []

        if scope == MatchScope.FIRST:
            return [matches[0]]
        if scope == MatchScope.LAST:
            return [matches[-1]]
        # ALL
        return matches
