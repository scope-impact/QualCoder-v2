"""
AI Services Policies

Cross-context policies that encapsulate business rules for AI-powered
code management operations.

Policies provide:
- Explicit, testable business rules
- Cross-context validation
- Configurable thresholds
- Clear decision objects with reasons

Usage:
    from src.application.ai_services.policies import (
        SuggestionApprovalPolicy,
        MergePolicy,
        evaluate_approval,
        evaluate_merge,
    )

    # OOP interface
    policy = SuggestionApprovalPolicy(code_repo, min_confidence=0.5)
    decision = policy.can_approve(suggestion, "Theme: Learning")

    # Functional interface
    result = evaluate_approval(suggestion, name, color, code_repo)
"""

from .approval_policy import (
    ApprovalDecision,
    SuggestionApprovalPolicy,
    evaluate_approval,
)
from .merge_policy import (
    MergeDecision,
    MergePolicy,
    evaluate_merge,
)

__all__ = [
    # Approval Policy
    "ApprovalDecision",
    "SuggestionApprovalPolicy",
    "evaluate_approval",
    # Merge Policy
    "MergeDecision",
    "MergePolicy",
    "evaluate_merge",
]
