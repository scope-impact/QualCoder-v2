"""
Sync Context: Domain Layer & Cross-Context Handlers.

Provides:
1. Pure domain logic for SQLite-Convex synchronization
2. Cross-context sync handlers for denormalized data
"""

from src.shared.core.sync.source_sync_handler import SourceSyncHandler

# Domain Entities
from src.shared.core.sync.entities import (
    PullResult,
    PullSummary,
    RemoteItem,
    SyncDomainState,
)

# Domain Events
from src.shared.core.sync.events import (
    RemoteChangesReceived,
    SyncPullCompleted,
    SyncPullFailed,
    SyncPullStarted,
)

# Domain Invariants
from src.shared.core.sync.invariants import (
    can_apply_remote_item,
    has_sync_conflicts,
    is_deletion_candidate,
    is_valid_remote_item,
)

# Domain Derivers
from src.shared.core.sync.derivers import (
    SyncDecision,
    derive_entity_pull_result,
    derive_pull_completed,
    derive_sync_changes,
)

# Commands
from src.shared.core.sync.commands import (
    SyncPullCommand,
    SyncStatusCommand,
)

__all__ = [
    # Cross-context handler
    "SourceSyncHandler",
    # Entities
    "RemoteItem",
    "SyncDomainState",
    "PullResult",
    "PullSummary",
    # Events
    "SyncPullStarted",
    "SyncPullCompleted",
    "SyncPullFailed",
    "RemoteChangesReceived",
    # Invariants
    "can_apply_remote_item",
    "is_deletion_candidate",
    "is_valid_remote_item",
    "has_sync_conflicts",
    # Derivers
    "SyncDecision",
    "derive_sync_changes",
    "derive_pull_completed",
    "derive_entity_pull_result",
    # Commands
    "SyncPullCommand",
    "SyncStatusCommand",
]
