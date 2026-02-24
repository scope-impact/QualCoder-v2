"""
Coding Interface Layer.

External API for the coding bounded context, including MCP tools and signal bridge.
"""

from src.contexts.coding.interface.mcp_tools import CodingTools
from src.contexts.coding.interface.signal_bridge import (
    CategoryPayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)

__all__ = [
    "CodingTools",
    "CodingSignalBridge",
    "CodePayload",
    "CategoryPayload",
    "SegmentPayload",
]
