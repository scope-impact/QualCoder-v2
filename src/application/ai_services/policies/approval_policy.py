"""
Suggestion Approval Policy

Cross-context policy that encapsulates rules for when an AI code suggestion
can be approved and converted into a Code entity.

This policy bridges:
- ai_services context (CodeSuggestion)
- coding context (Code, CodeRepository)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from returns.result import Failure, Result, Success

from src.contexts.coding.core.entities import Color

if TYPE_CHECKING:
    from src.contexts.ai_services.core.entities import CodeSuggestion
    from src.contexts.coding.core.entities import Code


class CodeLookup(Protocol):
    """Protocol for looking up codes by name."""

    def get_by_name(self, name: str) -> Code | None: ...


@dataclass(frozen=True)
class ApprovalDecision:
    """
    Result of policy evaluation.

    Attributes:
        allowed: Whether the approval is allowed
        reason: Explanation (required if not allowed)
        validated_name: Cleaned/validated name (if allowed)
        validated_color: Parsed Color object (if allowed)
    """

    allowed: bool
    reason: str | None = None
    validated_name: str | None = None
    validated_color: Color | None = None

    @classmethod
    def approve(cls, name: str, color: Color) -> ApprovalDecision:
        """Create an approval decision."""
        return cls(allowed=True, validated_name=name, validated_color=color)

    @classmethod
    def deny(cls, reason: str) -> ApprovalDecision:
        """Create a denial decision."""
        return cls(allowed=False, reason=reason)


class SuggestionApprovalPolicy:
    """
    Policy for approving AI code suggestions.

    Encapsulates cross-context business rules:
    1. Name cannot be empty
    2. Name must be unique in coding context
    3. Color must be valid hex format
    4. Confidence must meet threshold (optional)

    Example:
        policy = SuggestionApprovalPolicy(code_repo, min_confidence=0.5)
        decision = policy.can_approve(suggestion, final_name="Theme: Learning")

        if decision.allowed:
            # Proceed with approval
            code = Code(name=decision.validated_name, color=decision.validated_color, ...)
        else:
            # Handle denial
            print(f"Cannot approve: {decision.reason}")
    """

    def __init__(
        self,
        code_lookup: CodeLookup,
        min_confidence: float = 0.0,
        max_name_length: int = 100,
    ):
        """
        Initialize the policy.

        Args:
            code_lookup: Protocol for checking code name uniqueness
            min_confidence: Minimum confidence threshold (0.0 = no minimum)
            max_name_length: Maximum allowed code name length
        """
        self._code_lookup = code_lookup
        self._min_confidence = min_confidence
        self._max_name_length = max_name_length

    def can_approve(
        self,
        suggestion: CodeSuggestion,
        final_name: str,
        final_color: str | None = None,
    ) -> ApprovalDecision:
        """
        Evaluate if a suggestion can be approved.

        Args:
            suggestion: The AI suggestion to approve
            final_name: The name to use (may differ from suggestion)
            final_color: Override color (uses suggestion color if None)

        Returns:
            ApprovalDecision with allowed=True and validated values,
            or allowed=False with reason
        """
        # Rule 1: Name cannot be empty
        cleaned_name = final_name.strip() if final_name else ""
        if not cleaned_name:
            return ApprovalDecision.deny("Code name cannot be empty")

        # Rule 2: Name length limit
        if len(cleaned_name) > self._max_name_length:
            return ApprovalDecision.deny(
                f"Code name exceeds {self._max_name_length} characters"
            )

        # Rule 3: Name must be unique
        existing = self._code_lookup.get_by_name(cleaned_name)
        if existing is not None:
            return ApprovalDecision.deny(f"Code '{cleaned_name}' already exists")

        # Rule 4: Confidence threshold
        if suggestion.confidence < self._min_confidence:
            return ApprovalDecision.deny(
                f"Confidence {suggestion.confidence:.0%} below minimum {self._min_confidence:.0%}"
            )

        # Rule 5: Color must be valid
        color_hex = final_color or suggestion.color.to_hex()
        try:
            validated_color = Color.from_hex(color_hex)
        except ValueError as e:
            return ApprovalDecision.deny(f"Invalid color format: {e}")

        return ApprovalDecision.approve(cleaned_name, validated_color)


def evaluate_approval(
    suggestion: CodeSuggestion,
    final_name: str,
    final_color: str,
    code_lookup: CodeLookup,
    min_confidence: float = 0.0,
) -> Result[tuple[str, Color], str]:
    """
    Functional interface for approval policy.

    Convenience function that creates a policy and evaluates in one call.

    Args:
        suggestion: The suggestion to evaluate
        final_name: Name to use for the code
        final_color: Color hex string
        code_lookup: Protocol for name uniqueness check
        min_confidence: Minimum confidence threshold

    Returns:
        Success with (validated_name, validated_color) or Failure with reason
    """
    policy = SuggestionApprovalPolicy(code_lookup, min_confidence)
    decision = policy.can_approve(suggestion, final_name, final_color)

    if decision.allowed:
        return Success((decision.validated_name, decision.validated_color))
    return Failure(decision.reason)
