"""
Cases Context: Invariant Tests

Tests for pure predicate functions that validate business rules for Cases.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-030 Case Management"),
]


@allure.story("QC-030.01 Case Name Validation")
class TestCaseNameInvariants:
    """Tests for case name validation and uniqueness."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Participant A", True),
            ("Site-001", True),
            ("Interview_Subject_42", True),
            ("a" * 100, True),
            ("", False),
            ("   ", False),
            ("\t\n", False),
            ("a" * 101, False),
        ],
        ids=["normal", "hyphenated", "underscored", "max-length",
             "empty", "whitespace", "tabs-newlines", "too-long"],
    )
    @allure.title("Validates case names: accepts valid, rejects empty/whitespace/too-long")
    def test_validates_case_names(self, name, expected):
        """Normal alphanumeric names valid; empty, whitespace-only, and too-long rejected."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        assert is_valid_case_name(name) is expected

    @allure.title("Detects duplicate case names case-insensitively")
    def test_case_name_uniqueness(self):
        """Any name is unique in empty project; duplicates detected case-insensitively."""
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.invariants import is_case_name_unique
        from src.shared import CaseId

        assert is_case_name_unique("Participant A", []) is True

        existing = [Case(id=CaseId(value="1"), name="Participant A")]

        assert is_case_name_unique("Participant A", existing) is False
        assert is_case_name_unique("participant a", existing) is False
        assert is_case_name_unique("PARTICIPANT A", existing) is False
        assert is_case_name_unique("Participant B", existing) is True


@allure.story("QC-030.02 Case Attribute Validation")
class TestAttributeTypeAndNameInvariants:
    """Tests for attribute type and name validation."""

    @pytest.mark.parametrize(
        "attr_type, expected",
        [
            ("text", True),
            ("number", True),
            ("date", True),
            ("boolean", True),
            ("unknown", False),
            ("", False),
            ("integer", False),
        ],
        ids=["text", "number", "date", "boolean", "unknown", "empty", "integer"],
    )
    @allure.title("Validates attribute types: standard types accepted, others rejected")
    def test_validates_attribute_types(self, attr_type, expected):
        """Standard attribute types valid; unknown types rejected."""
        from src.contexts.cases.core.invariants import is_valid_attribute_type

        assert is_valid_attribute_type(attr_type) is expected

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("age", True),
            ("interview_date", True),
            ("Location", True),
            ("", False),
            ("   ", False),
            ("a" * 51, False),
        ],
        ids=["simple", "underscored", "capitalized", "empty", "whitespace", "too-long"],
    )
    @allure.title("Validates attribute names: normal accepted, empty/whitespace/too-long rejected")
    def test_validates_attribute_names(self, name, expected):
        """Normal names valid; empty, whitespace-only, and too-long rejected."""
        from src.contexts.cases.core.invariants import is_valid_attribute_name

        assert is_valid_attribute_name(name) is expected


@allure.story("QC-030.02 Case Attribute Value Validation")
class TestAttributeValueInvariants:
    """Tests for case attribute value validation by type."""

    @pytest.mark.parametrize(
        "value, attr_type, expected",
        [
            # Text
            ("hello", "text", True),
            ("", "text", True),
            # Number
            (42, "number", True),
            (3.14, "number", True),
            ("42", "number", True),
            ("hello", "number", False),
            ("", "number", False),
            # Date
            ("2026-01-31", "date", True),
            ("2026-12-25", "date", True),
            ("not-a-date", "date", False),
            ("31-01-2026", "date", False),
            ("", "date", False),
            # Boolean
            (True, "boolean", True),
            (False, "boolean", True),
            ("true", "boolean", True),
            ("false", "boolean", True),
            ("yes", "boolean", False),
            (1, "boolean", False),
            ("", "boolean", False),
        ],
        ids=[
            "text-string", "text-empty",
            "number-int", "number-float", "number-str", "number-non-numeric", "number-empty",
            "date-valid", "date-valid-2", "date-invalid", "date-wrong-format", "date-empty",
            "bool-true", "bool-false", "bool-str-true", "bool-str-false",
            "bool-yes", "bool-int", "bool-empty",
        ],
    )
    @allure.title("Validates attribute values by type")
    def test_validates_attribute_values(self, value, attr_type, expected):
        """Each attribute type accepts its valid values and rejects invalid ones."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value(value, attr_type) is expected
