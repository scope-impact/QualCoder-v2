"""
Tests for TextMatcher domain service.

Tests for pure text pattern matching functionality used in auto-coding.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.services.text_matcher import (
    MatchScope,
    MatchType,
    TextMatch,
    TextMatcher,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-029 Apply Codes to Text"),
]


# ============================================================
# TextMatch Value Object Tests
# ============================================================


class TestTextMatchCreation:
    """Tests for TextMatch value object creation."""

    def test_creates_text_match_with_valid_positions_and_length(self):
        """Should create TextMatch with valid positions and correct length."""
        match = TextMatch(start=0, end=10)

        assert match.start == 0
        assert match.end == 10

        match2 = TextMatch(start=5, end=15)

        assert match2.length == 10

        zero_length = TextMatch(start=5, end=5)

        assert zero_length.length == 0

    def test_validation_and_immutability(self):
        """TextMatch should be immutable and reject invalid positions."""
        match = TextMatch(start=0, end=10)

        with pytest.raises(AttributeError):
            match.start = 5  # type: ignore[misc]

        with pytest.raises(ValueError, match="start must be >= 0"):
            TextMatch(start=-1, end=10)

        with pytest.raises(ValueError, match="end.*must be >= start"):
            TextMatch(start=10, end=5)


# ============================================================
# TextMatcher EXACT Match Type Tests
# ============================================================


class TestTextMatcherExactMatches:
    """Tests for EXACT (word boundary) matching."""

    def test_exact_match_positions(self):
        """Should find exact matches at various positions including start/end."""
        # Single match in middle
        text = "The cat sat on the mat"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cat", MatchType.EXACT)
        assert len(matches) == 1
        assert matches[0].start == 4
        assert matches[0].end == 7

        # Multiple matches
        text2 = "cat and cat and another cat"
        matcher2 = TextMatcher(text2)
        matches2 = matcher2.find_matches("cat", MatchType.EXACT)
        assert len(matches2) == 3

        # Match at start of text
        text3 = "Hello world"
        matcher3 = TextMatcher(text3)
        matches3 = matcher3.find_matches("Hello", MatchType.EXACT)
        assert len(matches3) == 1
        assert matches3[0].start == 0

        # Match at end of text
        matches4 = matcher3.find_matches("world", MatchType.EXACT)
        assert len(matches4) == 1
        assert matches4[0].end == len(text3)

    def test_exact_match_respects_word_boundaries(self):
        """Should not match substring within word."""
        text = "The category contains cats and concatenation"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        # Should not match 'cat' in 'category', 'cats', or 'concatenation'
        assert len(matches) == 0

    def test_exact_match_case_sensitivity(self):
        """Should support both case-insensitive and case-sensitive matching."""
        text = "Cat CAT cat CaT"
        matcher = TextMatcher(text)

        matches_insensitive = matcher.find_matches("cat", MatchType.EXACT, case_sensitive=False)
        assert len(matches_insensitive) == 4

        matches_sensitive = matcher.find_matches("cat", MatchType.EXACT, case_sensitive=True)
        assert len(matches_sensitive) == 1
        assert text[matches_sensitive[0].start : matches_sensitive[0].end] == "cat"

    def test_exact_match_special_characters(self):
        """Should escape special regex characters in pattern."""
        # Dot character
        text = "The regex pattern and c.d patterns"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("c.d", MatchType.EXACT)
        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "c.d"

        # Parentheses
        text2 = "call func() now"
        matcher2 = TextMatcher(text2)
        matches2 = matcher2.find_matches("func()", MatchType.CONTAINS)
        assert len(matches2) == 1
        assert text2[matches2[0].start : matches2[0].end] == "func()"


# ============================================================
# TextMatcher CONTAINS Match Type Tests
# ============================================================


class TestTextMatcherContainsMatches:
    """Tests for CONTAINS (substring) matching."""

    def test_finds_substring_and_overlapping_matches(self):
        """Should find substrings including overlapping and whole-text matches."""
        # Basic substring
        text = "The category contains cats"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cat", MatchType.CONTAINS)
        assert len(matches) == 2  # 'category' and 'cats'

        # Overlapping substrings
        text2 = "aaaa"
        matcher2 = TextMatcher(text2)
        matches2 = matcher2.find_matches("aa", MatchType.CONTAINS)
        assert len(matches2) == 3
        assert matches2[0].start == 0
        assert matches2[1].start == 1
        assert matches2[2].start == 2

        # Whole text match
        text3 = "hello"
        matcher3 = TextMatcher(text3)
        matches3 = matcher3.find_matches("hello", MatchType.CONTAINS)
        assert len(matches3) == 1
        assert matches3[0].start == 0
        assert matches3[0].end == 5

    def test_contains_case_sensitivity(self):
        """Should support both case-insensitive and case-sensitive matching."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches_insensitive = matcher.find_matches("cat", MatchType.CONTAINS, case_sensitive=False)
        assert len(matches_insensitive) == 3

        matches_sensitive = matcher.find_matches("cat", MatchType.CONTAINS, case_sensitive=True)
        assert len(matches_sensitive) == 1

    def test_contains_preserves_original_positions(self):
        """Should return correct positions in original text."""
        text = "UPPERCASE lowercase MiXeD"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("case", MatchType.CONTAINS, case_sensitive=False)

        # Should find 'CASE' in UPPERCASE and 'case' in lowercase
        assert len(matches) == 2
        assert text[matches[0].start : matches[0].end] == "CASE"
        assert text[matches[1].start : matches[1].end] == "case"


# ============================================================
# TextMatcher REGEX Match Type Tests
# ============================================================


class TestTextMatcherRegexMatches:
    """Tests for REGEX matching."""

    def test_regex_pattern_types(self):
        """Should support various regex patterns: digits, groups, boundaries, classes, alternation."""
        # Basic pattern with digits
        text = "cat123 dog456 cat789"
        matcher = TextMatcher(text)
        matches = matcher.find_matches(r"cat\d+", MatchType.REGEX)
        assert len(matches) == 2

        # Groups
        text2 = "Hello World"
        matcher2 = TextMatcher(text2)
        matches2 = matcher2.find_matches(r"(\w+) (\w+)", MatchType.REGEX)
        assert len(matches2) == 1
        assert matches2[0].start == 0
        assert matches2[0].end == 11

        # Word boundary
        text3 = "cat category cats"
        matcher3 = TextMatcher(text3)
        matches3 = matcher3.find_matches(r"\bcat\b", MatchType.REGEX)
        assert len(matches3) == 1
        assert text3[matches3[0].start : matches3[0].end] == "cat"

        # Character class
        text4 = "a1b2c3d4"
        matcher4 = TextMatcher(text4)
        matches4 = matcher4.find_matches(r"[a-z]\d", MatchType.REGEX)
        assert len(matches4) == 4

        # Alternation
        text5 = "cat dog bird cat"
        matcher5 = TextMatcher(text5)
        matches5 = matcher5.find_matches(r"cat|dog", MatchType.REGEX)
        assert len(matches5) == 3

    def test_regex_case_sensitivity(self):
        """Should support both case-insensitive and case-sensitive regex."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches_insensitive = matcher.find_matches(r"cat", MatchType.REGEX, case_sensitive=False)
        assert len(matches_insensitive) == 3

        matches_sensitive = matcher.find_matches(r"cat", MatchType.REGEX, case_sensitive=True)
        assert len(matches_sensitive) == 1

    def test_invalid_regex_returns_empty(self):
        """Should return empty list for invalid regex pattern."""
        text = "Some text"
        matcher = TextMatcher(text)

        # Invalid regex - unmatched bracket
        matches = matcher.find_matches(r"[invalid", MatchType.REGEX)

        assert matches == []


# ============================================================
# TextMatcher Scope Tests
# ============================================================


class TestTextMatcherScope:
    """Tests for match scope filtering."""

    def test_match_scope_variants(self):
        """ALL returns all, FIRST returns first, LAST returns last."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches_all = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.ALL)
        assert len(matches_all) == 3

        matches_first = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.FIRST)
        assert len(matches_first) == 1
        assert matches_first[0].start == 0

        matches_last = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.LAST)
        assert len(matches_last) == 1
        assert matches_last[0].start == 8

    def test_scope_edge_cases(self):
        """Scope with single match and no matches."""
        # Single match - FIRST and LAST both return it
        text = "one cat here"
        matcher = TextMatcher(text)

        matches_first = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.FIRST)
        assert len(matches_first) == 1

        matches_last = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.LAST)
        assert len(matches_last) == 1

        # No matches - FIRST and LAST return empty
        text2 = "no match here"
        matcher2 = TextMatcher(text2)

        matches_first2 = matcher2.find_matches("xyz", MatchType.EXACT, scope=MatchScope.FIRST)
        assert matches_first2 == []

        matches_last2 = matcher2.find_matches("xyz", MatchType.EXACT, scope=MatchScope.LAST)
        assert matches_last2 == []


# ============================================================
# TextMatcher Edge Cases
# ============================================================


class TestTextMatcherEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_and_invalid_inputs(self):
        """Should return empty list for empty text, empty pattern, long pattern, whitespace-only text."""
        matcher = TextMatcher("")
        matches = matcher.find_matches("pattern", MatchType.EXACT)
        assert matches == []

        matcher = TextMatcher("some text")
        matches = matcher.find_matches("", MatchType.EXACT)
        assert matches == []

        matcher = TextMatcher("hi")
        matches = matcher.find_matches("hello world", MatchType.CONTAINS)
        assert matches == []

        matcher = TextMatcher("   \t\n  ")
        matches = matcher.find_matches("pattern", MatchType.EXACT)
        assert matches == []

    def test_whitespace_handling(self):
        """Should handle whitespace patterns and newlines in text."""
        text = "word1  word2"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("  ", MatchType.CONTAINS)
        assert len(matches) == 1

        text = "line1\nline2\nline1"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("line1", MatchType.EXACT)
        assert len(matches) == 2

    def test_unicode_support(self):
        """Should handle unicode characters in both text and pattern."""
        text = "Hello monde cafe"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cafe", MatchType.EXACT)
        assert len(matches) == 1

        text = "The cafe is nice"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cafe", MatchType.CONTAINS)
        assert len(matches) == 1

    def test_performance_scenarios(self):
        """Should handle very long text and repeated patterns."""
        text = "word " * 10000 + "target " + "word " * 10000
        matcher = TextMatcher(text)
        matches = matcher.find_matches("target", MatchType.EXACT)
        assert len(matches) == 1

        text = "a" * 100
        matcher = TextMatcher(text)
        matches = matcher.find_matches("a", MatchType.CONTAINS)
        assert len(matches) == 100


# ============================================================
# TextMatcher Immutability Tests
# ============================================================


class TestTextMatcherImmutability:
    """Tests verifying immutability and purity."""

    def test_immutability_and_consistency(self):
        """Text unmodified after search, repeated searches consistent, match types independent."""
        original = "The cat sat on the mat"
        text = original
        matcher = TextMatcher(text)
        matcher.find_matches("cat", MatchType.EXACT)
        assert text == original

        text = "cat dog cat"
        matcher = TextMatcher(text)
        matches1 = matcher.find_matches("cat", MatchType.EXACT)
        matches2 = matcher.find_matches("cat", MatchType.EXACT)
        assert len(matches1) == len(matches2)
        assert matches1[0].start == matches2[0].start
        assert matches1[0].end == matches2[0].end

        text = "category cat cats"
        matcher = TextMatcher(text)
        exact_matches = matcher.find_matches("cat", MatchType.EXACT)
        contains_matches = matcher.find_matches("cat", MatchType.CONTAINS)
        # EXACT should find only standalone "cat"
        assert len(exact_matches) == 1
        # CONTAINS should find "cat" in all words
        assert len(contains_matches) == 3


# ============================================================
# TextMatcher Default Parameters Tests
# ============================================================


class TestTextMatcherDefaults:
    """Tests for default parameter values."""

    def test_default_parameters(self):
        """Defaults: match type EXACT, scope ALL, case_sensitive False."""
        # Default match type is EXACT
        text = "category cat"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cat")
        # Should only match standalone "cat", not "cat" in "category"
        assert len(matches) == 1

        # Default scope is ALL
        text = "cat cat cat"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cat", MatchType.EXACT)
        assert len(matches) == 3

        # Default case_sensitive is False
        text = "Cat CAT cat"
        matcher = TextMatcher(text)
        matches = matcher.find_matches("cat", MatchType.EXACT)
        assert len(matches) == 3
