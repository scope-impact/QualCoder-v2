"""
AI Infrastructure: Code Analyzer Implementation

LLM-powered code suggestion service that analyzes uncoded text
and proposes new codes based on content and existing codebook.
"""

from __future__ import annotations

import hashlib
import random
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.contexts.ai_services.core.entities import (
    CodeSuggestion,
    SuggestionId,
    TextContext,
)
from src.contexts.coding.core.entities import Code, Color, TextPosition
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.infrastructure.ai.config import AIConfig
    from src.infrastructure.ai.llm_provider import AnthropicLLMProvider, MockLLMProvider


# System prompt for code suggestion
CODE_SUGGESTION_SYSTEM_PROMPT = """You are a qualitative research assistant helping to analyze text data.
Your task is to suggest new codes that could be useful for coding the given text.

A "code" in qualitative research is a label or tag that represents a theme, concept, or pattern in the data.

Guidelines:
1. Suggest codes that are specific and meaningful
2. Avoid codes that are too broad or generic
3. Consider the existing codes and avoid duplicates or very similar codes
4. Provide a clear rationale for each suggestion
5. Rate your confidence in each suggestion (0.0 to 1.0)

Respond in JSON format with the following structure:
{
  "suggestions": [
    {
      "name": "Code Name",
      "rationale": "Brief explanation of why this code is relevant",
      "confidence": 0.85,
      "relevant_excerpts": ["excerpt from text that supports this code"]
    }
  ]
}
"""


class LLMCodeAnalyzer:
    """
    Implementation of CodeAnalyzer protocol using LLM.

    Analyzes uncoded text and suggests appropriate codes
    based on content and existing codebook.
    """

    def __init__(
        self,
        llm_provider: AnthropicLLMProvider | MockLLMProvider,
        config: AIConfig | None = None,
    ) -> None:
        """
        Initialize the code analyzer.

        Args:
            llm_provider: LLM provider for inference
            config: AI configuration (uses defaults if not provided)
        """
        from src.infrastructure.ai.config import DEFAULT_CONFIG

        self._llm = llm_provider
        self._config = config or DEFAULT_CONFIG

    def suggest_codes(
        self,
        text: str,
        existing_codes: tuple[Code, ...],
        source_id: SourceId,
        max_suggestions: int | None = None,
    ) -> Result[list[CodeSuggestion], str]:
        """
        Analyze text and suggest new codes.

        Args:
            text: The uncoded text to analyze
            existing_codes: Current codes in the codebook
            source_id: ID of the source being analyzed
            max_suggestions: Maximum number of suggestions (uses config default if None)

        Returns:
            Success with list of suggestions, or Failure with error message
        """
        max_suggestions = max_suggestions or self._config.max_suggestions

        # Validate text length
        if len(text.strip()) < self._config.min_text_length:
            return Failure(
                f"Text too short (minimum {self._config.min_text_length} characters)"
            )

        # Build prompt
        prompt = self._build_suggestion_prompt(text, existing_codes, max_suggestions)

        # Get LLM response
        result = self._llm.complete_json(
            prompt=prompt,
            system=CODE_SUGGESTION_SYSTEM_PROMPT,
            max_tokens=self._config.max_tokens,
        )

        if isinstance(result, Failure):
            return result

        response_data = result.unwrap()

        # Parse suggestions
        try:
            suggestions = self._parse_suggestions(
                response_data,
                text,
                source_id,
                existing_codes,
            )
            return Success(suggestions)
        except Exception as e:
            return Failure(f"Failed to parse suggestions: {e!s}")

    def _build_suggestion_prompt(
        self,
        text: str,
        existing_codes: tuple[Code, ...],
        max_suggestions: int,
    ) -> str:
        """Build the prompt for code suggestion."""
        # Format existing codes
        if existing_codes:
            codes_list = "\n".join(
                f"- {code.name}" + (f": {code.memo}" if code.memo else "")
                for code in existing_codes[:50]  # Limit to prevent token overflow
            )
            existing_section = f"""
Existing codes in the project (avoid duplicates or very similar codes):
{codes_list}
"""
        else:
            existing_section = "\nNo existing codes in the project yet.\n"

        return f"""Analyze the following text and suggest up to {max_suggestions} new codes:

TEXT TO ANALYZE:
\"\"\"
{text[:3000]}
\"\"\"
{existing_section}
Suggest codes that would help categorize and understand this text.
Return your suggestions in the JSON format specified."""

    def _parse_suggestions(
        self,
        response_data: dict,
        text: str,
        source_id: SourceId,
        existing_codes: tuple[Code, ...],
    ) -> list[CodeSuggestion]:
        """Parse LLM response into CodeSuggestion entities."""
        suggestions = []
        existing_colors = tuple(c.color for c in existing_codes)

        raw_suggestions = response_data.get("suggestions", [])

        for item in raw_suggestions:
            name = item.get("name", "").strip()
            if not name:
                continue

            # Skip if too similar to existing code
            if self._is_similar_to_existing(name, existing_codes):
                continue

            # Filter by minimum confidence
            confidence = float(item.get("confidence", 0.5))
            if confidence < self._config.min_confidence:
                continue

            rationale = item.get("rationale", "No rationale provided")

            # Build context from excerpts
            excerpts = item.get("relevant_excerpts", [])
            contexts = self._build_contexts(excerpts, text, source_id)

            # Generate color
            color = self.generate_color(name, existing_colors)

            suggestion = CodeSuggestion(
                id=SuggestionId.new(),
                name=name,
                color=color,
                rationale=rationale,
                contexts=contexts,
                confidence=confidence,
                status="pending",
            )
            suggestions.append(suggestion)

        return suggestions

    def _is_similar_to_existing(
        self,
        name: str,
        existing_codes: tuple[Code, ...],
    ) -> bool:
        """Check if suggested name is too similar to existing codes."""
        name_lower = name.lower()
        for code in existing_codes:
            existing_lower = code.name.lower()
            # Exact match
            if name_lower == existing_lower:
                return True
            # One contains the other
            if name_lower in existing_lower or existing_lower in name_lower:
                return True
        return False

    def _build_contexts(
        self,
        excerpts: list[str],
        full_text: str,
        source_id: SourceId,
    ) -> tuple[TextContext, ...]:
        """Build TextContext objects from excerpts."""
        contexts = []
        for excerpt in excerpts[:3]:  # Limit contexts
            # Find position in text
            start = full_text.find(excerpt)
            if start == -1:
                # Fuzzy match - just use excerpt without position
                start = 0
                end = len(excerpt)
            else:
                end = start + len(excerpt)

            try:
                position = TextPosition(start=start, end=end)
                context = TextContext(
                    text=excerpt,
                    source_id=source_id,
                    position=position,
                )
                contexts.append(context)
            except ValueError:
                # Invalid position, skip
                continue

        return tuple(contexts)

    def generate_color(
        self,
        code_name: str,
        existing_colors: tuple[Color, ...],
    ) -> Color:
        """
        Generate an appropriate color for a code.

        Uses a deterministic hash of the code name to select from palette,
        then adjusts to avoid colors too similar to existing ones.

        Args:
            code_name: The name of the code
            existing_colors: Colors already in use

        Returns:
            A suitable Color for the code
        """
        palette = self._config.color_palette

        # Hash the code name to get a starting index
        name_hash = int(hashlib.md5(code_name.encode()).hexdigest(), 16)
        start_idx = name_hash % len(palette)

        # Try colors from the palette, avoiding similar ones
        existing_hexes = {c.to_hex().lower() for c in existing_colors}

        for i in range(len(palette)):
            idx = (start_idx + i) % len(palette)
            color_hex = palette[idx]

            if color_hex.lower() not in existing_hexes:
                return Color.from_hex(color_hex)

        # All colors used, add variation to a random one
        base_hex = random.choice(palette)
        base_color = Color.from_hex(base_hex)

        # Slightly adjust the color
        variation = random.randint(-30, 30)
        new_red = max(0, min(255, base_color.red + variation))
        new_green = max(0, min(255, base_color.green + variation))
        new_blue = max(0, min(255, base_color.blue + variation))

        return Color(red=new_red, green=new_green, blue=new_blue)


class MockCodeAnalyzer:
    """
    Mock code analyzer for testing.

    Returns predefined suggestions without LLM calls.
    """

    def __init__(
        self,
        suggestions: list[CodeSuggestion] | None = None,
    ) -> None:
        """
        Initialize the mock analyzer.

        Args:
            suggestions: Predefined suggestions to return
        """
        self._suggestions = suggestions or []
        self._call_count = 0

    def suggest_codes(
        self,
        text: str,  # noqa: ARG002
        existing_codes: tuple[Code, ...],  # noqa: ARG002
        source_id: SourceId,  # noqa: ARG002
        max_suggestions: int | None = None,
    ) -> Result[list[CodeSuggestion], str]:
        """Return mock suggestions."""
        self._call_count += 1
        max_count = max_suggestions or 5
        return Success(self._suggestions[:max_count])

    def generate_color(
        self,
        code_name: str,  # noqa: ARG002
        existing_colors: tuple[Color, ...],  # noqa: ARG002
    ) -> Color:
        """Generate a simple test color."""
        return Color(red=100, green=150, blue=200)

    @property
    def call_count(self) -> int:
        """Get number of times suggest_codes was called."""
        return self._call_count
