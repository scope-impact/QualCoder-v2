"""
Policy Infrastructure

Declarative policy pattern for cross-context reactions to domain events.

This module provides:
- `configure_policy()`: Declare policies that react to events
- `PolicyExecutor`: Execute policies when events are published
- `PolicyRegistry`: Store and lookup policy definitions

Usage:
    from src.application.policies import configure_policy, PolicyExecutor

    # Configure policies during application startup
    configure_policy(
        event_type=SourceRemoved,
        actions={
            "DELETE_SEGMENTS": remove_source_segments,
            "UNLINK_CASES": unlink_source_from_cases,
        },
        description="Cleanup when a source is removed"
    )

    # Create and start the executor
    executor = PolicyExecutor(event_bus)
    executor.start()

    # Later, when SourceRemoved is published, policies execute automatically
"""

from typing import Any, TypeVar

from src.application.policies.base import (
    PolicyAction,
    PolicyContext,
    PolicyDefinition,
    PolicyExecution,
)
from src.application.policies.executor import PolicyExecutor
from src.application.policies.registry import (
    PolicyRegistry,
    get_policy_registry,
    reset_policy_registry,
)

E = TypeVar("E")


def configure_policy(
    event_type: type[E],
    actions: dict[str, PolicyAction],
    description: str = "",
) -> PolicyDefinition[E]:
    """
    Configure a declarative policy for a domain event.

    Policies define reactions to events that should happen automatically.
    They are executed by the PolicyExecutor when matching events are published.

    Args:
        event_type: The domain event class to react to
        actions: Dict mapping action names to functions that take the event
        description: Human-readable description of the policy

    Returns:
        The created PolicyDefinition (also registered automatically)

    Example:
        configure_policy(
            event_type=SourceRemoved,
            actions={
                "DELETE_SEGMENTS": lambda e: segment_repo.delete_for_source(e.source_id),
                "UNLINK_CASES": lambda e: case_repo.unlink_source(e.source_id),
            },
            description="Cleanup when a source is removed"
        )
    """
    definition = PolicyDefinition(
        event_type=event_type,
        actions=actions,
        description=description,
    )
    get_policy_registry().register(definition)
    return definition


__all__ = [
    # Core API
    "configure_policy",
    "PolicyExecutor",
    # Types
    "PolicyAction",
    "PolicyContext",
    "PolicyDefinition",
    "PolicyExecution",
    # Registry
    "PolicyRegistry",
    "get_policy_registry",
    "reset_policy_registry",
]
