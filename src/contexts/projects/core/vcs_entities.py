"""
Version Control Entities - Immutable State Containers

Frozen dataclasses representing version control state.
Used as input to derivers for pure event derivation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionControlState:
    """
    State container for version control derivers.

    Immutable snapshot of VCS state used by derivers to make decisions.
    All fields are primitives or immutable collections.

    Usage:
        state = VersionControlState(
            is_initialized=git_adapter.is_initialized(),
            has_uncommitted_changes=git_adapter.has_staged_changes(),
            valid_refs=git_adapter.get_valid_refs(),
        )
        result = derive_auto_commit(events, state)
    """

    is_initialized: bool = False
    has_uncommitted_changes: bool = False
    valid_refs: tuple[str, ...] = ()
    current_ref: str = "HEAD"


# ============================================================
# Exports
# ============================================================

__all__ = [
    "VersionControlState",
]
