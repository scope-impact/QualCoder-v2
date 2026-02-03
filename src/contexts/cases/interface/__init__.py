"""
Cases Interface Layer.

External API for the cases bounded context, including MCP tools and signal bridge.
"""

from src.contexts.cases.interface.signal_bridge import (
    CaseAttributePayload,
    CasePayload,
    CasesSignalBridge,
    SourceLinkPayload,
)

__all__ = [
    "CasesSignalBridge",
    "CasePayload",
    "CaseAttributePayload",
    "SourceLinkPayload",
]
