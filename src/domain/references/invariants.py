"""
References Context: Invariants

Pure predicate functions for validating reference data.
No I/O, no side effects - boolean checks only.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

# =============================================================================
# Constants
# =============================================================================

MAX_TITLE_LENGTH = 500
MAX_AUTHORS_LENGTH = 1000
MIN_YEAR = 1000

# DOI pattern: 10.xxxx/xxxxx
DOI_PATTERN = re.compile(r"^10\.\d+/\S+$")


# =============================================================================
# Validation Functions
# =============================================================================


def is_valid_title(title: str) -> bool:
    """
    Check if reference title meets requirements.

    Title must be non-empty and not exceed MAX_TITLE_LENGTH characters.
    """
    if not title:
        return False
    stripped = title.strip()
    if not stripped:
        return False
    return 1 <= len(stripped) <= MAX_TITLE_LENGTH


def is_valid_year(year: int | None) -> bool:
    """
    Check if year is valid.

    Year is optional (None is valid). If provided, must be between
    MIN_YEAR and next year (for "in press" publications).
    """
    if year is None:
        return True
    current_year = datetime.now(UTC).year
    return MIN_YEAR <= year <= current_year + 1


def is_valid_doi(doi: str | None) -> bool:
    """
    Check if DOI follows standard format.

    DOI is optional (None or empty string is valid).
    If provided, must match pattern: 10.xxxx/xxxxx
    """
    if not doi:
        return True
    return bool(DOI_PATTERN.match(doi))


def is_valid_authors(authors: str) -> bool:
    """
    Check if authors string meets requirements.

    Authors must be non-empty and not exceed MAX_AUTHORS_LENGTH characters.
    """
    if not authors:
        return False
    stripped = authors.strip()
    if not stripped:
        return False
    return 1 <= len(stripped) <= MAX_AUTHORS_LENGTH
