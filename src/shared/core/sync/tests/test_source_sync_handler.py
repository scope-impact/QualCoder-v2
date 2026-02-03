"""
Tests for SourceSyncHandler.

Tests the cross-context denormalization sync that keeps source_name
columns in sync across bounded contexts when source events occur.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.contexts.projects.core.events import SourceRemoved, SourceRenamed
from src.shared.common.types import SourceId
from src.shared.core.sync import SourceSyncHandler
from src.shared.infra.event_bus import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    """Create a real EventBus for testing."""
    return EventBus()


@pytest.fixture
def mock_segment_repo() -> MagicMock:
    """Create a mock segment repository."""
    repo = MagicMock()
    repo.update_source_name = MagicMock()
    return repo


@pytest.fixture
def mock_case_repo() -> MagicMock:
    """Create a mock case repository."""
    repo = MagicMock()
    repo.update_source_name = MagicMock()
    return repo


@pytest.fixture
def mock_coding_context(mock_segment_repo: MagicMock) -> MagicMock:
    """Create a mock CodingContext."""
    context = MagicMock()
    context.segment_repo = mock_segment_repo
    return context


@pytest.fixture
def mock_cases_context(mock_case_repo: MagicMock) -> MagicMock:
    """Create a mock CasesContext."""
    context = MagicMock()
    context.case_repo = mock_case_repo
    return context


class TestSourceSyncHandlerLifecycle:
    """Tests for start/stop lifecycle."""

    def test_start_subscribes_to_events(self, event_bus: EventBus) -> None:
        """start() should subscribe to SourceRenamed and SourceRemoved events."""
        handler = SourceSyncHandler(event_bus)

        handler.start()

        # Verify subscriptions exist by checking internal state
        assert handler._subscribed is True

    def test_start_is_idempotent(self, event_bus: EventBus) -> None:
        """Calling start() multiple times should not create duplicate subscriptions."""
        handler = SourceSyncHandler(event_bus)

        handler.start()
        handler.start()
        handler.start()

        assert handler._subscribed is True

    def test_stop_unsubscribes_from_events(self, event_bus: EventBus) -> None:
        """stop() should unsubscribe from events."""
        handler = SourceSyncHandler(event_bus)
        handler.start()

        handler.stop()

        assert handler._subscribed is False

    def test_stop_is_idempotent(self, event_bus: EventBus) -> None:
        """Calling stop() multiple times should be safe."""
        handler = SourceSyncHandler(event_bus)
        handler.start()

        handler.stop()
        handler.stop()
        handler.stop()

        assert handler._subscribed is False

    def test_stop_without_start_is_safe(self, event_bus: EventBus) -> None:
        """Calling stop() without start() should be safe."""
        handler = SourceSyncHandler(event_bus)

        handler.stop()

        assert handler._subscribed is False


class TestSourceSyncHandlerContextSetters:
    """Tests for context setters."""

    def test_set_coding_context(
        self, event_bus: EventBus, mock_coding_context: MagicMock
    ) -> None:
        """set_coding_context() should set the coding context."""
        handler = SourceSyncHandler(event_bus)

        handler.set_coding_context(mock_coding_context)

        assert handler._coding_context is mock_coding_context

    def test_set_cases_context(
        self, event_bus: EventBus, mock_cases_context: MagicMock
    ) -> None:
        """set_cases_context() should set the cases context."""
        handler = SourceSyncHandler(event_bus)

        handler.set_cases_context(mock_cases_context)

        assert handler._cases_context is mock_cases_context


class TestSourceRenamedHandling:
    """Tests for SourceRenamed event handling."""

    def test_source_renamed_updates_coding_context(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_segment_repo: MagicMock,
    ) -> None:
        """SourceRenamed should update segment_repo.update_source_name."""
        handler = SourceSyncHandler(
            event_bus, coding_context=mock_coding_context, cases_context=None
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        mock_segment_repo.update_source_name.assert_called_once_with(
            source_id, "new.txt"
        )

    def test_source_renamed_updates_cases_context(
        self,
        event_bus: EventBus,
        mock_cases_context: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
        """SourceRenamed should update case_repo.update_source_name."""
        handler = SourceSyncHandler(
            event_bus, coding_context=None, cases_context=mock_cases_context
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        mock_case_repo.update_source_name.assert_called_once_with(source_id, "new.txt")

    def test_source_renamed_updates_both_contexts(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
        """SourceRenamed should update both contexts when both are set."""
        handler = SourceSyncHandler(
            event_bus,
            coding_context=mock_coding_context,
            cases_context=mock_cases_context,
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        mock_segment_repo.update_source_name.assert_called_once_with(
            source_id, "new.txt"
        )
        mock_case_repo.update_source_name.assert_called_once_with(source_id, "new.txt")

    def test_source_renamed_with_no_contexts_is_safe(self, event_bus: EventBus) -> None:
        """SourceRenamed should not fail when no contexts are set."""
        handler = SourceSyncHandler(event_bus)
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )

        # Should not raise
        event_bus.publish(event)

    def test_source_renamed_handles_coding_context_error(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
        """SourceRenamed should continue to cases context even if coding fails."""
        mock_segment_repo.update_source_name.side_effect = Exception("DB error")

        handler = SourceSyncHandler(
            event_bus,
            coding_context=mock_coding_context,
            cases_context=mock_cases_context,
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        # Coding context failed but cases should still be called
        mock_case_repo.update_source_name.assert_called_once_with(source_id, "new.txt")

    def test_source_renamed_handles_cases_context_error(
        self,
        event_bus: EventBus,
        mock_cases_context: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
        """SourceRenamed should handle cases context error gracefully."""
        mock_case_repo.update_source_name.side_effect = Exception("DB error")

        handler = SourceSyncHandler(
            event_bus, coding_context=None, cases_context=mock_cases_context
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )

        # Should not raise
        event_bus.publish(event)


class TestSourceRemovedHandling:
    """Tests for SourceRemoved event handling."""

    def test_source_removed_is_handled(self, event_bus: EventBus) -> None:
        """SourceRemoved should be handled without error."""
        handler = SourceSyncHandler(event_bus)
        handler.start()

        source_id = SourceId(42)
        event = SourceRemoved.create(
            source_id=source_id, name="deleted.txt", segments_removed=5
        )

        # Should not raise - currently just logs
        event_bus.publish(event)

    def test_source_removed_with_contexts_set(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
    ) -> None:
        """SourceRemoved should be handled when contexts are set."""
        handler = SourceSyncHandler(
            event_bus,
            coding_context=mock_coding_context,
            cases_context=mock_cases_context,
        )
        handler.start()

        source_id = SourceId(42)
        event = SourceRemoved.create(
            source_id=source_id, name="deleted.txt", segments_removed=5
        )

        # Should not raise - removal is handled by CASCADE
        event_bus.publish(event)


class TestEventNotReceivedWhenStopped:
    """Tests verifying events are not processed when handler is stopped."""

    def test_no_updates_when_stopped(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_segment_repo: MagicMock,
    ) -> None:
        """Events should not be processed after stop()."""
        handler = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        handler.start()
        handler.stop()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        mock_segment_repo.update_source_name.assert_not_called()

    def test_no_updates_when_never_started(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_segment_repo: MagicMock,
    ) -> None:
        """Events should not be processed if start() was never called."""
        _handler = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        # Note: start() never called

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

        mock_segment_repo.update_source_name.assert_not_called()
