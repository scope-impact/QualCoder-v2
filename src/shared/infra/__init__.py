"""
Shared infrastructure.

Contains cross-cutting infrastructure components:
- EventBus: Pub/sub backbone for domain events
- AppContext: Composition root and dependency container
- State: In-memory project state cache
- Lifecycle: Database connection management
- SignalBridge: Qt signal bridging for UI
- Migrations: Database schema evolution
"""

from src.shared.infra.app_context import (
    AppContext,
    create_app_context,
)
from src.shared.infra.event_bus import EventBus
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

__all__ = [
    "EventBus",
    "AppContext",
    "create_app_context",
    "ProjectState",
    "ProjectLifecycle",
]
