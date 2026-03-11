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

    @allure.title("complete/complete_json return sequences, defaults, record prompts, and reset")
    def test_complete_sequences_prompts_and_reset(self) -> None:
        provider = MockLLMProvider(
            responses=["First", "Second"],
            json_responses=[{"key": "value"}, {"suggestions": [{"name": "code1"}]}],
        )

        # Text responses in order, then default
        r1 = provider.complete("1")
        r2 = provider.complete("2")
        r3 = provider.complete("3")
        assert r1.unwrap() == "First"
        assert r2.unwrap() == "Second"
        assert r3.unwrap() == "Mock response"

        # JSON responses in order, then default
        j1 = provider.complete_json("j1")
        j2 = provider.complete_json("j2")
        j3 = provider.complete_json("j3")
        assert j1.unwrap() == {"key": "value"}
        assert j2.unwrap()["suggestions"][0]["name"] == "code1"
        assert j3.unwrap() == {"suggestions": []}

        # Prompts recorded
        assert "1" in provider.prompts
        assert "j1" in provider.prompts

        # Reset clears state
        provider.reset()
        assert len(provider.prompts) == 0


@allure.epic("Coding")
@allure.feature("QC-028 Code Management")
@allure.story("QC-028.08 Agent Suggest New Codes")
class TestLLMConfigAndFactory:
    """Tests for LLMConfig and create_llm_provider factory."""

    @allure.title("Default config and factory methods create correct configurations")
    def test_config_defaults_and_factory_methods(self) -> None:
        config = LLMConfig()
        assert config.provider == "openai-compatible"
        assert config.api_base_url == "http://localhost:11434/v1"
        assert config.model == "llama3.2"

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

    @allure.title("Factory creates correct provider types; unknown raises ValueError")
    def test_factory_creates_providers_and_rejects_unknown(self) -> None:
        mock_provider = create_llm_provider(LLMConfig.for_testing())
        assert isinstance(mock_provider, MockLLMProvider)

        openai_provider = create_llm_provider(LLMConfig(provider="openai-compatible"))
        assert isinstance(openai_provider, OpenAICompatibleLLMProvider)

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
