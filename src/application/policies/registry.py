"""
Policy Infrastructure: Registry

The PolicyRegistry is a singleton that stores all configured policies.
It provides lookup by event type for the PolicyExecutor.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any

from src.application.policies.base import PolicyAction, PolicyDefinition

logger = logging.getLogger(__name__)


class PolicyRegistry:
    """
    Registry for policy definitions.

    Stores policies indexed by event type for efficient lookup during execution.
    Thread-safe for registration and lookup.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        # Map from event type string to list of (action_name, action_fn) tuples
        self._policies: dict[str, list[tuple[str, PolicyAction]]] = {}
        # Store definitions for introspection
        self._definitions: list[PolicyDefinition[Any]] = []

    def register(self, definition: PolicyDefinition[Any]) -> None:
        """
        Register a policy definition.

        Args:
            definition: The policy to register
        """
        event_type = self._get_event_type_string(definition.event_type)

        with self._lock:
            if event_type not in self._policies:
                self._policies[event_type] = []

            # Add all actions from this definition
            for action_name, action_fn in definition.actions.items():
                self._policies[event_type].append((action_name, action_fn))

            self._definitions.append(definition)

        logger.debug(
            "Registered policy for %s with actions: %s",
            event_type,
            list(definition.actions.keys()),
        )

    def get_actions(self, event_type: str) -> list[tuple[str, PolicyAction]]:
        """
        Get all policy actions for an event type.

        Args:
            event_type: The event type string to look up

        Returns:
            List of (action_name, action_fn) tuples
        """
        with self._lock:
            return list(self._policies.get(event_type, []))

    def has_policies(self, event_type: str) -> bool:
        """
        Check if any policies are registered for an event type.

        Args:
            event_type: The event type string to check

        Returns:
            True if policies exist for this event type
        """
        with self._lock:
            return event_type in self._policies and len(self._policies[event_type]) > 0

    def list_event_types(self) -> list[str]:
        """
        List all event types with registered policies.

        Returns:
            List of event type strings
        """
        with self._lock:
            return list(self._policies.keys())

    def list_definitions(self) -> list[PolicyDefinition[Any]]:
        """
        List all registered policy definitions.

        Returns:
            List of policy definitions
        """
        with self._lock:
            return list(self._definitions)

    def clear(self) -> None:
        """Clear all registered policies."""
        with self._lock:
            self._policies.clear()
            self._definitions.clear()

    def _get_event_type_string(self, event_class: type) -> str:
        """
        Get the event type string for an event class.

        Uses the same logic as EventBus for consistency.
        """
        # Check for event_type attribute on class
        if hasattr(event_class, "event_type"):
            event_type = event_class.event_type
            if isinstance(event_type, str):
                return event_type

        # Generate from module and class name (same as EventBus)
        module = event_class.__module__
        parts = module.split(".")

        if "domain" in parts:
            idx = parts.index("domain")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        else:
            context = parts[-1] if parts else "unknown"

        # Convert class name from CamelCase to snake_case
        class_name = event_class.__name__
        snake_name = "".join(
            f"_{c.lower()}" if c.isupper() else c for c in class_name
        ).lstrip("_")

        return f"{context}.{snake_name}"


# Singleton instance
_registry: PolicyRegistry | None = None
_registry_lock = Lock()


def get_policy_registry() -> PolicyRegistry:
    """
    Get the singleton policy registry.

    Creates one if it doesn't exist.
    """
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = PolicyRegistry()
    return _registry


def reset_policy_registry() -> None:
    """Reset the singleton policy registry (for testing)."""
    global _registry
    with _registry_lock:
        if _registry is not None:
            _registry.clear()
        _registry = None


__all__ = [
    "PolicyRegistry",
    "get_policy_registry",
    "reset_policy_registry",
]
