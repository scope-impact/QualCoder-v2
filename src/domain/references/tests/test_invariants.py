"""
References Context: Invariant Tests

Tests for pure validation functions that check business rules.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestIsValidTitle:
    """Tests for is_valid_title invariant."""

    def test_valid_title(self):
        """Should return True for valid title."""
        from src.domain.references.invariants import is_valid_title

        assert is_valid_title("The Logic of Scientific Discovery") is True

    def test_empty_title_is_invalid(self):
        """Should return False for empty title."""
        from src.domain.references.invariants import is_valid_title

        assert is_valid_title("") is False

    def test_whitespace_only_title_is_invalid(self):
        """Should return False for whitespace-only title."""
        from src.domain.references.invariants import is_valid_title

        assert is_valid_title("   ") is False

    def test_title_too_long_is_invalid(self):
        """Should return False for title exceeding 500 characters."""
        from src.domain.references.invariants import MAX_TITLE_LENGTH, is_valid_title

        long_title = "a" * (MAX_TITLE_LENGTH + 1)
        assert is_valid_title(long_title) is False

    def test_title_at_max_length_is_valid(self):
        """Should return True for title at exactly max length."""
        from src.domain.references.invariants import MAX_TITLE_LENGTH, is_valid_title

        max_title = "a" * MAX_TITLE_LENGTH
        assert is_valid_title(max_title) is True


class TestIsValidYear:
    """Tests for is_valid_year invariant."""

    def test_valid_year(self):
        """Should return True for valid year."""
        from src.domain.references.invariants import is_valid_year

        assert is_valid_year(2023) is True

    def test_none_year_is_valid(self):
        """Should return True for None (optional year)."""
        from src.domain.references.invariants import is_valid_year

        assert is_valid_year(None) is True

    def test_year_too_old_is_invalid(self):
        """Should return False for year before 1000."""
        from src.domain.references.invariants import is_valid_year

        assert is_valid_year(999) is False

    def test_future_year_is_invalid(self):
        """Should return False for year more than 1 ahead of current."""
        from datetime import UTC, datetime

        from src.domain.references.invariants import is_valid_year

        future_year = datetime.now(UTC).year + 2
        assert is_valid_year(future_year) is False

    def test_next_year_is_valid(self):
        """Should return True for next year (in press publications)."""
        from datetime import UTC, datetime

        from src.domain.references.invariants import is_valid_year

        next_year = datetime.now(UTC).year + 1
        assert is_valid_year(next_year) is True


class TestIsValidDoi:
    """Tests for is_valid_doi invariant."""

    def test_valid_doi(self):
        """Should return True for valid DOI format."""
        from src.domain.references.invariants import is_valid_doi

        assert is_valid_doi("10.1234/example.2023") is True

    def test_none_doi_is_valid(self):
        """Should return True for None (optional DOI)."""
        from src.domain.references.invariants import is_valid_doi

        assert is_valid_doi(None) is True

    def test_empty_doi_is_valid(self):
        """Should return True for empty string (optional DOI)."""
        from src.domain.references.invariants import is_valid_doi

        assert is_valid_doi("") is True

    def test_invalid_doi_format(self):
        """Should return False for invalid DOI format."""
        from src.domain.references.invariants import is_valid_doi

        assert is_valid_doi("invalid-doi") is False

    def test_doi_without_prefix(self):
        """Should return False for DOI missing 10. prefix."""
        from src.domain.references.invariants import is_valid_doi

        assert is_valid_doi("1234/example") is False


class TestIsValidAuthors:
    """Tests for is_valid_authors invariant."""

    def test_valid_authors(self):
        """Should return True for valid authors string."""
        from src.domain.references.invariants import is_valid_authors

        assert is_valid_authors("Karl Popper") is True

    def test_empty_authors_is_invalid(self):
        """Should return False for empty authors."""
        from src.domain.references.invariants import is_valid_authors

        assert is_valid_authors("") is False

    def test_whitespace_only_authors_is_invalid(self):
        """Should return False for whitespace-only authors."""
        from src.domain.references.invariants import is_valid_authors

        assert is_valid_authors("   ") is False

    def test_multiple_authors(self):
        """Should return True for multiple authors."""
        from src.domain.references.invariants import is_valid_authors

        assert is_valid_authors("John Smith, Jane Doe, Bob Wilson") is True

    def test_authors_too_long_is_invalid(self):
        """Should return False for authors exceeding max length."""
        from src.domain.references.invariants import MAX_AUTHORS_LENGTH, is_valid_authors

        long_authors = "a" * (MAX_AUTHORS_LENGTH + 1)
        assert is_valid_authors(long_authors) is False
