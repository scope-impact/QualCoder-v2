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

from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer, MockCodeAnalyzer
from src.infrastructure.ai.code_comparator import (
    LLMCodeComparator,
    MockCodeComparator,
    VectorCodeComparator,
)
from src.infrastructure.ai.config import (
    AIConfig,
    EmbeddingConfig,
    LLMConfig,
    VectorStoreConfig,
)
from src.infrastructure.ai.embedding_provider import (
    MiniLMEmbeddingProvider,
    MockEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    create_embedding_provider,
)
from src.infrastructure.ai.llm_provider import (
    AnthropicLLMProvider,
    MockLLMProvider,
    OpenAICompatibleLLMProvider,
    create_llm_provider,
)
from src.infrastructure.ai.vector_store import (
    ChromaVectorStore,
    MockVectorStore,
    create_vector_store,
)

__all__ = [
    # Config
    "AIConfig",
    "EmbeddingConfig",
    "LLMConfig",
    "VectorStoreConfig",
    # LLM Providers
    "AnthropicLLMProvider",
    "MockLLMProvider",
    "OpenAICompatibleLLMProvider",
    "create_llm_provider",
    # Embedding Providers
    "MiniLMEmbeddingProvider",
    "MockEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "create_embedding_provider",
    # Vector Store
    "ChromaVectorStore",
    "MockVectorStore",
    "create_vector_store",
    # Code Analysis
    "LLMCodeAnalyzer",
    "MockCodeAnalyzer",
    "LLMCodeComparator",
    "MockCodeComparator",
    "VectorCodeComparator",
]
