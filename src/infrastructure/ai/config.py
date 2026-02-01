"""
AI Infrastructure: Configuration

Configuration settings for AI services including LLM providers,
model selection, and analysis parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class AIConfig:
    """
    Configuration for AI services.

    Immutable configuration object that controls AI behavior.
    Can be loaded from environment or settings file.
    """

    # LLM Provider Settings
    provider: Literal["anthropic", "openai", "mock"] = "anthropic"
    model: str = "claude-3-haiku-20240307"
    api_key_env_var: str = "ANTHROPIC_API_KEY"

    # Request Settings
    max_tokens: int = 1024
    temperature: float = 0.3
    timeout_seconds: int = 30

    # Code Suggestion Settings
    max_suggestions: int = 5
    min_confidence: float = 0.5
    min_text_length: int = 50

    # Duplicate Detection Settings
    similarity_threshold: float = 0.8
    max_comparisons: int = 1000  # Limit for large codebooks

    # Color Generation Settings
    color_palette: tuple[str, ...] = field(
        default_factory=lambda: (
            "#F44336",  # Red
            "#E91E63",  # Pink
            "#9C27B0",  # Purple
            "#673AB7",  # Deep Purple
            "#3F51B5",  # Indigo
            "#2196F3",  # Blue
            "#03A9F4",  # Light Blue
            "#00BCD4",  # Cyan
            "#009688",  # Teal
            "#4CAF50",  # Green
            "#8BC34A",  # Light Green
            "#CDDC39",  # Lime
            "#FFEB3B",  # Yellow
            "#FFC107",  # Amber
            "#FF9800",  # Orange
            "#FF5722",  # Deep Orange
            "#795548",  # Brown
            "#607D8B",  # Blue Grey
        )
    )

    @classmethod
    def for_testing(cls) -> AIConfig:
        """Create a configuration suitable for testing (uses mock provider)."""
        return cls(
            provider="mock",
            max_suggestions=3,
            similarity_threshold=0.7,
        )

    @classmethod
    def from_env(cls) -> AIConfig:
        """
        Create configuration from environment variables.

        Environment variables:
            QUALCODER_AI_PROVIDER: LLM provider (anthropic, openai, mock)
            QUALCODER_AI_MODEL: Model name
            ANTHROPIC_API_KEY: API key for Anthropic
            OPENAI_API_KEY: API key for OpenAI
        """
        import os

        provider = os.getenv("QUALCODER_AI_PROVIDER", "anthropic")
        model = os.getenv("QUALCODER_AI_MODEL", "claude-3-haiku-20240307")

        api_key_var = "ANTHROPIC_API_KEY"
        if provider == "openai":
            api_key_var = "OPENAI_API_KEY"

        return cls(
            provider=provider,  # type: ignore
            model=model,
            api_key_env_var=api_key_var,
        )


@dataclass(frozen=True)
class EmbeddingConfig:
    """
    Configuration for embedding providers.

    Supports both OpenAI-compatible APIs (including local servers)
    and local sentence-transformers models.
    """

    # Provider selection
    provider: Literal["openai-compatible", "minilm", "mock"] = "openai-compatible"

    # OpenAI-compatible settings (works with OpenAI, Azure, Ollama, LM Studio, vLLM)
    api_base_url: str = "http://localhost:11434/v1"  # Ollama default
    api_key: str | None = None  # Optional for local servers
    openai_model: str = "nomic-embed-text"  # Good default for Ollama

    # MiniLM local settings (sentence-transformers)
    minilm_model: str = "all-MiniLM-L6-v2"

    # Request settings
    timeout_seconds: int = 30
    batch_size: int = 32  # Max texts per batch request

    @classmethod
    def for_testing(cls) -> EmbeddingConfig:
        """Create a configuration suitable for testing (uses mock provider)."""
        return cls(provider="mock")

    @classmethod
    def for_openai(
        cls, api_key: str, model: str = "text-embedding-3-small"
    ) -> EmbeddingConfig:
        """Create configuration for OpenAI API."""
        return cls(
            provider="openai-compatible",
            api_base_url="https://api.openai.com/v1",
            api_key=api_key,
            openai_model=model,
        )

    @classmethod
    def for_ollama(
        cls,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434/v1",
    ) -> EmbeddingConfig:
        """Create configuration for Ollama."""
        return cls(
            provider="openai-compatible",
            api_base_url=base_url,
            openai_model=model,
        )

    @classmethod
    def for_local(cls, model: str = "all-MiniLM-L6-v2") -> EmbeddingConfig:
        """Create configuration for local sentence-transformers."""
        return cls(
            provider="minilm",
            minilm_model=model,
        )

    @classmethod
    def from_env(cls) -> EmbeddingConfig:
        """
        Create configuration from environment variables.

        Environment variables:
            QUALCODER_EMBEDDING_PROVIDER: Provider (openai-compatible, minilm, mock)
            QUALCODER_EMBEDDING_API_URL: API base URL for OpenAI-compatible
            QUALCODER_EMBEDDING_API_KEY: API key (optional for local)
            QUALCODER_EMBEDDING_MODEL: Model name
        """
        import os

        provider = os.getenv("QUALCODER_EMBEDDING_PROVIDER", "openai-compatible")
        api_url = os.getenv("QUALCODER_EMBEDDING_API_URL", "http://localhost:11434/v1")
        api_key = os.getenv("QUALCODER_EMBEDDING_API_KEY")
        model = os.getenv("QUALCODER_EMBEDDING_MODEL", "nomic-embed-text")

        return cls(
            provider=provider,  # type: ignore
            api_base_url=api_url,
            api_key=api_key,
            openai_model=model,
            minilm_model=model if provider == "minilm" else "all-MiniLM-L6-v2",
        )


@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration for LLM providers.

    Supports OpenAI-compatible APIs (including local servers like Ollama, LM Studio),
    Anthropic Claude, and mock for testing.
    """

    # Provider selection
    provider: Literal["openai-compatible", "anthropic", "mock"] = "openai-compatible"

    # OpenAI-compatible settings (works with OpenAI, Ollama, LM Studio, vLLM)
    api_base_url: str = "http://localhost:11434/v1"  # Ollama default
    api_key: str | None = None  # Optional for local servers
    model: str = "llama3.2"  # Good default for Ollama

    # Request settings
    max_tokens: int = 1024
    temperature: float = 0.3
    timeout_seconds: int = 60

    @classmethod
    def for_testing(cls) -> LLMConfig:
        """Create a configuration suitable for testing (uses mock provider)."""
        return cls(provider="mock")

    @classmethod
    def for_openai(
        cls,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> LLMConfig:
        """Create configuration for OpenAI API."""
        return cls(
            provider="openai-compatible",
            api_base_url="https://api.openai.com/v1",
            api_key=api_key,
            model=model,
        )

    @classmethod
    def for_ollama(
        cls,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434/v1",
    ) -> LLMConfig:
        """Create configuration for Ollama."""
        return cls(
            provider="openai-compatible",
            api_base_url=base_url,
            model=model,
        )

    @classmethod
    def for_anthropic(
        cls,
        model: str = "claude-3-haiku-20240307",
    ) -> LLMConfig:
        """Create configuration for Anthropic Claude."""
        return cls(
            provider="anthropic",
            model=model,
        )

    @classmethod
    def from_env(cls) -> LLMConfig:
        """
        Create configuration from environment variables.

        Environment variables:
            QUALCODER_LLM_PROVIDER: Provider (openai-compatible, anthropic, mock)
            QUALCODER_LLM_API_URL: API base URL for OpenAI-compatible
            QUALCODER_LLM_API_KEY: API key
            QUALCODER_LLM_MODEL: Model name
        """
        import os

        provider = os.getenv("QUALCODER_LLM_PROVIDER", "openai-compatible")
        api_url = os.getenv("QUALCODER_LLM_API_URL", "http://localhost:11434/v1")
        api_key = os.getenv("QUALCODER_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("QUALCODER_LLM_MODEL", "llama3.2")

        return cls(
            provider=provider,  # type: ignore
            api_base_url=api_url,
            api_key=api_key,
            model=model,
        )


@dataclass(frozen=True)
class VectorStoreConfig:
    """
    Configuration for vector store.

    Supports ChromaDB for persistent vector storage and similarity search.
    """

    # Storage settings
    persist_directory: str | None = None  # None = in-memory
    collection_name: str = "qualcoder_codes"

    # Search settings
    distance_metric: Literal["cosine", "l2", "ip"] = "cosine"
    default_n_results: int = 10

    # Performance settings
    batch_size: int = 100  # Items per batch for bulk operations

    @classmethod
    def for_testing(cls) -> VectorStoreConfig:
        """Create in-memory configuration for testing."""
        return cls(
            persist_directory=None,
            collection_name="test_collection",
        )

    @classmethod
    def for_project(
        cls, project_path: str, collection: str = "codes"
    ) -> VectorStoreConfig:
        """Create configuration for a specific project."""
        import os

        persist_dir = os.path.join(project_path, ".qualcoder", "vectors")
        return cls(
            persist_directory=persist_dir,
            collection_name=collection,
        )

    @classmethod
    def from_env(cls) -> VectorStoreConfig:
        """
        Create configuration from environment variables.

        Environment variables:
            QUALCODER_VECTOR_PERSIST_DIR: Directory for persistent storage
            QUALCODER_VECTOR_COLLECTION: Collection name
        """
        import os

        persist_dir = os.getenv("QUALCODER_VECTOR_PERSIST_DIR")
        collection = os.getenv("QUALCODER_VECTOR_COLLECTION", "qualcoder_codes")

        return cls(
            persist_directory=persist_dir,
            collection_name=collection,
        )


# Default configuration instances
DEFAULT_CONFIG = AIConfig()
DEFAULT_EMBEDDING_CONFIG = EmbeddingConfig()
DEFAULT_LLM_CONFIG = LLMConfig()
DEFAULT_VECTOR_STORE_CONFIG = VectorStoreConfig()
