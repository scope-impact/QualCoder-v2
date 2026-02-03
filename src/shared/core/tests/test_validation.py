"""
Tests for validation utilities - foundation for invariant functions.

Key business logic tested:
- String validators (non-empty, length bounds)
- Uniqueness validators (collection, name)
- Range validators (valid range, within bounds)
- Numeric validators (positive, non-negative, in_range)
- Hex color validation
- Hierarchy cycle detection (acyclic_hierarchy)
- Collection validators (all_exist, none_exist, has_no_references)
- Composite validators (validate_all, validate_field)
"""

from src.shared.core.validation import (
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


class TestValidationResultHelpers:
    """Test is_valid and is_invalid helpers."""

    def test_is_valid_returns_true_for_success(self):
        assert is_valid(ValidationSuccess()) is True

    def test_is_valid_returns_false_for_failure(self):
        assert is_valid(ValidationFailure(reason="error")) is False

    def test_is_invalid_returns_true_for_failure(self):
        assert is_invalid(ValidationFailure(reason="error")) is True

    def test_is_invalid_returns_false_for_success(self):
        assert is_invalid(ValidationSuccess()) is False


class TestValidationFailure:
    """Test ValidationFailure str representation."""

    def test_str_with_field(self):
        failure = ValidationFailure(reason="must be positive", field="age")

        assert str(failure) == "age: must be positive"

    def test_str_without_field(self):
        failure = ValidationFailure(reason="invalid input")

        assert str(failure) == "invalid input"


class TestIsNonEmptyString:
    """Test is_non_empty_string validator."""

    def test_valid_string(self):
        assert is_non_empty_string("hello") is True

    def test_empty_string(self):
        assert is_non_empty_string("") is False

    def test_whitespace_only(self):
        assert is_non_empty_string("   ") is False

    def test_whitespace_with_tabs_and_newlines(self):
        assert is_non_empty_string("\t\n  ") is False

    def test_string_with_spaces_and_content(self):
        assert is_non_empty_string("  hello  ") is True


class TestIsWithinLength:
    """Test is_within_length validator."""

    def test_within_default_bounds(self):
        assert is_within_length("hello") is True

    def test_at_min_boundary(self):
        assert is_within_length("a", min_len=1) is True

    def test_below_min_boundary(self):
        assert is_within_length("", min_len=1) is False

    def test_at_max_boundary(self):
        assert is_within_length("hello", max_len=5) is True

    def test_above_max_boundary(self):
        assert is_within_length("hello!", max_len=5) is False

    def test_empty_string_with_zero_min(self):
        assert is_within_length("", min_len=0) is True

    def test_none_treated_as_length_zero(self):
        # Edge case: None value should be handled
        assert is_within_length(None, min_len=0) is True
        assert is_within_length(None, min_len=1) is False


class TestIsUniqueInCollection:
    """Test is_unique_in_collection validator."""

    def test_unique_value_in_list(self):
        assert is_unique_in_collection(4, [1, 2, 3]) is True

    def test_duplicate_value_in_list(self):
        assert is_unique_in_collection(2, [1, 2, 3]) is False

    def test_empty_collection_always_unique(self):
        assert is_unique_in_collection("anything", []) is True

    def test_with_key_function(self):
        items = [{"name": "alice"}, {"name": "bob"}]

        assert (
            is_unique_in_collection(
                {"name": "charlie"},
                items,
                key=lambda x: x["name"],
            )
            is True
        )

        assert (
            is_unique_in_collection(
                {"name": "alice"},
                items,
                key=lambda x: x["name"],
            )
            is False
        )

    def test_with_exclude_for_updates(self):
        items = [1, 2, 3]
        # When updating item 2, it should be excluded from uniqueness check
        assert is_unique_in_collection(2, items, exclude=2) is True

    def test_exclude_with_key_function(self):
        items = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]

        # Updating alice's name to "alice" (same name) should be OK
        assert (
            is_unique_in_collection(
                {"id": 1, "name": "alice"},
                items,
                key=lambda x: x["name"],
                exclude={"id": 1, "name": "alice"},
            )
            is True
        )

    def test_none_key_uses_identity(self):
        assert is_unique_in_collection("x", ["a", "b", "c"], key=None) is True
        assert is_unique_in_collection("b", ["a", "b", "c"], key=None) is False


class TestIsNameUnique:
    """Test is_name_unique validator."""

    def test_unique_name(self):
        assert is_name_unique("Charlie", ["Alice", "Bob"]) is True

    def test_duplicate_name(self):
        assert is_name_unique("Alice", ["Alice", "Bob"]) is False

    def test_case_insensitive_default(self):
        assert is_name_unique("ALICE", ["Alice", "Bob"]) is False
        assert is_name_unique("alice", ["Alice", "Bob"]) is False

    def test_case_sensitive_when_enabled(self):
        assert is_name_unique("ALICE", ["Alice", "Bob"], case_sensitive=True) is True
        assert is_name_unique("Alice", ["Alice", "Bob"], case_sensitive=True) is False

    def test_exclude_name_for_renames(self):
        # Renaming "Alice" to "Alice" (no change) should be OK
        assert is_name_unique("Alice", ["Alice", "Bob"], exclude_name="Alice") is True

    def test_exclude_name_case_insensitive(self):
        # Renaming "alice" to "ALICE" should be OK
        assert (
            is_name_unique(
                "ALICE",
                ["Alice", "Bob"],
                case_sensitive=False,
                exclude_name="alice",
            )
            is True
        )

    def test_empty_existing_names(self):
        assert is_name_unique("Any", []) is True

    def test_with_generator(self):
        # Should work with generators, not just lists
        names_gen = (n for n in ["Alice", "Bob"])
        assert is_name_unique("Charlie", names_gen) is True


class TestIsValidRange:
    """Test is_valid_range validator."""

    def test_valid_range(self):
        assert is_valid_range(0, 10) is True

    def test_start_equals_end_invalid(self):
        assert is_valid_range(5, 5) is False

    def test_start_greater_than_end_invalid(self):
        assert is_valid_range(10, 5) is False

    def test_negative_range(self):
        assert is_valid_range(-10, -5) is True


class TestIsWithinBounds:
    """Test is_within_bounds validator."""

    def test_valid_range_within_bounds(self):
        assert is_within_bounds(0, 10, length=20) is True

    def test_start_at_zero(self):
        assert is_within_bounds(0, 5, length=10) is True

    def test_end_at_length(self):
        assert is_within_bounds(5, 10, length=10) is True

    def test_start_negative_invalid(self):
        assert is_within_bounds(-1, 5, length=10) is False

    def test_end_exceeds_length_invalid(self):
        assert is_within_bounds(5, 11, length=10) is False

    def test_start_equals_end_invalid(self):
        assert is_within_bounds(5, 5, length=10) is False

    def test_zero_length_allows_nothing(self):
        assert is_within_bounds(0, 1, length=0) is False
        # Even (0, 0) is invalid because start must be < end
        assert is_within_bounds(0, 0, length=0) is False


class TestNumericValidators:
    """Test is_positive, is_non_negative, is_in_range."""

    def test_is_positive_with_positive(self):
        assert is_positive(1) is True
        assert is_positive(100) is True

    def test_is_positive_with_zero(self):
        assert is_positive(0) is False

    def test_is_positive_with_negative(self):
        assert is_positive(-1) is False

    def test_is_non_negative_with_positive(self):
        assert is_non_negative(1) is True

    def test_is_non_negative_with_zero(self):
        assert is_non_negative(0) is True

    def test_is_non_negative_with_negative(self):
        assert is_non_negative(-1) is False

    def test_is_in_range_within(self):
        assert is_in_range(5, min_val=0, max_val=10) is True

    def test_is_in_range_at_boundaries(self):
        assert is_in_range(0, min_val=0, max_val=10) is True
        assert is_in_range(10, min_val=0, max_val=10) is True

    def test_is_in_range_outside(self):
        assert is_in_range(-1, min_val=0, max_val=10) is False
        assert is_in_range(11, min_val=0, max_val=10) is False


class TestIsValidHexColor:
    """Test is_valid_hex_color validator."""

    def test_valid_uppercase(self):
        assert is_valid_hex_color("#FF0000") is True

    def test_valid_lowercase(self):
        assert is_valid_hex_color("#ff0000") is True

    def test_valid_mixed_case(self):
        assert is_valid_hex_color("#Ff00Ab") is True

    def test_missing_hash(self):
        assert is_valid_hex_color("FF0000") is False

    def test_wrong_length_short(self):
        assert is_valid_hex_color("#F00") is False

    def test_wrong_length_long(self):
        assert is_valid_hex_color("#FF00000") is False

    def test_invalid_characters(self):
        assert is_valid_hex_color("#GGGGGG") is False
        assert is_valid_hex_color("#XY1234") is False

    def test_empty_string(self):
        assert is_valid_hex_color("") is False

    def test_none(self):
        assert is_valid_hex_color(None) is False


class TestIsAcyclicHierarchy:
    """Test is_acyclic_hierarchy - prevents parent-child cycles."""

    def test_moving_to_root_always_safe(self):
        def get_parent(node_id):
            return None

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=None,
                get_parent=get_parent,
            )
            is True
        )

    def test_cannot_be_own_parent(self):
        def get_parent(node_id):
            return None

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=1,
                get_parent=get_parent,
            )
            is False
        )

    def test_detects_direct_cycle(self):
        # Hierarchy: 1 -> 2 (1 is parent of 2)
        # Trying to make 2 the parent of 1 creates cycle
        parents = {1: None, 2: 1}

        def get_parent(node_id):
            return parents.get(node_id)

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=2,
                get_parent=get_parent,
            )
            is False
        )

    def test_detects_indirect_cycle(self):
        # Hierarchy: 1 -> 2 -> 3 (1 is grandparent of 3)
        # Trying to make 3 the parent of 1 creates cycle
        parents = {1: None, 2: 1, 3: 2}

        def get_parent(node_id):
            return parents.get(node_id)

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=3,
                get_parent=get_parent,
            )
            is False
        )

    def test_allows_valid_parent_change(self):
        # Hierarchy: 1, 2 (both roots)
        # Moving 1 under 2 is fine
        parents = {1: None, 2: None}

        def get_parent(node_id):
            return parents.get(node_id)

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=2,
                get_parent=get_parent,
            )
            is True
        )

    def test_allows_sibling_move(self):
        # Hierarchy: root -> [1, 2, 3]
        # Moving 1 under 2 is fine
        parents = {1: "root", 2: "root", 3: "root", "root": None}

        def get_parent(node_id):
            return parents.get(node_id)

        assert (
            is_acyclic_hierarchy(
                node_id=1,
                new_parent_id=2,
                get_parent=get_parent,
            )
            is True
        )

    def test_max_depth_prevents_infinite_loop(self):
        # Simulate corrupted data with infinite loop
        def get_parent(node_id):
            # Always returns something, never reaches root
            return node_id + 1

        # Should return True (no cycle detected within max_depth)
        # rather than hanging forever
        result = is_acyclic_hierarchy(
            node_id=1,
            new_parent_id=2,
            get_parent=get_parent,
            max_depth=10,
        )
        assert result is True  # No cycle found within depth limit


class TestCollectionValidators:
    """Test all_exist, none_exist, has_no_references."""

    def test_all_exist_when_all_present(self):
        existing = {1, 2, 3, 4, 5}

        assert all_exist([1, 2, 3], exists_fn=lambda x: x in existing) is True

    def test_all_exist_when_some_missing(self):
        existing = {1, 2, 3}

        assert all_exist([1, 2, 99], exists_fn=lambda x: x in existing) is False

    def test_all_exist_empty_list(self):
        assert all_exist([], exists_fn=lambda _x: False) is True

    def test_none_exist_when_all_missing(self):
        existing = {1, 2, 3}

        assert none_exist([4, 5, 6], exists_fn=lambda x: x in existing) is True

    def test_none_exist_when_some_present(self):
        existing = {1, 2, 3}

        assert none_exist([3, 4, 5], exists_fn=lambda x: x in existing) is False

    def test_none_exist_empty_list(self):
        assert none_exist([], exists_fn=lambda _x: True) is True

    def test_has_no_references_when_zero(self):
        assert has_no_references(1, count_references=lambda _x: 0) is True

    def test_has_no_references_when_some(self):
        assert has_no_references(1, count_references=lambda _x: 5) is False


class TestValidateAll:
    """Test validate_all composite validator."""

    def test_all_success_returns_success(self):
        result = validate_all(
            ValidationSuccess(),
            ValidationSuccess(),
            ValidationSuccess(),
        )

        assert isinstance(result, ValidationSuccess)

    def test_returns_first_failure(self):
        result = validate_all(
            ValidationSuccess(),
            ValidationFailure(reason="first error"),
            ValidationFailure(reason="second error"),
        )

        assert isinstance(result, ValidationFailure)
        assert result.reason == "first error"

    def test_empty_returns_success(self):
        result = validate_all()

        assert isinstance(result, ValidationSuccess)

    def test_single_failure(self):
        result = validate_all(ValidationFailure(reason="only error"))

        assert isinstance(result, ValidationFailure)


class TestValidateField:
    """Test validate_field helper."""

    def test_valid_field_returns_success(self):
        result = validate_field(
            field_name="age",
            value=25,
            predicate=lambda x: x > 0,
            error_message="must be positive",
        )

        assert isinstance(result, ValidationSuccess)

    def test_invalid_field_returns_failure(self):
        result = validate_field(
            field_name="age",
            value=-5,
            predicate=lambda x: x > 0,
            error_message="must be positive",
        )

        assert isinstance(result, ValidationFailure)
        assert result.field == "age"
        assert result.reason == "must be positive"
        assert result.value == -5

    def test_failure_captures_value(self):
        result = validate_field(
            field_name="name",
            value="",
            predicate=is_non_empty_string,
            error_message="cannot be empty",
        )

        assert result.value == ""
