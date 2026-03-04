"""
Exchange Infra: RQDA Reader

Reads RQDA SQLite databases (.rqda files) used by the R-based RQDA package.
RQDA uses status=1 for active records and status=0 for deleted.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from src.contexts.exchange.core.commands import DEFAULT_IMPORT_COLOR


@dataclass(frozen=True)
class RqdaCode:
    """A code from RQDA database."""

    id: int
    name: str
    color: str = DEFAULT_IMPORT_COLOR
    memo: str | None = None


@dataclass(frozen=True)
class RqdaSource:
    """A source from RQDA database."""

    id: int
    name: str
    fulltext: str = ""
    memo: str | None = None


@dataclass(frozen=True)
class RqdaCoding:
    """A coding (segment) from RQDA database."""

    code_id: int
    source_id: int
    selected_text: str
    start: int
    end: int


@dataclass
class RqdaParseResult:
    """Result of reading an RQDA database."""

    codes: list[RqdaCode] = field(default_factory=list)
    sources: list[RqdaSource] = field(default_factory=list)
    codings: list[RqdaCoding] = field(default_factory=list)


def read_rqda(db_path: Path | str) -> RqdaParseResult:
    """
    Read an RQDA SQLite database.

    Args:
        db_path: Path to the .rqda file

    Returns:
        RqdaParseResult with codes, sources, and codings
    """
    db_path = Path(db_path)
    result = RqdaParseResult()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Read codes (freecode table, status=1 means active)
        for row in conn.execute(
            "SELECT id, name, color, memo FROM freecode WHERE status=1"
        ):
            result.codes.append(
                RqdaCode(
                    id=row["id"],
                    name=row["name"],
                    color=row["color"] or DEFAULT_IMPORT_COLOR,
                    memo=row["memo"],
                )
            )

        # Read sources (source table)
        for row in conn.execute(
            "SELECT id, name, file, memo FROM source WHERE status=1"
        ):
            result.sources.append(
                RqdaSource(
                    id=row["id"],
                    name=row["name"],
                    fulltext=row["file"] or "",
                    memo=row["memo"],
                )
            )

        # Read codings
        for row in conn.execute(
            "SELECT cid, fid, seltext, selfirst, selend FROM coding WHERE status=1"
        ):
            result.codings.append(
                RqdaCoding(
                    code_id=row["cid"],
                    source_id=row["fid"],
                    selected_text=row["seltext"] or "",
                    start=row["selfirst"],
                    end=row["selend"],
                )
            )
    finally:
        conn.close()

    return result
