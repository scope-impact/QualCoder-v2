"""
References Context: Command DTOs

Command data transfer objects for reference operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AddReferenceCommand:
    """Command to add a new reference."""

    title: str
    authors: str
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    url: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class UpdateReferenceCommand:
    """Command to update an existing reference."""

    reference_id: int
    title: str
    authors: str
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    url: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class RemoveReferenceCommand:
    """Command to remove a reference."""

    reference_id: int


@dataclass(frozen=True)
class LinkReferenceToSegmentCommand:
    """Command to link a reference to a coded segment."""

    reference_id: int
    segment_id: int


@dataclass(frozen=True)
class UnlinkReferenceFromSegmentCommand:
    """Command to unlink a reference from a coded segment."""

    reference_id: int
    segment_id: int
