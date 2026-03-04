"""
Exchange Infra: REFI-QDA Writer

Generates REFI-QDA 1.0 compatible .qdpx archives (ZIP with project.qde XML).

REFI-QDA spec: https://www.qdasoftware.org/
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code, TextSegment
    from src.contexts.sources.core.entities import Source

REFI_NS = "urn:QDA-XML:project:1.0"


def write_refi_qda(
    codes: list[Code],
    categories: list[Category],
    sources: list[Source],
    segments: list[TextSegment],
    output_path: Path | str,
    project_name: str = "QualCoder Project",
) -> None:
    """
    Write a REFI-QDA .qdpx archive.

    Args:
        codes: All codes in the project
        categories: All categories
        sources: All text sources
        segments: All text segments (codings)
        output_path: Path for the .qdpx file
        project_name: Name of the project
    """
    output_path = Path(output_path)

    # Build XML
    root = ET.Element("Project")
    root.set("xmlns", REFI_NS)
    root.set("name", project_name)
    root.set("origin", "QualCoder v2")

    # Build code GUID mapping
    code_guids: dict[str, str] = {}
    source_guids: dict[str, str] = {}

    # CodeBook
    codebook = ET.SubElement(root, "CodeBook")
    codes_el = ET.SubElement(codebook, "Codes")

    # Map categories to their codes
    cat_map: dict[str, Category] = {cat.id.value: cat for cat in categories}
    codes_by_cat: dict[str | None, list[Code]] = {}
    for code in codes:
        key = code.category_id.value if code.category_id else None
        codes_by_cat.setdefault(key, []).append(code)

    # Write categorized codes (categories become non-codable Code elements)
    for cat_id_value, cat in cat_map.items():
        cat_guid = str(uuid4())
        cat_el = ET.SubElement(codes_el, "Code")
        cat_el.set("guid", cat_guid)
        cat_el.set("name", cat.name)
        cat_el.set("isCodable", "false")
        if cat.memo:
            desc = ET.SubElement(cat_el, "Description")
            desc.text = cat.memo

        for code in codes_by_cat.pop(cat_id_value, []):
            _add_code_element(cat_el, code, code_guids)

    # Write uncategorized codes
    for code in codes_by_cat.pop(None, []):
        _add_code_element(codes_el, code, code_guids)

    # Any remaining (orphaned category refs)
    for _, remaining in codes_by_cat.items():
        for code in remaining:
            _add_code_element(codes_el, code, code_guids)

    # Sources
    sources_el = ET.SubElement(root, "Sources")
    for source in sources:
        src_guid = str(uuid4())
        source_guids[source.id.value] = src_guid

        src_el = ET.SubElement(sources_el, "TextSource")
        src_el.set("guid", src_guid)
        src_el.set("name", source.name)

        if source.fulltext:
            # Reference the text file in the ZIP
            plain = ET.SubElement(src_el, "PlainTextContent")
            plain.text = source.fulltext

            # Add source file path reference
            src_el.set("plainTextPath", f"Sources/{source.name}")

    # Codings (segments)
    if segments:
        for seg in segments:
            code_guid = code_guids.get(seg.code_id.value)
            source_guid = source_guids.get(seg.source_id.value)
            if not code_guid or not source_guid:
                continue

            coding_el = ET.SubElement(root, "Coding")
            coding_el.set("guid", str(uuid4()))

            code_ref = ET.SubElement(coding_el, "CodeRef")
            code_ref.set("targetGUID", code_guid)

            # Text range
            range_el = ET.SubElement(coding_el, "TextRange")
            range_el.set("start", str(seg.position.start))
            range_el.set("end", str(seg.position.end))
            range_el.set("sourceGUID", source_guid)

    # Write ZIP
    xml_bytes = ET.tostring(root, encoding="unicode", xml_declaration=True)
    if not xml_bytes.startswith("<?xml"):
        xml_bytes = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_bytes

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.qde", xml_bytes)

        # Include source text files
        for source in sources:
            if source.fulltext:
                zf.writestr(f"Sources/{source.name}", source.fulltext)


def _add_code_element(
    parent: ET.Element,
    code: Code,
    code_guids: dict[str, str],
) -> ET.Element:
    """Add a Code element to the XML tree."""
    guid = str(uuid4())
    code_guids[code.id.value] = guid

    el = ET.SubElement(parent, "Code")
    el.set("guid", guid)
    el.set("name", code.name)
    el.set("isCodable", "true")
    el.set("color", code.color.to_hex())

    if code.memo:
        desc = ET.SubElement(el, "Description")
        desc.text = code.memo

    return el
