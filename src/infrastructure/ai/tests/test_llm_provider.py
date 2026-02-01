"""
Tests for LLM Provider Implementations

TDD tests for OpenAI-compatible, Anthropic, and Mock LLM providers.
"""

from __future__ import annotations

import pytest
from returns.result import Success

from src.infrastructure.ai.config import LLMConfig
from src.infrastructure.ai.llm_provider import (
    MockLLMProvider,
    OpenAICompatibleLLMProvider,
    create_llm_provider,
)

# ============================================================
# MockLLMProvider Tests
# ============================================================


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    def test_complete_returns_mock_response(self) -> None:
        """complete returns predefined response."""
        provider = MockLLMProvider(responses=["Hello, world!"])

        result = provider.complete("Say hello")

        assert isinstance(result, Success)
        assert result.unwrap() == "Hello, world!"

    def test_complete_returns_responses_in_order(self) -> None:
        """complete returns responses in sequence."""
        provider = MockLLMProvider(responses=["First", "Second", "Third"])

        r1 = provider.complete("1")
        r2 = provider.complete("2")
        r3 = provider.complete("3")

        assert r1.unwrap() == "First"
        assert r2.unwrap() == "Second"
        assert r3.unwrap() == "Third"

    def test_complete_returns_default_when_exhausted(self) -> None:
        """complete returns default response when predefined exhausted."""
        provider = MockLLMProvider(responses=["Only one"])

        provider.complete("1")
        result = provider.complete("2")

        assert result.unwrap() == "Mock response"

    def test_complete_json_returns_dict(self) -> None:
        """complete_json returns parsed JSON dict."""
        provider = MockLLMProvider(json_responses=[{"key": "value"}])

        result = provider.complete_json("Return JSON")

        assert isinstance(result, Success)
        assert result.unwrap() == {"key": "value"}

    def test_complete_json_returns_responses_in_order(self) -> None:
        """complete_json returns JSON responses in sequence."""
        provider = MockLLMProvider(
            json_responses=[
                {"suggestions": [{"name": "code1"}]},
                {"suggestions": [{"name": "code2"}]},
            ]
        )

        r1 = provider.complete_json("1")
        r2 = provider.complete_json("2")

        assert r1.unwrap()["suggestions"][0]["name"] == "code1"
        assert r2.unwrap()["suggestions"][0]["name"] == "code2"

    def test_complete_json_returns_empty_default(self) -> None:
        """complete_json returns empty suggestions when exhausted."""
        provider = MockLLMProvider(json_responses=[{"test": True}])

        provider.complete_json("1")
        result = provider.complete_json("2")

        assert result.unwrap() == {"suggestions": []}

    def test_prompts_are_recorded(self) -> None:
        """Prompts sent to provider are recorded."""
        provider = MockLLMProvider()

        provider.complete("First prompt")
        provider.complete_json("Second prompt")

        assert "First prompt" in provider.prompts
        assert "Second prompt" in provider.prompts

    def test_reset_clears_state(self) -> None:
        """reset clears call counts and prompts."""
        provider = MockLLMProvider(responses=["test"])

        provider.complete("prompt")
        provider.reset()

        assert len(provider.prompts) == 0


# ============================================================
# LLMConfig Tests
# ============================================================


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_config(self) -> None:
        """Default config uses openai-compatible provider."""
        config = LLMConfig()

        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"
        assert config.model == "llama3.2"

    def test_for_testing(self) -> None:
        """for_testing creates mock config."""
        config = LLMConfig.for_testing()

        assert config.provider == "mock"

    def test_for_openai(self) -> None:
        """for_openai creates OpenAI-compatible config."""
        config = LLMConfig.for_openai(api_key="sk-test")

        assert config.provider == "openai-compatible"
        assert config.api_base_url == "https://api.openai.com/v1"
        assert config.api_key == "sk-test"
        assert config.model == "gpt-4o-mini"

    def test_for_ollama(self) -> None:
        """for_ollama creates Ollama-compatible config."""
        config = LLMConfig.for_ollama(model="mistral")

        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"
        assert config.model == "mistral"

    def test_for_anthropic(self) -> None:
        """for_anthropic creates Anthropic config."""
        config = LLMConfig.for_anthropic()

        assert config.provider == "anthropic"
        assert config.model == "claude-3-haiku-20240307"

    def test_immutable(self) -> None:
        """Config is immutable (frozen dataclass)."""
        from dataclasses import FrozenInstanceError

        config = LLMConfig()

        with pytest.raises(FrozenInstanceError):
            config.model = "new-model"  # type: ignore


# ============================================================
# Factory Function Tests
# ============================================================


class TestCreateLLMProvider:
    """Tests for create_llm_provider factory."""

    def test_creates_mock_provider(self) -> None:
        """Factory creates MockLLMProvider for mock config."""
        config = LLMConfig.for_testing()

        provider = create_llm_provider(config)

        assert isinstance(provider, MockLLMProvider)

    def test_creates_openai_compatible_provider(self) -> None:
        """Factory creates OpenAICompatibleLLMProvider."""
        config = LLMConfig(provider="openai-compatible")

        provider = create_llm_provider(config)

        assert isinstance(provider, OpenAICompatibleLLMProvider)

    def test_unknown_provider_raises(self) -> None:
        """Factory raises ValueError for unknown provider."""
        # Create config with invalid provider (bypass type checking)
        config = LLMConfig()
        object.__setattr__(config, "provider", "unknown")

        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_provider(config)


# ============================================================
# OpenAICompatibleLLMProvider Tests (with mocking)
# ============================================================


class TestOpenAICompatibleLLMProvider:
    """Tests for OpenAICompatibleLLMProvider."""

    def test_init_with_config(self) -> None:
        """Provider initializes with config."""
        config = LLMConfig.for_ollama(model="llama3.2")

        provider = OpenAICompatibleLLMProvider(config)

        assert provider._config.model == "llama3.2"

    def test_init_with_default_config(self) -> None:
        """Provider uses default config when none provided."""
        provider = OpenAICompatibleLLMProvider()

        assert provider._config.provider == "openai-compatible"

    def test_client_is_lazy_loaded(self) -> None:
        """Client is not created until needed."""
        provider = OpenAICompatibleLLMProvider()

        assert provider._client is None
