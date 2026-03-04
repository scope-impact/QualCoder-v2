"""
Exchange Infra: Code List Parser

Parses a plain-text code list into structured code and category entries.

Format:
  - One code per line
  - Indented lines (spaces or tabs) become codes under the preceding
    non-indented line (which becomes a category)
  - Lines starting with # are comments
  - Empty lines are skipped
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedCode:
    """A code parsed from the text list."""

    name: str
    category_name: str | None = None


@dataclass(frozen=True)
class ParsedCategory:
    """A category parsed from the text list."""

    name: str


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing a code list."""

    codes: list[ParsedCode]
    categories: list[ParsedCategory]


def parse_code_list(text: str) -> ParseResult:
    """
    Parse a plain-text code list.

    Non-indented lines that are followed by indented lines become categories.
    Non-indented lines without indented children become standalone codes.
    Indented lines become codes belonging to the preceding category.

    Args:
        text: The raw text content

    Returns:
        ParseResult with codes and categories
    """
    lines = text.split("\n")
    entries: list[tuple[str, bool]] = []  # (name, is_indented)

    for line in lines:
        # Skip empty and comment lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        is_indented = line[0] in (" ", "\t") if line else False
        entries.append((stripped, is_indented))

    if not entries:
        return ParseResult(codes=[], categories=[])

    # Two-pass: first identify which non-indented entries are categories
    # (i.e., have at least one indented entry following them)
    category_indices: set[int] = set()
    for i, (_, is_indented) in enumerate(entries):
        if not is_indented and i + 1 < len(entries) and entries[i + 1][1]:
            category_indices.add(i)

    # Build result
    codes: list[ParsedCode] = []
    categories: list[ParsedCategory] = []
    current_category: str | None = None

    for i, (name, is_indented) in enumerate(entries):
        if i in category_indices:
            current_category = name
            categories.append(ParsedCategory(name=name))
        elif is_indented and current_category:
            codes.append(ParsedCode(name=name, category_name=current_category))
        else:
            current_category = None
            codes.append(ParsedCode(name=name, category_name=None))

    return ParseResult(codes=codes, categories=categories)
