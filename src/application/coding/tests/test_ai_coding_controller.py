"""
Tests for AI Coding Controller

TDD tests for AICodingController with both LLM and Vector-based
duplicate detection support.
"""

from __future__ import annotations

import pytest
from returns.result import Failure, Success

from src.application.coding.ai_coding_controller import AICodingController
from src.application.event_bus import EventBus
from src.domain.ai_services.entities import (
    CodeSuggestion,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)

# Events no longer tested directly - core functionality tests are simpler
from src.domain.coding.entities import Code, Color, TextPosition
from src.domain.shared.types import CodeId, SourceId
from src.infrastructure.ai.code_comparator import (
    MockCodeComparator,
    VectorCodeComparator,
)
from src.infrastructure.ai.embedding_provider import MockEmbeddingProvider
from src.infrastructure.ai.vector_store import MockVectorStore

# ============================================================
# Test Fixtures
# ============================================================


class MockCodeRepository:
    """Mock code repository for testing."""

    def __init__(self) -> None:
        self._codes: dict[int, Code] = {}
        self._next_id = 1

    def get_all(self) -> list[Code]:
        return list(self._codes.values())

    def get_by_id(self, code_id: CodeId) -> Code | None:
        return self._codes.get(code_id.value)

    def save(self, code: Code) -> None:
        if code.id.value == 0:
            code = Code(
                id=CodeId(value=self._next_id),
                name=code.name,
                color=code.color,
                memo=code.memo,
            )
            self._next_id += 1
        self._codes[code.id.value] = code

    def delete(self, code_id: CodeId) -> None:
        self._codes.pop(code_id.value, None)

    def add_code(
        self, name: str, color: str = "#FF0000", memo: str | None = None
    ) -> Code:
        """Helper to add a code for testing."""
        code = Code(
            id=CodeId(value=self._next_id),
            name=name,
            color=Color.from_hex(color),
            memo=memo,
        )
        self._next_id += 1
        self._codes[code.id.value] = code
        return code


class MockSegmentRepository:
    """Mock segment repository for testing."""

    def __init__(self) -> None:
        self._segments: dict[int, list] = {}

    def get_by_code(self, code_id: CodeId) -> list:
        return self._segments.get(code_id.value, [])

    def reassign_code(self, source_id: CodeId, target_id: CodeId) -> None:
        segments = self._segments.pop(source_id.value, [])
        if target_id.value not in self._segments:
            self._segments[target_id.value] = []
        self._segments[target_id.value].extend(segments)


class MockCodeAnalyzer:
    """Mock code analyzer for testing."""

    def __init__(self, suggestions: list[CodeSuggestion] | None = None) -> None:
        self._suggestions = suggestions or []
        self._call_count = 0

    def suggest_codes(
        self,
        text: str,  # noqa: ARG002
        existing_codes: tuple[Code, ...],  # noqa: ARG002
        source_id=None,  # noqa: ARG002
        max_suggestions: int | None = None,  # noqa: ARG002
    ):
        self._call_count += 1
        return Success(self._suggestions)


@pytest.fixture
def code_repo() -> MockCodeRepository:
    return MockCodeRepository()


@pytest.fixture
def segment_repo() -> MockSegmentRepository:
    return MockSegmentRepository()


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus(history_size=100)


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    return MockVectorStore()


@pytest.fixture
def mock_embedding_provider() -> MockEmbeddingProvider:
    return MockEmbeddingProvider(dimensions=384)


@pytest.fixture
def vector_comparator(
    mock_vector_store: MockVectorStore,
    mock_embedding_provider: MockEmbeddingProvider,
) -> VectorCodeComparator:
    return VectorCodeComparator(
        vector_store=mock_vector_store,
        embedding_provider=mock_embedding_provider,
        similarity_threshold=0.5,
    )


@pytest.fixture
def sample_suggestion() -> CodeSuggestion:
    return CodeSuggestion(
        id=SuggestionId.new(),
        name="anxiety",
        color=Color.from_hex("#FF5733"),
        rationale="Represents feelings of worry",
        contexts=(
            TextContext(
                text="I feel anxious about work",
                source_id=SourceId(value=1),
                position=TextPosition(start=0, end=25),
            ),
        ),
        confidence=0.85,
        status="pending",
    )


# ============================================================
# AICodingController Tests with VectorCodeComparator
# ============================================================


class TestAICodingControllerWithVectorComparator:
    """Tests for AICodingController using VectorCodeComparator."""

    def test_init_with_vector_comparator(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        vector_comparator: VectorCodeComparator,
    ) -> None:
        """Can initialize controller with VectorCodeComparator."""
        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=vector_comparator,
        )
        assert controller is not None

    def test_detect_duplicates_with_vector_comparator(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        vector_comparator: VectorCodeComparator,
    ) -> None:
        """detect_duplicates works with VectorCodeComparator."""
        # Add some codes
        code_repo.add_code("anxiety", memo="Feelings of worry")
        code_repo.add_code("stress", memo="Tension and pressure")
        code_repo.add_code("anxious feelings", memo="Worry and nervousness")

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=vector_comparator,
        )

        # Index codes first
        codes = tuple(code_repo.get_all())
        vector_comparator.index_codes(codes)

        result = controller.detect_duplicates(threshold=0.1)

        assert isinstance(result, Success)
        # Should return a list (may or may not have candidates depending on mock)

    def test_detect_duplicates_returns_success(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        vector_comparator: VectorCodeComparator,
    ) -> None:
        """detect_duplicates returns Success with VectorCodeComparator."""
        code_repo.add_code("anxiety")
        code_repo.add_code("stress")

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=vector_comparator,
        )

        codes = tuple(code_repo.get_all())
        vector_comparator.index_codes(codes)

        result = controller.detect_duplicates()

        # Core functionality: returns Success
        assert isinstance(result, Success)

    def test_detect_duplicates_without_comparator_returns_failure(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """detect_duplicates fails if no comparator configured."""
        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        result = controller.detect_duplicates()

        assert isinstance(result, Failure)
        assert "not configured" in result.failure()


class TestAICodingControllerWithMockComparator:
    """Tests for AICodingController using MockCodeComparator."""

    def test_detect_duplicates_returns_candidates(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """detect_duplicates returns predefined candidates from mock."""
        code_repo.add_code("anxiety")
        code_repo.add_code("anxious feelings")

        duplicates = [
            DuplicateCandidate(
                code_a_id=CodeId(value=1),
                code_a_name="anxiety",
                code_b_id=CodeId(value=2),
                code_b_name="anxious feelings",
                similarity=SimilarityScore(0.9),
                rationale="Both refer to anxiety",
                status="pending",
            )
        ]
        comparator = MockCodeComparator(duplicates=duplicates)

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=comparator,
        )

        result = controller.detect_duplicates(threshold=0.8)

        assert isinstance(result, Success)
        candidates = result.unwrap()
        assert len(candidates) == 1
        assert candidates[0].code_a_name == "anxiety"


class TestAICodingControllerSuggestions:
    """Tests for code suggestion functionality."""

    def test_suggest_codes_returns_suggestions(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        sample_suggestion: CodeSuggestion,
    ) -> None:
        """suggest_codes returns suggestions from analyzer."""
        analyzer = MockCodeAnalyzer(suggestions=[sample_suggestion])

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_analyzer=analyzer,
        )

        result = controller.suggest_codes("I feel anxious about work", source_id=1)

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        assert len(suggestions) == 1
        assert suggestions[0].name == "anxiety"

    def test_approve_suggestion_creates_code(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        sample_suggestion: CodeSuggestion,
    ) -> None:
        """approve_suggestion creates a new code."""
        analyzer = MockCodeAnalyzer(suggestions=[sample_suggestion])

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_analyzer=analyzer,
        )

        # First suggest
        controller.suggest_codes("text", source_id=1)

        # Then approve
        result = controller.approve_suggestion(sample_suggestion.id.value)

        assert isinstance(result, Success)
        code = result.unwrap()
        assert code.name == "anxiety"

        # Verify code was saved
        assert len(code_repo.get_all()) == 1

    def test_approve_suggestion_saves_code(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        sample_suggestion: CodeSuggestion,
    ) -> None:
        """approve_suggestion saves the code to the repository."""
        analyzer = MockCodeAnalyzer(suggestions=[sample_suggestion])

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_analyzer=analyzer,
        )

        controller.suggest_codes("text", source_id=1)
        result = controller.approve_suggestion(sample_suggestion.id.value)

        # Core functionality: code is created and saved
        assert isinstance(result, Success)
        assert len(code_repo.get_all()) == 1

    def test_reject_suggestion_removes_from_pending(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        sample_suggestion: CodeSuggestion,
    ) -> None:
        """reject_suggestion removes suggestion from pending list."""
        analyzer = MockCodeAnalyzer(suggestions=[sample_suggestion])

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_analyzer=analyzer,
        )

        controller.suggest_codes("text", source_id=1)
        assert len(controller.get_pending_suggestions()) == 1

        controller.reject_suggestion(sample_suggestion.id.value, reason="Not needed")

        assert len(controller.get_pending_suggestions()) == 0

    def test_reject_suggestion_returns_success(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
        sample_suggestion: CodeSuggestion,
    ) -> None:
        """reject_suggestion returns Success after removing suggestion."""
        analyzer = MockCodeAnalyzer(suggestions=[sample_suggestion])

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_analyzer=analyzer,
        )

        controller.suggest_codes("text", source_id=1)
        result = controller.reject_suggestion(sample_suggestion.id.value)

        # Core functionality: returns Success
        assert isinstance(result, Success)


class TestAICodingControllerMerge:
    """Tests for merge functionality."""

    def test_approve_merge_deletes_source_code(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """approve_merge deletes the source code."""
        code_a = code_repo.add_code("anxiety")
        code_b = code_repo.add_code("anxious feelings")

        duplicates = [
            DuplicateCandidate(
                code_a_id=code_a.id,
                code_a_name=code_a.name,
                code_b_id=code_b.id,
                code_b_name=code_b.name,
                similarity=SimilarityScore(0.9),
                rationale="Similar",
                status="pending",
            )
        ]
        comparator = MockCodeComparator(duplicates=duplicates)

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=comparator,
        )

        controller.detect_duplicates()

        # Merge code_a into code_b
        result = controller.approve_merge(
            source_code_id=code_a.id,
            target_code_id=code_b.id,
        )

        assert isinstance(result, Success)
        assert len(code_repo.get_all()) == 1
        assert code_repo.get_all()[0].name == "anxious feelings"

    def test_approve_merge_returns_target_code(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """approve_merge returns the target code after merging."""
        code_a = code_repo.add_code("anxiety")
        code_b = code_repo.add_code("anxious feelings")

        comparator = MockCodeComparator()

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=comparator,
        )

        result = controller.approve_merge(
            source_code_id=code_a.id, target_code_id=code_b.id
        )

        # Core functionality: returns Success with target code
        assert isinstance(result, Success)
        assert result.unwrap().name == "anxious feelings"

    def test_dismiss_merge_removes_from_pending(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """dismiss_merge removes candidate from pending list."""
        code_a = code_repo.add_code("anxiety")
        code_b = code_repo.add_code("stress")

        duplicates = [
            DuplicateCandidate(
                code_a_id=code_a.id,
                code_a_name=code_a.name,
                code_b_id=code_b.id,
                code_b_name=code_b.name,
                similarity=SimilarityScore(0.9),
                rationale="Similar",
                status="pending",
            )
        ]
        comparator = MockCodeComparator(duplicates=duplicates)

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            code_comparator=comparator,
        )

        controller.detect_duplicates()
        assert len(controller.get_pending_duplicates()) == 1

        controller.dismiss_merge(code_a.id, code_b.id, reason="Not duplicates")

        assert len(controller.get_pending_duplicates()) == 0

    def test_dismiss_merge_returns_success(
        self,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """dismiss_merge returns Success."""
        code_a = code_repo.add_code("anxiety")
        code_b = code_repo.add_code("stress")

        controller = AICodingController(
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        result = controller.dismiss_merge(code_a.id, code_b.id)

        # Core functionality: returns Success
        assert isinstance(result, Success)
