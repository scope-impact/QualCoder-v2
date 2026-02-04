"""
Factory function for creating AppContext instances.

Usage:
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    ctx.start()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.infra.event_bus import EventBus
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

from .context import AppContext

# Conditional imports for Qt (allows non-Qt tests to pass)
try:
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge

    HAS_QT = True
except ImportError:
    HAS_QT = False
    ProjectSignalBridge = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository


def create_app_context(
    settings_repo: UserSettingsRepository | None = None,
) -> AppContext:
    """
    Create a new AppContext instance with all dependencies.

    Args:
        settings_repo: Optional settings repository (created if not provided)

    Returns:
        Configured AppContext instance
    """
    # Local imports to avoid circular dependencies
    from src.contexts.cases.core.policies import configure_cases_policies
    from src.contexts.coding.core.policies import configure_coding_policies
    from src.shared.core.sync import SourceSyncHandler

    # Create core infrastructure components
    event_bus = EventBus(history_size=100)
    lifecycle = ProjectLifecycle()
    state = ProjectState()
    source_sync_handler = SourceSyncHandler(event_bus=event_bus)

    # Configure context-specific policies (subscribe to event bus)
    configure_coding_policies(event_bus)
    configure_cases_policies(event_bus)

    # Create settings repository (global, always available)
    if settings_repo is None:
        from src.contexts.settings.infra import UserSettingsRepository

        settings_repo = UserSettingsRepository()

    # Create signal bridge (only if Qt is available)
    signal_bridge: ProjectSignalBridge | None = None
    if HAS_QT and ProjectSignalBridge is not None:
        signal_bridge = ProjectSignalBridge.instance(event_bus)

    return AppContext(
        event_bus=event_bus,
        lifecycle=lifecycle,
        state=state,
        source_sync_handler=source_sync_handler,
        settings_repo=settings_repo,
        signal_bridge=signal_bridge,
    )
