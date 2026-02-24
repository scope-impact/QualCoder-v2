"""
Cascade Registry - Declarative Cross-Context Cascade Rules

Replaces imperative cascade deletes with a declarative registry.
Each bounded context registers rules describing what should happen
when trigger events fire (e.g., delete segments when code is deleted).

Usage:
    registry = CascadeRegistry(event_bus)

    # Register a cascade rule
    registry.register(CascadeRule(
        trigger_event_type="coding.category_deleted",
        handler=_uncategorize_codes,
        description="Uncategorize codes when category is deleted",
        context="coding",
    ))

    # Introspect rules
    rules = registry.get_rules_for("coding.category_deleted")
    all_rules = registry.list_all_rules()
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.shared.infra.event_bus import EventBus

logger = logging.getLogger(__name__)

Handler = Callable[[Any], None]


@dataclass(frozen=True)
class CascadeRule:
    """
    Declarative cascade rule.

    Describes a data-modifying reaction to a domain event.
    Audit-only logging should NOT use cascade rules - subscribe directly to EventBus.

    Attributes:
        trigger_event_type: Event type string that triggers this cascade
        handler: Function to call when the trigger event fires
        description: Human-readable description of what this cascade does
        context: Bounded context that owns this rule
    """

    trigger_event_type: str
    handler: Handler
    description: str
    context: str


class CascadeRegistry:
    """
    Registry for declarative cascade rules.

    Automatically subscribes to the EventBus for each registered rule's
    trigger event type. When a trigger event fires, all matching cascade
    handlers are executed.

    Provides introspection to see all registered cascade rules.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._rules: list[CascadeRule] = []
        self._subscribed_types: set[str] = set()

    def register(self, rule: CascadeRule) -> None:
        """
        Register a cascade rule.

        If this is the first rule for the trigger event type, subscribes
        to the EventBus automatically.

        Args:
            rule: The cascade rule to register
        """
        self._rules.append(rule)
        logger.debug(
            "Cascade rule registered: [%s] %s -> %s",
            rule.context,
            rule.trigger_event_type,
            rule.description,
        )

        # Subscribe to EventBus if first rule for this event type
        if rule.trigger_event_type not in self._subscribed_types:
            self._event_bus.subscribe(
                rule.trigger_event_type,
                self._make_dispatcher(rule.trigger_event_type),
            )
            self._subscribed_types.add(rule.trigger_event_type)

    def get_rules_for(self, event_type: str) -> list[CascadeRule]:
        """
        Get all cascade rules for a specific trigger event type.

        Args:
            event_type: The trigger event type string

        Returns:
            List of cascade rules for this event type
        """
        return [r for r in self._rules if r.trigger_event_type == event_type]

    def list_all_rules(self) -> list[CascadeRule]:
        """
        Get all registered cascade rules.

        Returns:
            List of all cascade rules
        """
        return list(self._rules)

    def _make_dispatcher(self, event_type: str) -> Handler:
        """Create a dispatcher that calls all handlers for an event type."""

        def dispatch(event: Any) -> None:
            rules = self.get_rules_for(event_type)
            for rule in rules:
                try:
                    rule.handler(event)
                except Exception:
                    logger.exception(
                        "Cascade handler failed: [%s] %s",
                        rule.context,
                        rule.description,
                    )
                    raise

        return dispatch
