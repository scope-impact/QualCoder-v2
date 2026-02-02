"""
AI Services Use Cases

Functional use cases for AI-powered coding operations.

Query use cases (no side effects):
- suggest_codes: Request AI code suggestions
- detect_duplicates: Detect potentially duplicate codes

Command use cases (database side effects):
- approve_code_suggestion: Create code from approved suggestion
- approve_merge: Merge duplicate codes
"""

from src.application.ai_services.usecases.approve_code_suggestion import (
    approve_code_suggestion,
)
from src.application.ai_services.usecases.approve_merge import approve_merge
from src.application.ai_services.usecases.detect_duplicates import detect_duplicates
from src.application.ai_services.usecases.suggest_codes import suggest_codes

__all__ = [
    "suggest_codes",
    "detect_duplicates",
    "approve_code_suggestion",
    "approve_merge",
]
