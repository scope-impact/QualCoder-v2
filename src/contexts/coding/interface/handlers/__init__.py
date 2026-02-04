"""
MCP Tool Handlers

Organized by feature area for maintainability.
"""

from typing import Any, Callable

from .base import CodingToolsContext, HandlerContext
from .core_handlers import CORE_HANDLERS
from .suggest_code_handlers import SUGGEST_CODE_HANDLERS
from .duplicate_handlers import DUPLICATE_HANDLERS
from .coding_suggestion_handlers import CODING_SUGGESTION_HANDLERS
from .auto_coding_handlers import AUTO_CODING_HANDLERS
from .batch_handlers import BATCH_HANDLERS

# Type alias for handler functions
HandlerFunc = Callable[[HandlerContext, dict[str, Any]], dict[str, Any]]

# Combine all handler registries
ALL_HANDLERS: dict[str, HandlerFunc] = {
    **CORE_HANDLERS,
    **SUGGEST_CODE_HANDLERS,
    **DUPLICATE_HANDLERS,
    **CODING_SUGGESTION_HANDLERS,
    **AUTO_CODING_HANDLERS,
    **BATCH_HANDLERS,
}

__all__ = [
    "CodingToolsContext",
    "HandlerContext",
    "HandlerFunc",
    "ALL_HANDLERS",
    "CORE_HANDLERS",
    "SUGGEST_CODE_HANDLERS",
    "DUPLICATE_HANDLERS",
    "CODING_SUGGESTION_HANDLERS",
    "AUTO_CODING_HANDLERS",
    "BATCH_HANDLERS",
]
