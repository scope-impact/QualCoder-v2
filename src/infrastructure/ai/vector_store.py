"""
AI Infrastructure: Vector Store Implementation

ChromaDB-based vector storage for semantic search and similarity operations.
Supports both persistent and in-memory storage modes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.infrastructure.ai.config import EmbeddingConfig, VectorStoreConfig
    from src.infrastructure.ai.embedding_provider import (
        MiniLMEmbeddingProvider,
        MockEmbeddingProvider,
        OpenAICompatibleEmbeddingProvider,
    )

logger = logging.getLogger(__name__)


# Type alias for embedding providers
EmbeddingProviderType = "OpenAICompatibleEmbeddingProvider | MiniLMEmbeddingProvider | MockEmbeddingProvider"


# ============================================================
# ChromaDB Vector Store
# ============================================================


class ChromaVectorStore:
    """
    Vector store implementation using ChromaDB.

    Provides persistent or in-memory vector storage with
    efficient similarity search using embeddings.
    """

    def __init__(
        self,
        config: VectorStoreConfig,
        embedding_provider: (
            OpenAICompatibleEmbeddingProvider
            | MiniLMEmbeddingProvider
            | MockEmbeddingProvider
        ),
    ) -> None:
        """
        Initialize the ChromaDB vector store.

        Args:
            config: Vector store configuration
            embedding_provider: Provider for generating embeddings

        Raises:
            ImportError: If chromadb is not installed
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as e:
            raise ImportError(
                "chromadb is required for vector storage. "
                "Install with: pip install chromadb"
            ) from e

        self._config = config
        self._embedding_provider = embedding_provider

        # Initialize ChromaDB client
        if config.persist_directory:
            logger.info(
                f"Initializing persistent ChromaDB at: {config.persist_directory}"
            )
            self._client = chromadb.PersistentClient(
                path=config.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            logger.info("Initializing in-memory ChromaDB")
            self._client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False),
            )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": config.distance_metric},
        )

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]] | None = None,
        metadata: list[dict] | None = None,
    ) -> Result[None, str]:
        """
        Add items to the vector store.

        Args:
            ids: Unique identifiers for each item
            texts: Text content for each item
            embeddings: Pre-computed embeddings (computed if not provided)
            metadata: Optional metadata for each item

        Returns:
            Success or Failure with error message
        """
        if not ids or not texts:
            return Success(None)

        if len(ids) != len(texts):
            return Failure(
                f"ids ({len(ids)}) and texts ({len(texts)}) must have same length"
            )

        try:
            # Generate embeddings if not provided
            if embeddings is None:
                result = self._embedding_provider.embed_batch(texts)
                if isinstance(result, Failure):
                    return result
                embeddings = result.unwrap()

            # Prepare metadata
            if metadata is None:
                metadata = [{} for _ in ids]

            # Add to collection in batches
            batch_size = self._config.batch_size
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                batch_texts = texts[i : i + batch_size]
                batch_embeddings = embeddings[i : i + batch_size]
                batch_metadata = metadata[i : i + batch_size]

                self._collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadata,
                )

            return Success(None)

        except Exception as e:
            logger.exception("Failed to add items to vector store")
            return Failure(f"Failed to add items: {e}")

    def query(
        self,
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        n_results: int = 10,
        where: dict | None = None,
    ) -> Result[list[dict], str]:
        """
        Query for similar items.

        Args:
            query_text: Text to search for (will be embedded)
            query_embedding: Pre-computed query embedding
            n_results: Maximum number of results
            where: Optional metadata filter

        Returns:
            Success with list of results containing id, text, distance, metadata
        """
        if query_text is None and query_embedding is None:
            return Failure("Either query_text or query_embedding must be provided")

        try:
            # Generate embedding for query text if needed
            if query_embedding is None and query_text is not None:
                result = self._embedding_provider.embed(query_text)
                if isinstance(result, Failure):
                    return result
                query_embedding = result.unwrap()

            # Query collection
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, self._collection.count() or n_results),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, item_id in enumerate(results["ids"][0]):
                    formatted.append(
                        {
                            "id": item_id,
                            "text": results["documents"][0][i]
                            if results["documents"]
                            else None,
                            "distance": results["distances"][0][i]
                            if results["distances"]
                            else None,
                            "metadata": results["metadatas"][0][i]
                            if results["metadatas"]
                            else {},
                        }
                    )

            return Success(formatted)

        except Exception as e:
            logger.exception("Failed to query vector store")
            return Failure(f"Query failed: {e}")

    def delete(self, ids: list[str]) -> Result[None, str]:
        """
        Delete items by ID.

        Args:
            ids: IDs of items to delete

        Returns:
            Success or Failure with error message
        """
        if not ids:
            return Success(None)

        try:
            self._collection.delete(ids=ids)
            return Success(None)
        except Exception as e:
            logger.exception("Failed to delete items from vector store")
            return Failure(f"Delete failed: {e}")

    def get(self, ids: list[str]) -> Result[list[dict], str]:
        """
        Get items by ID.

        Args:
            ids: IDs of items to retrieve

        Returns:
            Success with list of items containing id, text, embedding, metadata
        """
        if not ids:
            return Success([])

        try:
            results = self._collection.get(
                ids=ids,
                include=["documents", "embeddings", "metadatas"],
            )

            formatted = []
            if results["ids"]:
                for i, item_id in enumerate(results["ids"]):
                    formatted.append(
                        {
                            "id": item_id,
                            "text": results["documents"][i]
                            if results["documents"]
                            else None,
                            "embedding": results["embeddings"][i]
                            if results["embeddings"]
                            else None,
                            "metadata": results["metadatas"][i]
                            if results["metadatas"]
                            else {},
                        }
                    )

            return Success(formatted)

        except Exception as e:
            logger.exception("Failed to get items from vector store")
            return Failure(f"Get failed: {e}")

    def count(self) -> int:
        """Return the number of items in the store."""
        return self._collection.count()

    def clear(self) -> Result[None, str]:
        """Remove all items from the store."""
        try:
            # Delete and recreate collection
            self._client.delete_collection(self._config.collection_name)
            self._collection = self._client.create_collection(
                name=self._config.collection_name,
                metadata={"hnsw:space": self._config.distance_metric},
            )
            return Success(None)
        except Exception as e:
            logger.exception("Failed to clear vector store")
            return Failure(f"Clear failed: {e}")


# ============================================================
# Mock Vector Store (for testing)
# ============================================================


class MockVectorStore:
    """
    Mock vector store for testing.

    Uses in-memory dict storage without ChromaDB dependency.
    """

    def __init__(self) -> None:
        """Initialize empty mock store."""
        self._items: dict[str, dict] = {}
        self._call_counts = {
            "add": 0,
            "query": 0,
            "delete": 0,
            "get": 0,
        }

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]] | None = None,
        metadata: list[dict] | None = None,
    ) -> Result[None, str]:
        """Add items to mock store."""
        self._call_counts["add"] += 1

        if not ids or not texts:
            return Success(None)

        if embeddings is None:
            embeddings = [[0.0] * 384 for _ in ids]  # Mock embeddings

        if metadata is None:
            metadata = [{} for _ in ids]

        for i, item_id in enumerate(ids):
            self._items[item_id] = {
                "id": item_id,
                "text": texts[i],
                "embedding": embeddings[i] if i < len(embeddings) else [0.0] * 384,
                "metadata": metadata[i] if i < len(metadata) else {},
            }

        return Success(None)

    def query(
        self,
        query_text: str | None = None,  # noqa: ARG002
        query_embedding: list[float] | None = None,  # noqa: ARG002
        n_results: int = 10,
        where: dict | None = None,  # noqa: ARG002
    ) -> Result[list[dict], str]:
        """Return mock query results (returns first n items)."""
        self._call_counts["query"] += 1

        results = []
        for i, (item_id, item) in enumerate(self._items.items()):
            if i >= n_results:
                break
            results.append(
                {
                    "id": item_id,
                    "text": item["text"],
                    "distance": 0.1 * (i + 1),  # Mock distances
                    "metadata": item["metadata"],
                }
            )

        return Success(results)

    def delete(self, ids: list[str]) -> Result[None, str]:
        """Delete items from mock store."""
        self._call_counts["delete"] += 1

        for item_id in ids:
            self._items.pop(item_id, None)

        return Success(None)

    def get(self, ids: list[str]) -> Result[list[dict], str]:
        """Get items by ID from mock store."""
        self._call_counts["get"] += 1

        results = []
        for item_id in ids:
            if item_id in self._items:
                results.append(self._items[item_id])

        return Success(results)

    def count(self) -> int:
        """Return number of items in mock store."""
        return len(self._items)

    def clear(self) -> Result[None, str]:
        """Clear all items from mock store."""
        self._items.clear()
        return Success(None)

    @property
    def call_counts(self) -> dict[str, int]:
        """Return call counts for each method."""
        return self._call_counts.copy()


# ============================================================
# Factory Function
# ============================================================


def create_vector_store(
    config: VectorStoreConfig,
    embedding_config: EmbeddingConfig,
) -> ChromaVectorStore | MockVectorStore:
    """
    Create a vector store with configured embedding provider.

    Args:
        config: Vector store configuration
        embedding_config: Embedding provider configuration

    Returns:
        Configured vector store instance
    """
    from src.infrastructure.ai.embedding_provider import create_embedding_provider

    if embedding_config.provider == "mock":
        return MockVectorStore()

    embedding_provider = create_embedding_provider(embedding_config)
    return ChromaVectorStore(config, embedding_provider)
