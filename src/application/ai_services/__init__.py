"""
AI Services Application Layer

Functional use cases for AI-powered coding operations.
"""

from src.application.ai_services.commands import (
    ApproveCodeSuggestionCommand,
    ApproveMergeCommand,
    DetectDuplicatesCommand,
    DismissMergeCommand,
    RejectCodeSuggestionCommand,
    SuggestCodesCommand,
)
from src.application.ai_services.usecases import (
    approve_code_suggestion,
    approve_merge,
    detect_duplicates,
    suggest_codes,
)

__all__ = [
    # Commands
    "SuggestCodesCommand",
    "ApproveCodeSuggestionCommand",
    "RejectCodeSuggestionCommand",
    "DetectDuplicatesCommand",
    "ApproveMergeCommand",
    "DismissMergeCommand",
    # Use Cases
    "suggest_codes",
    "detect_duplicates",
    "approve_code_suggestion",
    "approve_merge",
]
