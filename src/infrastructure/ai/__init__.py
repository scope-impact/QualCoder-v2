"""
AI Infrastructure Layer

Provides concrete implementations of AI service protocols.
Handles LLM API calls, code analysis, and duplicate detection.

Components:
    - LLMProvider implementations (Anthropic, OpenAI, Mock)
    - CodeAnalyzer implementation
    - CodeComparator implementation
    - Configuration management
"""

from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer
from src.infrastructure.ai.code_comparator import LLMCodeComparator
from src.infrastructure.ai.config import AIConfig
from src.infrastructure.ai.llm_provider import (
    AnthropicLLMProvider,
    MockLLMProvider,
)

__all__ = [
    "AIConfig",
    "AnthropicLLMProvider",
    "LLMCodeAnalyzer",
    "LLMCodeComparator",
    "MockLLMProvider",
]
