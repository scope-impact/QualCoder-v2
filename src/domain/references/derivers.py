"""
References Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - return Event or Failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from returns.result import Failure

from src.domain.references.entities import Reference
from src.domain.references.events import (
    ReferenceAdded,
    ReferenceLinkedToSegment,
    ReferenceRemoved,
    ReferenceUnlinkedFromSegment,
    ReferenceUpdated,
)
from src.domain.references.invariants import (
    is_valid_authors,
    is_valid_doi,
    is_valid_title,
    is_valid_year,
)
from src.domain.shared.types import ReferenceId, SegmentId


# =============================================================================
# Failure Reasons
# =============================================================================


@dataclass(frozen=True)
class EmptyTitle:
    """Reference title is empty or whitespace-only."""

    message: str = "Reference title cannot be empty"


@dataclass(frozen=True)
class EmptyAuthors:
    """Reference authors is empty or whitespace-only."""

    message: str = "Reference authors cannot be empty"


@dataclass(frozen=True)
class InvalidYear:
    """Year value is invalid."""

    year: int | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message and self.year is not None:
            object.__setattr__(self, "message", f"Year {self.year} is invalid")


@dataclass(frozen=True)
class InvalidDoi:
    """DOI format is invalid."""

    doi: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self, "message", f"DOI '{self.doi}' is not in valid format"
            )


@dataclass(frozen=True)
class ReferenceNotFound:
    """Reference with given ID does not exist."""

    reference_id: ReferenceId = field(default_factory=lambda: ReferenceId(value=0))
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Reference with id {self.reference_id.value} not found",
            )


@dataclass(frozen=True)
class ReferenceAlreadyLinked:
    """Reference is already linked to the segment."""

    reference_id: ReferenceId = field(default_factory=lambda: ReferenceId(value=0))
    segment_id: SegmentId = field(default_factory=lambda: SegmentId(value=0))
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Reference {self.reference_id.value} is already linked to segment {self.segment_id.value}",
            )


@dataclass(frozen=True)
class ReferenceNotLinked:
    """Reference is not linked to the segment."""

    reference_id: ReferenceId = field(default_factory=lambda: ReferenceId(value=0))
    segment_id: SegmentId = field(default_factory=lambda: SegmentId(value=0))
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Reference {self.reference_id.value} is not linked to segment {self.segment_id.value}",
            )


# =============================================================================
# State Container
# =============================================================================


@dataclass(frozen=True)
class ReferenceState:
    """Immutable state container for reference operations."""

    existing_references: tuple[Reference, ...] = ()


# =============================================================================
# Helper Functions
# =============================================================================


def _find_reference(
    reference_id: ReferenceId, state: ReferenceState
) -> Reference | None:
    """Find a reference by ID in the state."""
    for ref in state.existing_references:
        if ref.id == reference_id:
            return ref
    return None


# =============================================================================
# Derivers
# =============================================================================


def derive_add_reference(
    title: str,
    authors: str,
    year: int | None,
    doi: str | None,
    source: str | None,
    url: str | None,
    memo: str | None,
    state: ReferenceState,
) -> ReferenceAdded | Failure:
    """
    Derive a reference addition event.

    Pure function - no I/O, no side effects.

    Args:
        title: Reference title (required)
        authors: Reference authors (required)
        year: Publication year (optional)
        doi: Digital Object Identifier (optional)
        source: Journal/publisher (optional)
        url: URL (optional)
        memo: Notes (optional)
        state: Current reference state

    Returns:
        ReferenceAdded event on success, Failure with reason on error
    """
    # Validate title
    if not is_valid_title(title):
        return Failure(EmptyTitle())

    # Validate authors
    if not is_valid_authors(authors):
        return Failure(EmptyAuthors())

    # Validate year
    if not is_valid_year(year):
        return Failure(InvalidYear(year=year))

    # Validate DOI format
    if doi and not is_valid_doi(doi):
        return Failure(InvalidDoi(doi=doi))

    # All validations passed
    return ReferenceAdded(
        title=title.strip(),
        authors=authors.strip(),
        year=year,
        source=source,
        doi=doi,
        url=url,
        memo=memo,
    )


def derive_update_reference(
    reference_id: ReferenceId,
    title: str,
    authors: str,
    year: int | None,
    doi: str | None,
    source: str | None,
    url: str | None,
    memo: str | None,
    state: ReferenceState,
) -> ReferenceUpdated | Failure:
    """
    Derive a reference update event.

    Pure function - no I/O, no side effects.

    Args:
        reference_id: ID of reference to update
        title: New reference title
        authors: New reference authors
        year: New publication year
        doi: New DOI
        source: New source
        url: New URL
        memo: New memo
        state: Current reference state

    Returns:
        ReferenceUpdated event on success, Failure with reason on error
    """
    # Check reference exists
    existing = _find_reference(reference_id, state)
    if existing is None:
        return Failure(ReferenceNotFound(reference_id=reference_id))

    # Validate title
    if not is_valid_title(title):
        return Failure(EmptyTitle())

    # Validate authors
    if not is_valid_authors(authors):
        return Failure(EmptyAuthors())

    # Validate year
    if not is_valid_year(year):
        return Failure(InvalidYear(year=year))

    # Validate DOI format
    if doi and not is_valid_doi(doi):
        return Failure(InvalidDoi(doi=doi))

    return ReferenceUpdated(
        reference_id=reference_id,
        title=title.strip(),
        authors=authors.strip(),
        year=year,
        source=source,
        doi=doi,
        url=url,
        memo=memo,
    )


def derive_remove_reference(
    reference_id: ReferenceId,
    state: ReferenceState,
) -> ReferenceRemoved | Failure:
    """
    Derive a reference removal event.

    Pure function - no I/O, no side effects.

    Args:
        reference_id: ID of reference to remove
        state: Current reference state

    Returns:
        ReferenceRemoved event on success, Failure with reason on error
    """
    # Check reference exists
    existing = _find_reference(reference_id, state)
    if existing is None:
        return Failure(ReferenceNotFound(reference_id=reference_id))

    return ReferenceRemoved(reference_id=reference_id)


def derive_link_reference_to_segment(
    reference_id: ReferenceId,
    segment_id: SegmentId,
    state: ReferenceState,
) -> ReferenceLinkedToSegment | Failure:
    """
    Derive a reference-segment link event.

    Pure function - no I/O, no side effects.

    Args:
        reference_id: ID of reference to link
        segment_id: ID of segment to link to
        state: Current reference state

    Returns:
        ReferenceLinkedToSegment event on success, Failure with reason on error
    """
    # Check reference exists
    existing = _find_reference(reference_id, state)
    if existing is None:
        return Failure(ReferenceNotFound(reference_id=reference_id))

    # Check not already linked
    if segment_id.value in existing.segment_ids:
        return Failure(
            ReferenceAlreadyLinked(reference_id=reference_id, segment_id=segment_id)
        )

    return ReferenceLinkedToSegment(
        reference_id=reference_id,
        segment_id=segment_id,
    )


def derive_unlink_reference_from_segment(
    reference_id: ReferenceId,
    segment_id: SegmentId,
    state: ReferenceState,
) -> ReferenceUnlinkedFromSegment | Failure:
    """
    Derive a reference-segment unlink event.

    Pure function - no I/O, no side effects.

    Args:
        reference_id: ID of reference to unlink
        segment_id: ID of segment to unlink from
        state: Current reference state

    Returns:
        ReferenceUnlinkedFromSegment event on success, Failure with reason on error
    """
    # Check reference exists
    existing = _find_reference(reference_id, state)
    if existing is None:
        return Failure(ReferenceNotFound(reference_id=reference_id))

    # Check is linked
    if segment_id.value not in existing.segment_ids:
        return Failure(
            ReferenceNotLinked(reference_id=reference_id, segment_id=segment_id)
        )

    return ReferenceUnlinkedFromSegment(
        reference_id=reference_id,
        segment_id=segment_id,
    )
