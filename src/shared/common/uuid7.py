"""UUID v7 utility — time-ordered, sortable unique identifiers."""

from __future__ import annotations

try:
    from uuid import uuid7  # Python 3.13+
except ImportError:
    from uuid_utils import uuid7  # type: ignore[no-redef]


def new_uuid7() -> str:
    """Generate a new UUID v7 string (time-ordered, 36-char hyphenated)."""
    return str(uuid7())
