"""
AI Infrastructure Layer

Provides concrete implementations of AI service protocols.
Handles LLM API calls, code analysis, duplicate detection, and embeddings.

Components:
    - LLMProvider implementations (Anthropic, OpenAI, Mock)
    - EmbeddingProvider implementations (OpenAI-compatible, MiniLM, Mock)
    - CodeAnalyzer implementation
    - CodeComparator implementation
    - Configuration management
"""

from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer
from src.infrastructure.ai.code_comparator import LLMCodeComparator
from src.infrastructure.ai.config import AIConfig, EmbeddingConfig
from src.infrastructure.ai.embedding_provider import (
    MiniLMEmbeddingProvider,
    MockEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    create_embedding_provider,
)
from src.infrastructure.ai.llm_provider import (
    AnthropicLLMProvider,
    MockLLMProvider,
)

__all__ = [
    "AIConfig",
    "AnthropicLLMProvider",
    "EmbeddingConfig",
    "LLMCodeAnalyzer",
    "LLMCodeComparator",
    "MiniLMEmbeddingProvider",
    "MockEmbeddingProvider",
    "MockLLMProvider",
    "OpenAICompatibleEmbeddingProvider",
    "create_embedding_provider",
]
