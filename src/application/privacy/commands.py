"""
Privacy application commands.

Command DTOs for privacy operations following CQRS pattern.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreatePseudonymCommand:
    """Command to create a new pseudonym mapping."""

    real_name: str
    alias: str
    category: str = "person"
    notes: str | None = None


@dataclass(frozen=True)
class UpdatePseudonymCommand:
    """Command to update an existing pseudonym."""

    pseudonym_id: int
    new_alias: str | None = None
    new_notes: str | None = None


@dataclass(frozen=True)
class DeletePseudonymCommand:
    """Command to delete a pseudonym."""

    pseudonym_id: int


@dataclass(frozen=True)
class ApplyPseudonymsCommand:
    """Command to apply pseudonyms to a source text."""

    source_id: int
    source_text: str
    pseudonym_ids: tuple[int, ...] | None = None  # None = apply all
    match_case: bool = False
    whole_word: bool = True


@dataclass(frozen=True)
class RevertAnonymizationCommand:
    """Command to revert anonymization to original text."""

    source_id: int
    session_id: str | None = None  # None = revert latest


@dataclass(frozen=True)
class DetectSpeakersCommand:
    """Command to detect speakers in source text."""

    source_id: int
    source_text: str
    custom_patterns: tuple[str, ...] | None = None
    include_defaults: bool = True


@dataclass(frozen=True)
class ConvertSpeakersToCodesCommand:
    """Command to convert speakers to codes and auto-code segments."""

    source_id: int
    source_text: str
    speakers: tuple[str, ...] | list[str]
    category_id: int | None = None
    custom_patterns: tuple[str, ...] | None = None


@dataclass(frozen=True)
class PreviewSpeakerConversionCommand:
    """Command to preview speaker-to-code conversion without persisting."""

    source_id: int
    source_text: str
    speakers: tuple[str, ...] | list[str]
