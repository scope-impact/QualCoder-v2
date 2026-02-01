"""
Privacy domain failure types.

Discriminated union types for failure reasons in privacy operations.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.privacy.entities import PseudonymId


# =============================================================================
# Failure Reasons
# =============================================================================


@dataclass(frozen=True)
class EmptyRealName:
    """Real name cannot be empty."""

    message: str = "Real name cannot be empty"


@dataclass(frozen=True)
class EmptyAlias:
    """Alias cannot be empty."""

    message: str = "Alias cannot be empty"


@dataclass(frozen=True)
class DuplicateRealName:
    """A pseudonym with this real name already exists."""

    real_name: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Pseudonym for '{self.real_name}' already exists"
        )


@dataclass(frozen=True)
class DuplicateAlias:
    """A pseudonym with this alias already exists."""

    alias: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, "message", f"Alias '{self.alias}' already in use")


@dataclass(frozen=True)
class PseudonymNotFound:
    """Pseudonym with given ID was not found."""

    pseudonym_id: PseudonymId
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Pseudonym {self.pseudonym_id.value} not found"
        )


@dataclass(frozen=True)
class SessionNotFound:
    """Anonymization session was not found."""

    session_id: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Anonymization session '{self.session_id}' not found"
        )


@dataclass(frozen=True)
class SessionAlreadyReverted:
    """Anonymization session has already been reverted."""

    session_id: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Session '{self.session_id}' has already been reverted"
        )


# Type alias for all privacy failure reasons
PrivacyFailureReason = (
    EmptyRealName
    | EmptyAlias
    | DuplicateRealName
    | DuplicateAlias
    | PseudonymNotFound
    | SessionNotFound
    | SessionAlreadyReverted
)
