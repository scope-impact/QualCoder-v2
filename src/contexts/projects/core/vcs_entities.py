"""Version Control Entities - Immutable state containers for derivers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionControlState:
    """Immutable VCS state used by derivers to make decisions."""

    is_initialized: bool = False
    has_uncommitted_changes: bool = False
    valid_refs: tuple[str, ...] = ()
    current_ref: str = "HEAD"


__all__ = ["VersionControlState"]
