"""
Cases Context: Failure Events

Publishable failure events for case operations.
These can trigger policies and provide rich error context for UI/AI.

Event naming convention: CASE_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent

# =============================================================================
# Case Creation Failures
# =============================================================================


@dataclass(frozen=True)
class CaseCreationFailed(FailureEvent):
    """Failure event when case creation fails."""

    name: str = ""
    suggestions: tuple[str, ...] = ()

    @classmethod
    def empty_name(cls) -> CaseCreationFailed:
        """Case name is empty or whitespace-only."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_CREATED/EMPTY_NAME",
            suggestions=("Provide a non-empty case name",),
        )

    @classmethod
    def name_too_long(cls, name: str) -> CaseCreationFailed:
        """Case name exceeds maximum length."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_CREATED/NAME_TOO_LONG",
            name=name,
            suggestions=(
                "Use a shorter name (max 100 characters)",
                "Abbreviate or use an acronym",
            ),
        )

    @classmethod
    def duplicate_name(cls, name: str) -> CaseCreationFailed:
        """Case name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_CREATED/DUPLICATE_NAME",
            name=name,
            suggestions=(
                "Use a different name",
                "Add a suffix to distinguish (e.g., 'Case A-2')",
            ),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "EMPTY_NAME":
            return "Case name cannot be empty"
        if reason == "NAME_TOO_LONG":
            return f"Case name '{self.name[:20]}...' exceeds 100 characters"
        if reason == "DUPLICATE_NAME":
            return f"Case name '{self.name}' already exists"
        return super().message


# =============================================================================
# Case Update Failures
# =============================================================================


@dataclass(frozen=True)
class CaseUpdateFailed(FailureEvent):
    """Failure event when case update fails."""

    case_id: int = 0
    name: str = ""
    suggestions: tuple[str, ...] = ()

    @classmethod
    def not_found(cls, case_id: int) -> CaseUpdateFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_UPDATED/NOT_FOUND",
            case_id=case_id,
            suggestions=("Verify the case ID is correct", "Refresh the case list"),
        )

    @classmethod
    def empty_name(cls, case_id: int) -> CaseUpdateFailed:
        """Case name is empty or whitespace-only."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_UPDATED/EMPTY_NAME",
            case_id=case_id,
            suggestions=("Provide a non-empty case name",),
        )

    @classmethod
    def name_too_long(cls, case_id: int, name: str) -> CaseUpdateFailed:
        """Case name exceeds maximum length."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_UPDATED/NAME_TOO_LONG",
            case_id=case_id,
            name=name,
            suggestions=("Use a shorter name (max 100 characters)",),
        )

    @classmethod
    def duplicate_name(cls, case_id: int, name: str) -> CaseUpdateFailed:
        """Case name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_UPDATED/DUPLICATE_NAME",
            case_id=case_id,
            name=name,
            suggestions=("Use a different name",),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        if reason == "EMPTY_NAME":
            return "Case name cannot be empty"
        if reason == "NAME_TOO_LONG":
            return f"Case name '{self.name[:20]}...' exceeds 100 characters"
        if reason == "DUPLICATE_NAME":
            return f"Case name '{self.name}' already exists"
        return super().message


# =============================================================================
# Case Deletion Failures
# =============================================================================


@dataclass(frozen=True)
class CaseDeletionFailed(FailureEvent):
    """Failure event when case deletion fails."""

    case_id: int = 0
    suggestions: tuple[str, ...] = ()

    @classmethod
    def not_found(cls, case_id: int) -> CaseDeletionFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CASE_NOT_DELETED/NOT_FOUND",
            case_id=case_id,
            suggestions=("Verify the case ID is correct", "Refresh the case list"),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        if self.reason == "NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        return super().message


# =============================================================================
# Attribute Failures
# =============================================================================


@dataclass(frozen=True)
class AttributeSetFailed(FailureEvent):
    """Failure event when setting case attribute fails."""

    case_id: int = 0
    attr_name: str = ""
    attr_type: str = ""
    suggestions: tuple[str, ...] = ()

    @classmethod
    def case_not_found(cls, case_id: int) -> AttributeSetFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_SET/CASE_NOT_FOUND",
            case_id=case_id,
            suggestions=("Verify the case ID is correct",),
        )

    @classmethod
    def invalid_name(cls, case_id: int) -> AttributeSetFailed:
        """Attribute name is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_SET/INVALID_NAME",
            case_id=case_id,
            suggestions=("Provide a non-empty attribute name",),
        )

    @classmethod
    def invalid_type(cls, case_id: int, attr_type: str) -> AttributeSetFailed:
        """Attribute type is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_SET/INVALID_TYPE",
            case_id=case_id,
            attr_type=attr_type,
            suggestions=(
                "Use one of: text, number, date, boolean",
                f"'{attr_type}' is not a valid attribute type",
            ),
        )

    @classmethod
    def invalid_value(
        cls, case_id: int, attr_name: str, attr_type: str
    ) -> AttributeSetFailed:
        """Attribute value doesn't match type."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_SET/INVALID_VALUE",
            case_id=case_id,
            attr_name=attr_name,
            attr_type=attr_type,
            suggestions=(f"Provide a valid {attr_type} value",),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "CASE_NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        if reason == "INVALID_NAME":
            return "Attribute name cannot be empty"
        if reason == "INVALID_TYPE":
            return f"Invalid attribute type '{self.attr_type}'. Must be: text, number, date, boolean"
        if reason == "INVALID_VALUE":
            return f"Value for attribute '{self.attr_name}' is not a valid {self.attr_type}"
        return super().message


@dataclass(frozen=True)
class AttributeRemovalFailed(FailureEvent):
    """Failure event when removing case attribute fails."""

    case_id: int = 0
    attr_name: str = ""
    suggestions: tuple[str, ...] = ()

    @classmethod
    def case_not_found(cls, case_id: int, attr_name: str) -> AttributeRemovalFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_REMOVED/CASE_NOT_FOUND",
            case_id=case_id,
            attr_name=attr_name,
            suggestions=("Verify the case ID is correct",),
        )

    @classmethod
    def attribute_not_found(
        cls, case_id: int, attr_name: str
    ) -> AttributeRemovalFailed:
        """Attribute does not exist on case."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="ATTRIBUTE_NOT_REMOVED/ATTRIBUTE_NOT_FOUND",
            case_id=case_id,
            attr_name=attr_name,
            suggestions=(
                f"Attribute '{attr_name}' does not exist on this case",
                "Refresh the attribute list",
            ),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "CASE_NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        if reason == "ATTRIBUTE_NOT_FOUND":
            return f"Attribute '{self.attr_name}' not found on case {self.case_id}"
        return super().message


# =============================================================================
# Source Link Failures
# =============================================================================


@dataclass(frozen=True)
class SourceLinkFailed(FailureEvent):
    """Failure event when linking source to case fails."""

    case_id: int = 0
    source_id: int = 0
    suggestions: tuple[str, ...] = ()

    @classmethod
    def case_not_found(cls, case_id: int, source_id: int) -> SourceLinkFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_LINKED/CASE_NOT_FOUND",
            case_id=case_id,
            source_id=source_id,
            suggestions=("Verify the case ID is correct",),
        )

    @classmethod
    def already_linked(cls, case_id: int, source_id: int) -> SourceLinkFailed:
        """Source is already linked to case."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_LINKED/ALREADY_LINKED",
            case_id=case_id,
            source_id=source_id,
            suggestions=("Source is already linked to this case",),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "CASE_NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        if reason == "ALREADY_LINKED":
            return f"Source {self.source_id} is already linked to case {self.case_id}"
        return super().message


@dataclass(frozen=True)
class SourceUnlinkFailed(FailureEvent):
    """Failure event when unlinking source from case fails."""

    case_id: int = 0
    source_id: int = 0
    suggestions: tuple[str, ...] = ()

    @classmethod
    def case_not_found(cls, case_id: int, source_id: int) -> SourceUnlinkFailed:
        """Case with given ID not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_UNLINKED/CASE_NOT_FOUND",
            case_id=case_id,
            source_id=source_id,
            suggestions=("Verify the case ID is correct",),
        )

    @classmethod
    def not_linked(cls, case_id: int, source_id: int) -> SourceUnlinkFailed:
        """Source is not linked to case."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_UNLINKED/NOT_LINKED",
            case_id=case_id,
            source_id=source_id,
            suggestions=("Source is not linked to this case",),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        reason = self.reason
        if reason == "CASE_NOT_FOUND":
            return f"Case with id {self.case_id} not found"
        if reason == "NOT_LINKED":
            return f"Source {self.source_id} is not linked to case {self.case_id}"
        return super().message
