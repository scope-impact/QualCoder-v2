"""
Tests for PrivacySignalBridge.

TDD tests written BEFORE implementation.
Converts privacy domain events to Qt signals for UI updates.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from src.domain.privacy.entities import AnonymizationSessionId, PseudonymId
from src.domain.privacy.events import (
    PseudonymCreated,
    PseudonymsApplied,
)
from src.domain.shared.types import SourceId

# Check if Qt tests should be skipped (headless environment)
_qt_available = False
try:
    # Only try to import if we have a display
    if os.environ.get("DISPLAY") or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        import importlib.util

        _qt_available = importlib.util.find_spec("PySide6.QtWidgets") is not None
except (ImportError, RuntimeError):
    pass


@pytest.fixture
def qapp():
    """Create a Qt application for testing."""
    if not _qt_available:
        pytest.skip("Qt not available in this environment")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for testing."""
    bus = Mock()
    bus.subscribe = Mock()
    bus.unsubscribe = Mock()
    bus.publish = Mock()
    return bus


class TestPrivacySignalBridgeSignals:
    """Tests for PrivacySignalBridge signal definitions."""

    def test_has_pseudonym_created_signal(self, qapp, mock_event_bus):
        """Should have pseudonym_created signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "pseudonym_created")

    def test_has_pseudonym_updated_signal(self, qapp, mock_event_bus):
        """Should have pseudonym_updated signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "pseudonym_updated")

    def test_has_pseudonym_deleted_signal(self, qapp, mock_event_bus):
        """Should have pseudonym_deleted signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "pseudonym_deleted")

    def test_has_pseudonyms_applied_signal(self, qapp, mock_event_bus):
        """Should have pseudonyms_applied signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "pseudonyms_applied")

    def test_has_anonymization_reverted_signal(self, qapp, mock_event_bus):
        """Should have anonymization_reverted signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "anonymization_reverted")

    def test_has_speakers_detected_signal(self, qapp, mock_event_bus):
        """Should have speakers_detected signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "speakers_detected")

    def test_has_speakers_converted_signal(self, qapp, mock_event_bus):
        """Should have speakers_converted signal."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert hasattr(bridge, "speakers_converted")


class TestPrivacySignalBridgeContext:
    """Tests for signal bridge context name."""

    def test_context_name_is_privacy(self, qapp, mock_event_bus):
        """Context name should be 'privacy'."""
        from src.application.privacy.signal_bridge import PrivacySignalBridge

        bridge = PrivacySignalBridge(mock_event_bus)
        assert bridge._get_context_name() == "privacy"


class TestPrivacyPayloads:
    """Tests for privacy signal payloads."""

    def test_pseudonym_payload_has_required_fields(self):
        """PseudonymPayload should have required fields."""
        from src.application.privacy.signal_bridge import PseudonymPayload

        payload = PseudonymPayload(
            event_type="privacy.pseudonym_created",
            pseudonym_id=1,
            real_name="John Smith",
            alias="P1",
            category="person",
        )

        assert payload.pseudonym_id == 1
        assert payload.real_name == "John Smith"
        assert payload.alias == "P1"
        assert payload.category == "person"

    def test_pseudonym_payload_is_immutable(self):
        """PseudonymPayload should be frozen."""
        from src.application.privacy.signal_bridge import PseudonymPayload

        payload = PseudonymPayload(
            event_type="privacy.pseudonym_created",
            pseudonym_id=1,
            real_name="Test",
            alias="T1",
            category="person",
        )

        with pytest.raises((AttributeError, TypeError)):
            payload.alias = "Changed"

    def test_anonymization_payload_has_required_fields(self):
        """AnonymizationPayload should have required fields."""
        from src.application.privacy.signal_bridge import AnonymizationPayload

        payload = AnonymizationPayload(
            event_type="privacy.pseudonyms_applied",
            session_id="anon_123",
            source_id=100,
            replacement_count=5,
        )

        assert payload.session_id == "anon_123"
        assert payload.source_id == 100
        assert payload.replacement_count == 5

    def test_speaker_conversion_payload(self):
        """SpeakerConversionPayload should have required fields."""
        from src.application.privacy.signal_bridge import SpeakerConversionPayload

        payload = SpeakerConversionPayload(
            event_type="privacy.speakers_converted",
            source_id=100,
            code_count=3,
            segment_count=10,
            speaker_names=("JOHN", "JANE", "BOB"),
        )

        assert payload.code_count == 3
        assert payload.segment_count == 10
        assert len(payload.speaker_names) == 3


class TestPrivacyEventConverters:
    """Tests for event-to-payload converters."""

    def test_pseudonym_created_converter(self):
        """Should convert PseudonymCreated to PseudonymPayload."""
        from src.application.privacy.signal_bridge import PseudonymCreatedConverter

        event = PseudonymCreated(
            event_id="evt_123",
            occurred_at=datetime.now(UTC),
            pseudonym_id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category="person",
        )

        converter = PseudonymCreatedConverter()
        payload = converter.convert(event)

        assert payload.pseudonym_id == 1
        assert payload.alias == "P1"
        assert payload.event_type == "privacy.pseudonym_created"

    def test_pseudonyms_applied_converter(self):
        """Should convert PseudonymsApplied to AnonymizationPayload."""
        from src.application.privacy.signal_bridge import PseudonymsAppliedConverter

        event = PseudonymsApplied(
            event_id="evt_456",
            occurred_at=datetime.now(UTC),
            session_id=AnonymizationSessionId(value="anon_test"),
            source_id=SourceId(value=100),
            pseudonym_count=2,
            replacement_count=5,
        )

        converter = PseudonymsAppliedConverter()
        payload = converter.convert(event)

        assert payload.session_id == "anon_test"
        assert payload.source_id == 100
        assert payload.replacement_count == 5
