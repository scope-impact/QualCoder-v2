"""
Tests for PresidioDetector infrastructure service.

TDD tests written BEFORE implementation.
Requires optional [pii] dependencies: presidio-analyzer, spacy.
"""

from __future__ import annotations

import pytest

from src.domain.privacy.entities import PseudonymCategory

# Skip all tests in this module if presidio is not installed
pytest.importorskip("presidio_analyzer", reason="Presidio not installed (optional [pii] dependency)")


@pytest.mark.pii
class TestPresidioDetector:
    """Tests for PresidioDetector PII detection service."""

    @pytest.fixture
    def detector(self):
        """Create a PresidioDetector instance."""
        from src.infrastructure.privacy.presidio_detector import PresidioDetector

        return PresidioDetector()

    def test_detects_person_names(self, detector):
        """Should detect person names in text."""
        text = "John Smith met with Sarah Johnson yesterday."

        identifiers = detector.detect(text)

        person_names = [i for i in identifiers if i.category == PseudonymCategory.PERSON]
        assert len(person_names) >= 2
        assert any("John Smith" in i.text for i in person_names)
        assert any("Sarah Johnson" in i.text for i in person_names)

    def test_detects_organizations(self, detector):
        """Should detect organization names."""
        text = "She works at Microsoft and previously worked at Google."

        identifiers = detector.detect(text)

        orgs = [i for i in identifiers if i.category == PseudonymCategory.ORGANIZATION]
        assert len(orgs) >= 1

    def test_detects_locations(self, detector):
        """Should detect location names."""
        text = "The interview was conducted in New York City."

        identifiers = detector.detect(text)

        locations = [i for i in identifiers if i.category == PseudonymCategory.LOCATION]
        assert len(locations) >= 1

    def test_detects_dates(self, detector):
        """Should detect dates."""
        text = "The event happened on January 15, 2024."

        identifiers = detector.detect(text)

        dates = [i for i in identifiers if i.category == PseudonymCategory.DATE]
        assert len(dates) >= 1

    def test_returns_confidence_scores(self, detector):
        """Should return confidence scores between 0 and 1."""
        text = "John Smith is a researcher."

        identifiers = detector.detect(text)

        for identifier in identifiers:
            assert 0.0 <= identifier.confidence <= 1.0

    def test_returns_correct_positions(self, detector):
        """Should return correct text positions."""
        text = "Hello John Smith, welcome."

        identifiers = detector.detect(text)

        for identifier in identifiers:
            for start, end in identifier.positions:
                assert text[start:end] == identifier.text

    def test_filters_by_minimum_confidence(self, detector):
        """Should filter results by minimum confidence threshold."""
        text = "John Smith works at Acme Corp in New York."

        # High threshold should return fewer results
        high_conf = detector.detect(text, min_confidence=0.9)
        low_conf = detector.detect(text, min_confidence=0.3)

        assert len(low_conf) >= len(high_conf)

    def test_filters_by_categories(self, detector):
        """Should filter results by specified categories."""
        text = "John Smith visited New York on January 1st."

        # Only detect persons
        persons_only = detector.detect(
            text, categories=[PseudonymCategory.PERSON]
        )

        assert all(i.category == PseudonymCategory.PERSON for i in persons_only)

    def test_handles_empty_text(self, detector):
        """Should handle empty text gracefully."""
        identifiers = detector.detect("")
        assert identifiers == []

    def test_handles_text_without_pii(self, detector):
        """Should return empty list for text without PII."""
        text = "The weather is nice today."

        identifiers = detector.detect(text)

        # May still detect some false positives, but should be minimal
        assert len(identifiers) <= 1

    def test_generates_suggested_aliases(self, detector):
        """Should generate suggested pseudonyms for detected entities."""
        text = "John Smith and Jane Doe are participants."

        identifiers = detector.detect(text, generate_suggestions=True)

        persons = [i for i in identifiers if i.category == PseudonymCategory.PERSON]
        # At least some should have suggestions
        assert any(i.suggested_alias is not None for i in persons)

    def test_suggested_aliases_are_unique(self, detector):
        """Suggested aliases should be unique within a detection run."""
        text = "John Smith, Jane Doe, and Bob Wilson participated."

        identifiers = detector.detect(text, generate_suggestions=True)

        suggestions = [i.suggested_alias for i in identifiers if i.suggested_alias]
        unique_suggestions = set(suggestions)
        assert len(suggestions) == len(unique_suggestions)
