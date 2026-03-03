"""
Exchange Context: Invariants (Pure Validation)

Pure predicate functions for validating import/export operations.
No I/O, no side effects.
"""
from __future__ import annotations

from pathlib import Path


def can_export_codebook(code_count: int) -> bool:
    """Codebook export requires at least one code."""
    return code_count > 0


def is_valid_output_path(path: str) -> bool:
    """Output path must be non-empty with an existing parent directory."""
    if not path:
        return False
    parent = Path(path).parent
    return parent.exists()
