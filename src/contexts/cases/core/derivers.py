"""
Cases Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - returns success events or failure events.

Per SKILL.md, derivers return direct failure events (not Failure wrappers)
for rich error context in UI and MCP/AI consumers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.contexts.cases.core.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.contexts.cases.core.failure_events import (
    AttributeRemovalFailed,
    AttributeSetFailed,
    CaseCreationFailed,
    CaseDeletionFailed,
    CaseUpdateFailed,
    SourceLinkFailed,
    SourceUnlinkFailed,
)
from src.contexts.cases.core.invariants import (
    is_case_name_unique,
    is_valid_attribute_name,
    is_valid_attribute_type,
    is_valid_attribute_value,
    is_valid_case_name,
)
from src.shared import CaseId, SourceId

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case


# =============================================================================
# State Container
# =============================================================================


@dataclass(frozen=True)
class CaseState:
    """Immutable state container for case operations."""

    existing_cases: tuple[Case, ...] = ()


# =============================================================================
# Derivers
# =============================================================================


def derive_create_case(
    name: str,
    description: str | None,
    memo: str | None,
    state: CaseState,
) -> CaseCreated | CaseCreationFailed:
    """
    Derive a case creation event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        name: The case name (1-100 characters)
        description: Optional description
        memo: Optional memo
        state: Current case state for invariant checking

    Returns:
        CaseCreated event on success, CaseCreationFailed on error
    """
    # Check for empty/whitespace name
    if not name or not name.strip():
        return CaseCreationFailed.empty_name()

    # Check name length
    if not is_valid_case_name(name):
        return CaseCreationFailed.name_too_long(name)

    # Check uniqueness
    if not is_case_name_unique(name, list(state.existing_cases)):
        return CaseCreationFailed.duplicate_name(name)

    return CaseCreated.create(
        name=name.strip(),
        description=description,
        memo=memo,
    )


def derive_update_case(
    case_id: CaseId,
    name: str,
    description: str | None,
    memo: str | None,
    state: CaseState,
) -> CaseUpdated | CaseUpdateFailed:
    """
    Derive a case update event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to update
        name: The new case name
        description: New description
        memo: New memo
        state: Current case state for invariant checking

    Returns:
        CaseUpdated event on success, CaseUpdateFailed on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return CaseUpdateFailed.not_found(case_id.value)

    # Check for empty/whitespace name
    if not name or not name.strip():
        return CaseUpdateFailed.empty_name(case_id.value)

    # Check name length
    if not is_valid_case_name(name):
        return CaseUpdateFailed.name_too_long(case_id.value, name)

    # Check uniqueness (excluding current case)
    if not is_case_name_unique(
        name, list(state.existing_cases), exclude_id=case_id.value
    ):
        return CaseUpdateFailed.duplicate_name(case_id.value, name)

    return CaseUpdated.create(
        case_id=case_id,
        name=name.strip(),
        description=description,
        memo=memo,
    )


def derive_remove_case(
    case_id: CaseId,
    state: CaseState,
) -> CaseRemoved | CaseDeletionFailed:
    """
    Derive a case removal event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to remove
        state: Current case state for invariant checking

    Returns:
        CaseRemoved event on success, CaseDeletionFailed on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return CaseDeletionFailed.not_found(case_id.value)

    return CaseRemoved.create(case_id=case_id)


def derive_set_case_attribute(
    case_id: CaseId,
    attr_name: str,
    attr_type: str,
    attr_value: Any,
    state: CaseState,
) -> CaseAttributeSet | AttributeSetFailed:
    """
    Derive a case attribute set event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to update
        attr_name: The attribute name
        attr_type: The attribute type (text, number, date, boolean)
        attr_value: The attribute value
        state: Current case state for invariant checking

    Returns:
        CaseAttributeSet event on success, AttributeSetFailed on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return AttributeSetFailed.case_not_found(case_id.value)

    # Validate attribute name
    if not is_valid_attribute_name(attr_name):
        return AttributeSetFailed.invalid_name(case_id.value)

    # Validate attribute type
    if not is_valid_attribute_type(attr_type):
        return AttributeSetFailed.invalid_type(case_id.value, attr_type)

    # Validate attribute value matches type
    if not is_valid_attribute_value(attr_value, attr_type):
        return AttributeSetFailed.invalid_value(case_id.value, attr_name, attr_type)

    return CaseAttributeSet.create(
        case_id=case_id,
        attr_name=attr_name.strip(),
        attr_type=attr_type.lower(),
        attr_value=attr_value,
    )


def derive_link_source_to_case(
    case_id: CaseId,
    source_id: SourceId,
    state: CaseState,
) -> SourceLinkedToCase | SourceLinkFailed:
    """
    Derive a source linked to case event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to link to
        source_id: The source ID to link
        state: Current case state for invariant checking

    Returns:
        SourceLinkedToCase event on success, SourceLinkFailed on error
    """
    # Find the case
    case = next((c for c in state.existing_cases if c.id == case_id), None)
    if case is None:
        return SourceLinkFailed.case_not_found(case_id.value, source_id.value)

    # Check if source is already linked
    if source_id.value in case.source_ids:
        return SourceLinkFailed.already_linked(case_id.value, source_id.value)

    return SourceLinkedToCase.create(
        case_id=case_id,
        source_id=source_id.value,
    )


def derive_unlink_source_from_case(
    case_id: CaseId,
    source_id: SourceId,
    state: CaseState,
) -> SourceUnlinkedFromCase | SourceUnlinkFailed:
    """
    Derive a source unlinked from case event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to unlink from
        source_id: The source ID to unlink
        state: Current case state for invariant checking

    Returns:
        SourceUnlinkedFromCase event on success, SourceUnlinkFailed on error
    """
    # Find the case
    case = next((c for c in state.existing_cases if c.id == case_id), None)
    if case is None:
        return SourceUnlinkFailed.case_not_found(case_id.value, source_id.value)

    # Check if source is linked
    if source_id.value not in case.source_ids:
        return SourceUnlinkFailed.not_linked(case_id.value, source_id.value)

    return SourceUnlinkedFromCase.create(
        case_id=case_id,
        source_id=source_id.value,
    )


def derive_remove_case_attribute(
    case_id: CaseId,
    attr_name: str,
    state: CaseState,
) -> CaseAttributeRemoved | AttributeRemovalFailed:
    """
    Derive a case attribute removal event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to remove attribute from
        attr_name: The attribute name to remove
        state: Current case state for invariant checking

    Returns:
        CaseAttributeRemoved event on success, AttributeRemovalFailed on error
    """
    # Find the case
    case = next((c for c in state.existing_cases if c.id == case_id), None)
    if case is None:
        return AttributeRemovalFailed.case_not_found(case_id.value, attr_name)

    # Check if attribute exists on case
    attr_exists = any(attr.name == attr_name for attr in case.attributes)
    if not attr_exists:
        return AttributeRemovalFailed.attribute_not_found(case_id.value, attr_name)

    return CaseAttributeRemoved.create(
        case_id=case_id,
        attr_name=attr_name,
    )
