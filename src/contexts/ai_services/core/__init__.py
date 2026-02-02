"""
AI Services Context - Core (Domain Layer)

Pure functions, entities, events for AI-powered code analysis.
No I/O operations.
"""

from src.contexts.ai_services.core.derivers import (
    AISuggestionState,
    DuplicatesNotDetected,
    MergeNotApproved,
    MergeNotCreated,
    MergeNotDismissed,
    SuggestionNotApproved,
    SuggestionNotCreated,
    SuggestionNotRejected,
)
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
    # State
    "AISuggestionState",
    # Entities
    "CodeSuggestion",
    "DuplicateCandidate",
    "SimilarityScore",
    "SuggestionId",
    "TextContext",
    # Success Events
    "CodeSuggestionApproved",
    "CodeSuggestionRejected",
    "DuplicatesDetected",
    "MergeSuggestionApproved",
    "MergeSuggestionDismissed",
    # Failure Events
    "DuplicatesNotDetected",
    "MergeNotApproved",
    "MergeNotCreated",
    "MergeNotDismissed",
    "SuggestionNotApproved",
    "SuggestionNotCreated",
    "SuggestionNotRejected",
    # Protocols
    "CodeAnalyzer",
    "CodeComparator",
    "EmbeddingProvider",
    "LLMProvider",
    "VectorStore",
]
