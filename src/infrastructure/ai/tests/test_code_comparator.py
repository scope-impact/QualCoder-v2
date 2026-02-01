"""
Tests for Code Comparator with VectorStore Integration

TDD tests for VectorCodeComparator that uses embeddings for fast
duplicate detection.
"""

from __future__ import annotations

import pytest
from returns.result import Success

from src.domain.ai_services.entities import DuplicateCandidate, SimilarityScore
from src.domain.coding.entities import Code, Color
from src.infrastructure.ai.code_comparator import (
    MockCodeComparator,
    VectorCodeComparator,
)
from src.infrastructure.ai.embedding_provider import MockEmbeddingProvider
from src.infrastructure.ai.vector_store import MockVectorStore

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> tuple[Code, ...]:
    """Create sample codes for testing."""
    return (
        Code(
            id=1,
            name="anxiety",
            color=Color.from_hex("#FF0000"),
            memo="Feelings of worry",
        ),
        Code(
            id=2,
            name="stress",
            color=Color.from_hex("#00FF00"),
            memo="Tension and pressure",
        ),
        Code(
            id=3,
            name="anxious feelings",
            color=Color.from_hex("#0000FF"),
            memo="Worry and nervousness",
        ),
        Code(
            id=4,
            name="happiness",
            color=Color.from_hex("#FFFF00"),
            memo="Positive emotions",
        ),
        Code(
            id=5,
            name="work pressure",
            color=Color.from_hex("#FF00FF"),
            memo="Job-related stress",
        ),
    )


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    """Create mock vector store."""
    return MockVectorStore()


@pytest.fixture
def mock_embedding_provider() -> MockEmbeddingProvider:
    """Create mock embedding provider."""
    return MockEmbeddingProvider(dimensions=384)


# ============================================================
# VectorCodeComparator Tests
# ============================================================


class TestVectorCodeComparator:
    """Tests for VectorCodeComparator."""

    def test_init_with_vector_store(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
    ) -> None:
        """Can initialize with vector store and embedding provider."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        assert comparator is not None

    def test_index_codes_adds_to_vector_store(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """index_codes adds all codes to vector store."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )

        result = comparator.index_codes(sample_codes)

        assert isinstance(result, Success)
        assert mock_vector_store.count() == 5

    def test_find_duplicates_returns_candidates(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """find_duplicates returns duplicate candidates."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        comparator.index_codes(sample_codes)

        result = comparator.find_duplicates(sample_codes, threshold=0.5)

        assert isinstance(result, Success)
        candidates = result.unwrap()
        assert isinstance(candidates, list)
        # Should find some candidates (mock returns deterministic results)

    def test_find_duplicates_respects_threshold(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """find_duplicates filters by threshold."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        comparator.index_codes(sample_codes)

        # High threshold should return fewer results
        high_result = comparator.find_duplicates(sample_codes, threshold=0.95)
        low_result = comparator.find_duplicates(sample_codes, threshold=0.1)

        high_candidates = high_result.unwrap()
        low_candidates = low_result.unwrap()

        assert len(high_candidates) <= len(low_candidates)

    def test_find_duplicates_returns_empty_for_single_code(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
    ) -> None:
        """find_duplicates returns empty list for single code."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        single_code = (Code(id=1, name="test", color=Color.from_hex("#FF0000")),)

        result = comparator.find_duplicates(single_code)

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_candidate_has_required_fields(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """Duplicate candidates have all required fields."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        comparator.index_codes(sample_codes)

        result = comparator.find_duplicates(sample_codes, threshold=0.1)
        candidates = result.unwrap()

        if candidates:
            candidate = candidates[0]
            assert hasattr(candidate, "code_a_id")
            assert hasattr(candidate, "code_a_name")
            assert hasattr(candidate, "code_b_id")
            assert hasattr(candidate, "code_b_name")
            assert hasattr(candidate, "similarity")
            assert hasattr(candidate, "rationale")
            assert hasattr(candidate, "status")

    def test_calculate_similarity_returns_float(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """calculate_similarity returns a float between 0 and 1."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )

        similarity = comparator.calculate_similarity(sample_codes[0], sample_codes[1])

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_sync_codes_updates_vector_store(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """sync_codes updates vector store with new codes."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )

        # Initial index
        comparator.index_codes(sample_codes[:3])
        assert mock_vector_store.count() == 3

        # Sync with more codes
        result = comparator.sync_codes(sample_codes)
        assert isinstance(result, Success)
        assert mock_vector_store.count() == 5

    def test_remove_code_from_index(
        self,
        mock_vector_store: MockVectorStore,
        mock_embedding_provider: MockEmbeddingProvider,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """Can remove a code from the index."""
        comparator = VectorCodeComparator(
            vector_store=mock_vector_store,
            embedding_provider=mock_embedding_provider,
        )
        comparator.index_codes(sample_codes)

        result = comparator.remove_code(sample_codes[0].id)

        assert isinstance(result, Success)
        assert mock_vector_store.count() == 4


# ============================================================
# MockCodeComparator Tests
# ============================================================


class TestMockCodeComparator:
    """Tests for MockCodeComparator."""

    def test_returns_predefined_duplicates(self) -> None:
        """Returns predefined duplicate candidates."""
        duplicates = [
            DuplicateCandidate(
                code_a_id=1,
                code_a_name="anxiety",
                code_b_id=3,
                code_b_name="anxious feelings",
                similarity=SimilarityScore(0.85),
                rationale="Both refer to anxiety",
                status="pending",
            )
        ]
        comparator = MockCodeComparator(duplicates=duplicates)

        result = comparator.find_duplicates((), threshold=0.8)

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 1

    def test_filters_by_threshold(self) -> None:
        """Filters duplicates by threshold."""
        duplicates = [
            DuplicateCandidate(
                code_a_id=1,
                code_a_name="a",
                code_b_id=2,
                code_b_name="b",
                similarity=SimilarityScore(0.9),
                rationale="High",
                status="pending",
            ),
            DuplicateCandidate(
                code_a_id=3,
                code_a_name="c",
                code_b_id=4,
                code_b_name="d",
                similarity=SimilarityScore(0.6),
                rationale="Low",
                status="pending",
            ),
        ]
        comparator = MockCodeComparator(duplicates=duplicates)

        result = comparator.find_duplicates((), threshold=0.8)

        assert len(result.unwrap()) == 1

    def test_tracks_call_count(self) -> None:
        """Tracks number of find_duplicates calls."""
        comparator = MockCodeComparator()
        assert comparator.call_count == 0

        comparator.find_duplicates(())
        comparator.find_duplicates(())

        assert comparator.call_count == 2
