"""
RIS Exporter - Domain Service

Pure function service for exporting references to RIS format.
No I/O, no side effects - takes Reference entities and returns RIS string.

RIS Format Reference:
- TY: Type of reference (JOUR for journal article)
- AU: Author (one per line for multiple authors)
- TI: Title
- JO: Journal name
- PY: Publication year
- DO: DOI
- UR: URL
- AB: Abstract
- ER: End of reference
"""

from __future__ import annotations

from src.domain.references.entities import Reference


class RisExporter:
    """
    Domain service for exporting references to RIS format.

    Pure function - no I/O, no side effects.

    Usage:
        exporter = RisExporter()
        ris_content = exporter.export(references)
    """

    def export(self, references: list[Reference]) -> str:
        """
        Export references to RIS format string.

        Args:
            references: List of Reference entities to export

        Returns:
            RIS format string with all references
        """
        if not references:
            return ""

        entries = []
        for ref in references:
            entry = self._export_reference(ref)
            entries.append(entry)

        return "\n".join(entries)

    def _export_reference(self, ref: Reference) -> str:
        """
        Export a single reference to RIS format.

        Args:
            ref: Reference entity to export

        Returns:
            RIS format string for the reference
        """
        lines = []

        # Type (always JOUR for now - could extend based on source type)
        lines.append("TY  - JOUR")

        # Authors - split by semicolon for multiple authors
        authors = ref.authors.split(";")
        for author in authors:
            author = author.strip()
            if author:
                lines.append(f"AU  - {author}")

        # Title
        lines.append(f"TI  - {ref.title}")

        # Source/Journal
        if ref.source:
            lines.append(f"JO  - {ref.source}")

        # Year
        if ref.year is not None:
            lines.append(f"PY  - {ref.year}")

        # DOI
        if ref.doi:
            lines.append(f"DO  - {ref.doi}")

        # URL
        if ref.url:
            lines.append(f"UR  - {ref.url}")

        # Abstract/Memo
        if ref.memo:
            lines.append(f"AB  - {ref.memo}")

        # End of reference
        lines.append("ER  -")

        return "\n".join(lines)
