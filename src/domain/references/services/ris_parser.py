"""
RIS Parser - Domain Service

Pure function service for parsing RIS (Research Information Systems) format files.
No I/O, no side effects - takes string input and returns parsed data.

RIS Format Reference:
- TY: Type of reference (JOUR, BOOK, etc.)
- AU/A1: Author
- TI/T1: Title
- JO/JF: Journal name
- PB: Publisher
- PY/Y1: Publication year
- DO: DOI
- UR: URL
- AB: Abstract
- ER: End of reference
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedReference:
    """
    Parsed reference data from RIS format.

    Contains extracted fields ready for conversion to Reference entity.
    """

    title: str
    authors: str
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    url: str | None = None
    memo: str | None = None


class RisParser:
    """
    Domain service for parsing RIS format content.

    Pure function - no I/O, no side effects.

    Usage:
        parser = RisParser()
        references = parser.parse(ris_content)
    """

    # Tag to field mapping with alternatives
    # Format: primary_tag -> (field_name, [alternative_tags])
    TAG_MAPPING = {
        "TI": "title",
        "T1": "title",
        "AU": "authors",
        "A1": "authors",
        "PY": "year",
        "Y1": "year",
        "JO": "source",
        "JF": "source",
        "PB": "source",  # Publisher for books
        "DO": "doi",
        "UR": "url",
        "AB": "memo",
    }

    def parse(self, content: str) -> list[ParsedReference]:
        """
        Parse RIS format content into list of ParsedReference objects.

        Args:
            content: RIS format string content

        Returns:
            List of ParsedReference objects for valid references
        """
        if not content or not content.strip():
            return []

        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        references = []
        current_ref: dict[str, str | list[str]] = {}

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse tag and value
            tag, value = self._parse_line(line)
            if not tag:
                continue

            # End of reference marker
            if tag == "ER":
                ref = self._build_reference(current_ref)
                if ref:
                    references.append(ref)
                current_ref = {}
                continue

            # Type marker - start new reference
            if tag == "TY":
                if current_ref:
                    ref = self._build_reference(current_ref)
                    if ref:
                        references.append(ref)
                current_ref = {}
                continue

            # Map tag to field
            field = self.TAG_MAPPING.get(tag)
            if not field:
                continue

            # Handle multiple authors
            if field == "authors":
                if "authors" not in current_ref:
                    current_ref["authors"] = []
                if isinstance(current_ref["authors"], list):
                    current_ref["authors"].append(value)
            else:
                # Don't overwrite if already set (prefer primary tags)
                if field not in current_ref:
                    current_ref[field] = value

        # Handle last reference if no ER tag
        if current_ref:
            ref = self._build_reference(current_ref)
            if ref:
                references.append(ref)

        return references

    def _parse_line(self, line: str) -> tuple[str | None, str]:
        """
        Parse a single RIS line into tag and value.

        RIS format: TAG  - Value

        Returns:
            Tuple of (tag, value) or (None, "") if invalid
        """
        # RIS line format: XX  - value
        match = re.match(r"^([A-Z][A-Z0-9])\s+-\s*(.*)$", line)
        if match:
            tag = match.group(1)
            value = match.group(2).strip()
            return tag, value
        return None, ""

    def _build_reference(
        self, data: dict[str, str | list[str]]
    ) -> ParsedReference | None:
        """
        Build a ParsedReference from collected data.

        Returns None if required fields (title, authors) are missing.
        """
        # Get title
        title = data.get("title", "")
        if isinstance(title, list):
            title = title[0] if title else ""
        title = str(title).strip()

        # Get authors
        authors_data = data.get("authors", [])
        if isinstance(authors_data, list):
            authors = "; ".join(str(a).strip() for a in authors_data)
        else:
            authors = str(authors_data).strip()

        # Require both title and authors
        if not title or not authors:
            return None

        # Parse year
        year = self._parse_year(data.get("year"))

        # Get optional fields
        source = self._get_string(data.get("source"))
        doi = self._get_string(data.get("doi"))
        url = self._get_string(data.get("url"))
        memo = self._get_string(data.get("memo"))

        return ParsedReference(
            title=title,
            authors=authors,
            year=year,
            source=source,
            doi=doi,
            url=url,
            memo=memo,
        )

    def _parse_year(self, value: str | list[str] | None) -> int | None:
        """
        Parse year from various formats.

        Handles: "2023", "2023/01/15", etc.
        """
        if not value:
            return None

        if isinstance(value, list):
            value = value[0] if value else ""

        value = str(value).strip()
        if not value:
            return None

        # Try to extract 4-digit year
        match = re.match(r"^(\d{4})", value)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

        # Try direct integer conversion
        try:
            return int(value)
        except ValueError:
            return None

    def _get_string(self, value: str | list[str] | None) -> str | None:
        """Get string value, handling list case."""
        if not value:
            return None

        if isinstance(value, list):
            value = value[0] if value else ""

        value = str(value).strip()
        return value if value else None
