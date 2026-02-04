"""
Auto-coding controller stub.

This provides a NoOp implementation of the AutoCodingController interface
to allow the presentation layer to function while the broader refactoring
moves this functionality to proper command handlers.

TODO: Replace with proper fDDD command handler implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.contexts.coding.core.services.text_matcher import MatchScope, MatchType


@dataclass
class Speaker:
    """Speaker detected in document."""

    name: str
    count: int = 0


@dataclass
class TextMatch:
    """A text match result."""

    start: int
    end: int


@dataclass
class Batch:
    """An auto-coding batch for undo."""

    batch_id: str
    pattern: str
    segment_count: int = 0


class AutoCodingController:
    """
    NoOp stub for auto-coding controller.

    This is a temporary implementation that allows the presentation layer
    to function without errors while the broader refactoring is in progress.

    All methods return empty results or default values.
    """

    def __init__(self) -> None:
        self._undo_stack: list[Batch] = []

    def detect_speakers(self, _text: str) -> Result[list[Speaker], str]:
        """Detect speaker patterns in text. Returns empty list (stub)."""
        return Success([])

    def get_speaker_segments(
        self, _text: str, _speaker_name: str
    ) -> Result[list[TextMatch], str]:
        """Get segments for a speaker. Returns empty list (stub)."""
        return Success([])

    def can_undo(self) -> bool:
        """Check if undo is available. Always False (stub)."""
        return False

    def undo_last_batch(self) -> Result[Batch, str]:
        """Undo last batch. Returns failure (stub)."""
        return Failure("Undo not available")

    def find_matches(
        self,
        text: str,
        pattern: str,
        _match_type: MatchType | None = None,
        _scope: MatchScope | None = None,
        case_sensitive: bool = True,
    ) -> Result[list[TextMatch], str]:
        """
        Find pattern matches in text.

        This is a minimal implementation that performs exact string matching.
        TODO: Implement full matching logic in proper command handler.
        """
        if not pattern:
            return Success([])

        matches = []
        search_text = text if case_sensitive else text.lower()
        search_pattern = pattern if case_sensitive else pattern.lower()

        start = 0
        while True:
            pos = search_text.find(search_pattern, start)
            if pos == -1:
                break
            matches.append(TextMatch(start=pos, end=pos + len(pattern)))
            start = pos + 1

        return Success(matches)


__all__ = [
    "AutoCodingController",
    "Batch",
    "Speaker",
    "TextMatch",
]
