"""
Tests for Embedding Providers

Tests the MockEmbeddingProvider and factory function.
OpenAI-compatible and MiniLM providers require external dependencies
and are tested via integration tests.
"""

from __future__ import annotations

import pytest
from returns.result import Success

from src.infrastructure.ai.config import EmbeddingConfig
from src.infrastructure.ai.embedding_provider import (
    MockEmbeddingProvider,
    create_embedding_provider,
)

# ============================================================
# MockEmbeddingProvider Tests
# ============================================================


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    def test_embed_returns_success(self) -> None:
        """Embed returns Success with vector."""
        provider = MockEmbeddingProvider(dimensions=384)
        result = provider.embed("test text")

        assert isinstance(result, Success)
        embedding = result.unwrap()
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_deterministic(self) -> None:
        """Same text produces same embedding."""
        provider = MockEmbeddingProvider()
        result1 = provider.embed("test text")
        result2 = provider.embed("test text")

        assert result1.unwrap() == result2.unwrap()

    def test_embed_different_texts_different_embeddings(self) -> None:
        """Different texts produce different embeddings."""
        provider = MockEmbeddingProvider()
        result1 = provider.embed("text one")
        result2 = provider.embed("text two")

        assert result1.unwrap() != result2.unwrap()

    def test_embed_batch_returns_success(self) -> None:
        """Batch embed returns Success with list of vectors."""
        provider = MockEmbeddingProvider(dimensions=384)
        texts = ["text one", "text two", "text three"]
        result = provider.embed_batch(texts)

        assert isinstance(result, Success)
        embeddings = result.unwrap()
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_embed_batch_empty_list(self) -> None:
        """Empty batch returns empty list."""
        provider = MockEmbeddingProvider()
        result = provider.embed_batch([])

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_dimensions_property(self) -> None:
        """Dimensions property returns configured value."""
        provider = MockEmbeddingProvider(dimensions=768)
        assert provider.dimensions == 768

    def test_model_name_property(self) -> None:
        """Model name property returns configured value."""
        provider = MockEmbeddingProvider(model_name="test-model")
        assert provider.model_name == "test-model"

    def test_call_count_tracking(self) -> None:
        """Call count increments on each embed call."""
        provider = MockEmbeddingProvider()
        assert provider.call_count == 0

        provider.embed("text 1")
        assert provider.call_count == 1

        provider.embed("text 2")
        assert provider.call_count == 2

    def test_embedding_values_in_range(self) -> None:
        """Embedding values are between -1 and 1."""
        provider = MockEmbeddingProvider()
        result = provider.embed("any text")
        embedding = result.unwrap()

        assert all(-1.0 <= x <= 1.0 for x in embedding)


# ============================================================
# EmbeddingConfig Tests
# ============================================================


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_default_config(self) -> None:
        """Default config uses openai-compatible provider."""
        config = EmbeddingConfig()
        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"

    def test_for_testing(self) -> None:
        """for_testing creates mock config."""
        config = EmbeddingConfig.for_testing()
        assert config.provider == "mock"

    def test_for_openai(self) -> None:
        """for_openai creates OpenAI config."""
        config = EmbeddingConfig.for_openai("test-key", "text-embedding-3-small")
        assert config.provider == "openai-compatible"
        assert config.api_base_url == "https://api.openai.com/v1"
        assert config.api_key == "test-key"
        assert config.openai_model == "text-embedding-3-small"

    def test_for_ollama(self) -> None:
        """for_ollama creates Ollama config."""
        config = EmbeddingConfig.for_ollama("nomic-embed-text")
        assert config.provider == "openai-compatible"
        assert "11434" in config.api_base_url
        assert config.openai_model == "nomic-embed-text"

    def test_for_local(self) -> None:
        """for_local creates MiniLM config."""
        config = EmbeddingConfig.for_local("all-MiniLM-L6-v2")
        assert config.provider == "minilm"
        assert config.minilm_model == "all-MiniLM-L6-v2"

    def test_immutable(self) -> None:
        """Config is immutable (frozen dataclass)."""
        config = EmbeddingConfig()
        with pytest.raises(AttributeError):
            config.provider = "mock"  # type: ignore


# ============================================================
# Factory Function Tests
# ============================================================


class TestCreateEmbeddingProvider:
    """Tests for create_embedding_provider factory."""

    def test_creates_mock_provider(self) -> None:
        """Factory creates MockEmbeddingProvider for mock config."""
        config = EmbeddingConfig.for_testing()
        provider = create_embedding_provider(config)

        assert isinstance(provider, MockEmbeddingProvider)

    def test_unknown_provider_raises(self) -> None:
        """Factory raises ValueError for unknown provider."""
        # Create config with invalid provider by bypassing validation
        config = EmbeddingConfig()
        # Use object.__setattr__ to bypass frozen
        object.__setattr__(config, "provider", "unknown")

        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_provider(config)
