"""
AI Infrastructure: Embedding Providers

Implementations of the EmbeddingProvider protocol for generating
text embeddings for semantic similarity operations.

Supports:
- OpenAI-compatible APIs (OpenAI, Azure, Ollama, LM Studio, vLLM)
- Local sentence-transformers (MiniLM)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.contexts.coding.infra.config import EmbeddingConfig

logger = logging.getLogger(__name__)


# ============================================================
# OpenAI-Compatible Embedding Provider
# ============================================================


class OpenAICompatibleEmbeddingProvider:
    """
    Embedding provider using OpenAI-compatible API.

    Works with:
    - OpenAI API (api.openai.com)
    - Azure OpenAI
    - Ollama (localhost:11434/v1)
    - LM Studio
    - vLLM
    - Any server exposing /v1/embeddings endpoint
    """

    def __init__(self, config: EmbeddingConfig) -> None:
        """
        Initialize the OpenAI-compatible embedding provider.

        Args:
            config: Embedding configuration with API settings
        """
        self._config = config
        self._base_url = config.api_base_url.rstrip("/")
        self._api_key = config.api_key
        self._model = config.openai_model
        self._dimensions: int | None = None

    def embed(self, text: str) -> Result[list[float], str]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Success with embedding vector, or Failure with error
        """
        result = self.embed_batch([text])
        if isinstance(result, Failure):
            return result
        embeddings = result.unwrap()
        return Success(embeddings[0])

    def embed_batch(
        self,
        texts: list[str],
    ) -> Result[list[list[float]], str]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Success with list of embedding vectors, or Failure with error
        """
        import httpx

        if not texts:
            return Success([])

        url = f"{self._base_url}/embeddings"

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "input": texts,
        }

        try:
            with httpx.Client(timeout=self._config.timeout_seconds) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]

                # Cache dimensions from first response
                if embeddings and self._dimensions is None:
                    self._dimensions = len(embeddings[0])

                return Success(embeddings)

        except httpx.TimeoutException:
            return Failure(
                f"Embedding request timed out after {self._config.timeout_seconds}s"
            )
        except httpx.HTTPStatusError as e:
            return Failure(
                f"Embedding API error: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            logger.exception("Embedding request failed")
            return Failure(f"Embedding request failed: {e}")

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions (fetches if unknown)."""
        if self._dimensions is None:
            # Fetch dimensions by embedding a test string
            result = self.embed("test")
            if isinstance(result, Success):
                self._dimensions = len(result.unwrap())
            else:
                # Default dimensions for common models
                defaults = {
                    "text-embedding-3-small": 1536,
                    "text-embedding-3-large": 3072,
                    "text-embedding-ada-002": 1536,
                    "nomic-embed-text": 768,
                    "all-minilm": 384,
                }
                self._dimensions = defaults.get(self._model, 768)
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model


# ============================================================
# MiniLM Local Embedding Provider
# ============================================================


class MiniLMEmbeddingProvider:
    """
    Embedding provider using local sentence-transformers.

    Uses the all-MiniLM-L6-v2 model by default, which provides
    good quality embeddings with low latency and no API calls.

    Requires: pip install sentence-transformers
    """

    def __init__(self, config: EmbeddingConfig) -> None:
        """
        Initialize the MiniLM embedding provider.

        Args:
            config: Embedding configuration with model settings

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        self._config = config
        self._model_name = config.minilm_model
        self._model = None  # Lazy load

    def _get_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for MiniLM embeddings. "
                    "Install with: pip install sentence-transformers"
                ) from e

            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, text: str) -> Result[list[float], str]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Success with embedding vector, or Failure with error
        """
        try:
            model = self._get_model()
            embedding = model.encode(text, convert_to_numpy=True)
            return Success(embedding.tolist())
        except Exception as e:
            logger.exception("MiniLM embedding failed")
            return Failure(f"Embedding failed: {e}")

    def embed_batch(
        self,
        texts: list[str],
    ) -> Result[list[list[float]], str]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Success with list of embedding vectors, or Failure with error
        """
        if not texts:
            return Success([])

        try:
            model = self._get_model()
            embeddings = model.encode(
                texts, convert_to_numpy=True, batch_size=self._config.batch_size
            )
            return Success([e.tolist() for e in embeddings])
        except Exception as e:
            logger.exception("MiniLM batch embedding failed")
            return Failure(f"Batch embedding failed: {e}")

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model_name


# ============================================================
# Mock Embedding Provider (for testing)
# ============================================================


class MockEmbeddingProvider:
    """
    Mock embedding provider for testing.

    Returns deterministic embeddings based on text hash.
    """

    def __init__(
        self,
        dimensions: int = 384,
        model_name: str = "mock-embedding-model",
    ) -> None:
        """
        Initialize mock provider.

        Args:
            dimensions: Number of dimensions for embeddings
            model_name: Name to report for the model
        """
        self._dimensions = dimensions
        self._model_name = model_name
        self._call_count = 0

    def embed(
        self,
        text: str,  # noqa: ARG002
    ) -> Result[list[float], str]:
        """Return a deterministic mock embedding."""
        self._call_count += 1
        # Generate deterministic embedding from text hash
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to floats between -1 and 1
        embedding = []
        for i in range(self._dimensions):
            byte_val = hash_bytes[i % len(hash_bytes)]
            embedding.append((byte_val / 127.5) - 1.0)
        return Success(embedding)

    def embed_batch(
        self,
        texts: list[str],
    ) -> Result[list[list[float]], str]:
        """Return mock embeddings for batch."""
        embeddings = []
        for text in texts:
            result = self.embed(text)
            if isinstance(result, Failure):
                return result
            embeddings.append(result.unwrap())
        return Success(embeddings)

    @property
    def dimensions(self) -> int:
        """Return configured dimensions."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Return configured model name."""
        return self._model_name

    @property
    def call_count(self) -> int:
        """Return number of embed calls made."""
        return self._call_count


# ============================================================
# Factory Function
# ============================================================


def create_embedding_provider(
    config: EmbeddingConfig,
) -> (
    OpenAICompatibleEmbeddingProvider | MiniLMEmbeddingProvider | MockEmbeddingProvider
):
    """
    Create an embedding provider based on configuration.

    Args:
        config: Embedding configuration

    Returns:
        Configured embedding provider instance

    Raises:
        ValueError: If provider type is unknown
    """
    match config.provider:
        case "openai-compatible":
            return OpenAICompatibleEmbeddingProvider(config)
        case "minilm":
            return MiniLMEmbeddingProvider(config)
        case "mock":
            return MockEmbeddingProvider()
        case _:
            raise ValueError(f"Unknown embedding provider: {config.provider}")
