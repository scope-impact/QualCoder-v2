"""
AI Services Context - Domain Layer

Provides AI-powered code suggestion and duplicate detection capabilities.
Pure domain logic with no I/O dependencies.

Entities:
    - CodeSuggestion: AI-proposed code with rationale
    - DuplicateCandidate: Pair of potentially duplicate codes
    - SimilarityScore: Semantic similarity measure

Events:
    - CodeSuggested: Agent proposed a new code
    - CodeSuggestionApproved/Rejected: Researcher decision
    - DuplicatesDetected: Agent found similar codes
    - MergeSuggested/Approved/Dismissed: Merge workflow

Protocols:
    - EmbeddingProvider: Text embedding interface
    - LLMProvider: Abstract LLM interface
    - CodeAnalyzer: Code suggestion service
    - CodeComparator: Duplicate detection service
"""

from src.domain.ai_services.entities import (
    CodeSuggestion,
    DetectionId,
    DuplicateCandidate,
    DuplicateDetectionResult,
    SimilarityScore,
    SuggestionBatch,
    SuggestionId,
    TextContext,
)
from src.domain.ai_services.events import (
    AIServiceEvent,
    CodeSuggested,
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicateEvent,
    DuplicatesDetected,
    MergeSuggested,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
    SuggestionEvent,
)
from src.domain.ai_services.protocols import (
    CodeAnalyzer,
    CodeComparator,
    DuplicateRepository,
    EmbeddingProvider,
    LLMProvider,
    SuggestionRepository,
)

__all__ = [
    # Entities
    "CodeSuggestion",
    "DuplicateCandidate",
    "DuplicateDetectionResult",
    "SimilarityScore",
    "SuggestionBatch",
    "SuggestionId",
    "DetectionId",
    "TextContext",
    # Events
    "AIServiceEvent",
    "CodeSuggested",
    "CodeSuggestionApproved",
    "CodeSuggestionRejected",
    "DuplicateEvent",
    "DuplicatesDetected",
    "MergeSuggested",
    "MergeSuggestionApproved",
    "MergeSuggestionDismissed",
    "SuggestionEvent",
    # Protocols
    "CodeAnalyzer",
    "CodeComparator",
    "DuplicateRepository",
    "EmbeddingProvider",
    "LLMProvider",
    "SuggestionRepository",
]
