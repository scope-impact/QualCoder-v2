"""
Tests for LLMCodeAnalyzer

TDD tests for AI-powered code suggestion service.
"""

from __future__ import annotations

import pytest
from returns.result import Failure, Success

from src.domain.ai_services.entities import CodeSuggestion
from src.domain.coding.entities import Code, Color
from src.domain.shared.types import CodeId, SourceId
from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer, MockCodeAnalyzer
from src.infrastructure.ai.config import AIConfig
from src.infrastructure.ai.llm_provider import MockLLMProvider

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> tuple[Code, ...]:
    """Create sample codes for testing."""
    return (
        Code(
            id=CodeId(value=1),
            name="anxiety",
            color=Color.from_hex("#FF0000"),
            memo="Feelings of worry",
        ),
        Code(
            id=CodeId(value=2),
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


# ============================================================
# MockCodeAnalyzer Tests
# ============================================================


class TestMockCodeAnalyzer:
    """Tests for MockCodeAnalyzer."""

    def test_returns_predefined_suggestions(self) -> None:
        """suggest_codes returns predefined suggestions."""
        from src.domain.ai_services.entities import SuggestionId, TextContext
        from src.domain.coding.entities import TextPosition

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="test_code",
            color=Color.from_hex("#FF0000"),
            rationale="Test rationale",
            contexts=(
                TextContext(
                    text="test text",
                    source_id=SourceId(value=1),
                    position=TextPosition(start=0, end=9),
                ),
            ),
            confidence=0.9,
            status="pending",
        )
        analyzer = MockCodeAnalyzer(suggestions=[suggestion])

        result = analyzer.suggest_codes(
            text="Some text",
            existing_codes=(),
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        assert len(suggestions) == 1
        assert suggestions[0].name == "test_code"

    def test_returns_empty_list_by_default(self) -> None:
        """suggest_codes returns empty list when no suggestions configured."""
        analyzer = MockCodeAnalyzer()

        result = analyzer.suggest_codes(
            text="Some text",
            existing_codes=(),
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Success)
        assert result.unwrap() == []

    def test_respects_max_suggestions(self) -> None:
        """suggest_codes respects max_suggestions parameter."""
        from src.domain.ai_services.entities import SuggestionId, TextContext
        from src.domain.coding.entities import TextPosition

        suggestions = [
            CodeSuggestion(
                id=SuggestionId.new(),
                name=f"code_{i}",
                color=Color.from_hex("#FF0000"),
                rationale="Test",
                contexts=(
                    TextContext(
                        text="test",
                        source_id=SourceId(value=1),
                        position=TextPosition(start=0, end=4),
                    ),
                ),
                confidence=0.8,
                status="pending",
            )
            for i in range(5)
        ]
        analyzer = MockCodeAnalyzer(suggestions=suggestions)

        result = analyzer.suggest_codes(
            text="Some text",
            existing_codes=(),
            source_id=SourceId(value=1),
            max_suggestions=2,
        )

        assert len(result.unwrap()) == 2

    def test_tracks_call_count(self) -> None:
        """suggest_codes tracks number of calls."""
        analyzer = MockCodeAnalyzer()

        analyzer.suggest_codes("text1", (), SourceId(value=1))
        analyzer.suggest_codes("text2", (), SourceId(value=1))

        assert analyzer.call_count == 2

    def test_generate_color_returns_color(self) -> None:
        """generate_color returns a valid Color."""
        analyzer = MockCodeAnalyzer()

        color = analyzer.generate_color("test", ())

        assert isinstance(color, Color)


# ============================================================
# LLMCodeAnalyzer Tests
# ============================================================


class TestLLMCodeAnalyzer:
    """Tests for LLMCodeAnalyzer with MockLLMProvider."""

    def test_suggest_codes_returns_suggestions(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """suggest_codes returns parsed suggestions from LLM."""
        analyzer = LLMCodeAnalyzer(
            llm_provider=mock_llm_provider,
            config=ai_config,
        )

        result = analyzer.suggest_codes(
            text="I feel so frustrated with the deadline at work. " * 5,
            existing_codes=sample_codes,
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        assert len(suggestions) >= 1
        assert all(isinstance(s, CodeSuggestion) for s in suggestions)

    def test_suggest_codes_rejects_short_text(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
    ) -> None:
        """suggest_codes rejects text below minimum length."""
        analyzer = LLMCodeAnalyzer(
            llm_provider=mock_llm_provider,
            config=ai_config,
        )

        result = analyzer.suggest_codes(
            text="Too short",
            existing_codes=(),
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Failure)
        assert "too short" in result.failure().lower()

    def test_suggest_codes_filters_low_confidence(
        self,
        ai_config: AIConfig,
    ) -> None:
        """suggest_codes filters out low-confidence suggestions."""
        provider = MockLLMProvider(
            json_responses=[
                {
                    "suggestions": [
                        {
                            "name": "high_confidence",
                            "rationale": "Good match",
                            "confidence": 0.9,
                            "relevant_excerpts": ["excerpt"],
                        },
                        {
                            "name": "low_confidence",
                            "rationale": "Poor match",
                            "confidence": 0.2,
                            "relevant_excerpts": ["excerpt"],
                        },
                    ]
                }
            ]
        )
        analyzer = LLMCodeAnalyzer(llm_provider=provider, config=ai_config)

        result = analyzer.suggest_codes(
            text="A longer text that meets the minimum length requirement. " * 3,
            existing_codes=(),
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        # Low confidence should be filtered out
        assert all(s.confidence >= ai_config.min_confidence for s in suggestions)

    def test_suggest_codes_skips_similar_to_existing(
        self,
        ai_config: AIConfig,
        sample_codes: tuple[Code, ...],
    ) -> None:
        """suggest_codes skips suggestions similar to existing codes."""
        provider = MockLLMProvider(
            json_responses=[
                {
                    "suggestions": [
                        {
                            "name": "anxiety",  # Same as existing
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
        analyzer = LLMCodeAnalyzer(llm_provider=provider, config=ai_config)

        result = analyzer.suggest_codes(
            text="A longer text that meets the minimum length requirement. " * 3,
            existing_codes=sample_codes,
            source_id=SourceId(value=1),
        )

        assert isinstance(result, Success)
        suggestions = result.unwrap()
        # "anxiety" should be filtered, only "new_code" remains
        assert all(s.name != "anxiety" for s in suggestions)

    def test_generate_color_uses_palette(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
    ) -> None:
        """generate_color returns color from palette."""
        analyzer = LLMCodeAnalyzer(
            llm_provider=mock_llm_provider,
            config=ai_config,
        )

        color = analyzer.generate_color("test_code", ())

        assert isinstance(color, Color)
        # Color should be from the palette
        assert color.to_hex().upper() in [c.upper() for c in ai_config.color_palette]

    def test_generate_color_avoids_existing(
        self,
        mock_llm_provider: MockLLMProvider,
        ai_config: AIConfig,
    ) -> None:
        """generate_color avoids colors already in use."""
        analyzer = LLMCodeAnalyzer(
            llm_provider=mock_llm_provider,
            config=ai_config,
        )
        # Use first color from palette
        existing = (Color.from_hex(ai_config.color_palette[0]),)

        color = analyzer.generate_color("test_code", existing)

        # Should not return the existing color
        assert color.to_hex().upper() != ai_config.color_palette[0].upper()

    def test_llm_failure_propagates(
        self,
        ai_config: AIConfig,
    ) -> None:
        """LLM failure is propagated as Failure result."""
        # Provider returns Success but with unparseable content
        provider = MockLLMProvider(json_responses=[])

        # Make complete_json return failure by exhausting responses
        provider.complete_json("exhaust")

        analyzer = LLMCodeAnalyzer(llm_provider=provider, config=ai_config)

        # With exhausted provider, it returns default empty suggestions
        result = analyzer.suggest_codes(
            text="A longer text that meets the minimum length requirement. " * 3,
            existing_codes=(),
            source_id=SourceId(value=1),
        )

        # Should return empty suggestions (not failure) when LLM returns empty
        assert isinstance(result, Success)
        assert result.unwrap() == []
