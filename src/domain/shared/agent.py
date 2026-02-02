"""
DEPRECATED: Use src.contexts.shared.core.agent instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.shared.core.agent import AgentSession, TrustLevel

__all__ = [
    "TrustLevel",
    "AgentSession",
]
