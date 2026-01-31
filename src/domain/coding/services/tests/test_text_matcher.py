"""
Tests for TextMatcher domain service.

TDD tests written BEFORE implementation.
Extracted from presentation/dialogs/auto_code_dialog.py AutoCodeFinder.
"""

from src.domain.coding.services.text_matcher import (
    MatchScope,
    MatchType,
    TextMatcher,
)


class TestTextMatcherExactMatching:
    """Tests for exact word boundary matching."""

    def test_finds_exact_word_match(self):
        """Should find exact word with word boundaries."""
        text = "The cat sat on the mat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].start == 4
        assert matches[0].end == 7

    def test_does_not_match_partial_word(self):
        """Should not match 'cat' inside 'category'."""
        text = "The category contains cats"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        # Should only match 'cats' would not match, but 'cat' as standalone doesn't exist
        assert len(matches) == 0

    def test_finds_multiple_exact_matches(self):
        """Should find all occurrences of exact word."""
        text = "The cat and the cat played with cat toys"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 3

    def test_case_insensitive_by_default(self):
        """Should match regardless of case by default."""
        text = "The Cat sat on the CAT mat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 2

    def test_case_sensitive_when_specified(self):
        """Should respect case when case_sensitive=True."""
        text = "The Cat sat on the cat mat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, case_sensitive=True)

        assert len(matches) == 1
        assert matches[0].start == 19  # Only lowercase 'cat'

    def test_empty_pattern_returns_empty(self):
        """Should return empty list for empty pattern."""
        text = "Some text here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("", MatchType.EXACT)

        assert matches == []


class TestTextMatcherContainsMatching:
    """Tests for substring/contains matching."""

    def test_finds_substring_match(self):
        """Should find substring within words."""
        text = "The category contains cats"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.CONTAINS)

        assert len(matches) == 2  # 'category' and 'cats'

    def test_finds_multiple_substring_occurrences(self):
        """Should find all substring occurrences."""
        text = "abcabcabc"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("abc", MatchType.CONTAINS)

        assert len(matches) == 3

    def test_case_insensitive_contains(self):
        """Should match substrings regardless of case."""
        text = "CATegorize the Category"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.CONTAINS)

        assert len(matches) == 2


class TestTextMatcherRegexMatching:
    """Tests for regex pattern matching."""

    def test_finds_simple_regex_match(self):
        """Should find matches using regex pattern."""
        text = "The cat sat on the mat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"\w+at", MatchType.REGEX)

        assert len(matches) == 3  # cat, sat, mat

    def test_finds_digit_patterns(self):
        """Should match digit patterns."""
        text = "Order 123 and Order 456"
        matcher = TextMatcher(text)

        matches = matcher.find_matches(r"\d+", MatchType.REGEX)

        assert len(matches) == 2
        assert matches[0].start == 6
        assert matches[0].end == 9  # "123"

    def test_handles_invalid_regex_gracefully(self):
        """Should return empty list for invalid regex."""
        text = "Some text"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("[invalid", MatchType.REGEX)

        assert matches == []

    def test_regex_case_insensitive(self):
        """Should support case-insensitive regex."""
        text = "Hello HELLO hello"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("hello", MatchType.REGEX)

        assert len(matches) == 3

    def test_regex_case_sensitive(self):
        """Should support case-sensitive regex."""
        text = "Hello HELLO hello"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("hello", MatchType.REGEX, case_sensitive=True)

        assert len(matches) == 1


class TestTextMatcherScopeFiltering:
    """Tests for scope filtering (all, first, last)."""

    def test_scope_all_returns_all_matches(self):
        """Should return all matches with scope=ALL."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.ALL)

        assert len(matches) == 3

    def test_scope_first_returns_only_first(self):
        """Should return only first match with scope=FIRST."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.FIRST)

        assert len(matches) == 1
        assert matches[0].start == 0

    def test_scope_last_returns_only_last(self):
        """Should return only last match with scope=LAST."""
        text = "cat cat cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT, scope=MatchScope.LAST)

        assert len(matches) == 1
        assert matches[0].start == 8

    def test_scope_first_on_no_matches_returns_empty(self):
        """Should return empty for first scope with no matches."""
        text = "no match here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("xyz", MatchType.EXACT, scope=MatchScope.FIRST)

        assert matches == []


class TestTextMatchReturnType:
    """Tests for TextMatch return value structure."""

    def test_match_has_start_end_positions(self):
        """TextMatch should have start and end positions."""
        text = "find me"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("me", MatchType.CONTAINS)

        assert len(matches) == 1
        match = matches[0]
        assert hasattr(match, "start")
        assert hasattr(match, "end")
        assert match.start == 5
        assert match.end == 7

    def test_match_extracts_correct_text(self):
        """Match positions should extract correct text."""
        text = "The important word here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("important", MatchType.EXACT)

        assert len(matches) == 1
        match = matches[0]
        extracted = text[match.start : match.end]
        assert extracted.lower() == "important"


class TestTextMatcherEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_text_returns_empty(self):
        """Should handle empty text."""
        matcher = TextMatcher("")

        matches = matcher.find_matches("test", MatchType.EXACT)

        assert matches == []

    def test_match_at_start_of_text(self):
        """Should find match at start of text."""
        text = "cat is here"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].start == 0

    def test_match_at_end_of_text(self):
        """Should find match at end of text."""
        text = "here is cat"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("cat", MatchType.EXACT)

        assert len(matches) == 1
        assert matches[0].end == len(text)

    def test_special_regex_chars_in_exact_mode(self):
        """Should escape special chars in exact mode."""
        text = "Use file.txt for input"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("file.txt", MatchType.EXACT)

        assert len(matches) == 1

    def test_unicode_text_matching(self):
        """Should handle unicode text."""
        text = "The caf\u00e9 serves caf\u00e9 au lait"
        matcher = TextMatcher(text)

        matches = matcher.find_matches("caf\u00e9", MatchType.EXACT)

        assert len(matches) == 2


class TestTextMatcherImmutability:
    """Tests verifying TextMatcher is a pure function-like service."""

    def test_matcher_does_not_modify_input(self):
        """TextMatcher should not modify input text."""
        original = "The cat sat"
        text = original
        matcher = TextMatcher(text)

        matcher.find_matches("cat", MatchType.EXACT)

        assert text == original

    def test_multiple_searches_independent(self):
        """Multiple searches should be independent."""
        text = "cat dog cat dog"
        matcher = TextMatcher(text)

        cats = matcher.find_matches("cat", MatchType.EXACT)
        dogs = matcher.find_matches("dog", MatchType.EXACT)

        assert len(cats) == 2
        assert len(dogs) == 2
