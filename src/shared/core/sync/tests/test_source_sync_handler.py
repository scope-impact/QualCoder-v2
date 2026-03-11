"""
Tests for SourceSyncHandler.

Tests the cross-context denormalization sync that keeps source_name
columns in sync across bounded contexts when source events occur.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import allure
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
    repo = MagicMock()
    repo.update_source_name = MagicMock()
    return repo


@pytest.fixture
def mock_case_repo() -> MagicMock:
    repo = MagicMock()
    repo.update_source_name = MagicMock()
    return repo


@pytest.fixture
def mock_coding_context(mock_segment_repo: MagicMock) -> MagicMock:
    context = MagicMock()
    context.segment_repo = mock_segment_repo
    return context


@pytest.fixture
def mock_cases_context(mock_case_repo: MagicMock) -> MagicMock:
    context = MagicMock()
    context.case_repo = mock_case_repo
    return context


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceSyncHandlerLifecycle:
    """Tests for start/stop lifecycle."""

    @allure.title("Start subscribes and is idempotent; stop unsubscribes and is idempotent")
    def test_start_stop_lifecycle(self, event_bus: EventBus) -> None:
        handler = SourceSyncHandler(event_bus)

        handler.start()
        assert handler._subscribed is True

        # Idempotent start
        handler.start()
        assert handler._subscribed is True

        handler.stop()
        assert handler._subscribed is False

        # Idempotent stop
        handler.stop()
        assert handler._subscribed is False

    @allure.title("Stop without start is safe")
    def test_stop_without_start_is_safe(self, event_bus: EventBus) -> None:
        handler = SourceSyncHandler(event_bus)
        handler.stop()
        assert handler._subscribed is False


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceSyncHandlerContextSetters:
    """Tests for context setters."""

    @allure.title("Setting coding and cases contexts stores references")
    def test_set_contexts(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
    ) -> None:
        handler = SourceSyncHandler(event_bus)

        handler.set_coding_context(mock_coding_context)
        assert handler._coding_context is mock_coding_context

        handler.set_cases_context(mock_cases_context)
        assert handler._cases_context is mock_cases_context


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceRenamedHandling:
    """Tests for SourceRenamed event handling."""

    @allure.title("SourceRenamed updates both coding and cases contexts")
    def test_source_renamed_updates_both_contexts(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
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

    @allure.title("SourceRenamed with no contexts does not raise")
    def test_source_renamed_with_no_contexts_is_safe(self, event_bus: EventBus) -> None:
        handler = SourceSyncHandler(event_bus)
        handler.start()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)

    @allure.title("SourceRenamed continues to cases context even if coding fails")
    def test_source_renamed_handles_coding_context_error(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
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

        mock_case_repo.update_source_name.assert_called_once_with(source_id, "new.txt")


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceRemovedHandling:
    """Tests for SourceRemoved event handling."""

    @allure.title("SourceRemoved is handled without error")
    def test_source_removed_is_handled(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
    ) -> None:
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
        event_bus.publish(event)


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestEventNotReceivedWhenStopped:
    """Tests verifying events are not processed when handler is stopped."""

    @allure.title("Events not processed after stop or when never started")
    def test_no_updates_when_stopped_or_never_started(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_segment_repo: MagicMock,
    ) -> None:
        handler = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        handler.start()
        handler.stop()

        source_id = SourceId(42)
        event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event)
        mock_segment_repo.update_source_name.assert_not_called()

        # Also verify never-started handler
        handler2 = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        event_bus.publish(event)
        mock_segment_repo.update_source_name.assert_not_called()
