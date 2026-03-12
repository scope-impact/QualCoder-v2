"""
Tests for Embedding Providers

Tests the MockEmbeddingProvider and factory function.
OpenAI-compatible and MiniLM providers require external dependencies
and are tested via integration tests.
"""

from __future__ import annotations

import allure
import pytest
from returns.result import Success

from src.contexts.coding.infra.config import EmbeddingConfig
from src.contexts.coding.infra.embedding_provider import (
    MockEmbeddingProvider,
    create_embedding_provider,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]

# ============================================================
# MockEmbeddingProvider Tests
# ============================================================


@allure.story("QC-028.11 Embedding Provider")
class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    @allure.title("Embed returns correct-dimension vector with values in range")
    def test_embed_returns_valid_vector(self) -> None:
        """Embed returns Success with correct-dimension vector, values in [-1, 1]."""
        provider = MockEmbeddingProvider(dimensions=384)
        result = provider.embed("test text")

        assert isinstance(result, Success)
        embedding = result.unwrap()
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert all(-1.0 <= x <= 1.0 for x in embedding)

    @allure.title("Same text produces same embedding; different texts differ")
    def test_deterministic_and_different(self) -> None:
        """Same text is deterministic; different texts produce different embeddings."""
        provider = MockEmbeddingProvider()
        r1 = provider.embed("test text")
        r2 = provider.embed("test text")
        assert r1.unwrap() == r2.unwrap()

        r3 = provider.embed("text one")
        r4 = provider.embed("text two")
        assert r3.unwrap() != r4.unwrap()

    @allure.title("Batch embed returns correct results including empty batch")
    def test_embed_batch(self) -> None:
        """Batch embed returns list of vectors; empty batch returns empty list."""
        provider = MockEmbeddingProvider(dimensions=384)
        texts = ["text one", "text two", "text three"]
        result = provider.embed_batch(texts)

        assert isinstance(result, Success)
        embeddings = result.unwrap()
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

        # Empty batch
        result2 = provider.embed_batch([])
        assert isinstance(result2, Success)
        assert result2.unwrap() == []

    @allure.title("Properties and call count tracking")
    def test_properties_and_call_count(self) -> None:
        """Dimensions, model_name properties; call count increments on embed."""
        provider = MockEmbeddingProvider(dimensions=768, model_name="test-model")
        assert provider.dimensions == 768
        assert provider.model_name == "test-model"
        assert provider.call_count == 0

        provider.embed("text 1")
        assert provider.call_count == 1

        provider.embed("text 2")
        assert provider.call_count == 2


# ============================================================
# EmbeddingConfig Tests
# ============================================================


@allure.story("QC-028.11 Embedding Provider")
class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    @allure.title(
        "Factory methods: default, for_testing, for_openai, for_ollama, for_local"
    )
    def test_factory_methods(self) -> None:
        """All factory methods create configs with correct settings."""
        # Default
        config = EmbeddingConfig()
        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"

        # for_testing
        config_test = EmbeddingConfig.for_testing()
        assert config_test.provider == "mock"

        # for_openai
        config_openai = EmbeddingConfig.for_openai("test-key", "text-embedding-3-small")
        assert config_openai.provider == "openai-compatible"
        assert config_openai.api_base_url == "https://api.openai.com/v1"
        assert config_openai.api_key == "test-key"
        assert config_openai.openai_model == "text-embedding-3-small"

        # for_ollama
        config_ollama = EmbeddingConfig.for_ollama("nomic-embed-text")
        assert config_ollama.provider == "openai-compatible"
        assert "11434" in config_ollama.api_base_url
        assert config_ollama.openai_model == "nomic-embed-text"

        # for_local
        config_local = EmbeddingConfig.for_local("all-MiniLM-L6-v2")
        assert config_local.provider == "minilm"
        assert config_local.minilm_model == "all-MiniLM-L6-v2"

    @allure.title("Config is immutable (frozen dataclass)")
    def test_immutable(self) -> None:
        """Config is immutable (frozen dataclass)."""
        config = EmbeddingConfig()
        with pytest.raises(AttributeError):
            config.provider = "mock"  # type: ignore


# ============================================================
# Factory Function Tests
# ============================================================


@allure.story("QC-028.11 Embedding Provider")
class TestCreateEmbeddingProvider:
    """Tests for create_embedding_provider factory."""

    @allure.title("Creates mock provider; raises for unknown provider")
    def test_creates_mock_and_rejects_unknown(self) -> None:
        """Factory creates MockEmbeddingProvider for mock; raises for unknown."""
        config = EmbeddingConfig.for_testing()
        provider = create_embedding_provider(config)
        assert isinstance(provider, MockEmbeddingProvider)

        # Unknown provider
        config_bad = EmbeddingConfig()
        object.__setattr__(config_bad, "provider", "unknown")
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_provider(config_bad)
