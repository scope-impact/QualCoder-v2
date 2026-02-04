"""
Sync Context: Domain Layer & Cross-Context Handlers.

This module provides:
1. Pure domain logic for SQLite-Convex synchronization (entities, events, derivers)
2. Cross-context sync handlers for denormalized data

Domain components (PURE - no I/O):
- entities: SyncDomainState, RemoteItem, SyncConflict, PullResult, PullSummary
- events: SyncPullStarted, SyncPullCompleted, SyncPullFailed, etc.
- invariants: is_conflicting_change(), can_apply_remote_item()
- derivers: derive_sync_changes(), derive_pull_completed()
- commands: SyncPullCommand, SyncPushCommand
"""

from src.shared.core.sync.source_sync_handler import SourceSyncHandler

# Domain Entities
from src.shared.core.sync.entities import (
    PullResult,
    PullSummary,
    RemoteItem,
    SyncConflict,
    SyncDomainState,
)

# Domain Events
from src.shared.core.sync.events import (
    RemoteChangesReceived,
    SyncChangePushed,
    SyncChangeQueued,
    SyncConflictDetected,
    SyncPullCompleted,
    SyncPullFailed,
    SyncPullStarted,
    SyncPushFailed,
    SyncStatusChanged,
)

# Domain Invariants
from src.shared.core.sync.invariants import (
    can_apply_remote_item,
    can_sync_entity_type,
    has_sync_conflicts,
    is_conflicting_change,
    is_deletion_candidate,
    is_empty_pull_result,
    is_valid_remote_item,
)

# Domain Derivers
from src.shared.core.sync.derivers import (
    SyncDecision,
    derive_entity_pull_result,
    derive_pull_completed,
    derive_pull_result_event,
    derive_should_notify_ui,
    derive_sync_changes,
)

# Commands
from src.shared.core.sync.commands import (
    SyncConnectCommand,
    SyncDisconnectCommand,
    SyncPullCommand,
    SyncPushCommand,
    SyncStatusCommand,
)

__all__ = [
    # Cross-context handler
    "SourceSyncHandler",
    # Entities
    "RemoteItem",
    "SyncConflict",
    "SyncDomainState",
    "PullResult",
    "PullSummary",
    # Events
    "SyncPullStarted",
    "SyncPullCompleted",
    "SyncPullFailed",
    "SyncChangeQueued",
    "SyncChangePushed",
    "SyncPushFailed",
    "RemoteChangesReceived",
    "SyncConflictDetected",
    "SyncStatusChanged",
    # Invariants
    "is_conflicting_change",
    "can_apply_remote_item",
    "is_deletion_candidate",
    "is_valid_remote_item",
    "can_sync_entity_type",
    "is_empty_pull_result",
    "has_sync_conflicts",
    # Derivers
    "SyncDecision",
    "derive_sync_changes",
    "derive_pull_completed",
    "derive_pull_result_event",
    "derive_entity_pull_result",
    "derive_should_notify_ui",
    # Commands
    "SyncPullCommand",
    "SyncPushCommand",
    "SyncStatusCommand",
    "SyncConnectCommand",
    "SyncDisconnectCommand",
]
