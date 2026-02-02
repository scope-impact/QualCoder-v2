"""
Tests for AI Services Policies

Tests cover:
- SuggestionApprovalPolicy rules
- MergePolicy rules
- Functional interfaces
"""

from __future__ import annotations

from returns.result import Failure, Success

from src.application.ai_services.policies import (
    ApprovalDecision,
    MergeDecision,
    MergePolicy,
    SuggestionApprovalPolicy,
    evaluate_approval,
    evaluate_merge,
)
from src.contexts.ai_services.core.entities import CodeSuggestion, SuggestionId
from src.contexts.coding.core.entities import Code, Color
from src.contexts.shared.core.types import CodeId

# =============================================================================
# Test Fixtures
# =============================================================================


class MockCodeLookup:
    """Mock code lookup for testing."""

    def __init__(self, existing_codes: dict[str, Code] | None = None):
        self._by_name: dict[str, Code] = existing_codes or {}

    def get_by_name(self, name: str) -> Code | None:
        return self._by_name.get(name)


class MockCodeRepository:
    """Mock code repository for merge policy testing."""

    def __init__(self, codes: dict[int, Code] | None = None):
        self._codes: dict[int, Code] = codes or {}

    def get_by_id(self, code_id: int) -> Code | None:
        return self._codes.get(code_id)


class MockSegmentCounter:
    """Mock segment counter for merge policy testing."""

    def __init__(self, counts: dict[int, int] | None = None):
        self._counts: dict[int, int] = counts or {}

    def count_by_code_id(self, code_id: int) -> int:
        return self._counts.get(code_id, 0)


def make_suggestion(
    suggestion_id: str = "sug-1",
    name: str = "Test Code",
    color: str = "#FF0000",
    confidence: float = 0.8,
) -> CodeSuggestion:
    """Create a test suggestion."""
    return CodeSuggestion(
        id=SuggestionId(value=suggestion_id),
        name=name,
        color=Color.from_hex(color),
        rationale="Test rationale",
        contexts=(),
        confidence=confidence,
    )


def make_code(code_id: int = 1, name: str = "Existing Code") -> Code:
    """Create a test code."""
    return Code(
        id=CodeId(value=code_id),
        name=name,
        color=Color.from_hex("#00FF00"),
        memo=None,
        category_id=None,
        owner=None,
    )


# =============================================================================
# SuggestionApprovalPolicy Tests
# =============================================================================


class TestSuggestionApprovalPolicy:
    """Tests for SuggestionApprovalPolicy."""

    def test_approves_valid_suggestion(self):
        """Policy approves when all rules pass."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "New Theme")

        assert decision.allowed is True
        assert decision.validated_name == "New Theme"
        assert decision.validated_color is not None
        assert decision.reason is None

    def test_denies_empty_name(self):
        """Policy denies empty name."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "")

        assert decision.allowed is False
        assert "empty" in decision.reason.lower()

    def test_denies_whitespace_only_name(self):
        """Policy denies whitespace-only name."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "   \t\n  ")

        assert decision.allowed is False
        assert "empty" in decision.reason.lower()

    def test_denies_duplicate_name(self):
        """Policy denies when name already exists."""
        existing = make_code(name="Duplicate Name")
        lookup = MockCodeLookup({"Duplicate Name": existing})
        policy = SuggestionApprovalPolicy(lookup)
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "Duplicate Name")

        assert decision.allowed is False
        assert "already exists" in decision.reason.lower()

    def test_denies_below_confidence_threshold(self):
        """Policy denies when confidence is below threshold."""
        policy = SuggestionApprovalPolicy(MockCodeLookup(), min_confidence=0.7)
        suggestion = make_suggestion(confidence=0.5)

        decision = policy.can_approve(suggestion, "Test Code")

        assert decision.allowed is False
        assert "confidence" in decision.reason.lower()

    def test_approves_at_confidence_threshold(self):
        """Policy approves when confidence equals threshold."""
        policy = SuggestionApprovalPolicy(MockCodeLookup(), min_confidence=0.7)
        suggestion = make_suggestion(confidence=0.7)

        decision = policy.can_approve(suggestion, "Test Code")

        assert decision.allowed is True

    def test_denies_name_too_long(self):
        """Policy denies names exceeding max length."""
        policy = SuggestionApprovalPolicy(MockCodeLookup(), max_name_length=10)
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "This name is too long")

        assert decision.allowed is False
        assert "exceeds" in decision.reason.lower()

    def test_denies_invalid_color(self):
        """Policy denies invalid color format."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "Valid Name", "not-a-color")

        assert decision.allowed is False
        assert "color" in decision.reason.lower()

    def test_uses_suggestion_color_when_not_overridden(self):
        """Policy uses suggestion color when no override provided."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion(color="#AABBCC")

        decision = policy.can_approve(suggestion, "Valid Name")

        assert decision.allowed is True
        assert decision.validated_color.to_hex().lower() == "#aabbcc"

    def test_uses_override_color_when_provided(self):
        """Policy uses override color when provided."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion(color="#AABBCC")

        decision = policy.can_approve(suggestion, "Valid Name", "#112233")

        assert decision.allowed is True
        assert decision.validated_color.to_hex().lower() == "#112233"

    def test_strips_whitespace_from_name(self):
        """Policy strips whitespace from name."""
        policy = SuggestionApprovalPolicy(MockCodeLookup())
        suggestion = make_suggestion()

        decision = policy.can_approve(suggestion, "  Padded Name  ")

        assert decision.allowed is True
        assert decision.validated_name == "Padded Name"


class TestApprovalDecision:
    """Tests for ApprovalDecision dataclass."""

    def test_approve_factory(self):
        """Test approve factory method."""
        color = Color.from_hex("#FF0000")
        decision = ApprovalDecision.approve("Test", color)

        assert decision.allowed is True
        assert decision.validated_name == "Test"
        assert decision.validated_color == color
        assert decision.reason is None

    def test_deny_factory(self):
        """Test deny factory method."""
        decision = ApprovalDecision.deny("Not allowed")

        assert decision.allowed is False
        assert decision.reason == "Not allowed"
        assert decision.validated_name is None
        assert decision.validated_color is None


class TestEvaluateApprovalFunction:
    """Tests for evaluate_approval functional interface."""

    def test_returns_success_on_approval(self):
        """Functional interface returns Success on approval."""
        suggestion = make_suggestion()

        result = evaluate_approval(
            suggestion=suggestion,
            final_name="New Code",
            final_color="#FF0000",
            code_lookup=MockCodeLookup(),
        )

        assert isinstance(result, Success)
        name, color = result.unwrap()
        assert name == "New Code"
        assert color.to_hex().lower() == "#ff0000"

    def test_returns_failure_on_denial(self):
        """Functional interface returns Failure on denial."""
        suggestion = make_suggestion()

        result = evaluate_approval(
            suggestion=suggestion,
            final_name="",
            final_color="#FF0000",
            code_lookup=MockCodeLookup(),
        )

        assert isinstance(result, Failure)
        assert "empty" in result.failure().lower()


# =============================================================================
# MergePolicy Tests
# =============================================================================


class TestMergePolicy:
    """Tests for MergePolicy."""

    def test_approves_valid_merge(self):
        """Policy approves valid merge."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        policy = MergePolicy(repo)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is True
        assert decision.source_code == source
        assert decision.target_code == target

    def test_denies_merge_with_self(self):
        """Policy denies merging code with itself."""
        code = make_code(1, "Code")
        repo = MockCodeRepository({1: code})
        policy = MergePolicy(repo)

        decision = policy.can_merge(1, 1)

        assert decision.allowed is False
        assert "itself" in decision.reason.lower()

    def test_denies_missing_source(self):
        """Policy denies when source code not found."""
        target = make_code(2, "Target")
        repo = MockCodeRepository({2: target})
        policy = MergePolicy(repo)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is False
        assert "source" in decision.reason.lower()
        assert "not found" in decision.reason.lower()

    def test_denies_missing_target(self):
        """Policy denies when target code not found."""
        source = make_code(1, "Source")
        repo = MockCodeRepository({1: source})
        policy = MergePolicy(repo)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is False
        assert "target" in decision.reason.lower()
        assert "not found" in decision.reason.lower()

    def test_denies_below_similarity_threshold(self):
        """Policy denies when similarity is below threshold."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        policy = MergePolicy(repo, min_similarity=0.8)

        decision = policy.can_merge(1, 2, similarity=0.5)

        assert decision.allowed is False
        assert "similarity" in decision.reason.lower()

    def test_approves_at_similarity_threshold(self):
        """Policy approves when similarity equals threshold."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        policy = MergePolicy(repo, min_similarity=0.8)

        decision = policy.can_merge(1, 2, similarity=0.8)

        assert decision.allowed is True

    def test_counts_segments_to_reassign(self):
        """Policy counts segments that will be reassigned."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        counter = MockSegmentCounter({1: 5, 2: 10})
        policy = MergePolicy(repo, counter)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is True
        assert decision.segments_to_reassign == 5

    def test_denies_larger_into_smaller_when_required(self):
        """Policy denies merging larger into smaller when required."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        counter = MockSegmentCounter({1: 10, 2: 5})  # Source has more
        policy = MergePolicy(repo, counter, require_smaller_to_larger=True)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is False
        assert "reverse" in decision.reason.lower()

    def test_allows_larger_into_smaller_when_not_required(self):
        """Policy allows merging larger into smaller when not required."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})
        counter = MockSegmentCounter({1: 10, 2: 5})
        policy = MergePolicy(repo, counter, require_smaller_to_larger=False)

        decision = policy.can_merge(1, 2)

        assert decision.allowed is True


class TestMergeDecision:
    """Tests for MergeDecision dataclass."""

    def test_approve_factory(self):
        """Test approve factory method."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        decision = MergeDecision.approve(source, target, 5)

        assert decision.allowed is True
        assert decision.source_code == source
        assert decision.target_code == target
        assert decision.segments_to_reassign == 5
        assert decision.reason is None

    def test_deny_factory(self):
        """Test deny factory method."""
        decision = MergeDecision.deny("Not allowed")

        assert decision.allowed is False
        assert decision.reason == "Not allowed"
        assert decision.source_code is None
        assert decision.target_code is None


class TestEvaluateMergeFunction:
    """Tests for evaluate_merge functional interface."""

    def test_returns_success_on_approval(self):
        """Functional interface returns Success on approval."""
        source = make_code(1, "Source")
        target = make_code(2, "Target")
        repo = MockCodeRepository({1: source, 2: target})

        result = evaluate_merge(
            source_code_id=1,
            target_code_id=2,
            code_repo=repo,
        )

        assert isinstance(result, Success)
        src, tgt, count = result.unwrap()
        assert src == source
        assert tgt == target

    def test_returns_failure_on_denial(self):
        """Functional interface returns Failure on denial."""
        repo = MockCodeRepository({})

        result = evaluate_merge(
            source_code_id=1,
            target_code_id=2,
            code_repo=repo,
        )

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()
