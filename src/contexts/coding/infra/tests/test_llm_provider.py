"""
Tests for LLM Provider Implementations

Consolidated tests for MockLLMProvider, LLMConfig, and factory function.
"""

from __future__ import annotations

import allure
import pytest
from returns.result import Success

from src.contexts.coding.infra.config import LLMConfig
from src.contexts.coding.infra.llm_provider import (
    MockLLMProvider,
    OpenAICompatibleLLMProvider,
    create_llm_provider,
)


@allure.epic("Coding")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    @allure.title("complete returns responses in order, then default")
    def test_complete_responses_sequence_and_default(self) -> None:
        provider = MockLLMProvider(responses=["First", "Second"])

        r1 = provider.complete("1")
        r2 = provider.complete("2")
        r3 = provider.complete("3")

        assert r1.unwrap() == "First"
        assert r2.unwrap() == "Second"
        assert r3.unwrap() == "Mock response"

    @allure.title("complete_json returns JSON responses in order, then default")
    def test_complete_json_sequence_and_default(self) -> None:
        provider = MockLLMProvider(
            json_responses=[{"key": "value"}, {"suggestions": [{"name": "code1"}]}]
        )

        r1 = provider.complete_json("1")
        r2 = provider.complete_json("2")
        r3 = provider.complete_json("3")

        assert r1.unwrap() == {"key": "value"}
        assert r2.unwrap()["suggestions"][0]["name"] == "code1"
        assert r3.unwrap() == {"suggestions": []}

    @allure.title("Prompts are recorded and reset clears state")
    def test_prompts_recorded_and_reset(self) -> None:
        provider = MockLLMProvider(responses=["test"])

        provider.complete("First prompt")
        provider.complete_json("Second prompt")
        assert "First prompt" in provider.prompts
        assert "Second prompt" in provider.prompts

        provider.reset()
        assert len(provider.prompts) == 0


@allure.epic("Coding")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestLLMConfig:
    """Tests for LLMConfig."""

    @allure.title("Default config uses openai-compatible provider with Ollama defaults")
    def test_default_config(self) -> None:
        config = LLMConfig()

        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"
        assert config.model == "llama3.2"

    @allure.title("Factory methods create correct configurations")
    def test_factory_methods(self) -> None:
        mock = LLMConfig.for_testing()
        assert mock.provider == "mock"

        openai = LLMConfig.for_openai(api_key="sk-test")
        assert openai.api_base_url == "https://api.openai.com/v1"
        assert openai.api_key == "sk-test"
        assert openai.model == "gpt-4o-mini"

        ollama = LLMConfig.for_ollama(model="mistral")
        assert ollama.api_base_url == "http://localhost:11434/v1"
        assert ollama.model == "mistral"

        anthropic = LLMConfig.for_anthropic()
        assert anthropic.provider == "anthropic"
        assert anthropic.model == "claude-3-haiku-20240307"


@allure.epic("Coding")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCreateLLMProvider:
    """Tests for create_llm_provider factory."""

    @allure.title("Factory creates correct provider type for each config")
    def test_creates_correct_provider_types(self) -> None:
        mock_provider = create_llm_provider(LLMConfig.for_testing())
        assert isinstance(mock_provider, MockLLMProvider)

        openai_provider = create_llm_provider(LLMConfig(provider="openai-compatible"))
        assert isinstance(openai_provider, OpenAICompatibleLLMProvider)

    @allure.title("Factory raises ValueError for unknown provider")
    def test_unknown_provider_raises(self) -> None:
        config = LLMConfig()
        object.__setattr__(config, "provider", "unknown")

        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_provider(config)


@allure.epic("Coding")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestOpenAICompatibleLLMProvider:
    """Tests for OpenAICompatibleLLMProvider."""

    @allure.title("Provider initializes with config and lazy-loads client")
    def test_init_and_lazy_loading(self) -> None:
        provider = OpenAICompatibleLLMProvider(LLMConfig.for_ollama(model="llama3.2"))
        assert provider._config.model == "llama3.2"
        assert provider._client is None

        default_provider = OpenAICompatibleLLMProvider()
        assert default_provider._config.provider == "openai-compatible"
