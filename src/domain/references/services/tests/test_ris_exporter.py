"""
RIS Exporter Tests - Domain Service

Tests for exporting references to RIS format.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestRisExporterBasic:
    """Tests for basic RIS export functionality."""

    def test_export_single_reference(self):
        """Should export a single reference to RIS format."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="The Logic of Scientific Discovery",
            authors="Popper, Karl",
            year=1959,
            source="Philosophy of Science",
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "TY  - JOUR" in result
        assert "TI  - The Logic of Scientific Discovery" in result
        assert "AU  - Popper, Karl" in result
        assert "PY  - 1959" in result
        assert "JO  - Philosophy of Science" in result
        assert "ER  -" in result

    def test_export_multiple_references(self):
        """Should export multiple references separated by blank lines."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
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

        exporter = RisExporter()
        result = exporter.export(refs)

        assert result.count("TY  - JOUR") == 2
        assert result.count("ER  -") == 2
        assert "First Article" in result
        assert "Second Article" in result

    def test_export_with_multiple_authors(self):
        """Should export multiple authors as separate AU tags."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Collaborative Research",
            authors="Smith, John; Doe, Jane; Wilson, Bob",
            year=2023,
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert result.count("AU  -") == 3
        assert "AU  - Smith, John" in result
        assert "AU  - Doe, Jane" in result
        assert "AU  - Wilson, Bob" in result

    def test_export_with_doi(self):
        """Should include DOI in export."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with DOI",
            authors="Author, Test",
            year=2023,
            doi="10.1234/test.2023.001",
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "DO  - 10.1234/test.2023.001" in result

    def test_export_with_url(self):
        """Should include URL in export."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with URL",
            authors="Author, Test",
            year=2023,
            url="https://example.com/article",
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "UR  - https://example.com/article" in result

    def test_export_with_memo_as_abstract(self):
        """Should export memo as abstract (AB tag)."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article with Abstract",
            authors="Author, Test",
            year=2023,
            memo="This is the abstract of the article.",
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "AB  - This is the abstract of the article." in result


class TestRisExporterEdgeCases:
    """Tests for edge cases in RIS export."""

    def test_export_empty_list(self):
        """Should return empty string for empty list."""
        from src.domain.references.services.ris_exporter import RisExporter

        exporter = RisExporter()
        result = exporter.export([])

        assert result == ""

    def test_export_without_optional_fields(self):
        """Should handle references without optional fields."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Minimal Reference",
            authors="Author, Test",
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "TY  - JOUR" in result
        assert "TI  - Minimal Reference" in result
        assert "AU  - Author, Test" in result
        assert "ER  -" in result
        # Should not have empty tags
        assert "PY  -" not in result or "PY  - \n" not in result

    def test_export_without_year(self):
        """Should omit year tag when year is None."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Article without Year",
            authors="Author, Test",
            year=None,
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        # Should not contain PY tag at all, or only with value
        lines = result.split("\n")
        py_lines = [l for l in lines if l.startswith("PY")]
        assert len(py_lines) == 0

    def test_export_preserves_special_characters(self):
        """Should preserve special characters in text."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.shared.types import ReferenceId

        ref = Reference(
            id=ReferenceId(value=1),
            title="Analysis of α-particles & β-decay",
            authors="Müller, Hans",
            year=2023,
        )

        exporter = RisExporter()
        result = exporter.export([ref])

        assert "Analysis of α-particles & β-decay" in result
        assert "Müller, Hans" in result


class TestRisExporterRoundTrip:
    """Tests for RIS export/import round-trip consistency."""

    def test_exported_ris_can_be_reimported(self):
        """Should produce RIS that can be parsed back."""
        from src.domain.references.entities import Reference
        from src.domain.references.services.ris_exporter import RisExporter
        from src.domain.references.services.ris_parser import RisParser
        from src.domain.shared.types import ReferenceId

        original = Reference(
            id=ReferenceId(value=1),
            title="Round Trip Test",
            authors="Smith, John; Doe, Jane",
            year=2023,
            source="Test Journal",
            doi="10.1234/test",
            url="https://example.com",
            memo="Test abstract",
        )

        # Export
        exporter = RisExporter()
        ris_content = exporter.export([original])

        # Re-import
        parser = RisParser()
        parsed = parser.parse(ris_content)

        assert len(parsed) == 1
        reimported = parsed[0]
        assert reimported.title == original.title
        assert reimported.year == original.year
        assert reimported.doi == original.doi
        assert reimported.url == original.url
