"""
AI Services Context - Core (Domain Layer)

Pure functions, entities, events for AI-powered code analysis.
No I/O operations.
"""

from src.contexts.ai_services.core.entities import (
    CodeSuggestion,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)
from src.contexts.ai_services.core.events import (
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicatesDetected,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
)
from src.contexts.ai_services.core.protocols import (
    CodeAnalyzer,
    CodeComparator,
    EmbeddingProvider,
    LLMProvider,
    VectorStore,
)

__all__ = [
    # Entities
    "CodeSuggestion",
    "DuplicateCandidate",
    "SimilarityScore",
    "SuggestionId",
    "TextContext",
    # Events
    "CodeSuggestionApproved",
    "CodeSuggestionRejected",
    "DuplicatesDetected",
    "MergeSuggestionApproved",
    "MergeSuggestionDismissed",
    # Protocols
    "CodeAnalyzer",
    "CodeComparator",
    "EmbeddingProvider",
    "LLMProvider",
    "VectorStore",
]
