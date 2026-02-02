"""
Tests for shared validation utilities.

These utilities provide common validation patterns used across all bounded contexts.
"""

from src.contexts.shared.core.validation import (
    ValidationFailure,
    ValidationSuccess,
    all_exist,
    has_no_references,
    is_acyclic_hierarchy,
    is_in_range,
    is_invalid,
    is_name_unique,
    is_non_empty_string,
    is_non_negative,
    is_positive,
    is_unique_in_collection,
    is_valid,
    is_valid_hex_color,
    is_valid_range,
    is_within_bounds,
    is_within_length,
    none_exist,
    validate_all,
    validate_field,
)


class TestValidationResultTypes:
    """Tests for ValidationSuccess and ValidationFailure types."""

    def test_is_valid_returns_true_for_success(self):
        """is_valid should return True for ValidationSuccess."""
        result = ValidationSuccess()
        assert is_valid(result) is True

    def test_is_valid_returns_false_for_failure(self):
        """is_valid should return False for ValidationFailure."""
        result = ValidationFailure(reason="test error")
        assert is_valid(result) is False

    def test_is_invalid_returns_true_for_failure(self):
        """is_invalid should return True for ValidationFailure."""
        result = ValidationFailure(reason="test error")
        assert is_invalid(result) is True

    def test_is_invalid_returns_false_for_success(self):
        """is_invalid should return False for ValidationSuccess."""
        result = ValidationSuccess()
        assert is_invalid(result) is False

    def test_validation_failure_str_without_field(self):
        """ValidationFailure str should just show reason without field."""
        failure = ValidationFailure(reason="Name is required")
        assert str(failure) == "Name is required"

    def test_validation_failure_str_with_field(self):
        """ValidationFailure str should show field and reason."""
        failure = ValidationFailure(reason="is required", field="name")
        assert str(failure) == "name: is required"


class TestStringValidators:
    """Tests for string validation utilities."""

    def test_is_non_empty_string_accepts_normal_strings(self):
        """Normal strings should pass."""
        assert is_non_empty_string("hello") is True
        assert is_non_empty_string("a") is True
        assert is_non_empty_string("Hello World") is True

    def test_is_non_empty_string_rejects_empty(self):
        """Empty strings should fail."""
        assert is_non_empty_string("") is False

    def test_is_non_empty_string_rejects_whitespace_only(self):
        """Whitespace-only strings should fail."""
        assert is_non_empty_string("   ") is False
        assert is_non_empty_string("\t\n") is False
        assert is_non_empty_string("  \t  \n  ") is False

    def test_is_within_length_accepts_valid_lengths(self):
        """Strings within length bounds should pass."""
        assert is_within_length("hello", 0, 10) is True
        assert is_within_length("hello", 5, 5) is True  # Exact length
        assert is_within_length("", 0, 10) is True  # Empty with min 0

    def test_is_within_length_rejects_too_short(self):
        """Strings shorter than min should fail."""
        assert is_within_length("hi", 5, 10) is False

    def test_is_within_length_rejects_too_long(self):
        """Strings longer than max should fail."""
        assert is_within_length("hello world", 0, 5) is False


class TestUniquenessValidators:
    """Tests for uniqueness validation utilities."""

    def test_is_unique_in_collection_empty(self):
        """Any value is unique in empty collection."""
        assert is_unique_in_collection("test", []) is True

    def test_is_unique_in_collection_with_duplicates(self):
        """Duplicate values should be detected."""
        assert is_unique_in_collection("a", ["a", "b", "c"]) is False

    def test_is_unique_in_collection_without_duplicates(self):
        """Unique values should pass."""
        assert is_unique_in_collection("d", ["a", "b", "c"]) is True

    def test_is_unique_in_collection_with_key_function(self):
        """Key function should be used for comparison."""
        items = [{"name": "Alice"}, {"name": "Bob"}]
        assert (
            is_unique_in_collection({"name": "Alice"}, items, key=lambda x: x["name"])
            is False
        )
        assert (
            is_unique_in_collection({"name": "Charlie"}, items, key=lambda x: x["name"])
            is True
        )

    def test_is_unique_in_collection_with_exclude(self):
        """Excluded item should be ignored."""
        assert is_unique_in_collection("a", ["a", "b", "c"], exclude="a") is True

    def test_is_name_unique_case_insensitive(self):
        """Default case-insensitive matching."""
        names = ["Alice", "Bob", "Charlie"]
        assert is_name_unique("alice", names) is False
        assert is_name_unique("ALICE", names) is False
        assert is_name_unique("Dave", names) is True

    def test_is_name_unique_case_sensitive(self):
        """Case-sensitive matching when specified."""
        names = ["Alice", "Bob", "Charlie"]
        assert is_name_unique("alice", names, case_sensitive=True) is True
        assert is_name_unique("Alice", names, case_sensitive=True) is False

    def test_is_name_unique_with_exclude(self):
        """Excluded name should be ignored."""
        names = ["Alice", "Bob", "Charlie"]
        assert is_name_unique("Alice", names, exclude_name="Alice") is True


class TestRangeValidators:
    """Tests for range validation utilities."""

    def test_is_valid_range_accepts_valid(self):
        """start < end should pass."""
        assert is_valid_range(0, 10) is True
        assert is_valid_range(-5, 5) is True

    def test_is_valid_range_rejects_invalid(self):
        """start >= end should fail."""
        assert is_valid_range(10, 10) is False
        assert is_valid_range(10, 5) is False

    def test_is_within_bounds_accepts_valid(self):
        """Valid ranges within bounds should pass."""
        assert is_within_bounds(0, 10, 100) is True
        assert is_within_bounds(0, 100, 100) is True

    def test_is_within_bounds_rejects_negative_start(self):
        """Negative start should fail."""
        assert is_within_bounds(-1, 10, 100) is False

    def test_is_within_bounds_rejects_end_exceeds_length(self):
        """End exceeding length should fail."""
        assert is_within_bounds(0, 101, 100) is False

    def test_is_positive_accepts_positive(self):
        """Positive values should pass."""
        assert is_positive(1) is True
        assert is_positive(100) is True

    def test_is_positive_rejects_zero_and_negative(self):
        """Zero and negative values should fail."""
        assert is_positive(0) is False
        assert is_positive(-1) is False

    def test_is_non_negative_accepts_zero_and_positive(self):
        """Zero and positive should pass."""
        assert is_non_negative(0) is True
        assert is_non_negative(1) is True

    def test_is_non_negative_rejects_negative(self):
        """Negative values should fail."""
        assert is_non_negative(-1) is False

    def test_is_in_range_accepts_values_in_range(self):
        """Values within range should pass."""
        assert is_in_range(5, 0, 10) is True
        assert is_in_range(0, 0, 10) is True  # At min
        assert is_in_range(10, 0, 10) is True  # At max

    def test_is_in_range_rejects_out_of_range(self):
        """Values outside range should fail."""
        assert is_in_range(-1, 0, 10) is False
        assert is_in_range(11, 0, 10) is False


class TestHexColorValidator:
    """Tests for hex color validation."""

    def test_is_valid_hex_color_accepts_valid(self):
        """Valid hex colors should pass."""
        assert is_valid_hex_color("#000000") is True
        assert is_valid_hex_color("#FFFFFF") is True
        assert is_valid_hex_color("#ff00ff") is True
        assert is_valid_hex_color("#123ABC") is True

    def test_is_valid_hex_color_rejects_invalid(self):
        """Invalid hex colors should fail."""
        assert is_valid_hex_color("") is False
        assert is_valid_hex_color("#FFF") is False  # Too short
        assert is_valid_hex_color("000000") is False  # Missing #
        assert is_valid_hex_color("#GGGGGG") is False  # Invalid chars
        assert is_valid_hex_color("#00000") is False  # Wrong length


class TestHierarchyValidation:
    """Tests for acyclic hierarchy validation."""

    def test_is_acyclic_hierarchy_root_always_valid(self):
        """Moving to root (None parent) should always be valid."""

        def get_parent(_x):
            return None

        assert is_acyclic_hierarchy("node1", None, get_parent) is True

    def test_is_acyclic_hierarchy_self_parent_invalid(self):
        """Node cannot be its own parent."""

        def get_parent(_x):
            return None

        assert is_acyclic_hierarchy("node1", "node1", get_parent) is False

    def test_is_acyclic_hierarchy_detects_cycle(self):
        """Should detect cycles in hierarchy."""
        # A -> B -> C, trying to make C parent of A
        parents = {"A": "B", "B": "C", "C": None}

        def get_parent(x):
            return parents.get(x)

        # Making A child of C is valid (no cycle)
        assert is_acyclic_hierarchy("A", "C", get_parent) is True

        # But making C child of A would create cycle (A->B->C->A)
        # Since C's current parent is None, we're testing hypothetically
        # If we made C's parent A, then walk from A: A->B->C, so we'd hit C
        # Actually the test is: if node_id=C is going to have new_parent=A,
        # we walk from A upward and check if we hit C
        # A's parent is B, B's parent is C, so we DO hit C - cycle detected
        # Wait, the function checks if walking UP from new_parent hits node_id
        # new_parent = A, node_id = C
        # Walk: A -> B -> C -> None
        # We hit C (node_id), so cycle detected
        assert is_acyclic_hierarchy("C", "A", get_parent) is False

    def test_is_acyclic_hierarchy_valid_reparenting(self):
        """Valid reparenting should be allowed."""
        # A -> B -> C, move C directly under A
        parents = {"A": None, "B": "A", "C": "B"}

        def get_parent(x):
            return parents.get(x)

        # Move C to be child of A directly
        # Walk from A: A -> None (no cycle)
        assert is_acyclic_hierarchy("C", "A", get_parent) is True


class TestCollectionValidation:
    """Tests for collection validation utilities."""

    def test_all_exist_returns_true_when_all_exist(self):
        """Should return True when all IDs exist."""

        def exists_fn(x):
            return x in [1, 2, 3]

        assert all_exist([1, 2, 3], exists_fn) is True
        assert all_exist([1, 2], exists_fn) is True
        assert all_exist([], exists_fn) is True  # Empty list

    def test_all_exist_returns_false_when_any_missing(self):
        """Should return False when any ID doesn't exist."""

        def exists_fn(x):
            return x in [1, 2, 3]

        assert all_exist([1, 2, 4], exists_fn) is False

    def test_none_exist_returns_true_when_none_exist(self):
        """Should return True when no IDs exist."""

        def exists_fn(x):
            return x in [1, 2, 3]

        assert none_exist([4, 5, 6], exists_fn) is True
        assert none_exist([], exists_fn) is True

    def test_none_exist_returns_false_when_any_exist(self):
        """Should return False when any ID exists."""

        def exists_fn(x):
            return x in [1, 2, 3]

        assert none_exist([3, 4, 5], exists_fn) is False

    def test_has_no_references_returns_true_for_zero(self):
        """Should return True when count is zero."""

        def count_fn(_x):
            return 0

        assert has_no_references("any_id", count_fn) is True

    def test_has_no_references_returns_false_for_nonzero(self):
        """Should return False when count is nonzero."""

        def count_fn(_x):
            return 5

        assert has_no_references("any_id", count_fn) is False


class TestCompositeValidation:
    """Tests for composite validation utilities."""

    def test_validate_all_returns_success_for_all_success(self):
        """Should return Success when all results are Success."""
        result = validate_all(
            ValidationSuccess(),
            ValidationSuccess(),
            ValidationSuccess(),
        )
        assert isinstance(result, ValidationSuccess)

    def test_validate_all_returns_first_failure(self):
        """Should return first Failure encountered."""
        result = validate_all(
            ValidationSuccess(),
            ValidationFailure(reason="First error"),
            ValidationFailure(reason="Second error"),
        )
        assert isinstance(result, ValidationFailure)
        assert result.reason == "First error"

    def test_validate_all_with_empty_args(self):
        """Should return Success for empty args."""
        result = validate_all()
        assert isinstance(result, ValidationSuccess)

    def test_validate_field_returns_success_when_valid(self):
        """Should return Success when predicate passes."""
        result = validate_field(
            field_name="name",
            value="hello",
            predicate=lambda x: len(x) > 0,
            error_message="Name is required",
        )
        assert isinstance(result, ValidationSuccess)

    def test_validate_field_returns_failure_when_invalid(self):
        """Should return Failure when predicate fails."""
        result = validate_field(
            field_name="name",
            value="",
            predicate=lambda x: len(x) > 0,
            error_message="Name is required",
        )
        assert isinstance(result, ValidationFailure)
        assert result.field == "name"
        assert result.reason == "Name is required"
        assert result.value == ""
