"""
Application layer for the Cases bounded context.

Provides use cases for case management operations and signal bridge
for reactive UI updates.
"""

from src.application.cases.signal_bridge import CasesSignalBridge
from src.application.cases.usecases import (
    create_case,
    link_source_to_case,
    remove_case,
    set_case_attribute,
    unlink_source_from_case,
    update_case,
)

__all__ = [
    # Use cases
    "create_case",
    "update_case",
    "remove_case",
    "link_source_to_case",
    "unlink_source_from_case",
    "set_case_attribute",
    # Signal bridge
    "CasesSignalBridge",
]
