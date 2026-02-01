"""
AI Infrastructure: Configuration

Configuration settings for AI services including LLM providers,
model selection, and analysis parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class AIConfig:
    """
    Configuration for AI services.

    Immutable configuration object that controls AI behavior.
    Can be loaded from environment or settings file.
    """

    # LLM Provider Settings
    provider: Literal["anthropic", "openai", "mock"] = "anthropic"
    model: str = "claude-3-haiku-20240307"
    api_key_env_var: str = "ANTHROPIC_API_KEY"

    # Request Settings
    max_tokens: int = 1024
    temperature: float = 0.3
    timeout_seconds: int = 30

    # Code Suggestion Settings
    max_suggestions: int = 5
    min_confidence: float = 0.5
    min_text_length: int = 50

    # Duplicate Detection Settings
    similarity_threshold: float = 0.8
    max_comparisons: int = 1000  # Limit for large codebooks

    # Color Generation Settings
    color_palette: tuple[str, ...] = field(
        default_factory=lambda: (
            "#F44336",  # Red
            "#E91E63",  # Pink
            "#9C27B0",  # Purple
            "#673AB7",  # Deep Purple
            "#3F51B5",  # Indigo
            "#2196F3",  # Blue
            "#03A9F4",  # Light Blue
            "#00BCD4",  # Cyan
            "#009688",  # Teal
            "#4CAF50",  # Green
            "#8BC34A",  # Light Green
            "#CDDC39",  # Lime
            "#FFEB3B",  # Yellow
            "#FFC107",  # Amber
            "#FF9800",  # Orange
            "#FF5722",  # Deep Orange
            "#795548",  # Brown
            "#607D8B",  # Blue Grey
        )
    )

    @classmethod
    def for_testing(cls) -> AIConfig:
        """Create a configuration suitable for testing (uses mock provider)."""
        return cls(
            provider="mock",
            max_suggestions=3,
            similarity_threshold=0.7,
        )

    @classmethod
    def from_env(cls) -> AIConfig:
        """
        Create configuration from environment variables.

        Environment variables:
            QUALCODER_AI_PROVIDER: LLM provider (anthropic, openai, mock)
            QUALCODER_AI_MODEL: Model name
            ANTHROPIC_API_KEY: API key for Anthropic
            OPENAI_API_KEY: API key for OpenAI
        """
        import os

        provider = os.getenv("QUALCODER_AI_PROVIDER", "anthropic")
        model = os.getenv("QUALCODER_AI_MODEL", "claude-3-haiku-20240307")

        api_key_var = "ANTHROPIC_API_KEY"
        if provider == "openai":
            api_key_var = "OPENAI_API_KEY"

        return cls(
            provider=provider,  # type: ignore
            model=model,
            api_key_env_var=api_key_var,
        )


# Default configuration instance
DEFAULT_CONFIG = AIConfig()
