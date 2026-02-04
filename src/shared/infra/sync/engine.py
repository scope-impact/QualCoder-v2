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

# Import ConvexClient at module level to avoid import deadlock in threads
# (PyO3-based modules can deadlock if imported from a thread while main holds import lock)
try:
    from convex import ConvexClient as _ConvexClient
except ImportError:
    _ConvexClient = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


def _subscription_worker(
    convex_client_class: type,
    url: str,
    query: str,
    entity_type: str,
    listeners: dict[str, list[Callable]],
    state: "SyncState",
) -> None:
    """
    Standalone subscription worker function.

    This is a module-level function (not a method) to avoid PyO3 GIL deadlocks
    that can occur when passing bound methods to threads. Each worker creates
    its own ConvexClient instance to avoid "already borrowed" threading errors.

    Args:
        convex_client_class: The ConvexClient class to instantiate
        url: Convex deployment URL
        query: Query to subscribe to (e.g., "codes:getAll")
        entity_type: Entity type for logging and callbacks
        listeners: Dict of entity_type -> list of callback functions
        state: SyncState object to update on errors
    """
    try:
        # Create a dedicated client for this thread
        thread_client = convex_client_class(url)

        # Subscribe and handle updates
        for data in thread_client.subscribe(query, {}):
            # Notify registered listeners
            for callback in listeners.get(entity_type, []):
                try:
                    callback("sync", {"items": data})
                except Exception:
                    pass  # Silently ignore callback errors

    except Exception as e:
        state.status = SyncStatus.ERROR
        state.error_message = str(e)


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
        enable_subscriptions: bool = False,
    ) -> None:
        """
        Initialize the sync engine.

        Args:
            sqlite_connection: SQLAlchemy connection to local SQLite
            convex_client: Optional Convex client for cloud sync
            enable_subscriptions: Whether to enable real-time Convex subscriptions.
                Disabled by default due to PyO3 threading issues. When disabled,
                inbound sync requires manual refresh or polling.
        """
        self._sqlite = sqlite_connection
        self._convex = convex_client
        # Store URL for creating per-thread clients (avoids PyO3 "already borrowed" error)
        self._convex_url: str | None = convex_client._url if convex_client else None
        self._enable_subscriptions = enable_subscriptions
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

        # Setup Convex subscriptions if available and enabled
        if self._convex and self._enable_subscriptions:
            self._state.status = SyncStatus.CONNECTING
            self._start_subscriptions()
        elif self._convex:
            # Convex available but subscriptions disabled - mark as synced
            self._state.status = SyncStatus.SYNCED

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
            self._convex_url = client._url if client else None

            if was_online and not client:
                # Going offline
                self._state.status = SyncStatus.OFFLINE
                logger.info("SyncEngine: went offline")

            elif client and not was_online:
                # Coming online
                self._state.status = SyncStatus.CONNECTING
                if self._enable_subscriptions:
                    self._start_subscriptions()
                else:
                    self._state.status = SyncStatus.SYNCED
                logger.info("SyncEngine: came online")

    def pull(self) -> dict[str, int]:
        """
        Pull remote changes from Convex (like 'git pull').

        Fetches all data from Convex and notifies registered listeners
        so they can update local SQLite. This is a manual alternative to
        real-time subscriptions.

        Returns:
            Dict mapping entity type to number of items pulled.
            Example: {"code": 5, "source": 10, "case": 2}

        Raises:
            RuntimeError: If not connected to Convex.
        """
        if not self._convex:
            raise RuntimeError("Not connected to Convex")

        self._state.status = SyncStatus.SYNCING
        results: dict[str, int] = {}

        try:
            # Pull each entity type
            pull_queries = [
                ("code", self._convex.get_all_codes),
                ("category", self._convex.get_all_categories),
                ("segment", self._convex.get_all_segments),
                ("source", self._convex.get_all_sources),
                ("folder", self._convex.get_all_folders),
                ("case", self._convex.get_all_cases),
            ]

            for entity_type, query_func in pull_queries:
                try:
                    items = query_func()
                    results[entity_type] = len(items)

                    # Notify listeners with the pulled data
                    self._notify_listeners(entity_type, items)

                    logger.debug(f"Pulled {len(items)} {entity_type}(s) from Convex")
                except Exception as e:
                    logger.warning(f"Failed to pull {entity_type}: {e}")
                    results[entity_type] = 0

            self._state.status = SyncStatus.SYNCED
            self._state.last_sync = datetime.now(UTC)
            logger.info(f"Pull complete: {results}")
            return results

        except Exception as e:
            self._state.status = SyncStatus.ERROR
            self._state.error_message = str(e)
            logger.error(f"Pull failed: {e}")
            raise

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
        if not self._convex_url:
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

        # Capture values to avoid closure over self (prevents PyO3 GIL deadlock)
        client_class = _ConvexClient
        if client_class is None:
            logger.error("ConvexClient not available for subscriptions")
            return

        url = self._convex_url
        listeners = self._change_listeners  # Dict reference, not method
        state = self._state  # State object reference

        for name, query, entity_type in subscriptions:
            thread = threading.Thread(
                target=_subscription_worker,
                args=(client_class, url, query, entity_type, listeners, state),
                daemon=True,
                name=f"SyncEngine-Sub-{name}",
            )
            thread.start()
            self._subscription_threads.append(thread)

        self._state.status = SyncStatus.SYNCED
        logger.info(f"Started {len(subscriptions)} Convex subscriptions")

    def _set_subscription_error(self, message: str) -> None:
        """Set subscription error state (thread-safe helper)."""
        self._state.status = SyncStatus.ERROR
        self._state.error_message = message

    def _subscription_loop(self, query: str, entity_type: str) -> None:
        """
        Subscribe to a Convex query and handle updates.

        Uses Convex's subscribe() which yields new data on every change.

        Note: Each subscription thread creates its own ConvexClient instance
        to avoid PyO3 "already borrowed" threading errors. The Convex Python
        client uses Rust bindings (PyO3) which don't support concurrent access
        from multiple threads on the same client instance.
        """
        if not self._convex_url:
            return

        try:
            # Create a dedicated client for this thread to avoid PyO3 threading issues
            if _ConvexClient is None:
                logger.error("ConvexClient not available")
                return

            thread_client = _ConvexClient(self._convex_url)
            logger.debug(f"Created dedicated Convex client for {entity_type} subscription")

            # The subscribe() method yields new data whenever it changes
            for data in thread_client.subscribe(query, {}):
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
