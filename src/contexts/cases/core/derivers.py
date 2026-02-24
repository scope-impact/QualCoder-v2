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
# Helpers
# =============================================================================


def _find_case(case_id: CaseId, state: CaseState) -> Case | None:
    """Find a case by ID in the state container."""
    return next((c for c in state.existing_cases if c.id == case_id), None)


# =============================================================================
# Derivers
# =============================================================================


def derive_create_case(
    name: str,
    description: str | None,
    memo: str | None,
    state: CaseState,
) -> CaseCreated | CaseCreationFailed:
    """Derive a case creation event. Pure function -- no I/O, no side effects."""
    if not name or not name.strip():
        return CaseCreationFailed.empty_name()

    if not is_valid_case_name(name):
        return CaseCreationFailed.name_too_long(name)

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
    """Derive a case update event. Pure function -- no I/O, no side effects."""
    if not any(c.id == case_id for c in state.existing_cases):
        return CaseUpdateFailed.not_found(case_id.value)

    if not name or not name.strip():
        return CaseUpdateFailed.empty_name(case_id.value)

    if not is_valid_case_name(name):
        return CaseUpdateFailed.name_too_long(case_id.value, name)

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
    """Derive a case removal event. Pure function -- no I/O, no side effects."""
    if not any(c.id == case_id for c in state.existing_cases):
        return CaseDeletionFailed.not_found(case_id.value)

    return CaseRemoved.create(case_id=case_id)


def derive_set_case_attribute(
    case_id: CaseId,
    attr_name: str,
    attr_type: str,
    attr_value: Any,
    state: CaseState,
) -> CaseAttributeSet | AttributeSetFailed:
    """Derive a case attribute set event. Pure function -- no I/O, no side effects."""
    if not any(c.id == case_id for c in state.existing_cases):
        return AttributeSetFailed.case_not_found(case_id.value)

    if not is_valid_attribute_name(attr_name):
        return AttributeSetFailed.invalid_name(case_id.value)

    if not is_valid_attribute_type(attr_type):
        return AttributeSetFailed.invalid_type(case_id.value, attr_type)

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
    """Derive a source-linked-to-case event. Pure function -- no I/O, no side effects."""
    case = _find_case(case_id, state)
    if case is None:
        return SourceLinkFailed.case_not_found(case_id.value, source_id.value)

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
    """Derive a source-unlinked-from-case event. Pure function -- no I/O, no side effects."""
    case = _find_case(case_id, state)
    if case is None:
        return SourceUnlinkFailed.case_not_found(case_id.value, source_id.value)

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
    """Derive a case attribute removal event. Pure function -- no I/O, no side effects."""
    case = _find_case(case_id, state)
    if case is None:
        return AttributeRemovalFailed.case_not_found(case_id.value, attr_name)

    if not any(attr.name == attr_name for attr in case.attributes):
        return AttributeRemovalFailed.attribute_not_found(case_id.value, attr_name)

    return CaseAttributeRemoved.create(
        case_id=case_id,
        attr_name=attr_name,
    )
