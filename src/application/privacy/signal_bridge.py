"""
Privacy Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Privacy context into Qt signals
for reactive UI updates.

Usage:
    from src.application.privacy.signal_bridge import PrivacySignalBridge
    from src.application.event_bus import get_event_bus

    bridge = PrivacySignalBridge.instance(get_event_bus())
    bridge.pseudonym_created.connect(on_pseudonym_created)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.protocols import EventConverter
from src.domain.privacy.events import (
    AnonymizationReverted,
    PseudonymCreated,
    PseudonymDeleted,
    PseudonymsApplied,
    PseudonymUpdated,
)


# =============================================================================
# Payloads - Data transferred via signals
# =============================================================================


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class PseudonymPayload:
    """Payload for pseudonym-related signals."""

    event_type: str
    pseudonym_id: int
    real_name: str
    alias: str
    category: str
    notes: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class AnonymizationPayload:
    """Payload for anonymization-related signals."""

    event_type: str
    session_id: str
    source_id: int
    replacement_count: int
    original_text: str | None = None
    timestamp: datetime = field(default_factory=_now)
    payload_session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SpeakerDetectionPayload:
    """Payload for speaker detection signals."""

    event_type: str
    source_id: int
    speaker_count: int
    speaker_names: tuple[str, ...]
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SpeakerConversionPayload:
    """Payload for speaker-to-code conversion signals."""

    event_type: str
    source_id: int
    code_count: int
    segment_count: int
    speaker_names: tuple[str, ...]
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Converters - Transform events to payloads
# =============================================================================


class PseudonymCreatedConverter(EventConverter):
    """Convert PseudonymCreated event to payload."""

    def convert(self, event: PseudonymCreated) -> PseudonymPayload:
        return PseudonymPayload(
            event_type="privacy.pseudonym_created",
            pseudonym_id=event.pseudonym_id.value,
            real_name=event.real_name,
            alias=event.alias,
            category=event.category,
        )


class PseudonymUpdatedConverter(EventConverter):
    """Convert PseudonymUpdated event to payload."""

    def convert(self, event: PseudonymUpdated) -> PseudonymPayload:
        return PseudonymPayload(
            event_type="privacy.pseudonym_updated",
            pseudonym_id=event.pseudonym_id.value,
            real_name="",  # Not in event
            alias=event.new_alias or "",
            category="",
            notes=event.new_notes,
        )


class PseudonymDeletedConverter(EventConverter):
    """Convert PseudonymDeleted event to payload."""

    def convert(self, event: PseudonymDeleted) -> PseudonymPayload:
        return PseudonymPayload(
            event_type="privacy.pseudonym_deleted",
            pseudonym_id=event.pseudonym_id.value,
            real_name="",
            alias="",
            category="",
        )


class PseudonymsAppliedConverter(EventConverter):
    """Convert PseudonymsApplied event to payload."""

    def convert(self, event: PseudonymsApplied) -> AnonymizationPayload:
        return AnonymizationPayload(
            event_type="privacy.pseudonyms_applied",
            session_id=event.session_id.value,
            source_id=event.source_id.value,
            replacement_count=event.replacement_count,
        )


class AnonymizationRevertedConverter(EventConverter):
    """Convert AnonymizationReverted event to payload."""

    def convert(self, event: AnonymizationReverted) -> AnonymizationPayload:
        return AnonymizationPayload(
            event_type="privacy.anonymization_reverted",
            session_id=event.session_id.value,
            source_id=event.source_id.value,
            replacement_count=0,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class PrivacySignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Privacy bounded context.

    Emits Qt signals when domain events occur, enabling reactive UI updates.

    Signals:
        pseudonym_created: Emitted when a new pseudonym is created
        pseudonym_updated: Emitted when a pseudonym is updated
        pseudonym_deleted: Emitted when a pseudonym is deleted
        pseudonyms_applied: Emitted when pseudonyms are applied to text
        anonymization_reverted: Emitted when anonymization is reverted
        speakers_detected: Emitted when speakers are detected in text
        speakers_converted: Emitted when speakers are converted to codes

    Usage:
        bridge = PrivacySignalBridge.instance(event_bus)
        bridge.pseudonym_created.connect(self._on_pseudonym_created)
        bridge.start()
    """

    # Pseudonym signals
    pseudonym_created = Signal(object)
    pseudonym_updated = Signal(object)
    pseudonym_deleted = Signal(object)

    # Anonymization signals
    pseudonyms_applied = Signal(object)
    anonymization_reverted = Signal(object)

    # Speaker signals
    speakers_detected = Signal(object)
    speakers_converted = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "privacy"

    def _register_converters(self) -> None:
        """Register all event converters."""
        # Pseudonym events
        self.register_converter(
            "privacy.pseudonym_created",
            PseudonymCreatedConverter(),
            "pseudonym_created",
        )
        self.register_converter(
            "privacy.pseudonym_updated",
            PseudonymUpdatedConverter(),
            "pseudonym_updated",
        )
        self.register_converter(
            "privacy.pseudonym_deleted",
            PseudonymDeletedConverter(),
            "pseudonym_deleted",
        )

        # Anonymization events
        self.register_converter(
            "privacy.pseudonyms_applied",
            PseudonymsAppliedConverter(),
            "pseudonyms_applied",
        )
        self.register_converter(
            "privacy.anonymization_reverted",
            AnonymizationRevertedConverter(),
            "anonymization_reverted",
        )
