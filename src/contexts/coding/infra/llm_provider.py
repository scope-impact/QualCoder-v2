"""
AI Infrastructure: LLM Provider Implementations

Concrete implementations of the LLMProvider protocol for different backends.
Supports OpenAI-compatible APIs (OpenAI, Ollama, LM Studio, vLLM),
Anthropic Claude, and a mock provider for testing.
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.contexts.coding.infra.config import AIConfig, LLMConfig

logger = logging.getLogger(__name__)


# ============================================================
# Anthropic Provider
# ============================================================


class AnthropicLLMProvider:
    """
    LLM provider implementation using Anthropic's Claude API.

    Requires the 'anthropic' package and ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, config: LLMConfig | AIConfig | None = None) -> None:
        """
        Initialize the Anthropic provider.

        Args:
            config: LLM or AI configuration (uses defaults if not provided)
        """
        from src.contexts.coding.infra.config import DEFAULT_LLM_CONFIG, LLMConfig

        # Handle both config types
        if config is None:
            self._config = DEFAULT_LLM_CONFIG
        elif isinstance(config, LLMConfig):
            self._config = config
        else:
            # Legacy AIConfig
            self._config = LLMConfig(
                provider="anthropic",
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            self._api_key_env_var = config.api_key_env_var

        self._client = None

    def _get_client(self):
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                # Try config api_key first, then environment variable
                api_key = self._config.api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError(
                        "Missing API key: set ANTHROPIC_API_KEY environment variable"
                    )
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError as e:
                raise ImportError(
                    "anthropic package not installed. Install with: pip install anthropic"
                ) from e
        return self._client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Result[str, str]:
        """
        Send a completion request to Claude.

        Args:
            prompt: The user prompt to complete
            system: Optional system prompt for context
            max_tokens: Maximum tokens in response (uses config default if None)
            temperature: Sampling temperature (uses config default if None)

        Returns:
            Success with completion text, or Failure with error message
        """
        try:
            client = self._get_client()

            messages = [{"role": "user", "content": prompt}]

            response = client.messages.create(
                model=self._config.model,
                max_tokens=max_tokens or self._config.max_tokens,
                temperature=temperature or self._config.temperature,
                system=system or "",
                messages=messages,
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                return Success(response.content[0].text)

            return Failure("Empty response from API")

        except Exception as e:
            return Failure(f"API error: {e!s}")

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> Result[dict, str]:
        """
        Send a completion request expecting JSON response.

        Args:
            prompt: The user prompt (should request JSON output)
            system: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Success with parsed JSON dict, or Failure with error message
        """
        result = self.complete(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.1,  # Lower temperature for structured output
        )

        if isinstance(result, Failure):
            return result

        text = result.unwrap()

        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            return Success(json.loads(text))

        except json.JSONDecodeError as e:
            return Failure(f"Failed to parse JSON: {e!s}")


# ============================================================
# OpenAI-Compatible Provider
# ============================================================


class OpenAICompatibleLLMProvider:
    """
    LLM provider using OpenAI-compatible API.

    Works with:
    - OpenAI API
    - Ollama (via /v1 endpoints)
    - LM Studio
    - vLLM
    - Any other OpenAI-compatible server
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        """
        Initialize the OpenAI-compatible provider.

        Args:
            config: LLM configuration (uses defaults if not provided)
        """
        from src.contexts.coding.infra.config import DEFAULT_LLM_CONFIG

        self._config = config or DEFAULT_LLM_CONFIG
        self._client = None

    def _get_client(self):
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    base_url=self._config.api_base_url,
                    api_key=self._config.api_key
                    or "not-needed",  # Local servers often don't need keys
                    timeout=self._config.timeout_seconds,
                )
            except ImportError as e:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                ) from e
        return self._client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Result[str, str]:
        """
        Send a completion request to the LLM.

        Args:
            prompt: The user prompt to complete
            system: Optional system prompt for context
            max_tokens: Maximum tokens in response (uses config default if None)
            temperature: Sampling temperature (uses config default if None)

        Returns:
            Success with completion text, or Failure with error message
        """
        try:
            client = self._get_client()

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                max_tokens=max_tokens or self._config.max_tokens,
                temperature=temperature or self._config.temperature,
            )

            # Extract text from response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return Success(content)
                return Failure("Empty response from API")

            return Failure("No choices in response")

        except Exception as e:
            logger.warning(f"LLM API error: {e}")
            return Failure(f"API error: {e!s}")

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> Result[dict, str]:
        """
        Send a completion request expecting JSON response.

        Args:
            prompt: The user prompt (should request JSON output)
            system: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Success with parsed JSON dict, or Failure with error message
        """
        result = self.complete(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.1,  # Lower temperature for structured output
        )

        if isinstance(result, Failure):
            return result

        text = result.unwrap()

        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            return Success(json.loads(text))

        except json.JSONDecodeError as e:
            return Failure(f"Failed to parse JSON: {e!s}")


# ============================================================
# Mock Provider
# ============================================================


class MockLLMProvider:
    """
    Mock LLM provider for testing.

    Returns predefined responses for testing without API calls.
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        json_responses: list[dict] | None = None,
    ) -> None:
        """
        Initialize the mock provider.

        Args:
            responses: List of text responses to return in order
            json_responses: List of JSON responses to return in order
        """
        self._responses = responses or []
        self._json_responses = json_responses or []
        self._call_count = 0
        self._json_call_count = 0
        self._prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        system: str | None = None,  # noqa: ARG002
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
    ) -> Result[str, str]:
        """
        Return a mock completion.

        Args:
            prompt: The user prompt (recorded for inspection)
            system: Ignored in mock
            max_tokens: Ignored in mock
            temperature: Ignored in mock

        Returns:
            Success with next mock response, or default response
        """
        self._prompts.append(prompt)

        if self._call_count < len(self._responses):
            response = self._responses[self._call_count]
            self._call_count += 1
            return Success(response)

        # Default response
        return Success("Mock response")

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,  # noqa: ARG002
        max_tokens: int | None = None,  # noqa: ARG002
    ) -> Result[dict, str]:
        """
        Return a mock JSON completion.

        Args:
            prompt: The user prompt (recorded for inspection)
            system: Ignored in mock
            max_tokens: Ignored in mock

        Returns:
            Success with next mock JSON response, or default response
        """
        self._prompts.append(prompt)

        if self._json_call_count < len(self._json_responses):
            response = self._json_responses[self._json_call_count]
            self._json_call_count += 1
            return Success(response)

        # Default response
        return Success({"suggestions": []})

    @property
    def prompts(self) -> list[str]:
        """Get all prompts sent to this provider."""
        return self._prompts

    def reset(self) -> None:
        """Reset call counts and recorded prompts."""
        self._call_count = 0
        self._json_call_count = 0
        self._prompts = []


# ============================================================
# Factory Functions
# ============================================================


def create_llm_provider(
    config: LLMConfig | AIConfig | None = None,
) -> OpenAICompatibleLLMProvider | AnthropicLLMProvider | MockLLMProvider:
    """
    Factory function to create an LLM provider based on configuration.

    Args:
        config: LLM or AI configuration (uses defaults if not provided)

    Returns:
        An LLM provider instance

    Raises:
        ValueError: If provider type is unknown
    """
    from src.contexts.coding.infra.config import DEFAULT_LLM_CONFIG, LLMConfig

    # Handle legacy AIConfig
    if config is not None and not isinstance(config, LLMConfig):
        # Convert AIConfig to LLMConfig for backwards compatibility
        llm_config = LLMConfig(
            provider=config.provider,  # type: ignore
            model=config.model,
            api_key=None,  # Will be read from env
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
    else:
        llm_config = config or DEFAULT_LLM_CONFIG

    if llm_config.provider == "openai-compatible":
        return OpenAICompatibleLLMProvider(llm_config)
    elif llm_config.provider == "anthropic":
        return AnthropicLLMProvider(llm_config)
    elif llm_config.provider == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unknown provider: {llm_config.provider}")
