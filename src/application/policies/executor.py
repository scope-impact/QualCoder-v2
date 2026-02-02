"""
Policy Infrastructure: Executor

The PolicyExecutor integrates with the EventBus to automatically
execute policy actions when domain events are published.
"""

from __future__ import annotations

import logging
from typing import Any

from src.application.event_bus import EventBus, Subscription
from src.application.policies.base import PolicyContext, PolicyExecution
from src.application.policies.registry import PolicyRegistry, get_policy_registry

logger = logging.getLogger(__name__)


class PolicyExecutor:
    """
    Executes policy actions in response to domain events.

    Subscribes to all events on the EventBus and routes them to
    registered policy actions.

    Usage:
        executor = PolicyExecutor(event_bus)
        executor.start()

        # Later...
        executor.stop()
    """

    def __init__(
        self,
        event_bus: EventBus,
        registry: PolicyRegistry | None = None,
        context: PolicyContext | None = None,
    ) -> None:
        """
        Initialize the policy executor.

        Args:
            event_bus: The event bus to subscribe to
            registry: Policy registry (defaults to singleton)
            context: Context passed to policy actions
        """
        self._event_bus = event_bus
        self._registry = registry or get_policy_registry()
        self._context = context or PolicyContext()
        self._subscription: Subscription | None = None
        self._executions: list[PolicyExecution] = []
        self._history_size = 100  # Keep last N executions

    def start(self) -> None:
        """
        Start listening for events and executing policies.

        Subscribes to all events on the event bus.
        """
        if self._subscription is not None:
            logger.warning("PolicyExecutor already started")
            return

        self._subscription = self._event_bus.subscribe_all(self._handle_event)
        logger.info("PolicyExecutor started")

    def stop(self) -> None:
        """
        Stop listening for events.

        Cancels the event bus subscription.
        """
        if self._subscription is not None:
            self._subscription.cancel()
            self._subscription = None
            logger.info("PolicyExecutor stopped")

    @property
    def is_running(self) -> bool:
        """Check if the executor is running."""
        return self._subscription is not None and self._subscription.is_active

    @property
    def context(self) -> PolicyContext:
        """Get the policy context."""
        return self._context

    def set_context(self, context: PolicyContext) -> None:
        """
        Set the policy context.

        Args:
            context: The new context to use
        """
        self._context = context

    def get_executions(self) -> list[PolicyExecution]:
        """
        Get the execution history.

        Returns:
            List of policy execution records
        """
        return list(self._executions)

    def clear_executions(self) -> None:
        """Clear the execution history."""
        self._executions.clear()

    def _handle_event(self, event: Any) -> None:
        """
        Handle an event from the event bus.

        Looks up and executes any registered policy actions.
        """
        # Get event type string
        event_type = self._get_event_type(event)

        # Get actions for this event type
        actions = self._registry.get_actions(event_type)

        if not actions:
            return  # No policies for this event

        logger.debug("Executing %d policy actions for %s", len(actions), event_type)

        # Execute each action
        for action_name, action_fn in actions:
            self._execute_action(event, event_type, action_name, action_fn)

    def _execute_action(
        self,
        event: Any,
        event_type: str,
        action_name: str,
        action_fn: Any,
    ) -> None:
        """
        Execute a single policy action.

        Records success or failure in execution history.
        """
        try:
            action_fn(event)
            execution = PolicyExecution.succeeded(event_type, action_name)
            logger.debug("Policy action '%s' succeeded for %s", action_name, event_type)

        except Exception as e:
            execution = PolicyExecution.failed(event_type, action_name, e)
            logger.error(
                "Policy action '%s' failed for %s: %s",
                action_name,
                event_type,
                e,
                exc_info=True,
            )

        # Record execution
        self._executions.append(execution)

        # Trim history
        while len(self._executions) > self._history_size:
            self._executions.pop(0)

    def _get_event_type(self, event: Any) -> str:
        """Get the event type string from an event instance."""
        # Check for event_type attribute
        if hasattr(event, "event_type"):
            return event.event_type

        # Generate from class
        event_class = type(event)
        module = event_class.__module__
        parts = module.split(".")

        if "domain" in parts:
            idx = parts.index("domain")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        else:
            context = parts[-1] if parts else "unknown"

        class_name = event_class.__name__
        snake_name = "".join(
            f"_{c.lower()}" if c.isupper() else c for c in class_name
        ).lstrip("_")

        return f"{context}.{snake_name}"


__all__ = [
    "PolicyExecutor",
]
