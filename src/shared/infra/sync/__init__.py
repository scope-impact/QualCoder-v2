"""
Sync Infrastructure for SQLite-Convex Bidirectional Synchronization.

Provides real-time sync between local SQLite and cloud Convex.

Components:
- SyncEngine: Core sync orchestration (I/O layer)
- SyncedRepositories: Decorators that add sync to SQLite repos
- Command Handlers: handle_sync_pull, handle_sync_status
"""

from src.shared.infra.sync.engine import (
    ChangeType,
    SyncChange,
    SyncEngine,
    SyncState,
    SyncStatus,
)
from src.shared.infra.sync.synced_repositories import (
    SyncedCaseRepository,
    SyncedCategoryRepository,
    SyncedCodeRepository,
    SyncedFolderRepository,
    SyncedSegmentRepository,
    SyncedSourceRepository,
)
from src.shared.infra.sync.commandHandlers import (
    handle_sync_pull,
    handle_sync_status,
)

__all__ = [
    # Engine
    "ChangeType",
    "SyncChange",
    "SyncEngine",
    "SyncState",
    "SyncStatus",
    # Synced Repositories
    "SyncedCaseRepository",
    "SyncedCategoryRepository",
    "SyncedCodeRepository",
    "SyncedFolderRepository",
    "SyncedSegmentRepository",
    "SyncedSourceRepository",
    # Command Handlers
    "handle_sync_pull",
    "handle_sync_status",
]
