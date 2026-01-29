"""Application Layer - Imperative Shell

Coordinates I/O operations and calls pure domain functions.
Handles side effects: database access, UI updates, external services.

Submodules:
    - signal_bridge: Thread-safe domain event → PyQt6 signal bridging
    - protocols: Controller and EventBus contracts
"""

from src.application.signal_bridge import (
    BaseSignalBridge,
    SignalPayload,
    ActivityItem,
    ActivityStatus,
    EventConverter,
)

__all__ = [
    "BaseSignalBridge",
    "SignalPayload",
    "ActivityItem",
    "ActivityStatus",
    "EventConverter",
]
