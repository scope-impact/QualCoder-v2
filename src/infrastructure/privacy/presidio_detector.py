"""
PresidioDetector - Infrastructure service for PII detection.

Wraps Microsoft Presidio for detecting personally identifiable information
in text and maps results to our domain entities.

Usage:
    detector = PresidioDetector()
    identifiers = detector.detect("John Smith works at Acme Corp.")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.privacy.entities import DetectedIdentifier, PseudonymCategory

if TYPE_CHECKING:
    pass

# Presidio entity types mapped to our categories
PRESIDIO_TO_CATEGORY: dict[str, PseudonymCategory] = {
    # Person names
    "PERSON": PseudonymCategory.PERSON,
    "PER": PseudonymCategory.PERSON,
    # Organizations
    "ORGANIZATION": PseudonymCategory.ORGANIZATION,
    "ORG": PseudonymCategory.ORGANIZATION,
    # Locations
    "LOCATION": PseudonymCategory.LOCATION,
    "LOC": PseudonymCategory.LOCATION,
    "GPE": PseudonymCategory.LOCATION,  # Geo-political entity
    # Dates
    "DATE": PseudonymCategory.DATE,
    "DATE_TIME": PseudonymCategory.DATE,
    # Other PII types → OTHER
    "EMAIL_ADDRESS": PseudonymCategory.OTHER,
    "PHONE_NUMBER": PseudonymCategory.OTHER,
    "CREDIT_CARD": PseudonymCategory.OTHER,
    "IP_ADDRESS": PseudonymCategory.OTHER,
    "US_SSN": PseudonymCategory.OTHER,
    "US_PASSPORT": PseudonymCategory.OTHER,
    "US_DRIVER_LICENSE": PseudonymCategory.OTHER,
    "NRP": PseudonymCategory.OTHER,  # Nationalities, religious, political groups
}

# Alias generation templates by category
ALIAS_TEMPLATES: dict[PseudonymCategory, list[str]] = {
    PseudonymCategory.PERSON: [
        "Participant {n}",
        "Respondent {n}",
        "Interviewee {n}",
        "Subject {n}",
        "Person {n}",
    ],
    PseudonymCategory.ORGANIZATION: [
        "Organization {n}",
        "Company {n}",
        "Institution {n}",
        "Agency {n}",
    ],
    PseudonymCategory.LOCATION: [
        "Location {n}",
        "Place {n}",
        "City {n}",
        "Site {n}",
    ],
    PseudonymCategory.DATE: [
        "Date {n}",
        "Time Period {n}",
    ],
    PseudonymCategory.OTHER: [
        "Identifier {n}",
        "Reference {n}",
    ],
}


class PresidioDetector:
    """
    Infrastructure service for detecting PII using Microsoft Presidio.

    Maps Presidio's detection results to our domain DetectedIdentifier entities.
    Provides confidence filtering and optional alias suggestions.
    """

    def __init__(self, language: str = "en") -> None:
        """
        Initialize the Presidio detector.

        Args:
            language: Language code for NLP model (default: "en")
        """
        self._language = language
        self._analyzer = None
        self._alias_counters: dict[PseudonymCategory, int] = {}

    def _get_analyzer(self):
        """Lazy-load the Presidio analyzer."""
        if self._analyzer is None:
            try:
                from presidio_analyzer import AnalyzerEngine

                self._analyzer = AnalyzerEngine()
            except ImportError as e:
                raise ImportError(
                    "Presidio is not installed. Install with: "
                    "pip install presidio-analyzer presidio-anonymizer && "
                    "python -m spacy download en_core_web_sm"
                ) from e
        return self._analyzer

    def detect(
        self,
        text: str,
        min_confidence: float = 0.5,
        categories: list[PseudonymCategory] | None = None,
        generate_suggestions: bool = False,
    ) -> list[DetectedIdentifier]:
        """
        Detect PII entities in text.

        Args:
            text: Text to analyze for PII
            min_confidence: Minimum confidence threshold (0.0-1.0)
            categories: Filter to specific categories (None = all)
            generate_suggestions: Generate suggested pseudonyms

        Returns:
            List of DetectedIdentifier entities with positions and confidence
        """
        if not text or not text.strip():
            return []

        # Reset alias counters for this detection run
        if generate_suggestions:
            self._alias_counters = {cat: 0 for cat in PseudonymCategory}

        analyzer = self._get_analyzer()

        # Determine which entity types to detect
        entities_to_detect = None  # None = all
        if categories:
            entities_to_detect = [
                entity_type
                for entity_type, category in PRESIDIO_TO_CATEGORY.items()
                if category in categories
            ]

        # Run Presidio analysis
        results = analyzer.analyze(
            text=text,
            language=self._language,
            entities=entities_to_detect,
            score_threshold=min_confidence,
        )

        # Convert to our domain entities
        identifiers: list[DetectedIdentifier] = []
        seen_texts: set[str] = set()  # For deduplication

        for result in results:
            entity_text = text[result.start : result.end]

            # Skip duplicates (same text already detected)
            if entity_text in seen_texts:
                continue
            seen_texts.add(entity_text)

            # Map Presidio entity type to our category
            category = PRESIDIO_TO_CATEGORY.get(
                result.entity_type, PseudonymCategory.OTHER
            )

            # Filter by category if specified
            if categories and category not in categories:
                continue

            # Find all positions of this text in the source
            positions = self._find_all_positions(text, entity_text)

            # Generate suggested alias if requested
            suggested_alias = None
            if generate_suggestions:
                suggested_alias = self._generate_alias(category)

            identifiers.append(
                DetectedIdentifier(
                    text=entity_text,
                    category=category,
                    positions=tuple(positions),
                    confidence=result.score,
                    suggested_alias=suggested_alias,
                )
            )

        # Sort by position (first occurrence)
        identifiers.sort(key=lambda x: x.positions[0][0] if x.positions else 0)

        return identifiers

    def _find_all_positions(
        self, text: str, search_text: str
    ) -> list[tuple[int, int]]:
        """Find all positions of search_text in text."""
        positions = []
        start = 0
        while True:
            pos = text.find(search_text, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(search_text)))
            start = pos + 1
        return positions

    def _generate_alias(self, category: PseudonymCategory) -> str:
        """Generate a unique alias for the given category."""
        self._alias_counters[category] = self._alias_counters.get(category, 0) + 1
        counter = self._alias_counters[category]

        templates = ALIAS_TEMPLATES.get(category, ["Entity {n}"])
        template = templates[0]  # Use first template

        return template.format(n=counter)


class PresidioDetectorFactory:
    """Factory for creating PresidioDetector instances."""

    _instance: PresidioDetector | None = None

    @classmethod
    def get_detector(cls, language: str = "en") -> PresidioDetector:
        """Get or create a detector instance (singleton per language)."""
        if cls._instance is None or cls._instance._language != language:
            cls._instance = PresidioDetector(language=language)
        return cls._instance
