"""
Cases Context: Invariant Tests

Tests for pure predicate functions that validate business rules for Cases.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestCaseNameInvariants:
    """Tests for case name validation."""

    def test_valid_case_name_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        assert is_valid_case_name("Participant A") is True
        assert is_valid_case_name("Site-001") is True
        assert is_valid_case_name("Interview_Subject_42") is True

    def test_valid_case_name_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        assert is_valid_case_name("") is False

    def test_valid_case_name_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        assert is_valid_case_name("   ") is False
        assert is_valid_case_name("\t\n") is False

    def test_valid_case_name_rejects_too_long(self):
        """Names exceeding 100 characters should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        long_name = "a" * 101
        assert is_valid_case_name(long_name) is False

    def test_valid_case_name_accepts_max_length(self):
        """Names at exactly 100 characters should be valid."""
        from src.contexts.cases.core.invariants import is_valid_case_name

        max_name = "a" * 100
        assert is_valid_case_name(max_name) is True


class TestCaseNameUniqueness:
    """Tests for case name uniqueness."""

    def test_case_name_unique_in_empty_project(self):
        """Any name is unique in a project with no cases."""
        from src.contexts.cases.core.invariants import is_case_name_unique

        assert is_case_name_unique("Participant A", []) is True

    def test_case_name_unique_detects_duplicate(self):
        """Duplicate names should be detected (case-insensitive)."""
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.invariants import is_case_name_unique
        from src.contexts.shared import CaseId

        existing = [
            Case(
                id=CaseId(value=1),
                name="Participant A",
            )
        ]

        assert is_case_name_unique("Participant A", existing) is False
        assert is_case_name_unique("participant a", existing) is False
        assert is_case_name_unique("PARTICIPANT A", existing) is False
        assert is_case_name_unique("Participant B", existing) is True


class TestAttributeTypeInvariants:
    """Tests for case attribute type validation."""

    def test_valid_attribute_types(self):
        """Standard attribute types should be valid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_type

        assert is_valid_attribute_type("text") is True
        assert is_valid_attribute_type("number") is True
        assert is_valid_attribute_type("date") is True
        assert is_valid_attribute_type("boolean") is True

    def test_invalid_attribute_types(self):
        """Unknown attribute types should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_type

        assert is_valid_attribute_type("unknown") is False
        assert is_valid_attribute_type("") is False
        assert is_valid_attribute_type("integer") is False


class TestAttributeNameInvariants:
    """Tests for case attribute name validation."""

    def test_valid_attribute_name_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_name

        assert is_valid_attribute_name("age") is True
        assert is_valid_attribute_name("interview_date") is True
        assert is_valid_attribute_name("Location") is True

    def test_valid_attribute_name_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_name

        assert is_valid_attribute_name("") is False

    def test_valid_attribute_name_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_name

        assert is_valid_attribute_name("   ") is False

    def test_valid_attribute_name_rejects_too_long(self):
        """Names exceeding 50 characters should be invalid."""
        from src.contexts.cases.core.invariants import is_valid_attribute_name

        long_name = "a" * 51
        assert is_valid_attribute_name(long_name) is False


class TestAttributeValueInvariants:
    """Tests for case attribute value validation."""

    def test_text_value_accepts_strings(self):
        """Text attributes should accept string values."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value("hello", "text") is True
        assert is_valid_attribute_value("", "text") is True  # Empty allowed

    def test_number_value_accepts_numeric(self):
        """Number attributes should accept numeric values."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value(42, "number") is True
        assert is_valid_attribute_value(3.14, "number") is True
        assert is_valid_attribute_value("42", "number") is True  # String number OK

    def test_number_value_rejects_non_numeric(self):
        """Number attributes should reject non-numeric strings."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value("hello", "number") is False
        assert is_valid_attribute_value("", "number") is False

    def test_date_value_accepts_valid_dates(self):
        """Date attributes should accept valid date strings."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value("2026-01-31", "date") is True
        assert is_valid_attribute_value("2026-12-25", "date") is True

    def test_date_value_rejects_invalid_dates(self):
        """Date attributes should reject invalid date strings."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value("not-a-date", "date") is False
        assert is_valid_attribute_value("31-01-2026", "date") is False  # Wrong format
        assert is_valid_attribute_value("", "date") is False

    def test_boolean_value_accepts_booleans(self):
        """Boolean attributes should accept boolean values."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value(True, "boolean") is True
        assert is_valid_attribute_value(False, "boolean") is True
        assert is_valid_attribute_value("true", "boolean") is True
        assert is_valid_attribute_value("false", "boolean") is True

    def test_boolean_value_rejects_non_booleans(self):
        """Boolean attributes should reject non-boolean values."""
        from src.contexts.cases.core.invariants import is_valid_attribute_value

        assert is_valid_attribute_value("yes", "boolean") is False
        assert is_valid_attribute_value(1, "boolean") is False
        assert is_valid_attribute_value("", "boolean") is False
