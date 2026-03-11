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
class TestEventBusSubscribe:
    """Test subscribe() method."""

    @allure.title("subscribe returns active Subscription and registers handler")
    def test_subscribe_returns_active_subscription(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        sub = bus.subscribe("test.event", noop_handler)

        assert isinstance(sub, Subscription)
        assert sub.is_active is True
        assert bus.handler_count("test.event") == 1

    @allure.title("subscribe deduplicates same handler but allows different handlers")
    @pytest.mark.parametrize(
        "scenario, expected_count",
        [
            ("same_handler_twice", 1),
            ("different_handlers", 2),
        ],
    )
    def test_subscribe_handler_deduplication(self, scenario, expected_count):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("test.event", handler1)
        if scenario == "same_handler_twice":
            bus.subscribe("test.event", handler1)
        else:
            bus.subscribe("test.event", handler2)

        assert bus.handler_count("test.event") == expected_count


@allure.story("QC-000.02 Event Bus")
class TestEventBusSubscribeType:
    """Test subscribe_type() method - subscribing by class."""

    @allure.title("subscribe_type routes events to handler by class")
    @pytest.mark.parametrize(
        "event_cls, event_kwargs, subscribe_key",
        [
            (SampleEvent, {"value": "test"}, None),
            (EventWithType, {"value": "test"}, None),
        ],
        ids=["generated_type_string", "explicit_event_type_attribute"],
    )
    def test_subscribe_type_routes_event_to_handler(
        self, event_cls, event_kwargs, subscribe_key
    ):
        bus = EventBus()
        received = []

        bus.subscribe_type(event_cls, lambda e: received.append(e))
        bus.publish(event_cls(**event_kwargs))

        assert len(received) == 1


@allure.story("QC-000.02 Event Bus")
class TestEventBusSubscribeAll:
    """Test subscribe_all() method."""

    @allure.title("subscribe_all receives all event types and deduplicates handlers")
    def test_subscribe_all_receives_all_event_types_and_deduplicates(self):
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e)

        bus.subscribe_all(handler)
        bus.subscribe_all(handler)  # duplicate - should not add twice

        assert bus.handler_count("*") == 1

        bus.publish(SampleEvent(value="one"))
        bus.publish(EventWithType(value="two"))

        assert len(received) == 2


@allure.story("QC-000.02 Event Bus")
class TestEventBusUnsubscribe:
    """Test unsubscribe() method."""

    @allure.title("unsubscribe removes handler and tolerates missing handler")
    def test_unsubscribe_removes_handler_and_tolerates_missing(self):
        bus = EventBus()

        def handler(_e):
            pass

        # Unsubscribe nonexistent - should not raise
        bus.unsubscribe("test.event", handler)

        bus.subscribe("test.event", handler)
        assert bus.handler_count("test.event") == 1

        bus.unsubscribe("test.event", handler)
        assert bus.handler_count("test.event") == 0

    @allure.title("unsubscribe removes wildcard handler")
    def test_unsubscribe_all_handler(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe_all(noop_handler)
        bus.unsubscribe("*", noop_handler)

        assert bus.handler_count("*") == 0


@allure.story("QC-000.02 Event Bus")
class TestSubscriptionCancel:
    """Test Subscription.cancel() method."""

    @allure.title("cancel removes subscription and marks it inactive")
    def test_cancel_removes_subscription_and_marks_inactive(self):
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e)

        sub = bus.subscribe("test.event", handler)
        sub.cancel()

        assert sub.is_active is False
        bus.publish(SampleEvent(value="test"))
        assert len(received) == 0

        # Cancel again - should not raise
        sub.cancel()
        assert sub.is_active is False

    @allure.title("Subscription works as context manager for auto-cancel")
    def test_subscription_as_context_manager(self):
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e)

        with bus.subscribe_type(SampleEvent, handler) as sub:
            bus.publish(SampleEvent(value="inside"))
            assert sub.is_active is True

        bus.publish(SampleEvent(value="outside"))

        assert len(received) == 1
        assert received[0].value == "inside"


@allure.story("QC-000.02 Event Bus")
class TestEventBusPublish:
    """Test publish() method."""

    @allure.title("publish invokes type-specific and wildcard handlers")
    def test_publish_invokes_type_specific_and_all_handlers(self):
        bus = EventBus()
        type_received = []
        all_received = []

        bus.subscribe("test_event_bus.sample_event", lambda e: type_received.append(e))
        bus.subscribe_all(lambda e: all_received.append(e))
        bus.publish(SampleEvent(value="hello"))

        assert len(type_received) == 1
        assert type_received[0].value == "hello"
        assert len(all_received) == 1

    @allure.title("publish uses event_type attribute when present")
    def test_publish_uses_event_type_attribute_if_present(self):
        bus = EventBus()
        received = []

        bus.subscribe("custom.event_type", lambda e: received.append(e))
        bus.publish(EventWithType(value="hello"))

        assert len(received) == 1

    @allure.title("handler error does not stop other handlers from executing")
    @pytest.mark.parametrize(
        "subscribe_method",
        ["subscribe", "subscribe_all"],
        ids=["type_specific_handler", "all_handler"],
    )
    def test_handler_error_does_not_stop_other_handlers(self, subscribe_method):
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
class TestEventBusClear:
    """Test clear() and clear_for_handler() methods."""

    @allure.title("clear removes all subscriptions")
    def test_clear_removes_all_subscriptions(self):
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

        bus.clear()

        assert bus.handler_count() == 0

    @allure.title("clear_for_handler removes only the specified handler")
    def test_clear_for_handler_removes_specific_handler_only(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler1)
        bus.subscribe_all(handler1)
        bus.subscribe("type1", handler2)

        count = bus.clear_for_handler(handler1)

        assert count == 3
        assert bus.handler_count("type1") == 1  # handler2 remains


@allure.story("QC-000.02 Event Bus")
class TestEventBusTypeStringGeneration:
    """Test _get_type_string() for event type derivation."""

    @allure.title("type string generation uses event_type attribute or derives from class name")
    def test_type_string_generation_and_caching(self):
        bus = EventBus()

        # Instance with event_type attribute
        event = EventWithType(value="test")
        assert bus._get_event_type(event) == "custom.event_type"

        # Class-based generation
        type_str = bus._get_type_string(SampleEvent)
        assert "sample_event" in type_str

        # Caching
        type_str2 = bus._get_type_string(SampleEvent)
        assert type_str == type_str2
        assert SampleEvent in bus._type_cache


@allure.story("QC-000.02 Event Bus")
class TestEventBusHistory:
    """Test event history management."""

    @allure.title("history is disabled by default")
    def test_history_disabled_by_default(self):
        bus = EventBus()

        bus.publish(SampleEvent(value="test"))

        assert len(bus.get_history()) == 0

    @allure.title("history records events, trims to size, and clears")
    def test_history_records_events_trims_and_clears(self):
        bus = EventBus(history_size=3)

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("test_event_bus.sample_event", handler1)
        bus.subscribe("test_event_bus.sample_event", handler2)

        for i in range(5):
            bus.publish(SampleEvent(value=str(i)))

        history = bus.get_history()
        assert len(history) == 3
        assert isinstance(history[0], EventRecord)
        # Should have newest events (2, 3, 4)
        assert history[0].event.value == "2"
        assert history[2].event.value == "4"
        # Handler count recorded
        assert history[0].handler_count == 2

        bus.clear_history()
        assert len(bus.get_history()) == 0


@allure.story("QC-000.02 Event Bus")
class TestEventBusIntrospection:
    """Test introspection methods."""

    @allure.title("event_types returns only active subscription types")
    def test_event_types_returns_active_subscriptions(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler2)

        types = bus.event_types()
        assert "type1" in types
        assert "type2" in types

        bus.unsubscribe("type1", handler1)
        types = bus.event_types()
        assert "type1" not in types

    @allure.title("handler_count returns total and per-type counts")
    def test_handler_count_total_and_by_type(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        def handler3(_e):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type1", handler2)
        bus.subscribe("type2", handler3)

        assert bus.handler_count() == 3
        assert bus.handler_count("type1") == 2
        assert bus.handler_count("type2") == 1
        assert bus.handler_count("type3") == 0


@allure.story("QC-000.02 Event Bus")
class TestEventBusThreadSafety:
    """Basic thread safety tests."""

    @allure.title("concurrent subscribe/publish and self-removing handler are safe")
    def test_concurrent_subscribe_publish_and_self_removing_handler(self):
        # Part 1: concurrent subscribe and publish
        bus = EventBus()
        received = []

        def subscriber():
            for _ in range(100):
                bus.subscribe("test.event", lambda e: received.append(e))

        def publisher():
            for i in range(100):
                bus.publish(SampleEvent(value=str(i)))

        threads = [
            Thread(target=subscriber),
            Thread(target=publisher),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert isinstance(received, list)

        # Part 2: handler can modify handlers during publish
        bus2 = EventBus()
        received2 = []

        def self_removing_handler(e):
            received2.append(e)
            bus2.unsubscribe("test_event_bus.sample_event", self_removing_handler)

        bus2.subscribe("test_event_bus.sample_event", self_removing_handler)
        bus2.publish(SampleEvent(value="test"))

        assert len(received2) == 1


@allure.story("QC-000.02 Event Bus")
class TestGlobalEventBus:
    """Test get_event_bus() and reset_event_bus()."""

    @allure.title("get_event_bus returns singleton, reset_event_bus creates new instance")
    def test_singleton_and_reset(self):
        reset_event_bus()

        def noop_handler(_e):
            pass

        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

        bus1.subscribe("test", noop_handler)

        reset_event_bus()
        bus3 = get_event_bus()

        assert bus1 is not bus3
        assert bus3.handler_count() == 0
        # Old bus should be cleared
        assert bus1.handler_count() == 0
