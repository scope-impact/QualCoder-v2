"""
Tests for Vector Store

Tests the MockVectorStore and VectorStoreConfig.
ChromaVectorStore requires chromadb and is tested via integration tests.
"""

from __future__ import annotations

import allure
import pytest
from returns.result import Success

from src.contexts.coding.infra.config import VectorStoreConfig
from src.contexts.coding.infra.vector_store import MockVectorStore

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]

# ============================================================
# MockVectorStore Tests
# ============================================================


@allure.story("QC-028.10 Vector Store")
class TestMockVectorStore:
    """Tests for MockVectorStore."""

    @allure.title("Add items with and without metadata, including empty lists")
    def test_add_items_with_metadata_and_empty(self) -> None:
        """Can add items, items with metadata, and empty lists."""
        store = MockVectorStore()

        # Add basic items
        result = store.add(ids=["1", "2"], texts=["hello world", "goodbye world"])
        assert isinstance(result, Success)
        assert store.count() == 2

        # Add with metadata
        store2 = MockVectorStore()
        result2 = store2.add(
            ids=["1"],
            texts=["test text"],
            metadata=[{"type": "code", "name": "anxiety"}],
        )
        assert isinstance(result2, Success)
        items = store2.get(["1"]).unwrap()
        assert items[0]["metadata"]["type"] == "code"

        # Add empty lists
        store3 = MockVectorStore()
        result3 = store3.add(ids=[], texts=[])
        assert isinstance(result3, Success)
        assert store3.count() == 0

    @allure.title("Query returns results from store and empty from empty store")
    def test_query_results_and_empty(self) -> None:
        """Query returns stored items; empty store returns empty list."""
        store = MockVectorStore()
        store.add(ids=["1", "2", "3"], texts=["first", "second", "third"])

        result = store.query(query_text="test", n_results=2)
        assert isinstance(result, Success)
        results = result.unwrap()
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["text"] == "first"
        assert "distance" in results[0]

        # Empty store
        empty_store = MockVectorStore()
        result2 = empty_store.query(query_text="test")
        assert isinstance(result2, Success)
        assert result2.unwrap() == []

    @allure.title("Delete items by ID including nonexistent IDs")
    def test_delete_items_and_nonexistent(self) -> None:
        """Can delete items by ID; nonexistent IDs don't fail."""
        store = MockVectorStore()
        store.add(ids=["1", "2", "3"], texts=["a", "b", "c"])

        result = store.delete(["1", "3"])
        assert isinstance(result, Success)
        assert store.count() == 1
        assert store.get(["2"]).unwrap()[0]["text"] == "b"

        # Nonexistent
        result2 = store.delete(["nonexistent"])
        assert isinstance(result2, Success)
        assert store.count() == 1

    @allure.title("Get items by ID including nonexistent IDs")
    def test_get_items_and_nonexistent(self) -> None:
        """Can get items by ID; nonexistent returns empty."""
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

        # Nonexistent
        result2 = store.get(["nonexistent"])
        assert isinstance(result2, Success)
        assert result2.unwrap() == []

    @allure.title("Count, clear, and upsert behavior")
    def test_count_clear_and_upsert(self) -> None:
        """Count tracks items; clear removes all; adding same ID updates."""
        store = MockVectorStore()
        assert store.count() == 0

        store.add(ids=["1", "2", "3"], texts=["a", "b", "c"])
        assert store.count() == 3

        store.delete(["1"])
        assert store.count() == 2

        # Clear
        result = store.clear()
        assert isinstance(result, Success)
        assert store.count() == 0

        # Upsert
        store.add(ids=["1"], texts=["original"])
        store.add(ids=["1"], texts=["updated"])
        result2 = store.get(["1"]).unwrap()
        assert result2[0]["text"] == "updated"
        assert store.count() == 1

    @allure.title("Call counts track method invocations")
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


# ============================================================
# VectorStoreConfig Tests
# ============================================================


@allure.story("QC-028.10 Vector Store")
class TestVectorStoreConfig:
    """Tests for VectorStoreConfig."""

    @allure.title("Default, for_testing, and for_project factory methods")
    def test_factory_methods(self) -> None:
        """Default uses in-memory; for_testing creates test config; for_project creates persistent config."""
        # Default
        config = VectorStoreConfig()
        assert config.persist_directory is None
        assert config.collection_name == "qualcoder_codes"
        assert config.distance_metric == "cosine"

        # for_testing
        config_test = VectorStoreConfig.for_testing()
        assert config_test.persist_directory is None
        assert config_test.collection_name == "test_collection"

        # for_project
        config_proj = VectorStoreConfig.for_project("/path/to/project", "my_codes")
        assert config_proj.persist_directory == "/path/to/project/.qualcoder/vectors"
        assert config_proj.collection_name == "my_codes"

    @allure.title("Config is immutable (frozen dataclass)")
    def test_immutable(self) -> None:
        """Config is immutable (frozen dataclass)."""
        config = VectorStoreConfig()
        with pytest.raises(AttributeError):
            config.collection_name = "other"  # type: ignore
