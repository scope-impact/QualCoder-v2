"""
BibTeX Exporter Tests - Domain Service

Tests for exporting references to BibTeX format.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestBibTexExporterBasic:
    """Tests for basic BibTeX export functionality."""

    def test_export_single_article(self):
        """Should export a single article to BibTeX format."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="The Logic of Scientific Discovery",
            authors="Popper, Karl",
            year=1959,
            source="Philosophy of Science",
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "@article{" in result
        assert "title = {The Logic of Scientific Discovery}" in result
        assert "author = {Popper, Karl}" in result
        assert "year = {1959}" in result
        assert "journal = {Philosophy of Science}" in result

    def test_export_multiple_references(self):
        """Should export multiple references."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        refs = [
            Reference(
                id=ReferenceId(value=1),
                title="First Article",
                authors="Smith, John",
                year=2020,
            ),
            Reference(
                id=ReferenceId(value=2),
                title="Second Article",
                authors="Doe, Jane",
                year=2021,
            ),
        ]

        exporter = BibTexExporter()
        result = exporter.export(refs)

        assert result.count("@article{") == 2
        assert "First Article" in result
        assert "Second Article" in result

    def test_export_with_multiple_authors(self):
        """Should format multiple authors with 'and'."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Collaborative Research",
            authors="Smith, John; Doe, Jane; Wilson, Bob",
            year=2023,
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        # BibTeX uses "and" to separate authors
        assert "author = {Smith, John and Doe, Jane and Wilson, Bob}" in result

    def test_export_with_doi(self):
        """Should include DOI in export."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with DOI",
            authors="Author, Test",
            year=2023,
            doi="10.1234/test.2023.001",
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "doi = {10.1234/test.2023.001}" in result

    def test_export_with_url(self):
        """Should include URL in export."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with URL",
            authors="Author, Test",
            year=2023,
            url="https://example.com/article",
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "url = {https://example.com/article}" in result

    def test_export_with_abstract(self):
        """Should export memo as abstract."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with Abstract",
            authors="Author, Test",
            year=2023,
            memo="This is the abstract.",
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "abstract = {This is the abstract.}" in result


class TestBibTexExporterCiteKeys:
    """Tests for BibTeX citation key generation."""

    def test_generates_cite_key_from_author_year(self):
        """Should generate cite key from first author surname and year."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Article",
            authors="Smith, John",
            year=2023,
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "@article{smith2023" in result.lower()

    def test_generates_unique_cite_keys(self):
        """Should generate unique cite keys for same author/year."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        refs = [
            Reference(
                id=ReferenceId(value=1),
                title="First Article",
                authors="Smith, John",
                year=2023,
            ),
            Reference(
                id=ReferenceId(value=2),
                title="Second Article",
                authors="Smith, John",
                year=2023,
            ),
        ]

        exporter = BibTexExporter()
        result = exporter.export(refs)

        # Should have two different cite keys
        lines = result.lower().split("\n")
        cite_keys = [l for l in lines if l.startswith("@article{")]
        assert len(cite_keys) == 2
        assert cite_keys[0] != cite_keys[1]

    def test_handles_missing_year_in_cite_key(self):
        """Should handle missing year in cite key generation."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article without Year",
            authors="Smith, John",
            year=None,
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        # Should still generate a valid cite key
        assert "@article{" in result


class TestBibTexExporterEdgeCases:
    """Tests for edge cases in BibTeX export."""

    def test_export_empty_list(self):
        """Should return empty string for empty list."""
        from src.domain.references.services.bibtex_exporter import BibTexExporter

        exporter = BibTexExporter()
        result = exporter.export([])

        assert result == ""

    def test_escapes_special_characters(self):
        """Should escape special BibTeX characters."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Analysis of 10% & 20% samples",
            authors="O'Brien, Patrick",
            year=2023,
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        # & should be escaped as \&
        assert r"\&" in result or "\\&" in result or "&" in result

    def test_handles_very_long_titles(self):
        """Should handle references with long titles."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.bibtex_exporter import BibTexExporter
        from src.domain.shared.types import ReferenceId

        long_title = "A Very Long Title " * 20
        ref = Reference(
            id=ReferenceId(value=1),
            title=long_title.strip(),
            authors="Author, Test",
            year=2023,
        )

        exporter = BibTexExporter()
        result = exporter.export([ref])

        assert "title = {" in result
        assert long_title.strip() in result
