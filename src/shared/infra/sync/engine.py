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

import contextlib
import json
import logging
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.shared.infra.convex import ConvexClientWrapper
    from src.shared.infra.sync.id_map import SyncIdMap

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
    state: SyncState,
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
    thread_name = f"SyncEngine-Sub-{entity_type}"
    logger.info("[%s] Subscription worker started (query=%s)", thread_name, query)
    try:
        # Create a dedicated client for this thread
        thread_client = convex_client_class(url)
        logger.debug("[%s] Convex client created, subscribing...", thread_name)

        # Subscribe and handle updates
        for data in thread_client.subscribe(query, {}):
            item_count = len(data) if isinstance(data, list) else 1
            listener_count = len(listeners.get(entity_type, []))
            logger.debug(
                "[%s] Received %d item(s), notifying %d listener(s)",
                thread_name,
                item_count,
                listener_count,
            )
            # Notify registered listeners
            for callback in listeners.get(entity_type, []):
                try:
                    callback("sync", {"items": data})
                except Exception as cb_err:
                    logger.error(
                        "[%s] Listener callback failed: %s",
                        thread_name,
                        cb_err,
                        exc_info=True,
                    )

    except Exception as e:
        logger.error(
            "[%s] Subscription worker crashed: %s", thread_name, e, exc_info=True
        )
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

        # Dedicated connection for sync infrastructure (sync_queue, sync_id_map tables).
        # Separate from self._sqlite to avoid cross-thread commit conflicts between
        # the Qt main thread (repo operations) and the sync daemon thread.
        self._sync_db_lock = threading.Lock()
        try:
            self._sync_connection = sqlite_connection.engine.connect()
            # Wait up to 5 s instead of immediately failing with "database is locked"
            # when the main connection holds a write transaction during pull.
            self._sync_connection.execute(text("PRAGMA busy_timeout = 5000"))
            self._sync_connection.commit()
        except Exception:
            # Fallback: share the main connection (less safe but functional)
            self._sync_connection = sqlite_connection

        # Ensure sync queue table exists for persistence
        self._ensure_sync_table()

        # ID mapping between local SQLite integer PKs and Convex document IDs
        from src.shared.infra.sync.id_map import SyncIdMap

        self._id_map = SyncIdMap(self._sync_connection, self._sync_db_lock)

    def _ensure_sync_table(self) -> None:
        """Create sync infrastructure tables if they don't exist."""
        try:
            with self._sync_db_lock:
                self._sync_connection.execute(
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
                # Transactional outbox — written atomically with domain writes
                self._sync_connection.execute(
                    text("""
                        CREATE TABLE IF NOT EXISTS sync_outbox (
                            id TEXT PRIMARY KEY,
                            entity_type TEXT NOT NULL,
                            entity_id TEXT NOT NULL,
                            operation TEXT NOT NULL,
                            data TEXT,
                            created_at TEXT NOT NULL,
                            UNIQUE(entity_type, entity_id)
                        )
                    """)
                )
                self._sync_connection.commit()
        except Exception as e:
            logger.warning(f"Failed to create sync tables: {e}")

    def _load_pending_changes(self) -> None:
        """Load pending changes from SQLite into the queue."""
        try:
            with self._sync_db_lock:
                result = self._sync_connection.execute(
                    text(
                        "SELECT id, entity_type, change_type, entity_id, data, timestamp, retry_count FROM sync_queue ORDER BY id"
                    )
                )
                rows = result.fetchall()

            for row in rows:
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
            # Serialize data, converting Enum values for JSON compatibility
            serializable_data = {
                k: (v.value if isinstance(v, Enum) else v)
                for k, v in change.data.items()
            }

            with self._sync_db_lock:
                self._sync_connection.execute(
                    text("""
                        INSERT INTO sync_queue (entity_type, change_type, entity_id, data, timestamp, retry_count)
                        VALUES (:entity_type, :change_type, :entity_id, :data, :timestamp, :retry_count)
                    """),
                    {
                        "entity_type": change.entity_type,
                        "change_type": change.change_type.value,
                        "entity_id": change.entity_id,
                        "data": json.dumps(serializable_data),
                        "timestamp": change.timestamp.isoformat(),
                        "retry_count": change.retry_count,
                    },
                )
                self._sync_connection.commit()
        except Exception as e:
            logger.warning(f"Failed to persist sync change: {e}")

    def _remove_persisted_change(self, change: SyncChange) -> None:
        """Remove a successfully synced change from SQLite."""
        try:
            with self._sync_db_lock:
                self._sync_connection.execute(
                    text(
                        "DELETE FROM sync_queue WHERE entity_type = :entity_type AND entity_id = :entity_id"
                    ),
                    {"entity_type": change.entity_type, "entity_id": change.entity_id},
                )
                self._sync_connection.commit()
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

    @property
    def id_map(self) -> SyncIdMap:
        """Access the ID mapping between local SQLite PKs and Convex document IDs."""
        return self._id_map

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
            logger.debug("SyncEngine status -> CONNECTING (subscriptions enabled)")
            self._start_subscriptions()
        elif self._convex:
            # Convex available but subscriptions disabled - mark as synced
            self._state.status = SyncStatus.SYNCED
            logger.debug(
                "SyncEngine status -> SYNCED (subscriptions disabled, Convex available)"
            )

        logger.info("SyncEngine started")

    def stop(self) -> None:
        """Stop the sync engine."""
        logger.info(
            "SyncEngine stopping (threads: outbound=%s, subscriptions=%d)",
            self._outbound_thread is not None,
            len(self._subscription_threads),
        )
        self._running = False

        # Wait for threads to finish
        if self._outbound_thread and self._outbound_thread.is_alive():
            logger.debug("Joining outbound sync thread...")
            self._outbound_thread.join(timeout=2.0)
            if self._outbound_thread.is_alive():
                logger.warning("Outbound sync thread did not stop within 2s timeout")
            else:
                logger.debug("Outbound sync thread joined")

        for thread in self._subscription_threads:
            if thread.is_alive():
                logger.debug("Joining subscription thread: %s", thread.name)
                thread.join(timeout=2.0)
                if thread.is_alive():
                    logger.warning(
                        "Subscription thread %s did not stop within 2s timeout",
                        thread.name,
                    )

        self._subscription_threads.clear()
        self._state.status = SyncStatus.OFFLINE

        # Close dedicated sync connection if it's separate from main
        if self._sync_connection is not self._sqlite:
            with contextlib.suppress(Exception):
                self._sync_connection.close()

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
                ("attribute", self._convex.get_all_attributes),
                ("source_link", self._convex.get_all_source_links),
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

    def get_pending_ids(self, entity_type: str) -> frozenset[str]:
        """
        Get IDs of entities with pending outbound changes.

        Used by sync derivers to detect conflicts between local
        pending changes and incoming remote changes.

        Args:
            entity_type: Entity type to check (e.g., "code", "source")

        Returns:
            Frozenset of entity IDs with pending changes
        """
        pending_ids: set[str] = set()

        # Check items in the queue (creates a snapshot)
        queue_items = list(self._outbound_queue.queue)
        for change in queue_items:
            if change.entity_type == entity_type:
                pending_ids.add(change.entity_id)

        return frozenset(pending_ids)

    # =========================================================================
    # Outbound Sync (Local -> Convex)
    # =========================================================================

    def _outbound_sync_loop(self) -> None:
        """Background thread: drains sync_outbox and pushes each row to Convex."""
        logger.info("[SyncEngine-Outbound] Outbound sync loop started")
        try:
            while self._running:
                try:
                    self._drain_legacy_queue()
                    self._drain_sync_outbox()
                    time.sleep(5.0)
                except Exception as e:
                    logger.exception(f"Error in outbound sync loop: {e}")
        finally:
            logger.info("[SyncEngine-Outbound] Outbound sync loop exiting")

    def _drain_legacy_queue(self) -> None:
        """Drain the legacy in-memory queue (no longer populated after SyncedRepos removal)."""
        while True:
            try:
                change = self._outbound_queue.get_nowait()
            except queue.Empty:
                break
            logger.debug(
                f"Convex push disabled -- skipping: "
                f"{change.entity_type}/{change.entity_id}"
            )
            self._remove_persisted_change(change)

    def _drain_sync_outbox(self) -> None:
        """
        Drain pending rows from sync_outbox and push each one to Convex.

        - "upsert" rows: CREATE if no id_map entry exists, UPDATE otherwise.
        - "delete" rows: look up Convex ID from id_map and call remove mutation.
        - Rows that succeed are deleted from the outbox.
        - Rows that are deferred (FK dependency not yet mapped) or that error
          are left in the outbox and retried on the next cycle.
        - If no Convex client is available the method returns immediately so
          outbox rows accumulate until the engine comes online.
        """
        if not self._convex:
            return

        try:
            with self._sync_db_lock:
                result = self._sync_connection.execute(
                    text(
                        "SELECT id, entity_type, entity_id, operation, data"
                        " FROM sync_outbox LIMIT 50"
                    )
                )
                rows = result.fetchall()

            if not rows:
                return

            succeeded_ids: list[str] = []
            deferred_count = 0

            for outbox_id, entity_type, entity_id, operation, data_json in rows:
                if operation == "delete":
                    change = SyncChange(
                        entity_type=entity_type,
                        change_type=ChangeType.DELETE,
                        entity_id=entity_id,
                        data={},
                    )
                else:
                    # "upsert" — resolve to CREATE or UPDATE via id_map
                    data = json.loads(data_json) if data_json else {}
                    change_type = (
                        ChangeType.UPDATE
                        if self._id_map.has_mapping(entity_type, entity_id)
                        else ChangeType.CREATE
                    )
                    change = SyncChange(
                        entity_type=entity_type,
                        change_type=change_type,
                        entity_id=entity_id,
                        data=data,
                    )

                outcome = self._sync_to_convex(change)

                if outcome == "success":
                    succeeded_ids.append(outbox_id)
                    logger.debug(
                        f"Pushed to Convex: {entity_type}/{entity_id} op={operation}"
                    )
                elif outcome == "deferred":
                    deferred_count += 1
                    logger.debug(f"Deferred (FK not mapped): {entity_type}/{entity_id}")
                else:
                    logger.warning(
                        f"Failed to push to Convex: {entity_type}/{entity_id}"
                    )

            if succeeded_ids:
                with self._sync_db_lock:
                    for outbox_id in succeeded_ids:
                        self._sync_connection.execute(
                            text("DELETE FROM sync_outbox WHERE id = :id"),
                            {"id": outbox_id},
                        )
                    self._sync_connection.commit()
                logger.info(f"Drained {len(succeeded_ids)} outbox row(s) to Convex")

            if deferred_count:
                logger.debug(
                    f"{deferred_count} outbox row(s) deferred (FK dependency pending)"
                )

        except Exception as e:
            logger.warning(f"Failed to drain sync_outbox: {e}")

    def _translate_fk_ids(
        self, entity_type: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Translate local integer FK fields to Convex document IDs.

        Returns translated data dict, or None if a required FK isn't mapped yet
        (dependency not synced).
        """
        from src.shared.infra.sync.id_map import FK_DEPENDENCIES

        fk_fields = FK_DEPENDENCIES.get(entity_type, {})
        if not fk_fields:
            return data

        translated = dict(data)
        for field_name, referenced_type in fk_fields.items():
            local_fk = translated.get(field_name)
            if local_fk is None:
                continue

            convex_fk = self._id_map.get_convex_id(referenced_type, str(local_fk))
            if convex_fk is None:
                logger.debug(
                    f"FK not mapped yet: {entity_type}.{field_name}={local_fk} "
                    f"-> {referenced_type} (deferring)"
                )
                return None

            translated[field_name] = convex_fk

        return translated

    def _sync_to_convex(self, change: SyncChange) -> str:
        """
        Sync a single change to Convex.

        Returns: "success", "deferred" (FK not mapped yet), or "error"
        """
        if not self._convex:
            return "error"

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
                ("attribute", ChangeType.CREATE): "cases:saveAttribute",
                ("attribute", ChangeType.UPDATE): "cases:saveAttribute",
                ("attribute", ChangeType.DELETE): "cases:removeAttribute",
                ("source_link", ChangeType.CREATE): "cases:linkSource",
                ("source_link", ChangeType.DELETE): "cases:removeSourceLink",
            }

            mutation = mutation_map.get((change.entity_type, change.change_type))
            if not mutation:
                logger.warning(
                    f"Unknown change: {change.entity_type}/{change.change_type}"
                )
                return "success"

            if change.change_type == ChangeType.DELETE:
                # Look up the Convex document ID for this entity
                convex_id = self._id_map.get_convex_id(
                    change.entity_type, str(change.entity_id)
                )
                if convex_id is None:
                    logger.warning(
                        f"No Convex ID mapped for delete: "
                        f"{change.entity_type}/{change.entity_id}, skipping"
                    )
                    return "success"

                self._convex.mutation(mutation, id=convex_id)
                self._id_map.remove(change.entity_type, str(change.entity_id))

            elif change.change_type == ChangeType.CREATE:
                # Strip None values and convert Enums
                data = {
                    k: (v.value if isinstance(v, Enum) else v)
                    for k, v in change.data.items()
                    if v is not None
                }

                # Translate FK fields to Convex document IDs
                translated = self._translate_fk_ids(change.entity_type, data)
                if translated is None:
                    return "deferred"

                # Call mutation — returns the new Convex document _id
                convex_doc_id = self._convex.mutation(mutation, **translated)

                # Store the mapping: local integer PK → Convex document _id
                if convex_doc_id:
                    self._id_map.put(
                        change.entity_type,
                        str(change.entity_id),
                        str(convex_doc_id),
                    )

            else:
                # UPDATE
                data = {
                    k: (v.value if isinstance(v, Enum) else v)
                    for k, v in change.data.items()
                    if v is not None
                }

                # Look up entity's own Convex ID
                convex_id = self._id_map.get_convex_id(
                    change.entity_type, str(change.entity_id)
                )
                if convex_id is None:
                    logger.warning(
                        f"No Convex ID mapped for update: "
                        f"{change.entity_type}/{change.entity_id}, skipping"
                    )
                    return "success"

                # Translate FK fields
                translated = self._translate_fk_ids(change.entity_type, data)
                if translated is None:
                    return "deferred"

                translated["id"] = convex_id
                self._convex.mutation(mutation, **translated)

            logger.debug(f"Synced to Convex: {change.entity_type}/{change.entity_id}")
            return "success"

        except Exception as e:
            logger.warning(f"Failed to sync to Convex: {e}")
            return "error"

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
            thread_name = f"SyncEngine-Sub-{name}"
            logger.debug(
                "Starting subscription thread: %s (query=%s)", thread_name, query
            )
            thread = threading.Thread(
                target=_subscription_worker,
                args=(client_class, url, query, entity_type, listeners, state),
                daemon=True,
                name=thread_name,
            )
            thread.start()
            self._subscription_threads.append(thread)

        self._state.status = SyncStatus.SYNCED
        logger.info(f"Started {len(subscriptions)} Convex subscriptions")

    def _notify_listeners(self, entity_type: str, data: list[dict]) -> None:
        """Notify registered listeners of remote data."""
        listeners = self._change_listeners.get(entity_type, [])
        for callback in listeners:
            try:
                # Pass full data set - listener handles diffing
                callback("sync", {"items": data})
            except Exception as e:
                logger.exception(f"Error in change listener for {entity_type}: {e}")
