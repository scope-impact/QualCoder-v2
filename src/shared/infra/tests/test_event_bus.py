"""
Tests for EventBus - domain event pub/sub infrastructure.

Key business logic tested:
- Subscribe/unsubscribe by string type and class
- Subscribe to all events
- Event publishing and handler invocation
- Event type string generation (module + class name conversion)
- Event history management (circular buffer)
- Handler error isolation
- Subscription lifecycle management
- Thread safety basics
"""

import warnings
from dataclasses import dataclass
from threading import Thread

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Infrastructure"),
]

from src.shared.infra.event_bus import (
    EventBus,
    EventRecord,
    Subscription,
    get_event_bus,
    reset_event_bus,
)


@dataclass
class SampleEvent:
    """Test event without event_type attribute."""

    value: str


@dataclass
class EventWithType:
    """Test event with explicit event_type."""

    event_type: str = "custom.event_type"
    value: str = ""


@allure.story("QC-000.02 Event Bus")
class TestEventBusSubscription:
    """Test subscribe(), subscribe_type(), subscribe_all(), and unsubscribe()."""

    @allure.title("subscribe returns active Subscription, deduplicates, and allows different handlers")
    def test_subscribe_and_deduplication(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        sub = bus.subscribe("test.event", handler1)
        assert isinstance(sub, Subscription)
        assert sub.is_active is True
        assert bus.handler_count("test.event") == 1

        # Duplicate same handler
        bus.subscribe("test.event", handler1)
        assert bus.handler_count("test.event") == 1

        # Different handler
        bus.subscribe("test.event", handler2)
        assert bus.handler_count("test.event") == 2

    @allure.title("subscribe_type routes events by class, subscribe_all receives all types")
    def test_subscribe_type_and_subscribe_all(self):
        bus = EventBus()
        type_received = []
        all_received = []

        def type_handler(e):
            type_received.append(e)

        def all_handler(e):
            all_received.append(e)

        bus.subscribe_type(SampleEvent, type_handler)
        bus.subscribe_type(EventWithType, type_handler)
        bus.subscribe_all(all_handler)
        bus.subscribe_all(all_handler)  # duplicate - should not add twice
        assert bus.handler_count("*") == 1

        bus.publish(SampleEvent(value="one"))
        bus.publish(EventWithType(value="two"))

        assert len(type_received) == 2
        assert len(all_received) == 2

    @allure.title("unsubscribe removes handler, tolerates missing, and removes wildcard")
    def test_unsubscribe(self):
        bus = EventBus()

        def handler(_e):
            pass

        # Unsubscribe nonexistent - should not raise
        bus.unsubscribe("test.event", handler)

        bus.subscribe("test.event", handler)
        assert bus.handler_count("test.event") == 1
        bus.unsubscribe("test.event", handler)
        assert bus.handler_count("test.event") == 0

        # Wildcard unsubscribe
        bus.subscribe_all(handler)
        bus.unsubscribe("*", handler)
        assert bus.handler_count("*") == 0


@allure.story("QC-000.02 Event Bus")
class TestSubscriptionLifecycle:
    """Test Subscription.cancel() and context manager."""

    @allure.title("cancel removes subscription, marks inactive, and works as context manager")
    def test_cancel_and_context_manager(self):
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e)

        # Cancel
        sub = bus.subscribe("test.event", handler)
        sub.cancel()
        assert sub.is_active is False
        bus.publish(SampleEvent(value="test"))
        assert len(received) == 0
        sub.cancel()  # idempotent
        assert sub.is_active is False

        # Context manager
        received.clear()
        with bus.subscribe_type(SampleEvent, handler) as sub:
            bus.publish(SampleEvent(value="inside"))
            assert sub.is_active is True

        bus.publish(SampleEvent(value="outside"))
        assert len(received) == 1
        assert received[0].value == "inside"


@allure.story("QC-000.02 Event Bus")
class TestEventBusPublish:
    """Test publish() method."""

    @allure.title("publish invokes type-specific, wildcard handlers and uses event_type attribute")
    def test_publish_routing_and_event_type_attribute(self):
        bus = EventBus()
        type_received = []
        all_received = []
        custom_received = []

        bus.subscribe("test_event_bus.sample_event", lambda e: type_received.append(e))
        bus.subscribe_all(lambda e: all_received.append(e))
        bus.subscribe("custom.event_type", lambda e: custom_received.append(e))

        bus.publish(SampleEvent(value="hello"))
        assert len(type_received) == 1
        assert type_received[0].value == "hello"
        assert len(all_received) == 1

        bus.publish(EventWithType(value="hello"))
        assert len(custom_received) == 1

    @pytest.mark.parametrize(
        "subscribe_method",
        ["subscribe", "subscribe_all"],
        ids=["type_specific_handler", "all_handler"],
    )
    @allure.title("handler error does not stop other handlers from executing")
    def test_handler_error_isolation(self, subscribe_method):
        bus = EventBus()
        received = []

        def bad_handler(e):
            raise ValueError("Handler failed")

        def good_handler(e):
            received.append(e)

        if subscribe_method == "subscribe":
            bus.subscribe("test_event_bus.sample_event", bad_handler)
            bus.subscribe("test_event_bus.sample_event", good_handler)
        else:
            bus.subscribe_all(bad_handler)
            bus.subscribe_all(good_handler)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bus.publish(SampleEvent(value="test"))

            runtime_warnings = [
                x for x in w if issubclass(x.category, RuntimeWarning)
            ]
            assert len(runtime_warnings) == 1
            assert "error" in str(runtime_warnings[0].message).lower()

        assert len(received) == 1


@allure.story("QC-000.02 Event Bus")
class TestEventBusClearAndIntrospection:
    """Test clear(), clear_for_handler(), event_types(), and handler_count()."""

    @allure.title("clear removes all, clear_for_handler removes specific, introspection works")
    def test_clear_and_introspection(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        def handler3(_e):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler2)
        bus.subscribe_all(handler3)

        # Introspection
        types = bus.event_types()
        assert "type1" in types
        assert "type2" in types
        assert bus.handler_count() == 3
        assert bus.handler_count("type1") == 1
        assert bus.handler_count("type3") == 0

        # clear_for_handler
        bus.subscribe("type1", handler1)  # already there (dedup)
        bus.subscribe("type2", handler1)
        bus.subscribe_all(handler1)
        count = bus.clear_for_handler(handler1)
        assert count == 3
        assert bus.handler_count("type1") == 0
        assert bus.handler_count("type2") == 1  # handler2 remains

        # clear all
        bus.clear()
        assert bus.handler_count() == 0

        # event_types after unsubscribe
        bus2 = EventBus()
        bus2.subscribe("type1", handler1)
        bus2.unsubscribe("type1", handler1)
        assert "type1" not in bus2.event_types()


@allure.story("QC-000.02 Event Bus")
class TestEventBusTypeStringAndHistory:
    """Test type string generation and event history."""

    @allure.title("type string generation, caching, history recording, trimming, and clearing")
    def test_type_string_and_history(self):
        bus = EventBus()

        # Type string from event_type attribute
        event = EventWithType(value="test")
        assert bus._get_event_type(event) == "custom.event_type"

        # Class-based generation and caching
        type_str = bus._get_type_string(SampleEvent)
        assert "sample_event" in type_str
        type_str2 = bus._get_type_string(SampleEvent)
        assert type_str == type_str2
        assert SampleEvent in bus._type_cache

        # History disabled by default
        bus_no_hist = EventBus()
        bus_no_hist.publish(SampleEvent(value="test"))
        assert len(bus_no_hist.get_history()) == 0

        # History enabled
        bus_hist = EventBus(history_size=3)

        def h1(_e):
            pass

        def h2(_e):
            pass

        bus_hist.subscribe("test_event_bus.sample_event", h1)
        bus_hist.subscribe("test_event_bus.sample_event", h2)

        for i in range(5):
            bus_hist.publish(SampleEvent(value=str(i)))

        history = bus_hist.get_history()
        assert len(history) == 3
        assert isinstance(history[0], EventRecord)
        assert history[0].event.value == "2"
        assert history[2].event.value == "4"
        assert history[0].handler_count == 2

        bus_hist.clear_history()
        assert len(bus_hist.get_history()) == 0


@allure.story("QC-000.02 Event Bus")
class TestEventBusThreadSafetyAndGlobal:
    """Thread safety and global singleton tests."""

    @allure.title("concurrent subscribe/publish, self-removing handler, singleton and reset")
    def test_thread_safety_and_global(self):
        # Concurrent subscribe and publish
        bus = EventBus()
        received = []

        def subscriber():
            for _ in range(100):
                bus.subscribe("test.event", lambda e: received.append(e))

        def publisher():
            for i in range(100):
                bus.publish(SampleEvent(value=str(i)))

        threads = [Thread(target=subscriber), Thread(target=publisher)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert isinstance(received, list)

        # Self-removing handler
        bus2 = EventBus()
        received2 = []

        def self_removing_handler(e):
            received2.append(e)
            bus2.unsubscribe("test_event_bus.sample_event", self_removing_handler)

        bus2.subscribe("test_event_bus.sample_event", self_removing_handler)
        bus2.publish(SampleEvent(value="test"))
        assert len(received2) == 1

        # Global singleton and reset
        reset_event_bus()

        def noop_handler(_e):
            pass

        bus_a = get_event_bus()
        bus_b = get_event_bus()
        assert bus_a is bus_b

        bus_a.subscribe("test", noop_handler)
        reset_event_bus()
        bus_c = get_event_bus()
        assert bus_a is not bus_c
        assert bus_c.handler_count() == 0
        assert bus_a.handler_count() == 0
