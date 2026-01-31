"""Application Layer - Imperative Shell

Coordinates I/O operations and calls pure domain functions.
Handles side effects: database access, UI updates, external services.

Submodules:
    - event_bus: Domain event pub/sub infrastructure
    - signal_bridge: Thread-safe domain event → PySide6 signal bridging
    - protocols: Controller and EventBus contracts
"""

from src.application.event_bus import (
    EventBus,
    EventRecord,
    Subscription,
    get_event_bus,
    reset_event_bus,
)
from src.application.signal_bridge import (
    ActivityItem,
    ActivityStatus,
    BaseSignalBridge,
    EventConverter,
    SignalPayload,
)

__all__ = [
    # Event Bus
    "EventBus",
    "Subscription",
    "EventRecord",
    "get_event_bus",
    "reset_event_bus",
    # Signal Bridge
    "BaseSignalBridge",
    "SignalPayload",
    "ActivityItem",
    "ActivityStatus",
    "EventConverter",
]
