"""
Merge Policy

Cross-context policy that encapsulates rules for when duplicate codes
can be merged.

This policy bridges:
- ai_services context (DuplicateCandidate)
- coding context (Code, Segment repositories)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Code


class CodeRepository(Protocol):
    """Protocol for code repository operations."""

    def get_by_id(self, code_id: int) -> Code | None: ...


class SegmentCounter(Protocol):
    """Protocol for counting segments."""

    def count_by_code_id(self, code_id: int) -> int: ...


@dataclass(frozen=True)
class MergeDecision:
    """
    Result of merge policy evaluation.

    Attributes:
        allowed: Whether the merge is allowed
        reason: Explanation (required if not allowed)
        source_code: The code to be deleted (if allowed)
        target_code: The code to keep (if allowed)
        segments_to_reassign: Count of segments that will be moved
    """

    allowed: bool
    reason: str | None = None
    source_code: Code | None = None
    target_code: Code | None = None
    segments_to_reassign: int = 0

    @classmethod
    def approve(
        cls,
        source: Code,
        target: Code,
        segment_count: int,
    ) -> MergeDecision:
        """Create an approval decision."""
        return cls(
            allowed=True,
            source_code=source,
            target_code=target,
            segments_to_reassign=segment_count,
        )

    @classmethod
    def deny(cls, reason: str) -> MergeDecision:
        """Create a denial decision."""
        return cls(allowed=False, reason=reason)


class MergePolicy:
    """
    Policy for merging duplicate codes.

    Encapsulates cross-context business rules:
    1. Cannot merge a code with itself
    2. Both codes must exist
    3. Source code must have fewer segments (merge smaller into larger)
    4. Minimum similarity threshold (optional)

    Example:
        policy = MergePolicy(code_repo, segment_counter, min_similarity=0.7)
        decision = policy.can_merge(source_id=5, target_id=3, similarity=0.85)

        if decision.allowed:
            # Proceed with merge
            print(f"Merging {decision.source_code.name} → {decision.target_code.name}")
            print(f"Reassigning {decision.segments_to_reassign} segments")
        else:
            print(f"Cannot merge: {decision.reason}")
    """

    def __init__(
        self,
        code_repo: CodeRepository,
        segment_counter: SegmentCounter | None = None,
        min_similarity: float = 0.0,
        require_smaller_to_larger: bool = True,
    ):
        """
        Initialize the policy.

        Args:
            code_repo: Repository for looking up codes
            segment_counter: Counter for segment counts (optional)
            min_similarity: Minimum similarity threshold (0.0 = no minimum)
            require_smaller_to_larger: If True, merge smaller code into larger
        """
        self._code_repo = code_repo
        self._segment_counter = segment_counter
        self._min_similarity = min_similarity
        self._require_smaller_to_larger = require_smaller_to_larger

    def can_merge(
        self,
        source_code_id: int,
        target_code_id: int,
        similarity: float = 1.0,
    ) -> MergeDecision:
        """
        Evaluate if two codes can be merged.

        Args:
            source_code_id: ID of code to delete (segments moved to target)
            target_code_id: ID of code to keep
            similarity: Similarity score between codes (0.0-1.0)

        Returns:
            MergeDecision with allowed=True and code details,
            or allowed=False with reason
        """
        # Rule 1: Cannot merge with self
        if source_code_id == target_code_id:
            return MergeDecision.deny("Cannot merge a code with itself")

        # Rule 2: Source code must exist
        source = self._code_repo.get_by_id(source_code_id)
        if source is None:
            return MergeDecision.deny(f"Source code {source_code_id} not found")

        # Rule 3: Target code must exist
        target = self._code_repo.get_by_id(target_code_id)
        if target is None:
            return MergeDecision.deny(f"Target code {target_code_id} not found")

        # Rule 4: Similarity threshold
        if similarity < self._min_similarity:
            return MergeDecision.deny(
                f"Similarity {similarity:.0%} below minimum {self._min_similarity:.0%}"
            )

        # Count segments for source
        segment_count = 0
        if self._segment_counter is not None:
            source_count = self._segment_counter.count_by_code_id(source_code_id)
            target_count = self._segment_counter.count_by_code_id(target_code_id)
            segment_count = source_count

            # Rule 5: Merge smaller into larger (optional)
            if self._require_smaller_to_larger and source_count > target_count:
                return MergeDecision.deny(
                    f"Source has more segments ({source_count}) than target ({target_count}). "
                    "Reverse the merge direction."
                )

        return MergeDecision.approve(source, target, segment_count)


def evaluate_merge(
    source_code_id: int,
    target_code_id: int,
    code_repo: CodeRepository,
    segment_counter: SegmentCounter | None = None,
    similarity: float = 1.0,
    min_similarity: float = 0.0,
) -> Result[tuple[Code, Code, int], str]:
    """
    Functional interface for merge policy.

    Convenience function that creates a policy and evaluates in one call.

    Args:
        source_code_id: ID of code to delete
        target_code_id: ID of code to keep
        code_repo: Repository for looking up codes
        segment_counter: Counter for segment counts
        similarity: Similarity score between codes
        min_similarity: Minimum similarity threshold

    Returns:
        Success with (source_code, target_code, segment_count) or Failure with reason
    """
    policy = MergePolicy(
        code_repo,
        segment_counter,
        min_similarity,
        require_smaller_to_larger=False,  # Don't enforce in functional interface
    )
    decision = policy.can_merge(source_code_id, target_code_id, similarity)

    if decision.allowed:
        return Success(
            (
                decision.source_code,
                decision.target_code,
                decision.segments_to_reassign,
            )
        )
    return Failure(decision.reason)
