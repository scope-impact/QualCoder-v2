"""
AI Infrastructure Layer

Provides concrete implementations of AI service protocols.
Handles LLM API calls, code analysis, duplicate detection, embeddings, and vector storage.

Components:
    - LLMProvider implementations (Anthropic, OpenAI, Mock)
    - EmbeddingProvider implementations (OpenAI-compatible, MiniLM, Mock)
    - VectorStore implementations (ChromaDB, Mock)
    - CodeAnalyzer implementation
    - CodeComparator implementation
    - Configuration management
"""

from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer
from src.infrastructure.ai.code_comparator import LLMCodeComparator
from src.infrastructure.ai.config import AIConfig, EmbeddingConfig, VectorStoreConfig
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
from src.infrastructure.ai.vector_store import (
    ChromaVectorStore,
    MockVectorStore,
    create_vector_store,
)

__all__ = [
    "AIConfig",
    "AnthropicLLMProvider",
    "ChromaVectorStore",
    "EmbeddingConfig",
    "LLMCodeAnalyzer",
    "LLMCodeComparator",
    "MiniLMEmbeddingProvider",
    "MockEmbeddingProvider",
    "MockLLMProvider",
    "MockVectorStore",
    "OpenAICompatibleEmbeddingProvider",
    "VectorStoreConfig",
    "create_embedding_provider",
    "create_vector_store",
]
