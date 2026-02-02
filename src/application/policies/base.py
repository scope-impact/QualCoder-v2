"""
Policy Infrastructure: Base Types

Defines the core types for the declarative policy pattern.
Policies define reactions to domain events, enabling cross-context coordination.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

# Type variable for events
E = TypeVar("E")

# Policy action: a function that takes an event and performs some side effect
PolicyAction = Callable[[Any], None]


@dataclass(frozen=True)
class PolicyDefinition(Generic[E]):
    """
    Definition of a policy that reacts to domain events.

    A policy declares:
    - Which event type triggers it
    - What actions to execute when the event occurs
    - A description for documentation/debugging

    Example:
        PolicyDefinition(
            event_type=SourceRemoved,
            actions={
                "DELETE_SEGMENTS": remove_source_segments,
                "UNLINK_CASES": unlink_source_from_cases,
            },
            description="Cleanup when a source is removed"
        )
    """

    event_type: type[E]
    actions: dict[str, PolicyAction]
    description: str = ""

    @property
    def event_class_name(self) -> str:
        """Get the class name of the event type."""
        return self.event_type.__name__

    @property
    def action_names(self) -> list[str]:
        """Get the names of all actions in this policy."""
        return list(self.actions.keys())


@dataclass
class PolicyExecution:
    """
    Record of a policy action execution.

    Used for debugging and auditing policy behavior.
    """

    event_type: str
    action_name: str
    success: bool
    error_message: str | None = None

    @classmethod
    def succeeded(cls, event_type: str, action_name: str) -> PolicyExecution:
        """Create a successful execution record."""
        return cls(
            event_type=event_type,
            action_name=action_name,
            success=True,
        )

    @classmethod
    def failed(
        cls, event_type: str, action_name: str, error: Exception
    ) -> PolicyExecution:
        """Create a failed execution record."""
        return cls(
            event_type=event_type,
            action_name=action_name,
            success=False,
            error_message=str(error),
        )


@dataclass
class PolicyContext:
    """
    Context passed to policy actions.

    Provides access to repositories and services needed to execute policies.
    This allows policies to remain decoupled from specific implementations.
    """

    # Repository/service getters - set by the application during initialization
    repositories: dict[str, Any] = field(default_factory=dict)

    def get_repository(self, name: str) -> Any:
        """Get a repository by name."""
        if name not in self.repositories:
            raise KeyError(f"Repository '{name}' not found in policy context")
        return self.repositories[name]


__all__ = [
    "PolicyAction",
    "PolicyDefinition",
    "PolicyExecution",
    "PolicyContext",
]
