"""
Sync Engine for SQLite-Convex Bidirectional Synchronization.

This module provides real-time sync between local SQLite and cloud Convex:
- SQLite is the primary local store (offline-first)
- Changes sync to Convex in background
- Convex subscriptions push remote changes to local SQLite
- Handles offline/online transitions gracefully

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                         SyncEngine                          │
    │                                                             │
    │   ┌─────────────┐                       ┌─────────────┐    │
    │   │   SQLite    │◄─── Read/Write ──────►│  Repository │    │
    │   │  (Primary)  │                       │   Layer     │    │
    │   └──────┬──────┘                       └─────────────┘    │
    │          │                                                  │
    │          │ Queue changes                                    │
    │          ▼                                                  │
    │   ┌─────────────┐      sync        ┌─────────────┐         │
    │   │  Outbound   │ ───────────────► │   Convex    │         │
    │   │   Queue     │                  │   Cloud     │         │
    │   └─────────────┘                  └──────┬──────┘         │
    │                                           │                 │
    │   ┌─────────────┐    subscribe           │                 │
    │   │  Inbound    │ ◄──────────────────────┘                 │
    │   │ Listeners   │                                          │
    │   └─────────────┘                                          │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.shared.infra.convex import ConvexClientWrapper

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Sync status for the engine."""

    OFFLINE = "offline"
    CONNECTING = "connecting"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


class ChangeType(str, Enum):
    """Type of data change."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class SyncChange:
    """Represents a change to be synced."""

    entity_type: str  # "code", "category", "segment", "source", "folder", "case"
    change_type: ChangeType
    entity_id: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0


@dataclass
class SyncState:
    """Current state of the sync engine."""

    status: SyncStatus = SyncStatus.OFFLINE
    last_sync: datetime | None = None
    pending_changes: int = 0
    error_message: str | None = None


class SyncEngine:
    """
    Bidirectional sync engine for SQLite and Convex.

    This engine keeps SQLite and Convex in sync:
    - SQLite is the local cache (works offline)
    - Convex is the source of truth (cloud)
    - Local writes go to SQLite first, then sync to Convex
    - Convex subscriptions push changes to SQLite in real-time

    Usage:
        engine = SyncEngine(sqlite_conn, convex_client)
        engine.start()

        # Register handlers for remote changes
        engine.on_remote_change("code", handle_code_update)

        # Queue local changes for sync
        engine.queue_change(SyncChange(...))
    """

    MAX_RETRY = 3
    BATCH_SIZE = 50

    def __init__(
        self,
        sqlite_connection: Connection,
        convex_client: ConvexClientWrapper | None = None,
    ) -> None:
        """
        Initialize the sync engine.

        Args:
            sqlite_connection: SQLAlchemy connection to local SQLite
            convex_client: Optional Convex client for cloud sync
        """
        self._sqlite = sqlite_connection
        self._convex = convex_client
        self._state = SyncState()

        # Change queue for outbound sync (local -> Convex)
        self._outbound_queue: queue.Queue[SyncChange] = queue.Queue()

        # Listeners for inbound remote changes (Convex -> local)
        self._change_listeners: dict[str, list[Callable[[str, dict], None]]] = {}

        # Threading
        self._outbound_thread: threading.Thread | None = None
        self._subscription_threads: list[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()

        # Ensure sync queue table exists for persistence
        self._ensure_sync_table()

    def _ensure_sync_table(self) -> None:
        """Create the sync_queue table if it doesn't exist."""
        try:
            from sqlalchemy import text

            self._sqlite.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT NOT NULL,
                        change_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0
                    )
                """)
            )
            self._sqlite.commit()
        except Exception as e:
            logger.warning(f"Failed to create sync_queue table: {e}")

    def _load_pending_changes(self) -> None:
        """Load pending changes from SQLite into the queue."""
        try:
            import json

            from sqlalchemy import text

            result = self._sqlite.execute(
                text("SELECT id, entity_type, change_type, entity_id, data, timestamp, retry_count FROM sync_queue ORDER BY id")
            )
            for row in result.fetchall():
                change = SyncChange(
                    entity_type=row[1],
                    change_type=ChangeType(row[2]),
                    entity_id=row[3],
                    data=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    retry_count=row[6],
                )
                self._outbound_queue.put(change)

            count = self._outbound_queue.qsize()
            if count > 0:
                logger.info(f"Loaded {count} pending sync changes from database")
                self._state.pending_changes = count
        except Exception as e:
            logger.warning(f"Failed to load pending sync changes: {e}")

    def _persist_change(self, change: SyncChange) -> None:
        """Persist a change to SQLite for durability."""
        try:
            import json

            from sqlalchemy import text

            self._sqlite.execute(
                text("""
                    INSERT INTO sync_queue (entity_type, change_type, entity_id, data, timestamp, retry_count)
                    VALUES (:entity_type, :change_type, :entity_id, :data, :timestamp, :retry_count)
                """),
                {
                    "entity_type": change.entity_type,
                    "change_type": change.change_type.value,
                    "entity_id": change.entity_id,
                    "data": json.dumps(change.data),
                    "timestamp": change.timestamp.isoformat(),
                    "retry_count": change.retry_count,
                },
            )
            self._sqlite.commit()
        except Exception as e:
            logger.warning(f"Failed to persist sync change: {e}")

    def _remove_persisted_change(self, change: SyncChange) -> None:
        """Remove a successfully synced change from SQLite."""
        try:
            from sqlalchemy import text

            self._sqlite.execute(
                text("DELETE FROM sync_queue WHERE entity_type = :entity_type AND entity_id = :entity_id"),
                {"entity_type": change.entity_type, "entity_id": change.entity_id},
            )
            self._sqlite.commit()
        except Exception as e:
            logger.warning(f"Failed to remove synced change from database: {e}")

    @property
    def state(self) -> SyncState:
        """Get current sync state."""
        return self._state

    @property
    def is_online(self) -> bool:
        """Check if connected to Convex."""
        return self._convex is not None

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def start(self) -> None:
        """Start the sync engine."""
        if self._running:
            return

        self._running = True
        self._state.status = SyncStatus.OFFLINE

        # Load any pending changes from previous session
        self._load_pending_changes()

        # Start outbound sync thread
        self._outbound_thread = threading.Thread(
            target=self._outbound_sync_loop,
            daemon=True,
            name="SyncEngine-Outbound",
        )
        self._outbound_thread.start()

        # Setup Convex subscriptions if available
        if self._convex:
            self._state.status = SyncStatus.CONNECTING
            self._start_subscriptions()

        logger.info("SyncEngine started")

    def stop(self) -> None:
        """Stop the sync engine."""
        self._running = False

        # Wait for threads to finish
        if self._outbound_thread and self._outbound_thread.is_alive():
            self._outbound_thread.join(timeout=2.0)

        for thread in self._subscription_threads:
            if thread.is_alive():
                thread.join(timeout=2.0)

        self._subscription_threads.clear()
        self._state.status = SyncStatus.OFFLINE
        logger.info("SyncEngine stopped")

    def set_convex_client(self, client: ConvexClientWrapper | None) -> None:
        """Update the Convex client (for online/offline transitions)."""
        with self._lock:
            was_online = self._convex is not None
            self._convex = client

            if was_online and not client:
                # Going offline
                self._state.status = SyncStatus.OFFLINE
                logger.info("SyncEngine: went offline")

            elif client and not was_online:
                # Coming online
                self._state.status = SyncStatus.CONNECTING
                self._start_subscriptions()
                logger.info("SyncEngine: came online")

    # =========================================================================
    # Change Management (Local -> Convex)
    # =========================================================================

    def queue_change(self, change: SyncChange) -> None:
        """
        Queue a local change for sync to Convex.

        The change should already be applied to SQLite.
        This queues it for background sync to Convex.
        Changes are persisted to SQLite so they survive app restart.
        """
        self._outbound_queue.put(change)
        self._persist_change(change)  # Persist for durability
        self._state.pending_changes = self._outbound_queue.qsize()
        logger.debug(f"Queued change: {change.entity_type}/{change.change_type}")

    def on_remote_change(
        self,
        entity_type: str,
        callback: Callable[[str, dict], None],
    ) -> None:
        """
        Register a callback for remote changes from Convex.

        When Convex subscription receives new data, the callback
        is invoked so the repository can update SQLite.

        Args:
            entity_type: Entity type to listen for (code, source, etc.)
            callback: Function(change_type, data) to handle the change
        """
        if entity_type not in self._change_listeners:
            self._change_listeners[entity_type] = []
        self._change_listeners[entity_type].append(callback)

    # =========================================================================
    # Outbound Sync (Local -> Convex)
    # =========================================================================

    def _outbound_sync_loop(self) -> None:
        """Background thread for syncing local changes to Convex."""
        while self._running:
            try:
                # Get change with timeout
                try:
                    change = self._outbound_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Skip if offline - re-queue for later
                if not self.is_online:
                    self._outbound_queue.put(change)
                    continue

                # Sync to Convex
                success = self._sync_to_convex(change)

                if success:
                    # Remove from persistent queue after successful sync
                    self._remove_persisted_change(change)
                else:
                    change.retry_count += 1
                    if change.retry_count < self.MAX_RETRY:
                        self._outbound_queue.put(change)
                    else:
                        # Max retries exceeded, remove from persistent queue
                        self._remove_persisted_change(change)
                        logger.error(
                            f"Sync failed after {self.MAX_RETRY} retries: "
                            f"{change.entity_type}/{change.entity_id}"
                        )

                self._state.pending_changes = self._outbound_queue.qsize()
                if self._state.pending_changes == 0:
                    self._state.status = SyncStatus.SYNCED
                    self._state.last_sync = datetime.now(UTC)

            except Exception as e:
                logger.exception(f"Error in outbound sync: {e}")
                self._state.status = SyncStatus.ERROR
                self._state.error_message = str(e)

    def _sync_to_convex(self, change: SyncChange) -> bool:
        """Sync a single change to Convex."""
        if not self._convex:
            return False

        try:
            self._state.status = SyncStatus.SYNCING

            # Map to Convex mutation
            mutation_map = {
                ("code", ChangeType.CREATE): "codes:create",
                ("code", ChangeType.UPDATE): "codes:update",
                ("code", ChangeType.DELETE): "codes:remove",
                ("category", ChangeType.CREATE): "categories:create",
                ("category", ChangeType.UPDATE): "categories:update",
                ("category", ChangeType.DELETE): "categories:remove",
                ("segment", ChangeType.CREATE): "segments:create",
                ("segment", ChangeType.UPDATE): "segments:update",
                ("segment", ChangeType.DELETE): "segments:remove",
                ("source", ChangeType.CREATE): "sources:create",
                ("source", ChangeType.UPDATE): "sources:update",
                ("source", ChangeType.DELETE): "sources:remove",
                ("folder", ChangeType.CREATE): "folders:create",
                ("folder", ChangeType.UPDATE): "folders:update",
                ("folder", ChangeType.DELETE): "folders:remove",
                ("case", ChangeType.CREATE): "cases:create",
                ("case", ChangeType.UPDATE): "cases:update",
                ("case", ChangeType.DELETE): "cases:remove",
            }

            mutation = mutation_map.get((change.entity_type, change.change_type))
            if not mutation:
                logger.warning(f"Unknown change: {change.entity_type}/{change.change_type}")
                return True

            if change.change_type == ChangeType.DELETE:
                self._convex.mutation(mutation, id=change.entity_id)
            else:
                self._convex.mutation(mutation, **change.data)

            logger.debug(f"Synced to Convex: {change.entity_type}/{change.entity_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to sync to Convex: {e}")
            return False

    # =========================================================================
    # Inbound Subscriptions (Convex -> Local)
    # =========================================================================

    def _start_subscriptions(self) -> None:
        """Start Convex subscription threads for real-time updates."""
        if not self._convex:
            return

        # Subscribe to each entity type
        subscriptions = [
            ("codes", "codes:getAll", "code"),
            ("categories", "categories:getAll", "category"),
            ("segments", "segments:getAll", "segment"),
            ("sources", "sources:getAll", "source"),
            ("folders", "folders:getAll", "folder"),
            ("cases", "cases:getAll", "case"),
        ]

        for name, query, entity_type in subscriptions:
            thread = threading.Thread(
                target=self._subscription_loop,
                args=(query, entity_type),
                daemon=True,
                name=f"SyncEngine-Sub-{name}",
            )
            thread.start()
            self._subscription_threads.append(thread)

        self._state.status = SyncStatus.SYNCED
        logger.info(f"Started {len(subscriptions)} Convex subscriptions")

    def _subscription_loop(self, query: str, entity_type: str) -> None:
        """
        Subscribe to a Convex query and handle updates.

        Uses Convex's subscribe() which yields new data on every change.
        """
        if not self._convex:
            return

        try:
            # The subscribe() method yields new data whenever it changes
            for data in self._convex.client.subscribe(query, {}):
                if not self._running:
                    break

                # Notify listeners of the update
                self._notify_listeners(entity_type, data)

        except Exception as e:
            if self._running:
                logger.error(f"Subscription error for {entity_type}: {e}")
                self._state.status = SyncStatus.ERROR
                self._state.error_message = str(e)

    def _notify_listeners(self, entity_type: str, data: list[dict]) -> None:
        """Notify registered listeners of remote data."""
        listeners = self._change_listeners.get(entity_type, [])
        for callback in listeners:
            try:
                # Pass full data set - listener handles diffing
                callback("sync", {"items": data})
            except Exception as e:
                logger.exception(f"Error in change listener for {entity_type}: {e}")
