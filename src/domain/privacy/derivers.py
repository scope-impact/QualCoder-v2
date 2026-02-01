"""
Privacy domain derivers.

Pure functions that validate inputs and produce domain events.
No I/O, no side effects - only business logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from returns.result import Failure, Result, Success

from src.domain.privacy.entities import (
    AnonymizationSession,
    Pseudonym,
    PseudonymId,
)
from src.domain.privacy.events import (
    PseudonymCreated,
    PseudonymDeleted,
    PseudonymUpdated,
)
from src.domain.privacy.types import (
    DuplicateAlias,
    DuplicateRealName,
    EmptyAlias,
    EmptyRealName,
    PseudonymNotFound,
)


# =============================================================================
# State Container
# =============================================================================


@dataclass(frozen=True)
class PrivacyState:
    """
    Immutable state container for privacy operations.

    Holds the current state needed for deriving events.
    """

    existing_pseudonyms: tuple[Pseudonym, ...]
    existing_sessions: tuple[AnonymizationSession, ...]


# =============================================================================
# Pseudonym Derivers
# =============================================================================


def derive_create_pseudonym(
    real_name: str,
    alias: str,
    category: str,
    notes: str | None,
    state: PrivacyState,
) -> PseudonymCreated | Failure:
    """
    Derive a pseudonym creation event from inputs and state.

    Pure function following fDDD pattern - no I/O, no side effects.

    Args:
        real_name: The real identifier to map (1+ characters)
        alias: The pseudonym to use (1+ characters)
        category: Category type (person, organization, etc.)
        notes: Optional notes about this pseudonym
        state: Current privacy state for invariant checking

    Returns:
        PseudonymCreated event on success, Failure with reason on error
    """
    # Validate real_name is not empty
    if not real_name or not real_name.strip():
        return Failure(EmptyRealName())

    # Validate alias is not empty
    if not alias or not alias.strip():
        return Failure(EmptyAlias())

    # Check for duplicate real_name (case-insensitive)
    real_name_lower = real_name.lower()
    for existing in state.existing_pseudonyms:
        if existing.real_name.lower() == real_name_lower:
            return Failure(DuplicateRealName(real_name=real_name))

    # Check for duplicate alias (case-insensitive)
    alias_lower = alias.lower()
    for existing in state.existing_pseudonyms:
        if existing.alias.lower() == alias_lower:
            return Failure(DuplicateAlias(alias=alias))

    # All validations passed - create event
    return PseudonymCreated.create(
        pseudonym_id=PseudonymId.new(),
        real_name=real_name.strip(),
        alias=alias.strip(),
        category=category,
    )


def derive_update_pseudonym(
    pseudonym_id: PseudonymId,
    new_alias: str | None,
    new_notes: str | None,
    state: PrivacyState,
) -> PseudonymUpdated | Failure:
    """
    Derive a pseudonym update event.

    Args:
        pseudonym_id: ID of pseudonym to update
        new_alias: New alias (if changing)
        new_notes: New notes (if changing)
        state: Current privacy state

    Returns:
        PseudonymUpdated event on success, Failure with reason on error
    """
    # Find the pseudonym
    pseudonym = None
    for existing in state.existing_pseudonyms:
        if existing.id == pseudonym_id:
            pseudonym = existing
            break

    if pseudonym is None:
        return Failure(PseudonymNotFound(pseudonym_id=pseudonym_id))

    # Validate new_alias if provided
    if new_alias is not None:
        if not new_alias or not new_alias.strip():
            return Failure(EmptyAlias())

        # Check for duplicate alias (excluding current pseudonym)
        alias_lower = new_alias.lower()
        for existing in state.existing_pseudonyms:
            if existing.id != pseudonym_id and existing.alias.lower() == alias_lower:
                return Failure(DuplicateAlias(alias=new_alias))

    # Create event with old and new values
    return PseudonymUpdated.create(
        pseudonym_id=pseudonym_id,
        old_alias=pseudonym.alias,
        new_alias=new_alias.strip() if new_alias else pseudonym.alias,
    )


def derive_delete_pseudonym(
    pseudonym_id: PseudonymId,
    state: PrivacyState,
) -> PseudonymDeleted | Failure:
    """
    Derive a pseudonym deletion event.

    Args:
        pseudonym_id: ID of pseudonym to delete
        state: Current privacy state

    Returns:
        PseudonymDeleted event on success, Failure with reason on error
    """
    # Find the pseudonym
    pseudonym = None
    for existing in state.existing_pseudonyms:
        if existing.id == pseudonym_id:
            pseudonym = existing
            break

    if pseudonym is None:
        return Failure(PseudonymNotFound(pseudonym_id=pseudonym_id))

    return PseudonymDeleted.create(
        pseudonym_id=pseudonym_id,
        alias=pseudonym.alias,
    )
