"""
AI Services Context: Protocols (Interfaces)

Defines contracts for AI service implementations.
Infrastructure layer provides concrete implementations.

These protocols follow the Dependency Inversion Principle:
domain depends on abstractions, not concrete implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from returns.result import Result

if TYPE_CHECKING:
    from src.domain.ai_services.entities import (
        CodeSuggestion,
        DuplicateCandidate,
    )
    from src.domain.coding.entities import Code, Color


# ============================================================
# Embedding Provider Protocol
# ============================================================


class EmbeddingProvider(Protocol):
    """
    Protocol for text embedding providers.

    Abstraction over different embedding backends (OpenAI-compatible,
    sentence-transformers, etc.) for semantic similarity operations.
    """

    def embed(self, text: str) -> Result[list[float], str]:
        """
        Generate embedding vector for a single text.

        Args:
            text: The text to embed

        Returns:
            Success with embedding vector, or Failure with error message
        """
        ...

    def embed_batch(
        self,
        texts: list[str],
    ) -> Result[list[list[float]], str]:
        """
        Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times.

        Args:
            texts: List of texts to embed

        Returns:
            Success with list of embedding vectors, or Failure with error
        """
        ...

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        ...

    @property
    def model_name(self) -> str:
        """Return the name of the embedding model being used."""
        ...


# ============================================================
# LLM Provider Protocol
# ============================================================


class LLMProvider(Protocol):
    """
    Protocol for Large Language Model providers.

    Abstraction over different LLM backends (Anthropic, OpenAI, etc.)
    allowing the domain to remain agnostic of implementation details.
    """

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> Result[str, str]:
        """
        Send a completion request to the LLM.

        Args:
            prompt: The user prompt to complete
            system: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Success with completion text, or Failure with error message
        """
        ...


# ============================================================
# Code Analysis Protocols
# ============================================================


class CodeAnalyzer(Protocol):
    """
    Protocol for AI-powered code suggestion.

    Analyzes uncoded text and suggests appropriate codes
    based on content and existing codebook.
    """

    def suggest_codes(
        self,
        text: str,
        existing_codes: tuple[Code, ...],
        max_suggestions: int = 5,
    ) -> Result[list[CodeSuggestion], str]:
        """
        Analyze text and suggest new codes.

        Args:
            text: The uncoded text to analyze
            existing_codes: Current codes in the codebook
            max_suggestions: Maximum number of suggestions

        Returns:
            Success with list of suggestions, or Failure with error message
        """
        ...

    def generate_color(
        self,
        code_name: str,
        existing_colors: tuple[Color, ...],
    ) -> Color:
        """
        Generate an appropriate color for a code.

        Considers semantic meaning and avoids colors too similar
        to existing ones.

        Args:
            code_name: The name of the code
            existing_colors: Colors already in use

        Returns:
            A suitable Color for the code
        """
        ...


class CodeComparator(Protocol):
    """
    Protocol for AI-powered duplicate detection.

    Compares codes semantically to identify potential duplicates
    that could be merged.
    """

    def find_duplicates(
        self,
        codes: tuple[Code, ...],
        threshold: float = 0.8,
    ) -> Result[list[DuplicateCandidate], str]:
        """
        Find potentially duplicate codes.

        Args:
            codes: All codes to compare
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Success with list of duplicate candidates, or Failure with error
        """
        ...

    def calculate_similarity(
        self,
        code_a: Code,
        code_b: Code,
    ) -> float:
        """
        Calculate semantic similarity between two codes.

        Considers name, memo, and optionally usage patterns.

        Args:
            code_a: First code
            code_b: Second code

        Returns:
            Similarity score between 0.0 and 1.0
        """
        ...


# ============================================================
# Repository Protocols
# ============================================================


class SuggestionRepository(Protocol):
    """
    Protocol for persisting code suggestions.

    Stores pending suggestions for researcher review.
    """

    def save(self, suggestion: CodeSuggestion) -> None:
        """Save a code suggestion."""
        ...

    def get_by_id(self, suggestion_id: str) -> CodeSuggestion | None:
        """Get a suggestion by ID."""
        ...

    def get_pending(self) -> list[CodeSuggestion]:
        """Get all pending suggestions."""
        ...

    def delete(self, suggestion_id: str) -> None:
        """Delete a suggestion."""
        ...


class DuplicateRepository(Protocol):
    """
    Protocol for persisting duplicate candidates.

    Stores duplicate detection results for researcher review.
    """

    def save(self, candidate: DuplicateCandidate) -> None:
        """Save a duplicate candidate."""
        ...

    def get_pending(self) -> list[DuplicateCandidate]:
        """Get all pending candidates."""
        ...

    def dismiss(self, code_a_id: int, code_b_id: int) -> None:
        """Mark a candidate as dismissed (not duplicates)."""
        ...
