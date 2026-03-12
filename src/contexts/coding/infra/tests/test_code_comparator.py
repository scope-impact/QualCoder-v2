"""Tests for Code Comparator with VectorStore Integration."""

from __future__ import annotations

import allure
import pytest
from returns.result import Success

from src.contexts.coding.core.ai_entities import DuplicateCandidate, SimilarityScore
from src.contexts.coding.core.entities import Code, Color
from src.contexts.coding.infra.code_comparator import (
    MockCodeComparator,
    VectorCodeComparator,
)
from src.contexts.coding.infra.embedding_provider import MockEmbeddingProvider
from src.contexts.coding.infra.vector_store import MockVectorStore
from src.shared.common.types import CodeId

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> tuple[Code, ...]:
    """Create sample codes for testing."""
    return (
        Code(id=CodeId(value="1"), name="anxiety", color=Color.from_hex("#FF0000"), memo="Feelings of worry"),
        Code(id=CodeId(value="2"), name="stress", color=Color.from_hex("#00FF00"), memo="Tension and pressure"),
        Code(id=CodeId(value="3"), name="anxious feelings", color=Color.from_hex("#0000FF"), memo="Worry and nervousness"),
        Code(id=CodeId(value="4"), name="happiness", color=Color.from_hex("#FFFF00"), memo="Positive emotions"),
        Code(id=CodeId(value="5"), name="work pressure", color=Color.from_hex("#FF00FF"), memo="Job-related stress"),
    )


@pytest.fixture
def comparator() -> VectorCodeComparator:
    """Create a VectorCodeComparator with mock dependencies."""
    return VectorCodeComparator(
        vector_store=MockVectorStore(),
        embedding_provider=MockEmbeddingProvider(dimensions=384),
    )


# ============================================================
# VectorCodeComparator Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.09 Agent Detect Duplicates")
class TestVectorCodeComparator:
    """Tests for VectorCodeComparator."""

    @allure.title("index_codes, find_duplicates with thresholds, single code, and similarity")
    def test_index_find_duplicates_and_similarity(
        self,
        comparator: VectorCodeComparator,
        sample_codes: tuple[Code, ...],
    ) -> None:
        # Index codes
        result = comparator.index_codes(sample_codes)
        assert isinstance(result, Success)
        assert comparator._store.count() == 5

        # find_duplicates respects threshold
        high_result = comparator.find_duplicates(sample_codes, threshold=0.95)
        low_result = comparator.find_duplicates(sample_codes, threshold=0.1)
        assert isinstance(high_result, Success)
        assert isinstance(low_result, Success)
        assert len(high_result.unwrap()) <= len(low_result.unwrap())

        for candidate in low_result.unwrap():
            assert hasattr(candidate, "code_a_id")
            assert hasattr(candidate, "code_b_id")
            assert hasattr(candidate, "similarity")

        # Single code returns empty
        single_code = (Code(id=CodeId(value="1"), name="test", color=Color.from_hex("#FF0000")),)
        result = comparator.find_duplicates(single_code)
        assert isinstance(result, Success)
        assert result.unwrap() == []

        # calculate_similarity returns float between 0 and 1
        similarity = comparator.calculate_similarity(sample_codes[0], sample_codes[1])
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    @allure.title("sync_codes updates and remove_code shrinks vector store")
    def test_sync_and_remove_codes(
        self,
        comparator: VectorCodeComparator,
        sample_codes: tuple[Code, ...],
    ) -> None:
        comparator.index_codes(sample_codes[:3])
        assert comparator._store.count() == 3

        result = comparator.sync_codes(sample_codes)
        assert isinstance(result, Success)
        assert comparator._store.count() == 5

        result = comparator.remove_code(sample_codes[0].id)
        assert isinstance(result, Success)
        assert comparator._store.count() == 4


# ============================================================
# MockCodeComparator Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.09 Agent Detect Duplicates")
class TestMockCodeComparator:
    """Tests for MockCodeComparator."""

    @allure.title("Returns predefined duplicates filtered by threshold and tracks calls")
    def test_returns_filtered_duplicates_and_tracks_calls(self) -> None:
        duplicates = [
            DuplicateCandidate(
                code_a_id=CodeId(value="1"), code_a_name="a",
                code_b_id=CodeId(value="2"), code_b_name="b",
                similarity=SimilarityScore(0.9), rationale="High", status="pending",
            ),
            DuplicateCandidate(
                code_a_id=CodeId(value="3"), code_a_name="c",
                code_b_id=CodeId(value="4"), code_b_name="d",
                similarity=SimilarityScore(0.6), rationale="Low", status="pending",
            ),
        ]
        comparator = MockCodeComparator(duplicates=duplicates)
        assert comparator.call_count == 0

        result = comparator.find_duplicates((), threshold=0.8)
        assert len(result.unwrap()) == 1

        comparator.find_duplicates(())
        assert comparator.call_count == 2
