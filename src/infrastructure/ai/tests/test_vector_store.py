"""
Tests for Vector Store

Tests the MockVectorStore and VectorStoreConfig.
ChromaVectorStore requires chromadb and is tested via integration tests.
"""

from __future__ import annotations

import pytest
from returns.result import Success

from src.infrastructure.ai.config import VectorStoreConfig
from src.infrastructure.ai.vector_store import MockVectorStore

# ============================================================
# MockVectorStore Tests
# ============================================================


class TestMockVectorStore:
    """Tests for MockVectorStore."""

    def test_add_items(self) -> None:
        """Can add items to the store."""
        store = MockVectorStore()

        result = store.add(
            ids=["1", "2"],
            texts=["hello world", "goodbye world"],
        )

        assert isinstance(result, Success)
        assert store.count() == 2

    def test_add_with_metadata(self) -> None:
        """Can add items with metadata."""
        store = MockVectorStore()

        result = store.add(
            ids=["1"],
            texts=["test text"],
            metadata=[{"type": "code", "name": "anxiety"}],
        )

        assert isinstance(result, Success)
        items = store.get(["1"]).unwrap()
        assert items[0]["metadata"]["type"] == "code"

    def test_add_empty_lists(self) -> None:
        """Adding empty lists returns Success."""
        store = MockVectorStore()
        result = store.add(ids=[], texts=[])

        assert isinstance(result, Success)
        assert store.count() == 0

    def test_query_returns_results(self) -> None:
        """Query returns stored items."""
        store = MockVectorStore()
        store.add(
            ids=["1", "2", "3"],
            texts=["first", "second", "third"],
        )

        result = store.query(query_text="test", n_results=2)

        assert isinstance(result, Success)
        results = result.unwrap()
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["text"] == "first"
        assert "distance" in results[0]

    def test_query_empty_store(self) -> None:
        """Query on empty store returns empty list."""
        store = MockVectorStore()
        result = store.query(query_text="test")

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_delete_items(self) -> None:
        """Can delete items by ID."""
        store = MockVectorStore()
        store.add(ids=["1", "2", "3"], texts=["a", "b", "c"])

        result = store.delete(["1", "3"])

        assert isinstance(result, Success)
        assert store.count() == 1
        assert store.get(["2"]).unwrap()[0]["text"] == "b"

    def test_delete_nonexistent(self) -> None:
        """Deleting nonexistent IDs doesn't fail."""
        store = MockVectorStore()
        store.add(ids=["1"], texts=["test"])

        result = store.delete(["nonexistent"])

        assert isinstance(result, Success)
        assert store.count() == 1

    def test_get_items(self) -> None:
        """Can get items by ID."""
        store = MockVectorStore()
        store.add(
            ids=["1", "2"],
            texts=["first", "second"],
            metadata=[{"idx": 1}, {"idx": 2}],
        )

        result = store.get(["2"])

        assert isinstance(result, Success)
        items = result.unwrap()
        assert len(items) == 1
        assert items[0]["id"] == "2"
        assert items[0]["text"] == "second"
        assert items[0]["metadata"]["idx"] == 2

    def test_get_nonexistent(self) -> None:
        """Getting nonexistent IDs returns empty list."""
        store = MockVectorStore()
        result = store.get(["nonexistent"])

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_count(self) -> None:
        """Count returns number of items."""
        store = MockVectorStore()
        assert store.count() == 0

        store.add(ids=["1", "2", "3"], texts=["a", "b", "c"])
        assert store.count() == 3

        store.delete(["1"])
        assert store.count() == 2

    def test_clear(self) -> None:
        """Clear removes all items."""
        store = MockVectorStore()
        store.add(ids=["1", "2"], texts=["a", "b"])

        result = store.clear()

        assert isinstance(result, Success)
        assert store.count() == 0

    def test_call_counts(self) -> None:
        """Call counts track method invocations."""
        store = MockVectorStore()

        store.add(ids=["1"], texts=["a"])
        store.add(ids=["2"], texts=["b"])
        store.query(query_text="test")
        store.get(["1"])
        store.delete(["1"])

        counts = store.call_counts
        assert counts["add"] == 2
        assert counts["query"] == 1
        assert counts["get"] == 1
        assert counts["delete"] == 1

    def test_upsert_behavior(self) -> None:
        """Adding same ID updates the item."""
        store = MockVectorStore()
        store.add(ids=["1"], texts=["original"])
        store.add(ids=["1"], texts=["updated"])

        result = store.get(["1"]).unwrap()
        assert result[0]["text"] == "updated"
        assert store.count() == 1


# ============================================================
# VectorStoreConfig Tests
# ============================================================


class TestVectorStoreConfig:
    """Tests for VectorStoreConfig."""

    def test_default_config(self) -> None:
        """Default config uses in-memory storage."""
        config = VectorStoreConfig()
        assert config.persist_directory is None
        assert config.collection_name == "qualcoder_codes"
        assert config.distance_metric == "cosine"

    def test_for_testing(self) -> None:
        """for_testing creates in-memory config."""
        config = VectorStoreConfig.for_testing()
        assert config.persist_directory is None
        assert config.collection_name == "test_collection"

    def test_for_project(self) -> None:
        """for_project creates persistent config."""
        config = VectorStoreConfig.for_project("/path/to/project", "my_codes")
        assert config.persist_directory == "/path/to/project/.qualcoder/vectors"
        assert config.collection_name == "my_codes"

    def test_immutable(self) -> None:
        """Config is immutable (frozen dataclass)."""
        config = VectorStoreConfig()
        with pytest.raises(AttributeError):
            config.collection_name = "other"  # type: ignore
