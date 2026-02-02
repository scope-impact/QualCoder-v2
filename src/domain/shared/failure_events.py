"""
DEPRECATED: Use src.contexts.shared.core.failure_events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.shared.core.failure_events import (
    AnyFailureEvent,
    FailureEvent,
)

__all__ = [
    "FailureEvent",
    "AnyFailureEvent",
]
