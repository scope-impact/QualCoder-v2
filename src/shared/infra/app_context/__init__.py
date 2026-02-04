"""
Application Context - Dependency Container for QualCoder.

AppContext is the composition root that holds all application-wide services
and bounded contexts directly. No unnecessary abstraction layers.

Usage:
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    ctx.start()

    # Use cases receive specific repos directly (Phase 3 DDD pattern)
    from src.contexts.sources.core.commandHandlers import add_source
    result = add_source(command, ctx.state, ctx.sources_context.source_repo, ctx.event_bus)

Architecture:
    AppContext
    ├── event_bus: Domain event pub/sub
    ├── lifecycle: Database connection management
    ├── state: In-memory session state
    ├── source_sync_handler: Cross-context sync
    ├── settings_repo: User settings (always available)
    ├── signal_bridge: Qt signal bridge (optional)
    ├── sources_context: Sources bounded context (when project open)
    ├── cases_context: Cases bounded context (when project open)
    ├── coding_context: Coding bounded context (when project open)
    └── projects_context: Projects bounded context (when project open)

Bounded Context Classes:
    This module also exports the bounded context classes (SourcesContext,
    CasesContext, CodingContext, ProjectsContext) that bundle repositories
    for each domain area. These are created when a project is opened.
"""

# Bounded context classes
from .bounded_contexts import (
    CasesContext,
    CodingContext,
    ProjectsContext,
    SourcesContext,
)

# Main AppContext class
from .context import AppContext

# Factory function
from .factory import create_app_context

__all__ = [
    # Bounded contexts
    "SourcesContext",
    "CasesContext",
    "CodingContext",
    "ProjectsContext",
    # Main class
    "AppContext",
    # Factory
    "create_app_context",
]
