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

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Core"),
]

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


@allure.story("QC-000.01 Validation Utilities")
class TestValidationResultHelpers:
    """Test is_valid and is_invalid helpers."""

    @allure.title("is_valid returns True for success, is_invalid returns True for failure")
    def test_is_valid_and_is_invalid(self):
        success = ValidationSuccess()
        failure = ValidationFailure(reason="error")

        assert is_valid(success) is True
        assert is_valid(failure) is False
        assert is_invalid(failure) is True
        assert is_invalid(success) is False


@allure.story("QC-000.01 Validation Utilities")
class TestValidationFailure:
    """Test ValidationFailure str representation."""

    @allure.title("ValidationFailure str includes field name when present")
    def test_str_with_and_without_field(self):
        with_field = ValidationFailure(reason="must be positive", field="age")
        without_field = ValidationFailure(reason="invalid input")

        assert str(with_field) == "age: must be positive"
        assert str(without_field) == "invalid input"


@allure.story("QC-000.01 Validation Utilities")
class TestIsNonEmptyString:
    """Test is_non_empty_string validator."""

    @allure.title("is_non_empty_string validates non-blank strings")
    @pytest.mark.parametrize("value, expected", [
        ("hello", True),
        ("", False),
        ("   ", False),
        ("\t\n  ", False),
        ("  hello  ", True),
    ])
    def test_is_non_empty_string(self, value, expected):
        assert is_non_empty_string(value) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestIsWithinLength:
    """Test is_within_length validator."""

    @allure.title("is_within_length validates string length bounds")
    @pytest.mark.parametrize("value, kwargs, expected", [
        ("hello", {}, True),
        ("a", {"min_len": 1}, True),
        ("", {"min_len": 1}, False),
        ("hello", {"max_len": 5}, True),
        ("hello!", {"max_len": 5}, False),
        ("", {"min_len": 0}, True),
        (None, {"min_len": 0}, True),
        (None, {"min_len": 1}, False),
    ])
    def test_is_within_length(self, value, kwargs, expected):
        assert is_within_length(value, **kwargs) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestIsUniqueInCollection:
    """Test is_unique_in_collection validator."""

    @allure.title("is_unique_in_collection detects duplicates in basic cases")
    def test_basic_cases(self):
        assert is_unique_in_collection(4, [1, 2, 3]) is True
        assert is_unique_in_collection(2, [1, 2, 3]) is False
        assert is_unique_in_collection("anything", []) is True
        assert is_unique_in_collection("x", ["a", "b", "c"], key=None) is True
        assert is_unique_in_collection("b", ["a", "b", "c"], key=None) is False

    @allure.title("is_unique_in_collection supports key function and exclude")
    def test_with_key_and_exclude(self):
        items = [{"name": "alice"}, {"name": "bob"}]
        key = lambda x: x["name"]

        assert is_unique_in_collection({"name": "charlie"}, items, key=key) is True
        assert is_unique_in_collection({"name": "alice"}, items, key=key) is False

        # exclude for updates
        assert is_unique_in_collection(2, [1, 2, 3], exclude=2) is True

        # exclude with key function
        items_with_id = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
        assert (
            is_unique_in_collection(
                {"id": 1, "name": "alice"},
                items_with_id,
                key=key,
                exclude={"id": 1, "name": "alice"},
            )
            is True
        )


@allure.story("QC-000.01 Validation Utilities")
class TestIsNameUnique:
    """Test is_name_unique validator."""

    @allure.title("is_name_unique validates case-insensitive name uniqueness")
    def test_basic_cases(self):
        assert is_name_unique("Charlie", ["Alice", "Bob"]) is True
        assert is_name_unique("Alice", ["Alice", "Bob"]) is False
        # case insensitive by default
        assert is_name_unique("ALICE", ["Alice", "Bob"]) is False
        assert is_name_unique("alice", ["Alice", "Bob"]) is False
        # empty list
        assert is_name_unique("Any", []) is True
        # generator support
        names_gen = (n for n in ["Alice", "Bob"])
        assert is_name_unique("Charlie", names_gen) is True

    @allure.title("is_name_unique supports case_sensitive and exclude_name options")
    def test_options_case_sensitive_and_exclude(self):
        assert is_name_unique("ALICE", ["Alice", "Bob"], case_sensitive=True) is True
        assert is_name_unique("Alice", ["Alice", "Bob"], case_sensitive=True) is False
        # exclude for renames
        assert is_name_unique("Alice", ["Alice", "Bob"], exclude_name="Alice") is True
        # exclude case insensitive
        assert (
            is_name_unique(
                "ALICE",
                ["Alice", "Bob"],
                case_sensitive=False,
                exclude_name="alice",
            )
            is True
        )


@allure.story("QC-000.01 Validation Utilities")
class TestIsValidRange:
    """Test is_valid_range validator."""

    @allure.title("is_valid_range validates start < end")
    @pytest.mark.parametrize("start, end, expected", [
        (0, 10, True),
        (5, 5, False),
        (10, 5, False),
        (-10, -5, True),
    ])
    def test_is_valid_range(self, start, end, expected):
        assert is_valid_range(start, end) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestIsWithinBounds:
    """Test is_within_bounds validator."""

    @allure.title("is_within_bounds validates range fits within length")
    @pytest.mark.parametrize("start, end, length, expected", [
        (0, 10, 20, True),
        (0, 5, 10, True),
        (5, 10, 10, True),
        (-1, 5, 10, False),
        (5, 11, 10, False),
        (5, 5, 10, False),
        (0, 1, 0, False),
        (0, 0, 0, False),
    ])
    def test_is_within_bounds(self, start, end, length, expected):
        assert is_within_bounds(start, end, length=length) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestNumericValidators:
    """Test is_positive, is_non_negative, is_in_range."""

    @allure.title("is_positive rejects zero and negative values")
    @pytest.mark.parametrize("value, expected", [
        (1, True),
        (100, True),
        (0, False),
        (-1, False),
    ])
    def test_is_positive(self, value, expected):
        assert is_positive(value) is expected

    @allure.title("is_non_negative accepts zero and positive values")
    @pytest.mark.parametrize("value, expected", [
        (1, True),
        (0, True),
        (-1, False),
    ])
    def test_is_non_negative(self, value, expected):
        assert is_non_negative(value) is expected

    @allure.title("is_in_range validates value within min/max bounds")
    @pytest.mark.parametrize("value, expected", [
        (5, True),
        (0, True),
        (10, True),
        (-1, False),
        (11, False),
    ])
    def test_is_in_range(self, value, expected):
        assert is_in_range(value, min_val=0, max_val=10) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestIsValidHexColor:
    """Test is_valid_hex_color validator."""

    @allure.title("is_valid_hex_color validates hex color format")
    @pytest.mark.parametrize("value, expected", [
        ("#FF0000", True),
        ("#ff0000", True),
        ("#Ff00Ab", True),
        ("FF0000", False),
        ("#F00", True),
        ("#FF00000", False),
        ("#GGGGGG", False),
        ("#XY1234", False),
        ("", False),
        (None, False),
    ])
    def test_is_valid_hex_color(self, value, expected):
        assert is_valid_hex_color(value) is expected


@allure.story("QC-000.01 Validation Utilities")
class TestIsAcyclicHierarchy:
    """Test is_acyclic_hierarchy - prevents parent-child cycles."""

    @allure.title("is_acyclic_hierarchy allows valid hierarchy moves")
    def test_valid_moves(self):
        # Moving to root is always safe
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=None, get_parent=lambda _: None)
            is True
        )

        # Moving between independent roots
        parents = {1: None, 2: None}
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=2, get_parent=parents.get)
            is True
        )

        # Moving to sibling
        parents = {1: "root", 2: "root", 3: "root", "root": None}
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=2, get_parent=parents.get)
            is True
        )

        # Max depth prevents infinite loop on corrupted data
        result = is_acyclic_hierarchy(
            node_id=1,
            new_parent_id=2,
            get_parent=lambda nid: nid + 1,
            max_depth=10,
        )
        assert result is True

    @allure.title("is_acyclic_hierarchy detects direct and indirect cycles")
    def test_cycle_detection(self):
        # Cannot be own parent
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=1, get_parent=lambda _: None)
            is False
        )

        # Direct cycle: 1 -> 2, trying to make 2 parent of 1
        parents = {1: None, 2: 1}
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=2, get_parent=parents.get)
            is False
        )

        # Indirect cycle: 1 -> 2 -> 3, trying to make 3 parent of 1
        parents = {1: None, 2: 1, 3: 2}
        assert (
            is_acyclic_hierarchy(node_id=1, new_parent_id=3, get_parent=parents.get)
            is False
        )


@allure.story("QC-000.01 Validation Utilities")
class TestCollectionValidators:
    """Test all_exist, none_exist, has_no_references."""

    @allure.title("all_exist and none_exist check collection membership")
    def test_all_exist_and_none_exist(self):
        existing = {1, 2, 3}
        exists_fn = lambda x: x in existing

        # all_exist
        assert all_exist([1, 2, 3], exists_fn=lambda x: x in {1, 2, 3, 4, 5}) is True
        assert all_exist([1, 2, 99], exists_fn=exists_fn) is False
        assert all_exist([], exists_fn=lambda _x: False) is True

        # none_exist
        assert none_exist([4, 5, 6], exists_fn=exists_fn) is True
        assert none_exist([3, 4, 5], exists_fn=exists_fn) is False
        assert none_exist([], exists_fn=lambda _x: True) is True

    @allure.title("has_no_references returns True when reference count is zero")
    def test_has_no_references(self):
        assert has_no_references(1, count_references=lambda _x: 0) is True
        assert has_no_references(1, count_references=lambda _x: 5) is False


@allure.story("QC-000.01 Validation Utilities")
class TestValidateAll:
    """Test validate_all composite validator."""

    @allure.title("validate_all returns first failure or success when all pass")
    def test_validate_all(self):
        # All success
        result = validate_all(
            ValidationSuccess(),
            ValidationSuccess(),
            ValidationSuccess(),
        )
        assert isinstance(result, ValidationSuccess)

        # Returns first failure
        result = validate_all(
            ValidationSuccess(),
            ValidationFailure(reason="first error"),
            ValidationFailure(reason="second error"),
        )
        assert isinstance(result, ValidationFailure)
        assert result.reason == "first error"

        # Empty returns success
        assert isinstance(validate_all(), ValidationSuccess)

        # Single failure
        result = validate_all(ValidationFailure(reason="only error"))
        assert isinstance(result, ValidationFailure)


@allure.story("QC-000.01 Validation Utilities")
class TestValidateField:
    """Test validate_field helper."""

    @allure.title("validate_field returns success or failure with field details")
    def test_validate_field(self):
        # Valid field
        result = validate_field(
            field_name="age",
            value=25,
            predicate=lambda x: x > 0,
            error_message="must be positive",
        )
        assert isinstance(result, ValidationSuccess)

        # Invalid field with all attributes
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

        # Failure captures value
        result = validate_field(
            field_name="name",
            value="",
            predicate=is_non_empty_string,
            error_message="cannot be empty",
        )
        assert result.value == ""
