"""
Infrastructure layer for the Coding bounded context.

Provides:
- SQLAlchemy Core implementations of repository protocols
- AI-assisted coding infrastructure (LLM, embeddings, vector store)
"""

from src.contexts.coding.infra.code_analyzer import LLMCodeAnalyzer, MockCodeAnalyzer
from src.contexts.coding.infra.code_comparator import (
    LLMCodeComparator,
    MockCodeComparator,
    VectorCodeComparator,
)
from src.contexts.coding.infra.config import (
    AIConfig,
    EmbeddingConfig,
    LLMConfig,
    VectorStoreConfig,
)
from src.contexts.coding.infra.embedding_provider import (
    MiniLMEmbeddingProvider,
    MockEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    create_embedding_provider,
)
from src.contexts.coding.infra.llm_provider import (
    AnthropicLLMProvider,
    MockLLMProvider,
    OpenAICompatibleLLMProvider,
    create_llm_provider,
)
from src.contexts.coding.infra.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.contexts.coding.infra.schema import (
    # V2 prefixed tables (preferred)
    cod_category,
    cod_code,
    cod_segment,
    # Compatibility aliases
    code_cat,
    code_name,
    code_text,
    create_all,
    drop_all,
    metadata,
)
from src.contexts.coding.infra.vector_store import (
    ChromaVectorStore,
    MockVectorStore,
    create_vector_store,
)

__all__ = [
    # V2 prefixed tables
    "cod_category",
    "cod_code",
    "cod_segment",
    # Compatibility aliases
    "code_cat",
    "code_name",
    "code_text",
    # Schema utilities
    "create_all",
    "drop_all",
    "metadata",
    # Repositories
    "SQLiteCategoryRepository",
    "SQLiteCodeRepository",
    "SQLiteSegmentRepository",
    # AI Config
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
