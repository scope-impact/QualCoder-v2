"""
Exchange Infra: Codebook Writer

Generates a plain-text codebook document from codes and categories.
Codes are grouped under their categories with color references.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code


def write_codebook(
    codes: list[Code],
    categories: list[Category],
    output_path: Path | str,
    include_memos: bool = True,
) -> None:
    """
    Write a codebook document as plain text.

    Codes are grouped under category headings. Uncategorized codes
    appear in a separate section at the end.

    Args:
        codes: All codes in the project
        categories: All categories in the project
        output_path: Path to write the output file
        include_memos: Whether to include memo text
    """
    output_path = Path(output_path)
    cat_map: dict[str, Category] = {cat.id.value: cat for cat in categories}

    # Group codes by category
    grouped: dict[str | None, list[Code]] = {}
    for code in codes:
        key = code.category_id.value if code.category_id else None
        grouped.setdefault(key, []).append(code)

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("CODEBOOK")
    lines.append("=" * 60)
    lines.append("")

    # Write categorized codes first
    for cat_id_value, cat in cat_map.items():
        cat_codes = grouped.pop(cat_id_value, [])
        _write_category_section(lines, cat, cat_codes, include_memos)

    # Write uncategorized codes
    uncategorized = grouped.pop(None, [])
    if uncategorized:
        lines.append("-" * 40)
        lines.append("Uncategorized")
        lines.append("-" * 40)
        lines.append("")
        for code in uncategorized:
            _write_code(lines, code, include_memos, indent="")

    # Write any codes with deleted/missing categories
    for _cat_id, remaining_codes in grouped.items():
        for code in remaining_codes:
            _write_code(lines, code, include_memos, indent="")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_category_section(
    lines: list[str],
    category: Category,
    codes: list[Code],
    include_memos: bool,
) -> None:
    """Write a category heading and its codes."""
    lines.append("-" * 40)
    lines.append(category.name)
    lines.append("-" * 40)
    if include_memos and category.memo:
        lines.append(f"  Memo: {category.memo}")
    lines.append("")

    for code in codes:
        _write_code(lines, code, include_memos, indent="  ")


def _write_code(
    lines: list[str],
    code: Code,
    include_memos: bool,
    indent: str,
) -> None:
    """Write a single code entry."""
    color_hex = code.color.to_hex()
    lines.append(f"{indent}{code.name}  [{color_hex}]")
    if include_memos and code.memo:
        lines.append(f"{indent}  Memo: {code.memo}")
    lines.append("")
