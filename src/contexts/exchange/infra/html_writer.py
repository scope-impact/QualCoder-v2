"""
Exchange Infra: HTML Writer

Generates an HTML document with coded text highlighted using
inline background colors and code name tooltips.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Code, TextSegment


def write_coded_html(
    sources_data: list[dict],
    output_path: Path | str,
) -> None:
    """
    Write coded text as an HTML document.

    Args:
        sources_data: List of dicts with keys:
            - name: source file name
            - fulltext: full text content
            - source_id: SourceId
            - segments: list of TextSegment
            - codes: dict mapping code_id value -> Code
        output_path: Path to write the HTML file
    """
    output_path = Path(output_path)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Coded Text Export</title>",
        "<style>",
        "body { font-family: sans-serif; margin: 2em; line-height: 1.6; }",
        "h2 { border-bottom: 2px solid #333; padding-bottom: 0.3em; }",
        ".source { margin-bottom: 2em; }",
        ".text { white-space: pre-wrap; font-family: monospace; background: #f9f9f9; "
        "padding: 1em; border-radius: 4px; }",
        ".coded { padding: 2px 4px; border-radius: 3px; cursor: help; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Coded Text Export</h1>",
    ]

    for source in sources_data:
        parts.append('<div class="source">')
        parts.append(f"<h2>{escape(source['name'])}</h2>")
        parts.append('<div class="text">')
        parts.append(
            _render_text_with_highlights(
                source["fulltext"],
                source["segments"],
                source["codes"],
            )
        )
        parts.append("</div>")
        parts.append("</div>")

    parts.append("</body>")
    parts.append("</html>")

    output_path.write_text("\n".join(parts), encoding="utf-8")


def _render_text_with_highlights(
    fulltext: str,
    segments: list[TextSegment],
    codes: dict[str, Code],
) -> str:
    """Render text with coded segments highlighted via spans."""
    if not segments:
        return escape(fulltext)

    # Sort segments by start position
    sorted_segs = sorted(segments, key=lambda s: s.position.start)

    result = []
    cursor = 0

    for seg in sorted_segs:
        start = seg.position.start
        end = seg.position.end

        # Clamp to text bounds
        start = max(0, min(start, len(fulltext)))
        end = max(start, min(end, len(fulltext)))

        # Text before this segment
        if cursor < start:
            result.append(escape(fulltext[cursor:start]))

        # The coded segment
        code = codes.get(seg.code_id.value)
        if code:
            color_hex = code.color.to_hex()
            code_name = escape(code.name)
            result.append(
                f'<span class="coded" style="background-color: {color_hex};" '
                f'title="{code_name}">'
            )
            result.append(escape(fulltext[start:end]))
            result.append("</span>")
        else:
            result.append(escape(fulltext[start:end]))

        cursor = end

    # Remaining text
    if cursor < len(fulltext):
        result.append(escape(fulltext[cursor:]))

    return "".join(result)
