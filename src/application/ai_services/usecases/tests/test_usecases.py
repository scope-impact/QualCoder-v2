"""
Tests for AI Services Use Cases

Tests for the functional use case pattern for AI-powered coding operations.
"""

from __future__ import annotations

import pytest
from returns.result import Failure, Success

from src.application.ai_services.commands import (
    ApproveCodeSuggestionCommand,
    ApproveMergeCommand,
    DetectDuplicatesCommand,
    SuggestCodesCommand,
)
from src.application.ai_services.usecases import (
    approve_code_suggestion,
    approve_merge,
    detect_duplicates,
    suggest_codes,
)
from src.application.event_bus import EventBus
from src.contexts.ai_services.core.entities import (
    CodeSuggestion,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)
from src.contexts.ai_services.core.events import (
    CodeSuggested,
    CodeSuggestionApproved,
    DuplicatesDetected,
    MergeSuggestionApproved,
)
from src.contexts.coding.core.entities import Code, Color, TextPosition
from src.contexts.coding.core.events import CodeCreated, CodesMerged
from src.contexts.shared.core.types import CodeId, SourceId

# ============================================================
# Test Fixtures (Mocks)
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

    def get_by_name(self, name: str) -> Code | None:
        for code in self._codes.values():
            if code.name.lower() == name.lower():
                return code
        return None

    def save(self, code: Code) -> None:
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

    def count_by_code(self, code_id: CodeId) -> int:
        return len(self._segments.get(code_id.value, []))

    def reassign_code(self, source_id: CodeId, target_id: CodeId) -> int:
        segments = self._segments.pop(source_id.value, [])
        if target_id.value not in self._segments:
            self._segments[target_id.value] = []
        self._segments[target_id.value].extend(segments)
        return len(segments)

    def add_segments(self, code_id: CodeId, count: int) -> None:
        """Helper to add mock segments for testing."""
        self._segments[code_id.value] = [f"segment_{i}" for i in range(count)]


class MockCodeAnalyzer:
    """Mock code analyzer for testing."""

    def __init__(self, suggestions: list[CodeSuggestion] | None = None) -> None:
        self._suggestions = suggestions or []

    def suggest_codes(
        self,
        text: str,
        existing_codes: tuple[Code, ...],
        source_id: SourceId,
        max_suggestions: int | None = None,
    ) -> Success[list[CodeSuggestion]]:
        return Success(
            self._suggestions[:max_suggestions]
            if max_suggestions
            else self._suggestions
        )


class MockCodeComparator:
    """Mock code comparator for testing."""

    def __init__(self, duplicates: list[DuplicateCandidate] | None = None) -> None:
        self._duplicates = duplicates or []

    def find_duplicates(
        self,
        codes: tuple[Code, ...],
        threshold: float | None = None,
    ) -> Success[list[DuplicateCandidate]]:
        return Success(self._duplicates)


class EventCapture:
    """Captures published events for testing."""

    def __init__(self) -> None:
        self.events: list = []

    def capture(self, event) -> None:
        self.events.append(event)

    def of_type(self, event_type: type) -> list:
        return [e for e in self.events if isinstance(e, event_type)]


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def code_repo() -> MockCodeRepository:
    return MockCodeRepository()


@pytest.fixture
def segment_repo() -> MockSegmentRepository:
    return MockSegmentRepository()


@pytest.fixture
def event_capture(event_bus: EventBus) -> EventCapture:
    capture = EventCapture()
    event_bus.subscribe_all(capture.capture)
    return capture


# ============================================================
# Test: suggest_codes
# ============================================================


class TestSuggestCodes:
    """Tests for suggest_codes use case."""

    def test_returns_suggestions_from_analyzer(
        self, event_bus: EventBus, event_capture: EventCapture
    ) -> None:
        """suggest_codes returns suggestions from the analyzer."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Test Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern X",
            contexts=(
                TextContext(
                    text="sample",
                    source_id=SourceId(value=1),
                    position=TextPosition(start=0, end=10),
                ),
            ),
            confidence=0.9,
        )
        analyzer = MockCodeAnalyzer(suggestions=[suggestion])

        command = SuggestCodesCommand(text="sample text", source_id=1)
        result = suggest_codes(
            command=command,
            code_analyzer=analyzer,
            existing_codes=(),
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        assert len(suggestions) == 1
        assert suggestions[0].name == "Test Code"

    def test_publishes_code_suggested_event(
        self, event_bus: EventBus, event_capture: EventCapture
    ) -> None:
        """suggest_codes publishes CodeSuggested event for each suggestion."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Test Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern X",
            contexts=(
                TextContext(
                    text="sample",
                    source_id=SourceId(value=1),
                    position=TextPosition(start=0, end=10),
                ),
            ),
            confidence=0.9,
        )
        analyzer = MockCodeAnalyzer(suggestions=[suggestion])

        command = SuggestCodesCommand(text="sample text", source_id=1)
        suggest_codes(
            command=command,
            code_analyzer=analyzer,
            existing_codes=(),
            event_bus=event_bus,
        )

        events = event_capture.of_type(CodeSuggested)
        assert len(events) == 1
        assert events[0].name == "Test Code"

    def test_fails_on_empty_text(self, event_bus: EventBus) -> None:
        """suggest_codes fails if text is empty."""
        analyzer = MockCodeAnalyzer()

        command = SuggestCodesCommand(text="", source_id=1)
        result = suggest_codes(
            command=command,
            code_analyzer=analyzer,
            existing_codes=(),
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "empty" in result.failure().lower()

    def test_respects_max_suggestions(self, event_bus: EventBus) -> None:
        """suggest_codes respects max_suggestions parameter."""
        suggestions = [
            CodeSuggestion(
                id=SuggestionId.new(),
                name=f"Code {i}",
                color=Color.from_hex("#FF0000"),
                rationale="Found pattern",
                contexts=(),
                confidence=0.9,
            )
            for i in range(5)
        ]
        analyzer = MockCodeAnalyzer(suggestions=suggestions)

        command = SuggestCodesCommand(
            text="sample text", source_id=1, max_suggestions=2
        )
        result = suggest_codes(
            command=command,
            code_analyzer=analyzer,
            existing_codes=(),
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 2


# ============================================================
# Test: detect_duplicates
# ============================================================


class TestDetectDuplicates:
    """Tests for detect_duplicates use case."""

    def test_returns_candidates_from_comparator(
        self, event_bus: EventBus, code_repo: MockCodeRepository
    ) -> None:
        """detect_duplicates returns candidates from the comparator."""
        code_a = code_repo.add_code("Happy")
        code_b = code_repo.add_code("Happiness")

        candidate = DuplicateCandidate(
            code_a_id=code_a.id,
            code_b_id=code_b.id,
            code_a_name=code_a.name,
            code_b_name=code_b.name,
            similarity=SimilarityScore(value=0.85),
            rationale="Semantic similarity",
        )
        comparator = MockCodeComparator(duplicates=[candidate])

        command = DetectDuplicatesCommand(threshold=0.8)
        result = detect_duplicates(
            command=command,
            code_comparator=comparator,
            existing_codes=tuple(code_repo.get_all()),
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        candidates = result.unwrap()
        assert len(candidates) == 1
        assert candidates[0].similarity.value == 0.85

    def test_publishes_duplicates_detected_event(
        self,
        event_bus: EventBus,
        event_capture: EventCapture,
        code_repo: MockCodeRepository,
    ) -> None:
        """detect_duplicates publishes DuplicatesDetected event."""
        code_a = code_repo.add_code("Happy")
        code_b = code_repo.add_code("Happiness")

        candidate = DuplicateCandidate(
            code_a_id=code_a.id,
            code_b_id=code_b.id,
            code_a_name=code_a.name,
            code_b_name=code_b.name,
            similarity=SimilarityScore(value=0.85),
            rationale="Semantic similarity",
        )
        comparator = MockCodeComparator(duplicates=[candidate])

        command = DetectDuplicatesCommand(threshold=0.8)
        detect_duplicates(
            command=command,
            code_comparator=comparator,
            existing_codes=tuple(code_repo.get_all()),
            event_bus=event_bus,
        )

        events = event_capture.of_type(DuplicatesDetected)
        assert len(events) == 1
        assert len(events[0].candidates) == 1

    def test_returns_empty_for_few_codes(
        self, event_bus: EventBus, code_repo: MockCodeRepository
    ) -> None:
        """detect_duplicates returns empty list if fewer than 2 codes."""
        code_repo.add_code("Only One")
        comparator = MockCodeComparator()

        command = DetectDuplicatesCommand()
        result = detect_duplicates(
            command=command,
            code_comparator=comparator,
            existing_codes=tuple(code_repo.get_all()),
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_fails_on_invalid_threshold(self, event_bus: EventBus) -> None:
        """detect_duplicates fails if threshold is out of range."""
        comparator = MockCodeComparator()

        command = DetectDuplicatesCommand(threshold=1.5)
        result = detect_duplicates(
            command=command,
            code_comparator=comparator,
            existing_codes=(),
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "threshold" in result.failure().lower()


# ============================================================
# Test: approve_code_suggestion
# ============================================================


class TestApproveCodeSuggestion:
    """Tests for approve_code_suggestion use case."""

    def test_creates_code_in_repository(
        self, event_bus: EventBus, code_repo: MockCodeRepository
    ) -> None:
        """approve_code_suggestion creates a new code in the repository."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Suggested Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern",
            contexts=(),
            confidence=0.9,
        )

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion.id.value,
            name="Final Name",
            color="#00FF00",
            memo="Created from AI suggestion",
        )
        result = approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=code_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        code = result.unwrap()
        assert code.name == "Final Name"
        assert code.color.to_hex() == "#00ff00"
        assert code.memo == "Created from AI suggestion"

        # Verify persisted
        saved = code_repo.get_by_name("Final Name")
        assert saved is not None
        assert saved.id == code.id

    def test_publishes_both_events(
        self,
        event_bus: EventBus,
        event_capture: EventCapture,
        code_repo: MockCodeRepository,
    ) -> None:
        """approve_code_suggestion publishes CodeSuggestionApproved and CodeCreated."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Suggested Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern",
            contexts=(),
            confidence=0.9,
        )

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion.id.value,
            name="Final Name",
            color="#00FF00",
        )
        approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=code_repo,
            event_bus=event_bus,
        )

        approved_events = event_capture.of_type(CodeSuggestionApproved)
        created_events = event_capture.of_type(CodeCreated)

        assert len(approved_events) == 1
        assert len(created_events) == 1
        assert approved_events[0].final_name == "Final Name"
        assert created_events[0].name == "Final Name"

    def test_fails_on_empty_name(
        self, event_bus: EventBus, code_repo: MockCodeRepository
    ) -> None:
        """approve_code_suggestion fails if name is empty."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Suggested Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern",
            contexts=(),
            confidence=0.9,
        )

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion.id.value,
            name="",
            color="#00FF00",
        )
        result = approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=code_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "empty" in result.failure().lower()

    def test_fails_on_duplicate_name(
        self, event_bus: EventBus, code_repo: MockCodeRepository
    ) -> None:
        """approve_code_suggestion fails if code name already exists."""
        code_repo.add_code("Existing Code")

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Suggested Code",
            color=Color.from_hex("#FF0000"),
            rationale="Found pattern",
            contexts=(),
            confidence=0.9,
        )

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion.id.value,
            name="Existing Code",  # Duplicate!
            color="#00FF00",
        )
        result = approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=code_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "already exists" in result.failure().lower()


# ============================================================
# Test: approve_merge
# ============================================================


class TestApproveMerge:
    """Tests for approve_merge use case."""

    def test_merges_codes_and_reassigns_segments(
        self,
        event_bus: EventBus,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
    ) -> None:
        """approve_merge reassigns segments and deletes source code."""
        source = code_repo.add_code("Happy")
        target = code_repo.add_code("Happiness")
        segment_repo.add_segments(source.id, 3)

        command = ApproveMergeCommand(
            source_code_id=source.id.value,
            target_code_id=target.id.value,
        )
        result = approve_merge(
            command=command,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Success)
        assert result.unwrap().id == target.id

        # Source should be deleted
        assert code_repo.get_by_id(source.id) is None

        # Target should have the segments
        assert segment_repo.count_by_code(target.id) == 3

    def test_publishes_both_events(
        self,
        event_bus: EventBus,
        event_capture: EventCapture,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
    ) -> None:
        """approve_merge publishes MergeSuggestionApproved and CodesMerged."""
        source = code_repo.add_code("Happy")
        target = code_repo.add_code("Happiness")
        segment_repo.add_segments(source.id, 3)

        command = ApproveMergeCommand(
            source_code_id=source.id.value,
            target_code_id=target.id.value,
        )
        approve_merge(
            command=command,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        approved_events = event_capture.of_type(MergeSuggestionApproved)
        merged_events = event_capture.of_type(CodesMerged)

        assert len(approved_events) == 1
        assert len(merged_events) == 1
        assert approved_events[0].segments_moved == 3
        assert merged_events[0].segments_moved == 3

    def test_fails_if_source_not_found(
        self,
        event_bus: EventBus,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
    ) -> None:
        """approve_merge fails if source code doesn't exist."""
        target = code_repo.add_code("Target")

        command = ApproveMergeCommand(
            source_code_id=999,  # Doesn't exist
            target_code_id=target.id.value,
        )
        result = approve_merge(
            command=command,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_fails_if_merging_with_self(
        self,
        event_bus: EventBus,
        code_repo: MockCodeRepository,
        segment_repo: MockSegmentRepository,
    ) -> None:
        """approve_merge fails if trying to merge code with itself."""
        code = code_repo.add_code("Code")

        command = ApproveMergeCommand(
            source_code_id=code.id.value,
            target_code_id=code.id.value,  # Same!
        )
        result = approve_merge(
            command=command,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert isinstance(result, Failure)
        assert "itself" in result.failure().lower()
