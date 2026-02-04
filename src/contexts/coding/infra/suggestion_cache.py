"""
Coding Context: In-Memory Suggestion Cache

Key-value cache for AI suggestions awaiting researcher approval.
In-memory only - suggestions don't persist between sessions.

This is intentional: suggestions are temporary workflow items, not data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.contexts.coding.core.ai_entities import (
    CodeSuggestion,
    CodingSuggestion,
    CodingSuggestionBatch,
    CodingSuggestionBatchId,
    CodingSuggestionId,
    DuplicateCandidate,
    DuplicateDetectionResult,
    MergeSuggestion,
    MergeSuggestionId,
    SuggestionId,
)
from src.shared.common.types import SourceId


# ============================================================
# Cache Implementations
# ============================================================


@dataclass
class CodeSuggestionCache:
    """Cache for pending code suggestions."""

    _items: dict[str, CodeSuggestion] = field(default_factory=dict)

    def add(self, suggestion: CodeSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def get_by_id(self, suggestion_id: SuggestionId) -> CodeSuggestion | None:
        return self._items.get(suggestion_id.value)

    def get_all_pending(self) -> list[CodeSuggestion]:
        return [s for s in self._items.values() if s.is_pending]

    def update(self, suggestion: CodeSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def remove(self, suggestion_id: SuggestionId) -> None:
        self._items.pop(suggestion_id.value, None)

    def clear(self) -> None:
        self._items.clear()


@dataclass
class CodingSuggestionCache:
    """Cache for pending coding suggestions (code applications to text)."""

    _items: dict[str, CodingSuggestion] = field(default_factory=dict)
    _batches: dict[str, CodingSuggestionBatch] = field(default_factory=dict)

    def add(self, suggestion: CodingSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def get_by_id(self, suggestion_id: CodingSuggestionId) -> CodingSuggestion | None:
        return self._items.get(suggestion_id.value)

    def get_by_source(self, source_id: SourceId) -> list[CodingSuggestion]:
        return [
            s for s in self._items.values()
            if s.source_id == source_id and s.is_pending
        ]

    def get_all_pending(self) -> list[CodingSuggestion]:
        return [s for s in self._items.values() if s.is_pending]

    def update(self, suggestion: CodingSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def remove(self, suggestion_id: CodingSuggestionId) -> None:
        self._items.pop(suggestion_id.value, None)

    def add_batch(self, batch: CodingSuggestionBatch) -> None:
        self._batches[batch.id.value] = batch
        for suggestion in batch.suggestions:
            self.add(suggestion)

    def get_batch(self, batch_id: CodingSuggestionBatchId) -> CodingSuggestionBatch | None:
        return self._batches.get(batch_id.value)

    def update_batch(self, batch: CodingSuggestionBatch) -> None:
        self._batches[batch.id.value] = batch

    def clear(self) -> None:
        self._items.clear()
        self._batches.clear()


@dataclass
class DuplicateDetectionCache:
    """Cache for duplicate detection results."""

    _results: list[DuplicateDetectionResult] = field(default_factory=list)
    _candidates: dict[tuple[int, int], DuplicateCandidate] = field(default_factory=dict)

    def add(self, result: DuplicateDetectionResult) -> None:
        self._results.append(result)
        for candidate in result.candidates:
            key = (candidate.code_a_id.value, candidate.code_b_id.value)
            self._candidates[key] = candidate

    def get_latest(self) -> DuplicateDetectionResult | None:
        return self._results[-1] if self._results else None

    def get_pending_candidates(self) -> list[DuplicateCandidate]:
        return [c for c in self._candidates.values() if c.is_pending]

    def update_candidate(self, candidate: DuplicateCandidate) -> None:
        key = (candidate.code_a_id.value, candidate.code_b_id.value)
        self._candidates[key] = candidate

    def clear(self) -> None:
        self._results.clear()
        self._candidates.clear()


@dataclass
class MergeSuggestionCache:
    """Cache for pending merge suggestions."""

    _items: dict[str, MergeSuggestion] = field(default_factory=dict)

    def add(self, suggestion: MergeSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def get_by_id(self, suggestion_id: MergeSuggestionId) -> MergeSuggestion | None:
        return self._items.get(suggestion_id.value)

    def get_all_pending(self) -> list[MergeSuggestion]:
        return [s for s in self._items.values() if s.is_pending]

    def update(self, suggestion: MergeSuggestion) -> None:
        self._items[suggestion.id.value] = suggestion

    def remove(self, suggestion_id: MergeSuggestionId) -> None:
        self._items.pop(suggestion_id.value, None)

    def clear(self) -> None:
        self._items.clear()


# ============================================================
# Unified Cache
# ============================================================


@dataclass
class SuggestionCache:
    """
    Unified cache for all AI suggestion types.

    This is the main interface for the MCP tools to use.
    """

    code_suggestions: CodeSuggestionCache = field(default_factory=CodeSuggestionCache)
    coding_suggestions: CodingSuggestionCache = field(default_factory=CodingSuggestionCache)
    duplicate_detections: DuplicateDetectionCache = field(default_factory=DuplicateDetectionCache)
    merge_suggestions: MergeSuggestionCache = field(default_factory=MergeSuggestionCache)

    def clear_all(self) -> None:
        """Clear all cached suggestions."""
        self.code_suggestions.clear()
        self.coding_suggestions.clear()
        self.duplicate_detections.clear()
        self.merge_suggestions.clear()
