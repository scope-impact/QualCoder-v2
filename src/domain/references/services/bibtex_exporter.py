"""
BibTeX Exporter - Domain Service

Pure function service for exporting references to BibTeX format.
No I/O, no side effects - takes Reference entities and returns BibTeX string.

BibTeX Format Reference:
@article{citekey,
  author = {Last, First and Last2, First2},
  title = {Title of the Article},
  journal = {Journal Name},
  year = {2023},
  doi = {10.1234/example},
  url = {https://example.com},
  abstract = {Abstract text}
}
"""

from __future__ import annotations

import re
import unicodedata

from src.domain.references.entities import Reference


class BibTexExporter:
    """
    Domain service for exporting references to BibTeX format.

    Pure function - no I/O, no side effects.

    Usage:
        exporter = BibTexExporter()
        bibtex_content = exporter.export(references)
    """

    def __init__(self) -> None:
        """Initialize the exporter with cite key tracking."""
        self._used_cite_keys: set[str] = set()

    def export(self, references: list[Reference]) -> str:
        """
        Export references to BibTeX format string.

        Args:
            references: List of Reference entities to export

        Returns:
            BibTeX format string with all references
        """
        if not references:
            return ""

        # Reset cite key tracking for each export
        self._used_cite_keys = set()

        entries = []
        for ref in references:
            entry = self._export_reference(ref)
            entries.append(entry)

        return "\n\n".join(entries)

    def _export_reference(self, ref: Reference) -> str:
        """
        Export a single reference to BibTeX format.

        Args:
            ref: Reference entity to export

        Returns:
            BibTeX format string for the reference
        """
        cite_key = self._generate_cite_key(ref)
        lines = [f"@article{{{cite_key},"]

        # Author - convert semicolon-separated to "and" separated
        authors = ref.authors.replace(";", " and ")
        # Clean up extra spaces
        authors = re.sub(r"\s+and\s+", " and ", authors)
        authors = authors.strip()
        lines.append(f"  author = {{{authors}}},")

        # Title
        lines.append(f"  title = {{{ref.title}}},")

        # Journal/Source
        if ref.source:
            lines.append(f"  journal = {{{ref.source}}},")

        # Year
        if ref.year is not None:
            lines.append(f"  year = {{{ref.year}}},")

        # DOI
        if ref.doi:
            lines.append(f"  doi = {{{ref.doi}}},")

        # URL
        if ref.url:
            lines.append(f"  url = {{{ref.url}}},")

        # Abstract
        if ref.memo:
            lines.append(f"  abstract = {{{ref.memo}}},")

        # Close entry (remove trailing comma from last field)
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        lines.append("}")

        return "\n".join(lines)

    def _generate_cite_key(self, ref: Reference) -> str:
        """
        Generate a unique citation key for the reference.

        Format: authorsurname + year (e.g., smith2023)
        Adds suffix (a, b, c...) for duplicates.

        Args:
            ref: Reference entity

        Returns:
            Unique citation key string
        """
        # Extract first author surname
        authors = ref.authors.split(";")[0].strip()
        # Handle "Last, First" format
        if "," in authors:
            surname = authors.split(",")[0].strip()
        else:
            # Handle "First Last" format
            parts = authors.split()
            surname = parts[-1] if parts else "unknown"

        # Normalize surname (remove accents, lowercase, alphanumeric only)
        surname = self._normalize_for_key(surname)

        # Add year
        year = str(ref.year) if ref.year else ""
        base_key = f"{surname}{year}"

        # Ensure uniqueness
        cite_key = base_key
        suffix_index = 0
        while cite_key in self._used_cite_keys:
            suffix = chr(ord("a") + suffix_index)
            cite_key = f"{base_key}{suffix}"
            suffix_index += 1

        self._used_cite_keys.add(cite_key)
        return cite_key

    def _normalize_for_key(self, text: str) -> str:
        """
        Normalize text for use in citation key.

        Removes accents, converts to lowercase, keeps only alphanumeric.
        """
        # Remove accents
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # Lowercase and keep only alphanumeric
        text = text.lower()
        text = re.sub(r"[^a-z0-9]", "", text)

        return text or "unknown"
