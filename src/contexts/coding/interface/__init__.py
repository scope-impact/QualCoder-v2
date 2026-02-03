"""
Coding Interface Layer.

External API for the coding bounded context, including MCP tools and signal bridge.
"""

from src.contexts.coding.interface.signal_bridge import (
    CategoryPayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)

__all__ = [
    "CodingSignalBridge",
    "CodePayload",
    "CategoryPayload",
    "SegmentPayload",
]
