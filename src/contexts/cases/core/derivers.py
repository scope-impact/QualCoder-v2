"""
Cases Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - returns events or Failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.contexts.cases.core.events import (
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.contexts.cases.core.invariants import (
    is_case_name_unique,
    is_valid_attribute_name,
    is_valid_attribute_type,
    is_valid_attribute_value,
    is_valid_case_name,
)
from src.contexts.shared import CaseId, Failure, SourceId

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case


# =============================================================================
# Failure Reasons
# =============================================================================


@dataclass(frozen=True)
class EmptyCaseName:
    """Case name is empty or whitespace-only."""

    message: str = "Case name cannot be empty"


@dataclass(frozen=True)
class CaseNameTooLong:
    """Case name exceeds maximum length."""

    name: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Case name '{self.name[:20]}...' exceeds 100 characters",
            )


@dataclass(frozen=True)
class DuplicateCaseName:
    """Case name already exists."""

    name: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self, "message", f"Case name '{self.name}' already exists"
            )


@dataclass(frozen=True)
class CaseNotFound:
    """Case with given ID not found."""

    case_id: CaseId | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message and self.case_id:
            object.__setattr__(
                self, "message", f"Case with id {self.case_id.value} not found"
            )


@dataclass(frozen=True)
class InvalidAttributeType:
    """Attribute type is not valid."""

    attr_type: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Invalid attribute type '{self.attr_type}'. Must be: text, number, date, boolean",
            )


@dataclass(frozen=True)
class InvalidAttributeValue:
    """Attribute value does not match expected type."""

    attr_name: str = ""
    attr_type: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Value for attribute '{self.attr_name}' is not a valid {self.attr_type}",
            )


@dataclass(frozen=True)
class InvalidAttributeName:
    """Attribute name is invalid."""

    message: str = "Attribute name cannot be empty"


@dataclass(frozen=True)
class SourceAlreadyLinked:
    """Source is already linked to case."""

    case_id: CaseId | None = None
    source_id: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message and self.case_id:
            object.__setattr__(
                self,
                "message",
                f"Source {self.source_id} is already linked to case {self.case_id.value}",
            )


@dataclass(frozen=True)
class SourceNotLinked:
    """Source is not linked to case."""

    case_id: CaseId | None = None
    source_id: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message and self.case_id:
            object.__setattr__(
                self,
                "message",
                f"Source {self.source_id} is not linked to case {self.case_id.value}",
            )


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
) -> CaseCreated | Failure:
    """
    Derive a case creation event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        name: The case name (1-100 characters)
        description: Optional description
        memo: Optional memo
        state: Current case state for invariant checking

    Returns:
        CaseCreated event on success, Failure with reason on error
    """
    # Check for empty/whitespace name
    if not name or not name.strip():
        return Failure(EmptyCaseName())

    # Check name length
    if not is_valid_case_name(name):
        return Failure(CaseNameTooLong(name=name))

    # Check uniqueness
    if not is_case_name_unique(name, list(state.existing_cases)):
        return Failure(DuplicateCaseName(name=name))

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
) -> CaseUpdated | Failure:
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
        CaseUpdated event on success, Failure with reason on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return Failure(CaseNotFound(case_id=case_id))

    # Check for empty/whitespace name
    if not name or not name.strip():
        return Failure(EmptyCaseName())

    # Check name length
    if not is_valid_case_name(name):
        return Failure(CaseNameTooLong(name=name))

    # Check uniqueness (excluding current case)
    if not is_case_name_unique(
        name, list(state.existing_cases), exclude_id=case_id.value
    ):
        return Failure(DuplicateCaseName(name=name))

    return CaseUpdated.create(
        case_id=case_id,
        name=name.strip(),
        description=description,
        memo=memo,
    )


def derive_remove_case(
    case_id: CaseId,
    state: CaseState,
) -> CaseRemoved | Failure:
    """
    Derive a case removal event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to remove
        state: Current case state for invariant checking

    Returns:
        CaseRemoved event on success, Failure with reason on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return Failure(CaseNotFound(case_id=case_id))

    return CaseRemoved.create(case_id=case_id)


def derive_set_case_attribute(
    case_id: CaseId,
    attr_name: str,
    attr_type: str,
    attr_value: Any,
    state: CaseState,
) -> CaseAttributeSet | Failure:
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
        CaseAttributeSet event on success, Failure with reason on error
    """
    # Check case exists
    case_exists = any(c.id == case_id for c in state.existing_cases)
    if not case_exists:
        return Failure(CaseNotFound(case_id=case_id))

    # Validate attribute name
    if not is_valid_attribute_name(attr_name):
        return Failure(InvalidAttributeName())

    # Validate attribute type
    if not is_valid_attribute_type(attr_type):
        return Failure(InvalidAttributeType(attr_type=attr_type))

    # Validate attribute value matches type
    if not is_valid_attribute_value(attr_value, attr_type):
        return Failure(InvalidAttributeValue(attr_name=attr_name, attr_type=attr_type))

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
) -> SourceLinkedToCase | Failure:
    """
    Derive a source linked to case event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to link to
        source_id: The source ID to link
        state: Current case state for invariant checking

    Returns:
        SourceLinkedToCase event on success, Failure with reason on error
    """
    # Find the case
    case = next((c for c in state.existing_cases if c.id == case_id), None)
    if case is None:
        return Failure(CaseNotFound(case_id=case_id))

    # Check if source is already linked
    if source_id.value in case.source_ids:
        return Failure(SourceAlreadyLinked(case_id=case_id, source_id=source_id.value))

    return SourceLinkedToCase.create(
        case_id=case_id,
        source_id=source_id.value,
    )


def derive_unlink_source_from_case(
    case_id: CaseId,
    source_id: SourceId,
    state: CaseState,
) -> SourceUnlinkedFromCase | Failure:
    """
    Derive a source unlinked from case event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        case_id: The case ID to unlink from
        source_id: The source ID to unlink
        state: Current case state for invariant checking

    Returns:
        SourceUnlinkedFromCase event on success, Failure with reason on error
    """
    # Find the case
    case = next((c for c in state.existing_cases if c.id == case_id), None)
    if case is None:
        return Failure(CaseNotFound(case_id=case_id))

    # Check if source is linked
    if source_id.value not in case.source_ids:
        return Failure(SourceNotLinked(case_id=case_id, source_id=source_id.value))

    return SourceUnlinkedFromCase.create(
        case_id=case_id,
        source_id=source_id.value,
    )
