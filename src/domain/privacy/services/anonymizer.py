"""
TextAnonymizer - Domain Service.

Pure functions for applying pseudonyms to text. No I/O, no side effects.

Usage:
    anonymizer = TextAnonymizer(text)
    result = anonymizer.apply_pseudonyms(pseudonyms)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.privacy.entities import Pseudonym, TextReplacement


@dataclass(frozen=True)
class ReplacementPreview:
    """Preview of a single replacement without applying it."""

    original_text: str
    replacement_text: str
    positions: tuple[tuple[int, int], ...]
    pseudonym_id: int


@dataclass(frozen=True)
class AnonymizationResult:
    """Result of applying pseudonyms to text."""

    anonymized_text: str
    replacements: tuple[TextReplacement, ...]


class TextAnonymizer:
    """
    Domain service for applying pseudonyms to text.

    Performs case-sensitive or case-insensitive matching.
    Tracks all replacements for reversibility.
    """

    def __init__(self, text: str) -> None:
        """
        Initialize anonymizer with text to process.

        Args:
            text: The text to anonymize
        """
        self._text = text

    def apply_pseudonyms(
        self,
        pseudonyms: list[Pseudonym],
        match_case: bool = False,
        whole_word: bool = True,
    ) -> AnonymizationResult:
        """
        Apply pseudonyms to text, returning result with all replacements.

        Args:
            pseudonyms: List of pseudonyms to apply
            match_case: If True, match case exactly. If False, case-insensitive.
            whole_word: If True, only match whole words.

        Returns:
            AnonymizationResult containing new text and all replacements made
        """
        if not pseudonyms:
            return AnonymizationResult(
                anonymized_text=self._text,
                replacements=(),
            )

        # Collect all replacements first
        all_replacements: list[TextReplacement] = []

        # Track positions that have been matched to avoid overlapping
        # We process longest matches first to handle overlapping names
        sorted_pseudonyms = sorted(
            pseudonyms, key=lambda p: len(p.real_name), reverse=True
        )

        # Find all matches for each pseudonym
        match_info: list[tuple[Pseudonym, list[tuple[int, int]]]] = []

        for pseudonym in sorted_pseudonyms:
            positions = self._find_positions(
                pseudonym.real_name, match_case, whole_word
            )
            if positions:
                match_info.append((pseudonym, positions))

        # Now apply replacements from end to start to preserve positions
        result_text = self._text

        # Collect all position/replacement pairs and sort by position (descending)
        all_positions: list[tuple[int, int, str, str, Pseudonym]] = []
        for pseudonym, positions in match_info:
            for start, end in positions:
                all_positions.append(
                    (start, end, self._text[start:end], pseudonym.alias, pseudonym)
                )

        # Sort by start position descending (process from end first)
        all_positions.sort(key=lambda x: x[0], reverse=True)

        # Filter out overlapping matches (keep longest/first found)
        used_ranges: list[tuple[int, int]] = []
        filtered_positions: list[tuple[int, int, str, str, Pseudonym]] = []

        for start, end, orig, alias, pseudonym in all_positions:
            overlaps = False
            for used_start, used_end in used_ranges:
                if not (end <= used_start or start >= used_end):
                    overlaps = True
                    break
            if not overlaps:
                used_ranges.append((start, end))
                filtered_positions.append((start, end, orig, alias, pseudonym))

        # Apply replacements
        for start, end, orig, alias, pseudonym in filtered_positions:
            result_text = result_text[:start] + alias + result_text[end:]

        # Build replacement records grouped by pseudonym
        replacement_map: dict[int, list[tuple[int, int]]] = {}
        pseudonym_map: dict[int, Pseudonym] = {}

        for start, end, orig, alias, pseudonym in filtered_positions:
            pid = pseudonym.id.value
            if pid not in replacement_map:
                replacement_map[pid] = []
                pseudonym_map[pid] = pseudonym
            replacement_map[pid].append((start, end))

        # Create TextReplacement objects
        for pid, positions in replacement_map.items():
            pseudonym = pseudonym_map[pid]
            all_replacements.append(
                TextReplacement(
                    original_text=pseudonym.real_name,
                    replacement_text=pseudonym.alias,
                    positions=tuple(sorted(positions)),
                )
            )

        return AnonymizationResult(
            anonymized_text=result_text,
            replacements=tuple(all_replacements),
        )

    def preview_replacements(
        self,
        pseudonyms: list[Pseudonym],
        match_case: bool = False,
        whole_word: bool = True,
    ) -> list[ReplacementPreview]:
        """
        Preview what would be replaced without modifying text.

        Args:
            pseudonyms: List of pseudonyms to preview
            match_case: If True, match case exactly
            whole_word: If True, only match whole words

        Returns:
            List of ReplacementPreview objects
        """
        previews: list[ReplacementPreview] = []

        for pseudonym in pseudonyms:
            positions = self._find_positions(
                pseudonym.real_name, match_case, whole_word
            )
            if positions:
                previews.append(
                    ReplacementPreview(
                        original_text=pseudonym.real_name,
                        replacement_text=pseudonym.alias,
                        positions=tuple(positions),
                        pseudonym_id=pseudonym.id.value,
                    )
                )

        return previews

    def _find_positions(
        self,
        search_text: str,
        match_case: bool,
        whole_word: bool,
    ) -> list[tuple[int, int]]:
        """
        Find all positions of search_text in the source text.

        Args:
            search_text: Text to search for
            match_case: If True, match case exactly
            whole_word: If True, only match whole words

        Returns:
            List of (start, end) position tuples
        """
        positions: list[tuple[int, int]] = []

        if not search_text:
            return positions

        # Build regex pattern
        pattern = re.escape(search_text)

        if whole_word:
            pattern = r"\b" + pattern + r"\b"

        flags = 0 if match_case else re.IGNORECASE

        for match in re.finditer(pattern, self._text, flags):
            positions.append((match.start(), match.end()))

        return positions
