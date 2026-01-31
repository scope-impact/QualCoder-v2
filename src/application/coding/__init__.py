"""
Application layer for the Coding bounded context.

Provides the CodingController for handling commands and queries,
and CodingSignalBridge for reactive UI updates.
"""

from src.application.coding.controller import CodingControllerImpl
from src.application.coding.signal_bridge import (
    CategoryPayload,
    CodeMergePayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)

__all__ = [
    "CategoryPayload",
    "CodeMergePayload",
    "CodePayload",
    "CodingControllerImpl",
    "CodingSignalBridge",
    "SegmentPayload",
]
