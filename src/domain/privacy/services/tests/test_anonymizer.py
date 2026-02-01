"""
Tests for TextAnonymizer domain service.

TDD tests written BEFORE implementation.
"""

from __future__ import annotations

import pytest


class TestTextAnonymizer:
    """Tests for TextAnonymizer domain service."""

    def test_apply_single_pseudonym(self):
        """Should replace single name with pseudonym."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "John Smith said hello."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="Participant A",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms)

        assert result.anonymized_text == "Participant A said hello."
        assert len(result.replacements) == 1
        assert result.replacements[0].original_text == "John Smith"
        assert result.replacements[0].replacement_text == "Participant A"

    def test_apply_multiple_occurrences(self):
        """Should replace all occurrences of a name."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "John Smith met Jane. Later, John Smith left."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms)

        assert result.anonymized_text == "P1 met Jane. Later, P1 left."
        assert len(result.replacements) == 1
        assert len(result.replacements[0].positions) == 2

    def test_apply_multiple_pseudonyms(self):
        """Should replace multiple different names."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "John Smith works at Acme Corp."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            ),
            Pseudonym(
                id=PseudonymId(value=2),
                real_name="Acme Corp",
                alias="Company X",
                category=PseudonymCategory.ORGANIZATION,
            ),
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms)

        assert result.anonymized_text == "P1 works at Company X."
        assert len(result.replacements) == 2

    def test_case_insensitive_matching(self):
        """Should match case-insensitively when option enabled."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "JOHN SMITH and john smith attended."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms, match_case=False)

        assert "P1" in result.anonymized_text
        # Both instances should be replaced
        assert result.anonymized_text.count("P1") == 2

    def test_case_sensitive_matching(self):
        """Should match case-sensitively when option enabled."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "JOHN SMITH and John Smith attended."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms, match_case=True)

        # Only exact case match should be replaced
        assert result.anonymized_text == "JOHN SMITH and P1 attended."

    def test_whole_word_matching(self):
        """Should only match whole words when option enabled."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "Johnson is not John."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms, whole_word=True)

        # "Johnson" should not be affected
        assert result.anonymized_text == "Johnson is not P1."

    def test_no_matches_returns_original(self):
        """Should return original text when no matches found."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "No names here."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms)

        assert result.anonymized_text == text
        assert len(result.replacements) == 0

    def test_preview_replacements(self):
        """Should preview replacements without modifying text."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "John Smith met Jane Doe."
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            ),
            Pseudonym(
                id=PseudonymId(value=2),
                real_name="Jane Doe",
                alias="P2",
                category=PseudonymCategory.PERSON,
            ),
        ]

        anonymizer = TextAnonymizer(text)
        previews = anonymizer.preview_replacements(pseudonyms)

        assert len(previews) == 2
        # Check preview contains position info
        assert any(p.original_text == "John Smith" for p in previews)
        assert any(p.original_text == "Jane Doe" for p in previews)

    def test_empty_pseudonym_list(self):
        """Should handle empty pseudonym list."""
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "Some text here."
        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms([])

        assert result.anonymized_text == text
        assert len(result.replacements) == 0

    def test_positions_track_original_locations(self):
        """Replacement positions should reference original text positions."""
        from src.domain.privacy.entities import (
            Pseudonym,
            PseudonymCategory,
            PseudonymId,
        )
        from src.domain.privacy.services.anonymizer import TextAnonymizer

        text = "Hello John Smith!"
        pseudonyms = [
            Pseudonym(
                id=PseudonymId(value=1),
                real_name="John Smith",
                alias="P1",
                category=PseudonymCategory.PERSON,
            )
        ]

        anonymizer = TextAnonymizer(text)
        result = anonymizer.apply_pseudonyms(pseudonyms)

        replacement = result.replacements[0]
        # "John Smith" starts at position 6
        assert replacement.positions[0] == (6, 16)


class TestAnonymizationResult:
    """Tests for AnonymizationResult value object."""

    def test_result_contains_all_fields(self):
        """Should contain anonymized text and replacements."""
        from src.domain.privacy.entities import TextReplacement
        from src.domain.privacy.services.anonymizer import AnonymizationResult

        result = AnonymizationResult(
            anonymized_text="P1 said hello.",
            replacements=(
                TextReplacement(
                    original_text="John Smith",
                    replacement_text="P1",
                    positions=((0, 10),),
                ),
            ),
        )

        assert result.anonymized_text == "P1 said hello."
        assert len(result.replacements) == 1

    def test_result_is_immutable(self):
        """AnonymizationResult should be frozen."""
        from src.domain.privacy.services.anonymizer import AnonymizationResult

        result = AnonymizationResult(
            anonymized_text="Test",
            replacements=(),
        )

        with pytest.raises((AttributeError, TypeError)):
            result.anonymized_text = "Changed"
