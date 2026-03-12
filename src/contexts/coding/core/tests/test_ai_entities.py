"""
Tests for AI-Assisted Coding Entities - Domain Layer.

Consolidated tests for CodeSuggestion, DuplicateCandidate, and related value objects.
"""

import allure
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


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestValueObjects:
    """Tests for SimilarityScore, TextContext, and SuggestionId value objects."""

    @allure.title(
        "SimilarityScore: valid scores, properties, boundary, and invalid rejection"
    )
    def test_similarity_score_valid_invalid_and_properties(self):
        score = SimilarityScore(value=0.85)
        assert score.value == 0.85
        assert score.percentage == 85

        high = SimilarityScore(value=0.9)
        low = SimilarityScore(value=0.5)
        assert high.is_high is True
        assert low.is_high is False

        # Boundary values
        assert SimilarityScore(value=0.0).value == 0.0
        assert SimilarityScore(value=1.0).value == 1.0

        # Invalid scores
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            SimilarityScore(value=-0.1)
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            SimilarityScore(value=1.5)

    @allure.title(
        "TextContext: stores text/position, truncates preview, and SuggestionId uniqueness"
    )
    def test_text_context_and_suggestion_id(self):
        context = TextContext(
            text="This is some relevant text",
            source_id=SourceId(value="1"),
            position=TextPosition(start=10, end=50),
        )
        assert context.text == "This is some relevant text"
        assert context.source_id.value == "1"
        assert context.position.start == 10
        assert context.preview == "This is some relevant text"

        # Long text is truncated
        long_context = TextContext(
            text="x" * 150,
            source_id=SourceId(value="1"),
            position=TextPosition(start=0, end=150),
        )
        assert len(long_context.preview) == 100
        assert long_context.preview.endswith("...")

        # SuggestionId generates unique IDs with sug_ prefix
        id1 = SuggestionId.new()
        id2 = SuggestionId.new()
        assert id1.value != id2.value
        assert id1.value.startswith("sug_")


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCodeSuggestion:
    """Tests for CodeSuggestion entity."""

    @allure.title("CodeSuggestion: properties, derived values, and invalid inputs")
    def test_create_properties_and_validation(self):
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

        # Invalid confidence
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Test",
                color=Color(red=100, green=100, blue=100),
                rationale="Test",
                confidence=1.5,
            )
        # Invalid status
        with pytest.raises(ValueError, match="Invalid status"):
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Test",
                color=Color(red=100, green=100, blue=100),
                rationale="Test",
                confidence=0.5,
                status="invalid",
            )

    @allure.title("with_status and with_name return new instances")
    def test_with_status_and_with_name(self):
        original = CodeSuggestion(
            id=SuggestionId.new(),
            name="Original",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            confidence=0.5,
            status="pending",
        )

        approved = original.with_status("approved")
        assert original.status == "pending"
        assert approved.status == "approved"
        assert approved.name == original.name

        renamed = original.with_name("New Name")
        assert original.name == "Original"
        assert renamed.name == "New Name"


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestAggregateEntities:
    """Tests for DuplicateCandidate, SuggestionBatch, and DuplicateDetectionResult."""

    @allure.title("DuplicateCandidate: properties, total_segments, and with_status")
    def test_duplicate_candidate(self):
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Anxiety",
            code_b_id=CodeId(value="2"),
            code_b_name="Anxiousness",
            similarity=SimilarityScore(value=0.92),
            rationale="Both codes refer to feelings of worry",
            code_a_segment_count=15,
            code_b_segment_count=8,
        )
        assert candidate.code_a_name == "Anxiety"
        assert candidate.similarity.value == 0.92
        assert candidate.total_segments == 23
        assert candidate.is_pending is True

        merged = candidate.with_status("merged")
        assert candidate.status == "pending"
        assert merged.status == "merged"

    @allure.title("SuggestionBatch and DuplicateDetectionResult: creation and counts")
    def test_batch_and_detection_result(self):
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="Test",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            confidence=0.5,
        )
        batch = SuggestionBatch(
            suggestions=(suggestion,),
            source_id=SourceId(value="1"),
            text_analyzed="Some text to analyze",
        )
        assert batch.count == 1
        assert batch.pending_count == 1

        long_batch = SuggestionBatch(
            suggestions=(),
            source_id=SourceId(value="1"),
            text_analyzed="x" * 300,
        )
        assert len(long_batch.text_preview) == 200
        assert long_batch.text_preview.endswith("...")

        # DuplicateDetectionResult
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="A",
            code_b_id=CodeId(value="2"),
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
