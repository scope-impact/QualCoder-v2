"""
Tests for the policy infrastructure.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.event_bus import EventBus
from src.application.policies import (
    PolicyDefinition,
    PolicyExecution,
    PolicyExecutor,
    configure_policy,
    get_policy_registry,
    reset_policy_registry,
)


@dataclass(frozen=True)
class FakeEvent:
    """Test event for policy tests."""

    event_id: str
    occurred_at: datetime
    value: str

    @classmethod
    def create(cls, value: str) -> "FakeEvent":
        return cls(
            event_id="test-id",
            occurred_at=datetime.now(UTC),
            value=value,
        )


@dataclass(frozen=True)
class AnotherFakeEvent:
    """Another test event."""

    event_id: str
    occurred_at: datetime
    count: int


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    """Reset the policy registry before each test."""
    reset_policy_registry()


class TestConfigurePolicy:
    """Tests for configure_policy function."""

    def test_configure_policy_registers_in_registry(self) -> None:
        """configure_policy should add the policy to the registry."""
        actions_called: list[str] = []

        def action1(event: FakeEvent) -> None:
            actions_called.append("action1")

        configure_policy(
            event_type=FakeEvent,
            actions={"ACTION_1": action1},
            description="Test policy",
        )

        registry = get_policy_registry()
        # Event type is derived from module path: test_policy_infrastructure.fake_event
        event_types = registry.list_event_types()
        assert len(event_types) == 1
        assert "fake_event" in event_types[0]

    def test_configure_policy_returns_definition(self) -> None:
        """configure_policy should return the created definition."""
        definition = configure_policy(
            event_type=FakeEvent,
            actions={"ACTION_1": lambda _e: None},
            description="Test policy",
        )

        assert isinstance(definition, PolicyDefinition)
        assert definition.event_type == FakeEvent
        assert definition.description == "Test policy"
        assert "ACTION_1" in definition.actions


class TestPolicyExecutor:
    """Tests for PolicyExecutor."""

    def test_executor_starts_and_stops(self) -> None:
        """Executor should track running state."""
        bus = EventBus()
        executor = PolicyExecutor(bus)

        assert not executor.is_running

        executor.start()
        assert executor.is_running

        executor.stop()
        assert not executor.is_running

    def test_executor_executes_policy_actions(self) -> None:
        """Executor should run policy actions when matching events published."""
        actions_called: list[str] = []

        def action1(event: FakeEvent) -> None:
            actions_called.append(f"action1:{event.value}")

        def action2(event: FakeEvent) -> None:
            actions_called.append(f"action2:{event.value}")

        configure_policy(
            event_type=FakeEvent,
            actions={
                "ACTION_1": action1,
                "ACTION_2": action2,
            },
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()

        bus.publish(FakeEvent.create("test-value"))

        assert "action1:test-value" in actions_called
        assert "action2:test-value" in actions_called
        assert len(actions_called) == 2

    def test_executor_only_matches_correct_event_type(self) -> None:
        """Executor should not run actions for non-matching events."""
        actions_called: list[str] = []

        def action1(event: FakeEvent) -> None:
            actions_called.append("action1")

        configure_policy(
            event_type=FakeEvent,
            actions={"ACTION_1": action1},
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()

        # Publish a different event type
        bus.publish(
            AnotherFakeEvent(event_id="x", occurred_at=datetime.now(UTC), count=5)
        )

        assert len(actions_called) == 0

    def test_executor_records_executions(self) -> None:
        """Executor should record execution history."""
        configure_policy(
            event_type=FakeEvent,
            actions={"ACTION_1": lambda _e: None},
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()

        bus.publish(FakeEvent.create("test"))

        executions = executor.get_executions()
        assert len(executions) == 1
        assert executions[0].success is True
        assert executions[0].action_name == "ACTION_1"

    def test_executor_records_failed_executions(self) -> None:
        """Executor should record failures when actions raise."""

        def failing_action(event: FakeEvent) -> None:
            raise ValueError("Test error")

        configure_policy(
            event_type=FakeEvent,
            actions={"FAILING_ACTION": failing_action},
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()

        bus.publish(FakeEvent.create("test"))

        executions = executor.get_executions()
        assert len(executions) == 1
        assert executions[0].success is False
        assert executions[0].action_name == "FAILING_ACTION"
        assert "Test error" in (executions[0].error_message or "")

    def test_executor_continues_after_action_failure(self) -> None:
        """Executor should continue executing other actions after a failure."""
        actions_called: list[str] = []

        def failing_action(event: FakeEvent) -> None:
            raise ValueError("Test error")

        def success_action(event: FakeEvent) -> None:
            actions_called.append("success")

        configure_policy(
            event_type=FakeEvent,
            actions={
                "FAILING": failing_action,
                "SUCCESS": success_action,
            },
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()

        bus.publish(FakeEvent.create("test"))

        # Both actions should have been attempted
        executions = executor.get_executions()
        assert len(executions) == 2

    def test_executor_does_nothing_when_stopped(self) -> None:
        """Executor should not process events when stopped."""
        actions_called: list[str] = []

        configure_policy(
            event_type=FakeEvent,
            actions={"ACTION_1": lambda _e: actions_called.append("called")},
        )

        bus = EventBus()
        executor = PolicyExecutor(bus)
        executor.start()
        executor.stop()

        bus.publish(FakeEvent.create("test"))

        assert len(actions_called) == 0


class TestPolicyExecution:
    """Tests for PolicyExecution record."""

    def test_succeeded_creates_success_record(self) -> None:
        """succeeded() should create a successful execution record."""
        execution = PolicyExecution.succeeded("test.event", "ACTION_1")

        assert execution.success is True
        assert execution.event_type == "test.event"
        assert execution.action_name == "ACTION_1"
        assert execution.error_message is None

    def test_failed_creates_failure_record(self) -> None:
        """failed() should create a failure execution record."""
        error = ValueError("Test error message")
        execution = PolicyExecution.failed("test.event", "ACTION_1", error)

        assert execution.success is False
        assert execution.event_type == "test.event"
        assert execution.action_name == "ACTION_1"
        assert "Test error message" in (execution.error_message or "")
