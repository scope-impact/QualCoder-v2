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
    """Tests for start/stop lifecycle and context setters."""

    @allure.title("Start/stop lifecycle, idempotency, and context setters")
    def test_lifecycle_and_context_setters(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
    ) -> None:
        handler = SourceSyncHandler(event_bus)

        # Start subscribes and is idempotent
        handler.start()
        assert handler._subscribed is True
        handler.start()
        assert handler._subscribed is True

        # Stop unsubscribes and is idempotent
        handler.stop()
        assert handler._subscribed is False
        handler.stop()
        assert handler._subscribed is False

        # Stop without start is safe
        handler2 = SourceSyncHandler(event_bus)
        handler2.stop()
        assert handler2._subscribed is False

        # Context setters store references
        handler.set_coding_context(mock_coding_context)
        assert handler._coding_context is mock_coding_context
        handler.set_cases_context(mock_cases_context)
        assert handler._cases_context is mock_cases_context


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceRenamedHandling:
    """Tests for SourceRenamed event handling."""

    @allure.title("SourceRenamed updates both contexts; safe with no contexts; handles errors")
    def test_source_renamed_scenarios(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
        mock_case_repo: MagicMock,
    ) -> None:
        # Updates both contexts
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
        handler.stop()

        # Safe with no contexts
        handler2 = SourceSyncHandler(event_bus)
        handler2.start()
        event2 = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event2)
        handler2.stop()

        # Handles coding context error, still updates cases
        mock_segment_repo.reset_mock()
        mock_case_repo.reset_mock()
        mock_segment_repo.update_source_name.side_effect = Exception("DB error")

        handler3 = SourceSyncHandler(
            event_bus,
            coding_context=mock_coding_context,
            cases_context=mock_cases_context,
        )
        handler3.start()
        event3 = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(event3)
        mock_case_repo.update_source_name.assert_called_once_with(source_id, "new.txt")
        handler3.stop()


@allure.epic("Shared")
@allure.feature("Shared Core")
@allure.story("QC-000.06 Source Sync")
class TestSourceRemovedAndStoppedHandling:
    """Tests for SourceRemoved and stopped handler behavior."""

    @allure.title("SourceRemoved handled; events ignored when stopped or never started")
    def test_removed_and_stopped_behavior(
        self,
        event_bus: EventBus,
        mock_coding_context: MagicMock,
        mock_cases_context: MagicMock,
        mock_segment_repo: MagicMock,
    ) -> None:
        # SourceRemoved is handled without error
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
        handler.stop()

        # Events not processed after stop
        mock_segment_repo.reset_mock()
        handler2 = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        handler2.start()
        handler2.stop()

        rename_event = SourceRenamed.create(
            source_id=source_id, old_name="old.txt", new_name="new.txt"
        )
        event_bus.publish(rename_event)
        mock_segment_repo.update_source_name.assert_not_called()

        # Never-started handler also ignores events
        handler3 = SourceSyncHandler(event_bus, coding_context=mock_coding_context)
        event_bus.publish(rename_event)
        mock_segment_repo.update_source_name.assert_not_called()
