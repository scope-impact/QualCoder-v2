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
