"""
Tests for AI-Assisted Coding Entities - Domain Layer.

Tests for CodeSuggestion, DuplicateCandidate, and related value objects.
"""

import pytest

from src.contexts.coding.core.ai_entities import (
    CodeSuggestion,
    DetectionId,
    DuplicateCandidate,
    DuplicateDetectionResult,
    SimilarityScore,
    SuggestionBatch,
    SuggestionId,
    TextContext,
)
from src.contexts.coding.core.entities import Color, TextPosition
from src.shared.common.types import CodeId, SourceId


class TestSimilarityScore:
    """Tests for SimilarityScore value object."""

    def test_valid_similarity_score(self):
        """SimilarityScore should accept values between 0.0 and 1.0."""
        score = SimilarityScore(value=0.85)
        assert score.value == 0.85
        assert score.percentage == 85

    def test_high_similarity(self):
        """is_high should return True for scores >= 0.8."""
        high_score = SimilarityScore(value=0.9)
        low_score = SimilarityScore(value=0.5)

        assert high_score.is_high is True
        assert low_score.is_high is False

    def test_boundary_values(self):
        """Boundary values 0.0 and 1.0 should be valid."""
        zero = SimilarityScore(value=0.0)
        one = SimilarityScore(value=1.0)

        assert zero.value == 0.0
        assert one.value == 1.0

    def test_invalid_similarity_score_negative(self):
        """SimilarityScore should reject negative values."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            SimilarityScore(value=-0.1)

    def test_invalid_similarity_score_above_one(self):
        """SimilarityScore should reject values above 1.0."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            SimilarityScore(value=1.5)


class TestSuggestionId:
    """Tests for SuggestionId typed identifier."""

    def test_new_generates_unique_ids(self):
        """new() should generate unique IDs."""
        id1 = SuggestionId.new()
        id2 = SuggestionId.new()

        assert id1.value != id2.value
        assert id1.value.startswith("sug_")
        assert id2.value.startswith("sug_")


class TestTextContext:
    """Tests for TextContext value object."""

    def test_create_text_context(self):
        """TextContext should store text and position."""
        position = TextPosition(start=10, end=50)
        context = TextContext(
            text="This is some relevant text",
            source_id=SourceId(value=1),
            position=position,
        )

        assert context.text == "This is some relevant text"
        assert context.source_id.value == 1
        assert context.position.start == 10

    def test_preview_short_text(self):
        """preview should return full text if under 100 chars."""
        context = TextContext(
            text="Short text",
            source_id=SourceId(value=1),
            position=TextPosition(start=0, end=10),
        )

        assert context.preview == "Short text"

    def test_preview_long_text(self):
        """preview should truncate text over 100 chars."""
        long_text = "x" * 150
        context = TextContext(
            text=long_text,
            source_id=SourceId(value=1),
            position=TextPosition(start=0, end=150),
        )

        assert len(context.preview) == 100
        assert context.preview.endswith("...")


class TestCodeSuggestion:
    """Tests for CodeSuggestion entity."""

    def test_create_code_suggestion(self):
        """CodeSuggestion should store all properties."""
        suggestion = CodeSuggestion(
            id=SuggestionId(value="sug_test123"),
            name="Anxiety",
            color=Color(red=255, green=87, blue=34),
            rationale="This text discusses feelings of worry and stress",
            confidence=0.85,
            status="pending",
        )

        assert suggestion.name == "Anxiety"
        assert suggestion.confidence == 0.85
        assert suggestion.is_pending is True
        assert suggestion.confidence_percentage == 85

    def test_invalid_confidence(self):
        """CodeSuggestion should reject invalid confidence."""
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Test",
                color=Color(red=100, green=100, blue=100),
                rationale="Test",
                confidence=1.5,
            )

    def test_invalid_status(self):
        """CodeSuggestion should reject invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Test",
                color=Color(red=100, green=100, blue=100),
                rationale="Test",
                confidence=0.5,
                status="invalid",
            )

    def test_with_status(self):
        """with_status should return new suggestion with updated status."""
        original = CodeSuggestion(
            id=SuggestionId.new(),
            name="Test",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            confidence=0.5,
            status="pending",
        )

        approved = original.with_status("approved")

        assert original.status == "pending"
        assert approved.status == "approved"
        assert approved.name == original.name

    def test_with_name(self):
        """with_name should return new suggestion with updated name."""
        original = CodeSuggestion(
            id=SuggestionId.new(),
            name="Original",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            confidence=0.5,
        )

        renamed = original.with_name("New Name")

        assert original.name == "Original"
        assert renamed.name == "New Name"


class TestDuplicateCandidate:
    """Tests for DuplicateCandidate entity."""

    def test_create_duplicate_candidate(self):
        """DuplicateCandidate should store all properties."""
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Anxiety",
            code_b_id=CodeId(value=2),
            code_b_name="Anxiousness",
            similarity=SimilarityScore(value=0.92),
            rationale="Both codes refer to feelings of worry",
            code_a_segment_count=15,
            code_b_segment_count=8,
        )

        assert candidate.code_a_name == "Anxiety"
        assert candidate.code_b_name == "Anxiousness"
        assert candidate.similarity.value == 0.92
        assert candidate.total_segments == 23
        assert candidate.is_pending is True

    def test_with_status(self):
        """with_status should return new candidate with updated status."""
        original = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="A",
            code_b_id=CodeId(value=2),
            code_b_name="B",
            similarity=SimilarityScore(value=0.8),
            rationale="Test",
        )

        merged = original.with_status("merged")

        assert original.status == "pending"
        assert merged.status == "merged"


class TestSuggestionBatch:
    """Tests for SuggestionBatch entity."""

    def test_create_suggestion_batch(self):
        """SuggestionBatch should group suggestions."""
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Test",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            confidence=0.5,
        )

        batch = SuggestionBatch(
            suggestions=(suggestion,),
            source_id=SourceId(value=1),
            text_analyzed="Some text to analyze",
        )

        assert batch.count == 1
        assert batch.pending_count == 1

    def test_text_preview_truncation(self):
        """text_preview should truncate long text."""
        batch = SuggestionBatch(
            suggestions=(),
            source_id=SourceId(value=1),
            text_analyzed="x" * 300,
        )

        assert len(batch.text_preview) == 200
        assert batch.text_preview.endswith("...")


class TestDuplicateDetectionResult:
    """Tests for DuplicateDetectionResult entity."""

    def test_create_detection_result(self):
        """DuplicateDetectionResult should store results."""
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="A",
            code_b_id=CodeId(value=2),
            code_b_name="B",
            similarity=SimilarityScore(value=0.85),
            rationale="Similar",
        )

        result = DuplicateDetectionResult(
            id=DetectionId.new(),
            candidates=(candidate,),
            threshold=0.8,
            codes_analyzed=10,
        )

        assert result.candidate_count == 1
        assert result.threshold == 0.8
        assert len(result.pending_candidates) == 1
