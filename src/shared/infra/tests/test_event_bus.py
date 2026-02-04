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


class TestEventBusSubscribe:
    """Test subscribe() method."""

    def test_subscribe_returns_subscription(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        sub = bus.subscribe("test.event", noop_handler)

        assert isinstance(sub, Subscription)
        assert sub.is_active is True

    def test_subscribe_adds_handler(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe("test.event", noop_handler)

        assert bus.handler_count("test.event") == 1

    def test_subscribe_same_handler_twice_only_adds_once(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe("test.event", noop_handler)
        bus.subscribe("test.event", noop_handler)

        assert bus.handler_count("test.event") == 1

    def test_subscribe_different_handlers(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)

        assert bus.handler_count("test.event") == 2


class TestEventBusSubscribeType:
    """Test subscribe_type() method - subscribing by class."""

    def test_subscribe_type_uses_generated_type_string(self):
        bus = EventBus()
        received = []

        bus.subscribe_type(SampleEvent, lambda e: received.append(e))
        bus.publish(SampleEvent(value="test"))

        assert len(received) == 1
        assert received[0].value == "test"

    def test_subscribe_type_respects_event_type_attribute(self):
        bus = EventBus()
        received = []

        bus.subscribe_type(EventWithType, lambda e: received.append(e))
        bus.publish(EventWithType(value="test"))

        assert len(received) == 1


class TestEventBusSubscribeAll:
    """Test subscribe_all() method."""

    def test_subscribe_all_receives_all_events(self):
        bus = EventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e))
        bus.publish(SampleEvent(value="one"))
        bus.publish(EventWithType(value="two"))

        assert len(received) == 2

    def test_subscribe_all_same_handler_twice_only_adds_once(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe_all(noop_handler)
        bus.subscribe_all(noop_handler)

        assert bus.handler_count("*") == 1


class TestEventBusUnsubscribe:
    """Test unsubscribe() method."""

    def test_unsubscribe_removes_handler(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe("test.event", noop_handler)
        bus.unsubscribe("test.event", noop_handler)

        assert bus.handler_count("test.event") == 0

    def test_unsubscribe_nonexistent_handler_no_error(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        # Should not raise
        bus.unsubscribe("test.event", noop_handler)

    def test_unsubscribe_all_handler(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe_all(noop_handler)
        bus.unsubscribe("*", noop_handler)

        assert bus.handler_count("*") == 0


class TestSubscriptionCancel:
    """Test Subscription.cancel() method."""

    def test_cancel_removes_subscription(self):
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e)

        sub = bus.subscribe("test.event", handler)
        sub.cancel()
        bus.publish(SampleEvent(value="test"))

        assert len(received) == 0

    def test_cancel_marks_subscription_inactive(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        sub = bus.subscribe("test.event", noop_handler)
        sub.cancel()

        assert sub.is_active is False

    def test_cancel_twice_no_error(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        sub = bus.subscribe("test.event", noop_handler)
        sub.cancel()
        sub.cancel()  # Should not raise

        assert sub.is_active is False

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


class TestEventBusPublish:
    """Test publish() method."""

    def test_publish_invokes_type_specific_handlers(self):
        bus = EventBus()
        received = []

        bus.subscribe("test_event_bus.sample_event", lambda e: received.append(e))
        bus.publish(SampleEvent(value="hello"))

        assert len(received) == 1
        assert received[0].value == "hello"

    def test_publish_invokes_all_handlers(self):
        bus = EventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e))
        bus.publish(SampleEvent(value="hello"))

        assert len(received) == 1

    def test_publish_invokes_both_type_and_all_handlers(self):
        bus = EventBus()
        type_received = []
        all_received = []

        bus.subscribe("test_event_bus.sample_event", lambda e: type_received.append(e))
        bus.subscribe_all(lambda e: all_received.append(e))
        bus.publish(SampleEvent(value="hello"))

        assert len(type_received) == 1
        assert len(all_received) == 1

    def test_publish_uses_event_type_attribute_if_present(self):
        bus = EventBus()
        received = []

        bus.subscribe("custom.event_type", lambda e: received.append(e))
        bus.publish(EventWithType(value="hello"))

        assert len(received) == 1

    def test_handler_error_does_not_stop_other_handlers(self):
        bus = EventBus()
        received = []

        def bad_handler(e):
            raise ValueError("Handler failed")

        def good_handler(e):
            received.append(e)

        bus.subscribe("test_event_bus.sample_event", bad_handler)
        bus.subscribe("test_event_bus.sample_event", good_handler)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bus.publish(SampleEvent(value="test"))

            # Filter for RuntimeWarning (handler errors), ignore DeprecationWarning (event_type)
            runtime_warnings = [x for x in w if issubclass(x.category, RuntimeWarning)]
            assert len(runtime_warnings) == 1
            assert "Handler error" in str(runtime_warnings[0].message)

        # Good handler should still be called
        assert len(received) == 1

    def test_all_handler_error_does_not_stop_other_all_handlers(self):
        bus = EventBus()
        received = []

        def bad_handler(e):
            raise ValueError("Handler failed")

        def good_handler(e):
            received.append(e)

        bus.subscribe_all(bad_handler)
        bus.subscribe_all(good_handler)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            bus.publish(SampleEvent(value="test"))

        assert len(received) == 1


class TestEventBusClear:
    """Test clear() and clear_for_handler() methods."""

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

    def test_clear_for_handler_removes_specific_handler(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe("type1", noop_handler)
        bus.subscribe("type2", noop_handler)
        bus.subscribe_all(noop_handler)

        count = bus.clear_for_handler(noop_handler)

        assert count == 3
        assert bus.handler_count() == 0

    def test_clear_for_handler_leaves_other_handlers(self):
        bus = EventBus()

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type1", handler2)

        bus.clear_for_handler(handler1)

        assert bus.handler_count("type1") == 1


class TestEventBusTypeStringGeneration:
    """Test _get_type_string() for event type derivation."""

    def test_uses_event_type_attribute_from_instance(self):
        bus = EventBus()

        event = EventWithType(value="test")
        type_str = bus._get_event_type(event)

        assert type_str == "custom.event_type"

    def test_generates_from_module_and_class_name(self):
        bus = EventBus()

        type_str = bus._get_type_string(SampleEvent)

        # Should be derived from module path
        assert "sample_event" in type_str

    def test_caches_type_string(self):
        bus = EventBus()

        type_str1 = bus._get_type_string(SampleEvent)
        type_str2 = bus._get_type_string(SampleEvent)

        assert type_str1 == type_str2
        assert SampleEvent in bus._type_cache


class TestEventBusHistory:
    """Test event history management."""

    def test_history_disabled_by_default(self):
        bus = EventBus()

        bus.publish(SampleEvent(value="test"))

        assert len(bus.get_history()) == 0

    def test_history_enabled_records_events(self):
        bus = EventBus(history_size=10)

        bus.publish(SampleEvent(value="test"))

        history = bus.get_history()
        assert len(history) == 1
        assert isinstance(history[0], EventRecord)
        assert history[0].event.value == "test"

    def test_history_trims_to_size_limit(self):
        bus = EventBus(history_size=3)

        for i in range(5):
            bus.publish(SampleEvent(value=str(i)))

        history = bus.get_history()
        assert len(history) == 3
        # Should have newest events (2, 3, 4)
        assert history[0].event.value == "2"
        assert history[2].event.value == "4"

    def test_history_records_handler_count(self):
        bus = EventBus(history_size=10)

        def handler1(_e):
            pass

        def handler2(_e):
            pass

        bus.subscribe("test_event_bus.sample_event", handler1)
        bus.subscribe("test_event_bus.sample_event", handler2)
        bus.publish(SampleEvent(value="test"))

        history = bus.get_history()
        assert history[0].handler_count == 2

    def test_clear_history(self):
        bus = EventBus(history_size=10)

        bus.publish(SampleEvent(value="test"))
        bus.clear_history()

        assert len(bus.get_history()) == 0


class TestEventBusIntrospection:
    """Test introspection methods."""

    def test_event_types_returns_subscribed_types(self):
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

    def test_event_types_excludes_empty_handler_lists(self):
        bus = EventBus()

        def noop_handler(_e):
            pass

        bus.subscribe("type1", noop_handler)
        bus.unsubscribe("type1", noop_handler)

        types = bus.event_types()

        assert "type1" not in types

    def test_handler_count_total(self):
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

        assert bus.handler_count() == 3

    def test_handler_count_by_type(self):
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

        assert bus.handler_count("type1") == 2
        assert bus.handler_count("type2") == 1
        assert bus.handler_count("type3") == 0


class TestEventBusThreadSafety:
    """Basic thread safety tests."""

    def test_concurrent_subscribe_and_publish(self):
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

        # Should not crash; some events may be received
        assert isinstance(received, list)

    def test_publish_copies_handler_list(self):
        """Ensure handlers can be modified during iteration."""
        bus = EventBus()
        received = []

        def self_removing_handler(e):
            received.append(e)
            bus.unsubscribe("test_event_bus.sample_event", self_removing_handler)

        bus.subscribe("test_event_bus.sample_event", self_removing_handler)

        # Should not raise despite modifying handlers during publish
        bus.publish(SampleEvent(value="test"))

        assert len(received) == 1


class TestGlobalEventBus:
    """Test get_event_bus() and reset_event_bus()."""

    def test_get_event_bus_returns_singleton(self):
        reset_event_bus()

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus_clears_singleton(self):
        reset_event_bus()

        def noop_handler(_e):
            pass

        bus1 = get_event_bus()
        bus1.subscribe("test", noop_handler)

        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2
        assert bus2.handler_count() == 0

    def test_reset_event_bus_clears_handlers(self):
        reset_event_bus()

        def noop_handler(_e):
            pass

        bus = get_event_bus()
        bus.subscribe("test", noop_handler)

        reset_event_bus()

        # Old bus should be cleared
        assert bus.handler_count() == 0
