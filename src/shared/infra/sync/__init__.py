"""
Sync Infrastructure for SQLite-Convex Bidirectional Synchronization.

Provides real-time sync between local SQLite and cloud Convex.

Components:
- SyncEngine: Core sync orchestration (I/O layer)
- OutboxWriter: Transactional outbox for atomic domain + sync writes
- Command Handlers: handle_sync_pull, handle_sync_status
"""

from src.shared.infra.sync.commandHandlers import (
    handle_sync_pull,
    handle_sync_status,
)
from src.shared.infra.sync.engine import (
    ChangeType,
    SyncChange,
    SyncEngine,
    SyncState,
    SyncStatus,
)
from src.shared.infra.sync.outbox import OutboxWriter

__all__ = [
    # Engine
    "ChangeType",
    "SyncChange",
    "SyncEngine",
    "SyncState",
    "SyncStatus",
    # Outbox
    "OutboxWriter",
    # Command Handlers
    "handle_sync_pull",
    "handle_sync_status",
]
