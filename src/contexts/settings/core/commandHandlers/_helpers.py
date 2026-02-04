"""
Helper utilities for settings command handlers.
"""

from __future__ import annotations

from typing import Any


def extract_failure_message(failure_reason: Any) -> str:
    """
    Extract error message from a failure reason.

    Handles both objects with a .message attribute and plain values.

    Args:
        failure_reason: The failure value from a Result

    Returns:
        String error message
    """
    if hasattr(failure_reason, "message"):
        return failure_reason.message
    return str(failure_reason)
