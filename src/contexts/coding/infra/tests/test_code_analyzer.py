"""Tests for LLMCodeAnalyzer and MockCodeAnalyzer."""

from __future__ import annotations

import allure
import pytest
from returns.result import Failure, Success

from src.contexts.coding.core.ai_entities import (
    CodeSuggestion,
    SuggestionId,
    TextContext,
)
from src.contexts.coding.core.entities import Code, Color, TextPosition
from src.contexts.coding.infra.code_analyzer import LLMCodeAnalyzer, MockCodeAnalyzer
from src.contexts.coding.infra.config import AIConfig
from src.contexts.coding.infra.llm_provider import MockLLMProvider
from src.shared.common.types import CodeId, SourceId

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> tuple[Code, ...]:
    """Create sample codes for testing."""
    return (
        Code(
            id=CodeId(value="1"),
            name="anxiety",
            color=Color.from_hex("#FF0000"),
            memo="Feelings of worry",
        ),
        Code(
            id=CodeId(value="2"),
            name="stress",
            color=Color.from_hex("#00FF00"),
            memo="Tension and pressure",
        ),
    )


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Create mock LLM provider with sample response."""
    return MockLLMProvider(
        json_responses=[
            {
                "suggestions": [
                    {
                        "name": "frustration",
                        "rationale": "Text expresses feelings of frustration",
                        "confidence": 0.85,
                        "relevant_excerpts": ["I feel so frustrated"],
                    },
                    {
                        "name": "work pressure",
                        "rationale": "Work-related stress is mentioned",
                        "confidence": 0.75,
                        "relevant_excerpts": ["deadline at work"],
                    },
                ]
            }
        ]
    )


@pytest.fixture
def ai_config() -> AIConfig:
    """Create test AI config."""
    return AIConfig.for_testing()


LONG_TEXT = "I feel so frustrated with the deadline at work. " * 5


# ============================================================
# MockCodeAnalyzer Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestMockCodeAnalyzer:
    """Tests for MockCodeAnalyzer."""

    @allure.title(
        "Returns predefined suggestions, respects max, tracks calls, defaults, and generate_color"
    )
    def test_suggestions_limits_tracking_and_defaults(self) -> None:
        suggestions = [
            CodeSuggestion(
                id=SuggestionId.new(),
                name=f"code_{i}",
                color=Color.from_hex("#FF0000"),
                rationale="Test",
                contexts=(
                    TextContext(
                        text="test",
                        source_id=SourceId(value="1"),
                        position=TextPosition(start=0, end=4),
                    ),
                ),
                confidence=0.8,
                status="pending",
            )
            for i in range(5)
        ]
        analyzer = MockCodeAnalyzer(suggestions=suggestions)

        # Returns all by default
        result = analyzer.suggest_codes("text", (), SourceId(value="1"))
        assert isinstance(result, Success)
        assert len(result.unwrap()) == 5

        # Respects max_suggestions
        result = analyzer.suggest_codes(
            "text", (), SourceId(value="1"), max_suggestions=2
        )
        assert len(result.unwrap()) == 2
        assert analyzer.call_count == 2

        # Default returns empty; generate_color returns Color
        default_analyzer = MockCodeAnalyzer()
        result = default_analyzer.suggest_codes("text", (), SourceId(value="1"))
        assert isinstance(result, Success)
        assert result.unwrap() == []

        color = default_analyzer.generate_color("test", ())
        assert isinstance(color, Color)


# ============================================================
# LLMCodeAnalyzer Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestLLMCodeAnalyzer:
    """Tests for LLMCodeAnalyzer with MockLLMProvider."""

    @allure.title(
        "suggest_codes returns parsed suggestions and filters by confidence/existing"
    )
    def test_suggest_codes_parsing_and_filtering(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
        sample_codes: tuple[Code, ...],
    ) -> None:
        analyzer = LLMCodeAnalyzer(llm_provider=mock_llm_provider, config=ai_config)
        result = analyzer.suggest_codes(
            text=LONG_TEXT, existing_codes=sample_codes, source_id=SourceId(value="1")
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        assert len(suggestions) >= 1
        assert all(isinstance(s, CodeSuggestion) for s in suggestions)

    @allure.title(
        "Rejects short text, filters low confidence, and skips existing code names"
    )
    def test_rejects_short_text_filters_confidence_skips_existing(
        self, ai_config: AIConfig, sample_codes: tuple[Code, ...]
    ) -> None:
        provider_low = MockLLMProvider(
            json_responses=[
                {
                    "suggestions": [
                        {
                            "name": "high",
                            "rationale": "Good",
                            "confidence": 0.9,
                            "relevant_excerpts": ["e"],
                        },
                        {
                            "name": "low",
                            "rationale": "Poor",
                            "confidence": 0.2,
                            "relevant_excerpts": ["e"],
                        },
                    ]
                }
            ]
        )
        analyzer = LLMCodeAnalyzer(llm_provider=provider_low, config=ai_config)

        # Short text -> Failure
        result = analyzer.suggest_codes(
            text="Too short", existing_codes=(), source_id=SourceId(value="1")
        )
        assert isinstance(result, Failure)
        assert "too short" in result.failure().lower()

        # Low confidence filtered
        result = analyzer.suggest_codes(
            text=LONG_TEXT, existing_codes=(), source_id=SourceId(value="1")
        )
        assert isinstance(result, Success)
        assert all(s.confidence >= ai_config.min_confidence for s in result.unwrap())

        # Skips existing code names
        provider2 = MockLLMProvider(
            json_responses=[
                {
                    "suggestions": [
                        {
                            "name": "anxiety",
                            "rationale": "Matches existing",
                            "confidence": 0.9,
                            "relevant_excerpts": ["anxious"],
                        },
                        {
                            "name": "new_code",
                            "rationale": "Truly new",
                            "confidence": 0.9,
                            "relevant_excerpts": ["excerpt"],
                        },
                    ]
                }
            ]
        )
        analyzer2 = LLMCodeAnalyzer(llm_provider=provider2, config=ai_config)
        result = analyzer2.suggest_codes(
            text=LONG_TEXT, existing_codes=sample_codes, source_id=SourceId(value="1")
        )
        assert isinstance(result, Success)
        assert all(s.name != "anxiety" for s in result.unwrap())

    @allure.title("generate_color uses palette; exhausted provider returns empty")
    def test_generate_color_and_exhausted_provider(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
    ) -> None:
        analyzer = LLMCodeAnalyzer(llm_provider=mock_llm_provider, config=ai_config)

        color = analyzer.generate_color("test_code", ())
        assert isinstance(color, Color)
        assert color.to_hex().upper() in [c.upper() for c in ai_config.color_palette]

        existing = (Color.from_hex(ai_config.color_palette[0]),)
        color = analyzer.generate_color("test_code", existing)
        assert color.to_hex().upper() != ai_config.color_palette[0].upper()

        # Exhausted provider returns empty
        provider = MockLLMProvider(json_responses=[])
        provider.complete_json("exhaust")
        analyzer2 = LLMCodeAnalyzer(llm_provider=provider, config=ai_config)
        result = analyzer2.suggest_codes(
            text=LONG_TEXT, existing_codes=(), source_id=SourceId(value="1")
        )
        assert isinstance(result, Success)
        assert result.unwrap() == []
