"""
AI Infrastructure: Code Comparator Implementation

LLM-powered duplicate detection service that identifies semantically
similar codes that could be merged.
"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.domain.ai_services.entities import (
    DuplicateCandidate,
    SimilarityScore,
)
from src.domain.coding.entities import Code

if TYPE_CHECKING:
    from src.infrastructure.ai.config import AIConfig
    from src.infrastructure.ai.llm_provider import AnthropicLLMProvider, MockLLMProvider


# System prompt for duplicate detection
DUPLICATE_DETECTION_SYSTEM_PROMPT = """You are a qualitative research assistant helping to identify duplicate codes.

Your task is to compare codes and determine if they represent the same or very similar concepts.

Consider:
1. Semantic similarity - Do they mean the same thing?
2. Scope overlap - Would they be applied to the same text segments?
3. Conceptual hierarchy - Is one a subset of the other?

For each pair, provide:
- similarity: A score from 0.0 (completely different) to 1.0 (identical meaning)
- rationale: Brief explanation of the relationship

Respond in JSON format:
{
  "comparisons": [
    {
      "code_a": "Code A Name",
      "code_b": "Code B Name",
      "similarity": 0.85,
      "rationale": "Both refer to expressions of frustration..."
    }
  ]
}
"""


class LLMCodeComparator:
    """
    Implementation of CodeComparator protocol using LLM.

    Compares codes semantically to identify potential duplicates
    that could be merged.
    """

    def __init__(
        self,
        llm_provider: AnthropicLLMProvider | MockLLMProvider,
        config: AIConfig | None = None,
    ) -> None:
        """
        Initialize the code comparator.

        Args:
            llm_provider: LLM provider for inference
            config: AI configuration (uses defaults if not provided)
        """
        from src.infrastructure.ai.config import DEFAULT_CONFIG

        self._llm = llm_provider
        self._config = config or DEFAULT_CONFIG

    def find_duplicates(
        self,
        codes: tuple[Code, ...],
        threshold: float | None = None,
    ) -> Result[list[DuplicateCandidate], str]:
        """
        Find potentially duplicate codes.

        Uses a two-phase approach:
        1. Quick string similarity to pre-filter pairs
        2. LLM semantic comparison for likely candidates

        Args:
            codes: All codes to compare
            threshold: Minimum similarity score (uses config default if None)

        Returns:
            Success with list of duplicate candidates, or Failure with error
        """
        threshold = threshold or self._config.similarity_threshold

        if len(codes) < 2:
            return Success([])

        # Phase 1: Pre-filter using string similarity
        candidate_pairs = self._prefilter_pairs(codes, min_string_similarity=0.4)

        if not candidate_pairs:
            return Success([])

        # Limit comparisons
        if len(candidate_pairs) > self._config.max_comparisons:
            candidate_pairs = candidate_pairs[: self._config.max_comparisons]

        # Phase 2: LLM semantic comparison
        result = self._compare_pairs_with_llm(candidate_pairs)

        if isinstance(result, Failure):
            # Fall back to string-based similarity
            return Success(self._fallback_string_comparison(candidate_pairs, threshold))

        comparisons = result.unwrap()

        # Filter by threshold and build candidates
        candidates = []
        for comp in comparisons:
            if comp["similarity"] >= threshold:
                # Find the code objects
                code_a = next((c for c in codes if c.name == comp["code_a"]), None)
                code_b = next((c for c in codes if c.name == comp["code_b"]), None)

                if code_a and code_b:
                    candidate = DuplicateCandidate(
                        code_a_id=code_a.id,
                        code_a_name=code_a.name,
                        code_b_id=code_b.id,
                        code_b_name=code_b.name,
                        similarity=SimilarityScore(comp["similarity"]),
                        rationale=comp.get("rationale", "Semantically similar codes"),
                        status="pending",
                    )
                    candidates.append(candidate)

        # Sort by similarity descending
        candidates.sort(key=lambda c: c.similarity.value, reverse=True)

        return Success(candidates)

    def _prefilter_pairs(
        self,
        codes: tuple[Code, ...],
        min_string_similarity: float,
    ) -> list[tuple[Code, Code]]:
        """Pre-filter code pairs using string similarity."""
        pairs = []

        for i, code_a in enumerate(codes):
            for code_b in codes[i + 1 :]:
                # Calculate string similarity
                similarity = self._string_similarity(code_a.name, code_b.name)

                # Also check memos if present
                if code_a.memo and code_b.memo:
                    memo_sim = self._string_similarity(code_a.memo, code_b.memo)
                    similarity = max(similarity, memo_sim)

                if similarity >= min_string_similarity:
                    pairs.append((code_a, code_b))

        return pairs

    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate string similarity using sequence matcher."""
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _compare_pairs_with_llm(
        self,
        pairs: list[tuple[Code, Code]],
    ) -> Result[list[dict], str]:
        """Compare code pairs using LLM."""
        # Build prompt
        pairs_text = "\n".join(
            f'- "{a.name}" vs "{b.name}"'
            + (f" (memos: '{a.memo}' vs '{b.memo}')" if a.memo or b.memo else "")
            for a, b in pairs
        )

        prompt = f"""Compare these pairs of qualitative research codes and rate their semantic similarity:

{pairs_text}

For each pair, determine if they represent the same concept and should be merged.
Return your analysis in the JSON format specified."""

        result = self._llm.complete_json(
            prompt=prompt,
            system=DUPLICATE_DETECTION_SYSTEM_PROMPT,
            max_tokens=self._config.max_tokens,
        )

        if isinstance(result, Failure):
            return result

        response_data = result.unwrap()
        comparisons = response_data.get("comparisons", [])

        return Success(comparisons)

    def _fallback_string_comparison(
        self,
        pairs: list[tuple[Code, Code]],
        threshold: float,
    ) -> list[DuplicateCandidate]:
        """Fallback to string-based comparison when LLM fails."""
        candidates = []

        for code_a, code_b in pairs:
            similarity = self._string_similarity(code_a.name, code_b.name)

            # Boost similarity if memos are similar
            if code_a.memo and code_b.memo:
                memo_sim = self._string_similarity(code_a.memo, code_b.memo)
                similarity = (similarity + memo_sim) / 2

            if similarity >= threshold:
                candidate = DuplicateCandidate(
                    code_a_id=code_a.id,
                    code_a_name=code_a.name,
                    code_b_id=code_b.id,
                    code_b_name=code_b.name,
                    similarity=SimilarityScore(similarity),
                    rationale=f"Names are {int(similarity * 100)}% similar",
                    status="pending",
                )
                candidates.append(candidate)

        return candidates

    def calculate_similarity(
        self,
        code_a: Code,
        code_b: Code,
    ) -> float:
        """
        Calculate semantic similarity between two codes.

        Uses LLM for semantic comparison with string similarity fallback.

        Args:
            code_a: First code
            code_b: Second code

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Try LLM comparison first
        result = self._compare_pairs_with_llm([(code_a, code_b)])

        if isinstance(result, Success):
            comparisons = result.unwrap()
            if comparisons:
                return comparisons[0].get("similarity", 0.0)

        # Fallback to string similarity
        return self._string_similarity(code_a.name, code_b.name)


class MockCodeComparator:
    """
    Mock code comparator for testing.

    Returns predefined duplicates without LLM calls.
    """

    def __init__(
        self,
        duplicates: list[DuplicateCandidate] | None = None,
    ) -> None:
        """
        Initialize the mock comparator.

        Args:
            duplicates: Predefined duplicate candidates to return
        """
        self._duplicates = duplicates or []
        self._call_count = 0

    def find_duplicates(
        self,
        codes: tuple[Code, ...],  # noqa: ARG002
        threshold: float | None = None,
    ) -> Result[list[DuplicateCandidate], str]:
        """Return mock duplicate candidates."""
        self._call_count += 1
        threshold = threshold or 0.8

        # Filter by threshold
        filtered = [d for d in self._duplicates if d.similarity.value >= threshold]

        return Success(filtered)

    def calculate_similarity(
        self,
        code_a: Code,
        code_b: Code,
    ) -> float:
        """Calculate simple string similarity."""
        return difflib.SequenceMatcher(
            None, code_a.name.lower(), code_b.name.lower()
        ).ratio()

    @property
    def call_count(self) -> int:
        """Get number of times find_duplicates was called."""
        return self._call_count
