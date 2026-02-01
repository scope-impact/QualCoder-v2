"""
RIS Parser Tests - Domain Service

Tests for parsing RIS (Research Information Systems) format files.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestRisParserBasic:
    """Tests for basic RIS parsing functionality."""

    def test_parse_single_journal_article(self):
        """Should parse a single journal article reference."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Popper, Karl
TI  - The Logic of Scientific Discovery
JO  - Philosophy of Science
PY  - 1959
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        ref = results[0]
        assert ref.title == "The Logic of Scientific Discovery"
        assert ref.authors == "Popper, Karl"
        assert ref.year == 1959
        assert ref.source == "Philosophy of Science"

    def test_parse_multiple_references(self):
        """Should parse multiple references from RIS content."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Smith, John
TI  - First Article
PY  - 2020
ER  -
TY  - BOOK
AU  - Doe, Jane
TI  - Second Book
PY  - 2021
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 2
        assert results[0].title == "First Article"
        assert results[1].title == "Second Book"

    def test_parse_multiple_authors(self):
        """Should combine multiple authors into single string."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Smith, John
AU  - Doe, Jane
AU  - Wilson, Bob
TI  - Collaborative Research
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        ref = results[0]
        assert "Smith, John" in ref.authors
        assert "Doe, Jane" in ref.authors
        assert "Wilson, Bob" in ref.authors

    def test_parse_with_doi(self):
        """Should extract DOI from reference."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article with DOI
PY  - 2023
DO  - 10.1234/test.2023.001
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].doi == "10.1234/test.2023.001"

    def test_parse_with_url(self):
        """Should extract URL from reference."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article with URL
PY  - 2023
UR  - https://example.com/article
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].url == "https://example.com/article"

    def test_parse_with_abstract_as_memo(self):
        """Should use abstract as memo field."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article with Abstract
PY  - 2023
AB  - This is the abstract of the article.
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].memo == "This is the abstract of the article."


class TestRisParserAlternativeTags:
    """Tests for alternative RIS tag handling."""

    def test_parse_t1_as_title(self):
        """Should use T1 tag as title when TI not present."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
T1  - Title from T1 Tag
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].title == "Title from T1 Tag"

    def test_parse_y1_as_year(self):
        """Should extract year from Y1 tag when PY not present."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article Title
Y1  - 2023/05/15
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].year == 2023

    def test_parse_jf_as_source(self):
        """Should use JF tag as source when JO not present."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article Title
JF  - Journal from JF Tag
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].source == "Journal from JF Tag"

    def test_parse_a1_as_author(self):
        """Should use A1 tag as author when AU not present."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
A1  - Primary, Author
TI  - Article Title
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].authors == "Primary, Author"


class TestRisParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_empty_content(self):
        """Should return empty list for empty content."""
        from src.domain.references.services.ris_parser import RisParser

        parser = RisParser()
        results = parser.parse("")

        assert results == []

    def test_parse_whitespace_only(self):
        """Should return empty list for whitespace-only content."""
        from src.domain.references.services.ris_parser import RisParser

        parser = RisParser()
        results = parser.parse("   \n\n   ")

        assert results == []

    def test_parse_missing_required_fields(self):
        """Should skip references missing required title or author."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author Only
ER  -
TY  - JOUR
TI  - Title Only
ER  -
TY  - JOUR
AU  - Valid, Author
TI  - Valid Reference
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        # Only the valid reference should be returned
        assert len(results) == 1
        assert results[0].title == "Valid Reference"

    def test_parse_handles_windows_line_endings(self):
        """Should handle Windows-style line endings (CRLF)."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = "TY  - JOUR\r\nAU  - Author, Test\r\nTI  - Windows Line Endings\r\nPY  - 2023\r\nER  - \r\n"

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].title == "Windows Line Endings"

    def test_parse_handles_extra_whitespace(self):
        """Should trim extra whitespace from values."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  -   Author With Spaces
TI  -   Title With Spaces
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].title == "Title With Spaces"
        assert results[0].authors == "Author With Spaces"

    def test_parse_invalid_year_uses_none(self):
        """Should use None for invalid year values."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article with Invalid Year
PY  - not-a-year
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].year is None

    def test_parse_year_from_date_string(self):
        """Should extract year from date strings like 2023/01/15."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - JOUR
AU  - Author, Test
TI  - Article
PY  - 2023/01/15
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].year == 2023


class TestRisParserReferenceTypes:
    """Tests for different reference types."""

    def test_parse_book_reference(self):
        """Should parse book reference type."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - BOOK
AU  - Kuhn, Thomas
TI  - The Structure of Scientific Revolutions
PB  - University of Chicago Press
PY  - 1962
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        ref = results[0]
        assert ref.title == "The Structure of Scientific Revolutions"
        assert ref.source == "University of Chicago Press"

    def test_parse_conference_paper(self):
        """Should parse conference paper reference type."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - CPAPER
AU  - Researcher, Test
TI  - Conference Paper Title
T2  - Proceedings of Test Conference
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].title == "Conference Paper Title"

    def test_parse_thesis(self):
        """Should parse thesis reference type."""
        from src.domain.references.services.ris_parser import RisParser

        ris_content = """TY  - THES
AU  - Student, Graduate
TI  - Doctoral Dissertation Title
PB  - University Name
PY  - 2023
ER  - """

        parser = RisParser()
        results = parser.parse(ris_content)

        assert len(results) == 1
        assert results[0].title == "Doctoral Dissertation Title"
