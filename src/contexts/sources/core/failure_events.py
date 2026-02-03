"""
Sources Context: Failure Events

Publishable failure events for the sources bounded context.
These events can be published to the event bus and trigger policies.

Note: For backward compatibility, the actual failure event definitions are in
projects/core/failure_events.py. This module re-exports them for use in the
Sources bounded context. A future migration will move the definitions here.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

# Re-export from projects for backward compatibility
# These failure events conceptually belong to Sources but are currently defined in Projects
from src.contexts.projects.core.failure_events import (
    SourceFailureEvent,
    SourceNotAdded,
    SourceNotMoved,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)

__all__ = [
    # Source Failure Events
    "SourceNotAdded",
    "SourceNotRemoved",
    "SourceNotOpened",
    "SourceNotUpdated",
    "SourceNotMoved",
    # Type Union
    "SourceFailureEvent",
]
