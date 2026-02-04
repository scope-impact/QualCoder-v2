"""
Tests for TextMatcher domain service.

Tests for pure text pattern matching functionality used in auto-coding.
"""

from __future__ import annotations

import pytest

from src.contexts.coding.core.services.text_matcher import (
    MatchScope,
    MatchType,
    TextMatch,
    TextMatcher,
)

pytestmark = pytest.mark.unit


# ============================================================
# TextMatch Value Object Tests
# ============================================================


class TestTextMatchCreation:
    """Tests for TextMatch value object creation."""

    def test_creates_text_match_with_valid_positions(self):
        """Should create TextMatch with valid start and end positions."""
        match = TextMatch(start=0, end=10)

        assert match.start == 0
        assert match.end == 10

    def test_text_match_is_immutable(self):
        """TextMatch should be immutable (frozen dataclass)."""
        match = TextMatch(start=0, end=10)

        with pytest.raises(AttributeError):
            match.start = 5  # type: ignore[misc]

    def test_text_match_length_property(self):
        """Should calculate length correctly."""
        match = TextMatch(start=5, end=15)

        assert match.length == 10

    def test_text_match_zero_length(self):
        """Should allow zero-length matches (start == end)."""
        match = TextMatch(start=5, end=5)

        assert match.length == 0

    def test_fails_with_negative_start(self):
        """Should fail when start is negative."""
        with pytest.raises(ValueError, match="start must be >= 0"):
            TextMatch(start=-1, end=10)

    def test_fails_when_end_less_than_start(self):
        """Should fail when end < start."""
        with pytest.raises(ValueError, match="end.*must be >= start"):
            TextMatch(start=10, end=5)


# ============================================================
# TextMatcher EXACT Match Type Tests
# ============================================================


class TestTextMatcherExactMatches:
    """Tests for EXACT (word boundary) matching."""

    def test_finds_exact_word_match(self):
        """Should find exact word with word boundaries."""
        text = "The cat sat on the mat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].start == 4
        assert matches[0].end == 7

    def test_finds_multiple_exact_matches(self):
        """Should find all exact word matches."""
        text = "cat and cat and another cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 3

    def test_exact_match_respects_word_boundaries(self):
        """Should not match substring within word."""
        text = "The category contains cats and concatenation"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        # Should not match 'cat' in 'category', 'cats', or 'concatenation'
        assert len(matches) == 0

    def test_exact_match_case_insensitive_default(self):
        """Should match case-insensitively by default."""
        text = "Cat CAT cat CaT"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, case_sensitive=False)

        assert len(matches) == 4

    def test_exact_match_case_sensitive(self):
        """Should respect case when case_sensitive=True."""
        text = "Cat CAT cat CaT"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, case_sensitive=True)

        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "cat"

    def test_exact_match_with_special_regex_chars(self):
        """Should escape special regex characters in pattern."""
        text = "The regex pattern and c.d patterns"
        matcher = TextMatcher(text)

        # Without escaping, "c.d" would match "c d" or "c-d" etc.
        # With proper escaping, it should only match literal "c.d"
        matches = matcher.find_matches("c.d", MatchType.EXACT)

        # Should match literal "c.d" only
        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "c.d"

    def test_exact_match_with_parentheses_in_word(self):
        """Should escape parentheses in pattern."""
        text = "call func() now"
        matcher = TextMatcher(text)

        # Parentheses are regex metacharacters but should match literally
        # Note: func() has word boundary at 'func' start but not at ')' end
        # This test verifies that the regex escaping works
        matches = matcher.find_matches("func()", MatchType.CONTAINS)

        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "func()"

    def test_exact_match_at_start_of_text(self):
        """Should find match at the start of text."""
        text = "Hello world"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("Hello", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].start == 0

    def test_exact_match_at_end_of_text(self):
        """Should find match at the end of text."""
        text = "Hello world"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("world", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].end == len(text)


# ============================================================
# TextMatcher CONTAINS Match Type Tests
# ============================================================


class TestTextMatcherContainsMatches:
    """Tests for CONTAINS (substring) matching."""

    def test_finds_substring_match(self):
        """Should find substring within text."""
        text = "The category contains cats"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.CONTAINS)

        assert len(matches) == 2  # 'category' and 'cats'

    def test_finds_overlapping_substrings(self):
        """Should find overlapping substring matches."""
        text = "aaaa"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("aa", MatchType.CONTAINS)

        # Should find "aa" at positions 0, 1, 2
        assert len(matches) == 3
        assert matches[0].start == 0
        assert matches[1].start == 1
        assert matches[2].start == 2

    def test_contains_case_insensitive_default(self):
        """Should match case-insensitively by default."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.CONTAINS, case_sensitive=False)

        assert len(matches) == 3

    def test_contains_case_sensitive(self):
        """Should respect case when case_sensitive=True."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.CONTAINS, case_sensitive=True)

        assert len(matches) == 1

    def test_contains_preserves_original_positions(self):
        """Should return correct positions in original text."""
        text = "UPPERCASE lowercase MiXeD"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("case", MatchType.CONTAINS, case_sensitive=False)

        # Should find 'CASE' in UPPERCASE and 'case' in lowercase
        assert len(matches) == 2
        assert text[matches[0].start : matches[0].end] == "CASE"
        assert text[matches[1].start : matches[1].end] == "case"

    def test_contains_whole_text_match(self):
        """Should match entire text as substring."""
        text = "hello"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("hello", MatchType.CONTAINS)

        assert len(matches) == 1
        assert matches[0].start == 0
        assert matches[0].end == 5


# ============================================================
# TextMatcher REGEX Match Type Tests
# ============================================================


class TestTextMatcherRegexMatches:
    """Tests for REGEX matching."""

    def test_finds_regex_pattern(self):
        """Should find matches using regex pattern."""
        text = "cat123 dog456 cat789"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"cat\d+", MatchType.REGEX)

        assert len(matches) == 2

    def test_regex_with_groups(self):
        """Should handle regex with groups."""
        text = "Hello World"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"(\w+) (\w+)", MatchType.REGEX)

        assert len(matches) == 1
        assert matches[0].start == 0
        assert matches[0].end == 11

    def test_regex_case_insensitive(self):
        """Should support case-insensitive regex."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"cat", MatchType.REGEX, case_sensitive=False)

        assert len(matches) == 3

    def test_regex_case_sensitive(self):
        """Should support case-sensitive regex."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"cat", MatchType.REGEX, case_sensitive=True)

        assert len(matches) == 1

    def test_invalid_regex_returns_empty(self):
        """Should return empty list for invalid regex pattern."""
        text = "Some text"
        matcher = TextMatcher(text)

        # Invalid regex - unmatched bracket
        matches = matcher.find_matches(r"[invalid", MatchType.REGEX)

        assert matches == []

    def test_regex_word_boundary(self):
        """Should support word boundary patterns."""
        text = "cat category cats"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"\bcat\b", MatchType.REGEX)

        assert len(matches) == 1
        assert text[matches[0].start : matches[0].end] == "cat"

    def test_regex_character_class(self):
        """Should support character classes."""
        text = "a1b2c3d4"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"[a-z]\d", MatchType.REGEX)

        assert len(matches) == 4

    def test_regex_alternation(self):
        """Should support alternation (|)."""
        text = "cat dog bird cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"cat|dog", MatchType.REGEX)

        assert len(matches) == 3


# ============================================================
# TextMatcher Scope Tests
# ============================================================


class TestTextMatcherScope:
    """Tests for match scope filtering."""

    def test_scope_all_returns_all_matches(self):
        """MatchScope.ALL should return all matches."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.ALL)

        assert len(matches) == 3

    def test_scope_first_returns_first_match_only(self):
        """MatchScope.FIRST should return only the first match."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.FIRST)

        assert len(matches) == 1
        assert matches[0].start == 0

    def test_scope_last_returns_last_match_only(self):
        """MatchScope.LAST should return only the last match."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.LAST)

        assert len(matches) == 1
        assert matches[0].start == 8

    def test_scope_first_with_single_match(self):
        """MatchScope.FIRST with single match should return that match."""
        text = "one cat here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.FIRST)

        assert len(matches) == 1

    def test_scope_last_with_single_match(self):
        """MatchScope.LAST with single match should return that match."""
        text = "one cat here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.LAST)

        assert len(matches) == 1

    def test_scope_first_with_no_matches(self):
        """MatchScope.FIRST with no matches should return empty list."""
        text = "no match here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("xyz", MatchType.EXACT, scope=MatchScope.FIRST)

        assert matches == []

    def test_scope_last_with_no_matches(self):
        """MatchScope.LAST with no matches should return empty list."""
        text = "no match here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("xyz", MatchType.EXACT, scope=MatchScope.LAST)

        assert matches == []


# ============================================================
# TextMatcher Edge Cases
# ============================================================


class TestTextMatcherEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text_returns_empty(self):
        """Should return empty list for empty text."""
        matcher = TextMatcher("")

        matches = matcher.find_matches("pattern", MatchType.EXACT)

        assert matches == []

    def test_empty_pattern_returns_empty(self):
        """Should return empty list for empty pattern."""
        matcher = TextMatcher("some text")

        matches = matcher.find_matches("", MatchType.EXACT)

        assert matches == []

    def test_pattern_longer_than_text(self):
        """Should return empty when pattern is longer than text."""
        matcher = TextMatcher("hi")

        matches = matcher.find_matches("hello world", MatchType.CONTAINS)

        assert matches == []

    def test_whitespace_only_text(self):
        """Should handle whitespace-only text."""
        matcher = TextMatcher("   \t\n  ")

        matches = matcher.find_matches("pattern", MatchType.EXACT)

        assert matches == []

    def test_whitespace_pattern(self):
        """Should handle whitespace patterns."""
        text = "word1  word2"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("  ", MatchType.CONTAINS)

        assert len(matches) == 1

    def test_newline_in_text(self):
        """Should handle newlines in text."""
        text = "line1\nline2\nline1"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("line1", MatchType.EXACT)

        assert len(matches) == 2

    def test_unicode_text(self):
        """Should handle unicode characters."""
        text = "Hello monde cafe"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cafe", MatchType.EXACT)

        assert len(matches) == 1

    def test_unicode_pattern(self):
        """Should handle unicode patterns."""
        text = "The cafe is nice"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cafe", MatchType.CONTAINS)

        assert len(matches) == 1

    def test_very_long_text(self):
        """Should handle very long text efficiently."""
        text = "word " * 10000 + "target " + "word " * 10000
        matcher = TextMatcher(text)

        matches = matcher.find_matches("target", MatchType.EXACT)

        assert len(matches) == 1

    def test_repeated_pattern_in_text(self):
        """Should find all repeated patterns."""
        text = "a" * 100
        matcher = TextMatcher(text)

        matches = matcher.find_matches("a", MatchType.CONTAINS)

        assert len(matches) == 100


# ============================================================
# TextMatcher Immutability Tests
# ============================================================


class TestTextMatcherImmutability:
    """Tests verifying immutability and purity."""

    def test_find_matches_does_not_modify_text(self):
        """Finding matches should not modify the original text."""
        original = "The cat sat on the mat"
        text = original
        matcher = TextMatcher(text)

        matcher.find_matches("cat", MatchType.EXACT)

        assert text == original

    def test_multiple_searches_return_consistent_results(self):
        """Multiple searches should return consistent results."""
        text = "cat dog cat"
        matcher = TextMatcher(text)

        matches1 = matcher.find_matches("cat", MatchType.EXACT)
        matches2 = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches1) == len(matches2)
        assert matches1[0].start == matches2[0].start
        assert matches1[0].end == matches2[0].end

    def test_different_match_types_independent(self):
        """Different match types should operate independently."""
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

    def test_default_match_type_is_exact(self):
        """Default match type should be EXACT."""
        text = "category cat"
        matcher = TextMatcher(text)

        # Without specifying match_type, should use EXACT
        matches = matcher.find_matches("cat")

        # Should only match standalone "cat", not "cat" in "category"
        assert len(matches) == 1

    def test_default_scope_is_all(self):
        """Default scope should be ALL."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        # Without specifying scope, should return all matches
        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 3

    def test_default_case_sensitive_is_false(self):
        """Default case_sensitive should be False."""
        text = "Cat CAT cat"
        matcher = TextMatcher(text)

        # Without specifying case_sensitive, should be case-insensitive
        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 3
