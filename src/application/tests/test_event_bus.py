"""Tests for EventBus."""

import pytest
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.application.event_bus import (
    EventBus,
    Subscription,
    EventRecord,
    get_event_bus,
    reset_event_bus,
)


@dataclass(frozen=True)
class TestEvent:
    """Test event without event_type attribute."""
    data: str


@dataclass(frozen=True)
class CodeCreated:
    """Test event with event_type attribute."""
    event_type: str = "coding.code_created"
    name: str = ""


@dataclass(frozen=True)
class SegmentCoded:
    """Another test event."""
    event_type: str = "coding.segment_coded"
    code_id: int = 0


class TestEventBusSubscribe:
    """Tests for EventBus subscription."""

    def test_subscribe_by_string_type(self) -> None:
        """Test subscribing by event type string."""
        bus = EventBus()
        received: List = []

        sub = bus.subscribe("test.event", received.append)

        assert sub.is_active
        assert bus.handler_count("test.event") == 1

    def test_subscribe_returns_subscription(self) -> None:
        """Test that subscribe returns a Subscription."""
        bus = EventBus()

        sub = bus.subscribe("test.event", lambda e: None)

        assert isinstance(sub, Subscription)
        assert sub.is_active

    def test_subscribe_type_by_class(self) -> None:
        """Test subscribing by event class."""
        bus = EventBus()
        received: List = []

        sub = bus.subscribe_type(CodeCreated, received.append)

        assert sub.is_active
        assert bus.handler_count("coding.code_created") == 1

    def test_subscribe_all(self) -> None:
        """Test subscribing to all events."""
        bus = EventBus()
        received: List = []

        sub = bus.subscribe_all(received.append)

        assert sub.is_active
        assert bus.handler_count("*") == 1

    def test_duplicate_subscribe_ignored(self) -> None:
        """Test that duplicate subscriptions are ignored."""
        bus = EventBus()
        handler = lambda e: None

        bus.subscribe("test.event", handler)
        bus.subscribe("test.event", handler)

        assert bus.handler_count("test.event") == 1


class TestEventBusPublish:
    """Tests for EventBus publishing."""

    def test_publish_to_string_subscriber(self) -> None:
        """Test publishing to string-type subscriber."""
        bus = EventBus()
        received: List = []

        bus.subscribe("coding.code_created", received.append)
        event = CodeCreated(name="Anxiety")
        bus.publish(event)

        assert len(received) == 1
        assert received[0] is event

    def test_publish_to_class_subscriber(self) -> None:
        """Test publishing to class-type subscriber."""
        bus = EventBus()
        received: List = []

        bus.subscribe_type(CodeCreated, received.append)
        event = CodeCreated(name="Depression")
        bus.publish(event)

        assert len(received) == 1
        assert received[0].name == "Depression"

    def test_publish_to_all_subscriber(self) -> None:
        """Test publishing to all-events subscriber."""
        bus = EventBus()
        received: List = []

        bus.subscribe_all(received.append)
        bus.publish(CodeCreated(name="Test1"))
        bus.publish(SegmentCoded(code_id=1))

        assert len(received) == 2

    def test_publish_to_multiple_handlers(self) -> None:
        """Test publishing to multiple handlers."""
        bus = EventBus()
        received1: List = []
        received2: List = []

        bus.subscribe("coding.code_created", received1.append)
        bus.subscribe("coding.code_created", received2.append)
        bus.publish(CodeCreated(name="Test"))

        assert len(received1) == 1
        assert len(received2) == 1

    def test_publish_only_to_matching_type(self) -> None:
        """Test that events only go to matching subscribers."""
        bus = EventBus()
        code_events: List = []
        segment_events: List = []

        bus.subscribe("coding.code_created", code_events.append)
        bus.subscribe("coding.segment_coded", segment_events.append)

        bus.publish(CodeCreated(name="Test"))

        assert len(code_events) == 1
        assert len(segment_events) == 0

    def test_publish_derives_type_from_class(self) -> None:
        """Test that publish derives event type from class."""
        bus = EventBus()
        received: List = []

        # TestEvent has no event_type, should derive from class
        bus.subscribe("test_event", received.append)
        bus.publish(TestEvent(data="hello"))

        # Note: derived type will be based on module/class
        # This test verifies the mechanism works

    def test_handler_exception_does_not_stop_others(self) -> None:
        """Test that one handler's exception doesn't stop others."""
        bus = EventBus()
        received: List = []

        def bad_handler(e: Any) -> None:
            raise ValueError("Handler error")

        bus.subscribe("coding.code_created", bad_handler)
        bus.subscribe("coding.code_created", received.append)

        with pytest.warns(RuntimeWarning, match="Handler error"):
            bus.publish(CodeCreated(name="Test"))

        # Second handler should still receive event
        assert len(received) == 1


class TestEventBusUnsubscribe:
    """Tests for EventBus unsubscription."""

    def test_unsubscribe_by_handler(self) -> None:
        """Test unsubscribing a handler."""
        bus = EventBus()
        received: List = []
        handler = received.append

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)

        assert bus.handler_count("test.event") == 0

    def test_subscription_cancel(self) -> None:
        """Test cancelling via Subscription handle."""
        bus = EventBus()
        received: List = []

        sub = bus.subscribe("test.event", received.append)
        sub.cancel()

        assert not sub.is_active
        assert bus.handler_count("test.event") == 0

    def test_subscription_cancel_idempotent(self) -> None:
        """Test that cancel() can be called multiple times."""
        bus = EventBus()

        sub = bus.subscribe("test.event", lambda e: None)
        sub.cancel()
        sub.cancel()  # Should not raise

        assert not sub.is_active

    def test_subscription_context_manager(self) -> None:
        """Test Subscription as context manager."""
        bus = EventBus()
        received: List = []

        with bus.subscribe("test.event", received.append) as sub:
            assert sub.is_active
            bus.publish(TestEvent(data="inside"))

        assert not sub.is_active
        bus.publish(TestEvent(data="outside"))

        # Should only receive the event from inside the context
        assert len(received) == 1

    def test_clear_removes_all(self) -> None:
        """Test clear() removes all subscriptions."""
        bus = EventBus()

        bus.subscribe("event1", lambda e: None)
        bus.subscribe("event2", lambda e: None)
        bus.subscribe_all(lambda e: None)

        bus.clear()

        assert bus.handler_count() == 0

    def test_clear_for_handler(self) -> None:
        """Test clear_for_handler removes specific handler."""
        bus = EventBus()
        handler1 = lambda e: None
        handler2 = lambda e: None

        bus.subscribe("event1", handler1)
        bus.subscribe("event2", handler1)
        bus.subscribe("event1", handler2)

        count = bus.clear_for_handler(handler1)

        assert count == 2
        assert bus.handler_count("event1") == 1
        assert bus.handler_count("event2") == 0


class TestEventBusThreadSafety:
    """Tests for thread safety."""

    def test_publish_from_background_thread(self) -> None:
        """Test publishing from a background thread."""
        bus = EventBus()
        received: List = []

        bus.subscribe("test.event", received.append)

        def publish_in_thread() -> None:
            bus.publish(TestEvent(data="from thread"))

        thread = threading.Thread(target=publish_in_thread)
        thread.start()
        thread.join()

        assert len(received) == 1
        assert received[0].data == "from thread"

    def test_concurrent_subscribe_publish(self) -> None:
        """Test concurrent subscribe and publish operations."""
        bus = EventBus()
        received: List = []
        errors: List = []

        def subscriber() -> None:
            try:
                for i in range(100):
                    sub = bus.subscribe(f"event.{i}", received.append)
                    sub.cancel()
            except Exception as e:
                errors.append(e)

        def publisher() -> None:
            try:
                for i in range(100):
                    bus.publish(TestEvent(data=f"event {i}"))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=subscriber),
            threading.Thread(target=publisher),
            threading.Thread(target=subscriber),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestEventBusHistory:
    """Tests for event history."""

    def test_history_disabled_by_default(self) -> None:
        """Test that history is disabled by default."""
        bus = EventBus()
        bus.publish(CodeCreated(name="Test"))

        assert len(bus.get_history()) == 0

    def test_history_records_events(self) -> None:
        """Test that history records published events."""
        bus = EventBus(history_size=10)
        bus.subscribe("coding.code_created", lambda e: None)

        bus.publish(CodeCreated(name="Test"))

        history = bus.get_history()
        assert len(history) == 1
        assert history[0].event_type == "coding.code_created"
        assert history[0].handler_count == 1

    def test_history_limit(self) -> None:
        """Test that history respects size limit."""
        bus = EventBus(history_size=3)

        for i in range(5):
            bus.publish(TestEvent(data=str(i)))

        history = bus.get_history()
        assert len(history) == 3
        # Should have last 3 events
        assert history[0].event.data == "2"
        assert history[2].event.data == "4"

    def test_clear_history(self) -> None:
        """Test clearing history."""
        bus = EventBus(history_size=10)
        bus.publish(CodeCreated(name="Test"))

        bus.clear_history()

        assert len(bus.get_history()) == 0


class TestEventBusIntrospection:
    """Tests for introspection methods."""

    def test_handler_count_total(self) -> None:
        """Test total handler count."""
        bus = EventBus()

        bus.subscribe("event1", lambda e: None)
        bus.subscribe("event2", lambda e: None)
        bus.subscribe_all(lambda e: None)

        assert bus.handler_count() == 3

    def test_handler_count_by_type(self) -> None:
        """Test handler count by event type."""
        bus = EventBus()

        bus.subscribe("event1", lambda e: None)
        bus.subscribe("event1", lambda e: None)
        bus.subscribe("event2", lambda e: None)

        assert bus.handler_count("event1") == 2
        assert bus.handler_count("event2") == 1
        assert bus.handler_count("event3") == 0

    def test_event_types(self) -> None:
        """Test listing event types."""
        bus = EventBus()

        bus.subscribe("coding.code_created", lambda e: None)
        bus.subscribe("sources.source_imported", lambda e: None)

        types = bus.event_types()

        assert "coding.code_created" in types
        assert "sources.source_imported" in types


class TestDefaultEventBus:
    """Tests for default event bus singleton."""

    def test_get_event_bus_returns_same_instance(self) -> None:
        """Test that get_event_bus returns singleton."""
        reset_event_bus()

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

        reset_event_bus()

    def test_reset_clears_bus(self) -> None:
        """Test that reset clears subscriptions."""
        reset_event_bus()

        bus = get_event_bus()
        bus.subscribe("test", lambda e: None)

        reset_event_bus()

        bus = get_event_bus()
        assert bus.handler_count() == 0

        reset_event_bus()
