"""
Exchange Infra: REFI-QDA Reader

Parses REFI-QDA .qdpx archives (ZIP with project.qde XML)
into structured data for import.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


REFI_NS = "urn:QDA-XML:project:1.0"


@dataclass(frozen=True)
class ParsedCode:
    """A code parsed from REFI-QDA XML."""
    guid: str
    name: str
    color: str = "#808080"
    category_guid: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class ParsedCategory:
    """A category (non-codable Code) from REFI-QDA XML."""
    guid: str
    name: str
    memo: str | None = None


@dataclass(frozen=True)
class ParsedSource:
    """A text source from REFI-QDA XML."""
    guid: str
    name: str
    fulltext: str = ""


@dataclass(frozen=True)
class ParsedCoding:
    """A coding (segment) from REFI-QDA XML."""
    code_guid: str
    source_guid: str
    start: int
    end: int


@dataclass
class RefiQdaParseResult:
    """Result of parsing a REFI-QDA archive."""
    project_name: str = ""
    codes: list[ParsedCode] = field(default_factory=list)
    categories: list[ParsedCategory] = field(default_factory=list)
    sources: list[ParsedSource] = field(default_factory=list)
    codings: list[ParsedCoding] = field(default_factory=list)


def read_refi_qda(qdpx_path: Path | str) -> RefiQdaParseResult:
    """
    Parse a REFI-QDA .qdpx archive.

    Args:
        qdpx_path: Path to the .qdpx ZIP file

    Returns:
        RefiQdaParseResult with parsed project data
    """
    qdpx_path = Path(qdpx_path)
    result = RefiQdaParseResult()

    with zipfile.ZipFile(qdpx_path) as zf:
        xml_content = zf.read("project.qde")
        source_files = {n: zf.read(n).decode("utf-8", errors="replace")
                        for n in zf.namelist() if n.startswith("Sources/")}

    root = ET.fromstring(xml_content)

    # Strip namespace for easier element access
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    result.project_name = root.get("name", "")

    # Parse codes
    codebook = root.find(f"{ns}CodeBook")
    if codebook is not None:
        codes_el = codebook.find(f"{ns}Codes")
        if codes_el is not None:
            _parse_codes(codes_el, ns, result, parent_guid=None)

    # Parse sources
    sources_el = root.find(f"{ns}Sources")
    if sources_el is not None:
        for src_el in sources_el:
            tag = src_el.tag.replace(ns, "")
            if "Source" in tag:
                guid = src_el.get("guid", "")
                name = src_el.get("name", "")

                # Get text content
                fulltext = ""
                plain_el = src_el.find(f"{ns}PlainTextContent")
                if plain_el is not None and plain_el.text:
                    fulltext = plain_el.text

                # Fall back to source file in ZIP
                if not fulltext:
                    plain_path = src_el.get("plainTextPath", "")
                    if plain_path and plain_path in source_files:
                        fulltext = source_files[plain_path]

                result.sources.append(ParsedSource(
                    guid=guid, name=name, fulltext=fulltext,
                ))

    # Parse codings
    for coding_el in root.findall(f"{ns}Coding"):
        code_ref = coding_el.find(f"{ns}CodeRef")
        text_range = coding_el.find(f"{ns}TextRange")

        if code_ref is not None and text_range is not None:
            result.codings.append(ParsedCoding(
                code_guid=code_ref.get("targetGUID", ""),
                source_guid=text_range.get("sourceGUID", ""),
                start=int(text_range.get("start", "0")),
                end=int(text_range.get("end", "0")),
            ))

    return result


def _parse_codes(
    parent_el: ET.Element,
    ns: str,
    result: RefiQdaParseResult,
    parent_guid: str | None,
) -> None:
    """Recursively parse Code elements (categories and codes)."""
    for code_el in parent_el.findall(f"{ns}Code"):
        guid = code_el.get("guid", "")
        name = code_el.get("name", "")
        is_codable = code_el.get("isCodable", "true").lower() == "true"
        color = code_el.get("color", "#808080")

        memo = None
        desc_el = code_el.find(f"{ns}Description")
        if desc_el is not None and desc_el.text:
            memo = desc_el.text

        if is_codable:
            result.codes.append(ParsedCode(
                guid=guid, name=name, color=color,
                category_guid=parent_guid, memo=memo,
            ))
        else:
            # Non-codable = category
            result.categories.append(ParsedCategory(
                guid=guid, name=name, memo=memo,
            ))
            # Recurse into nested codes
            _parse_codes(code_el, ns, result, parent_guid=guid)
