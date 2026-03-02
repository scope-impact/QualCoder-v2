# Sync Engine Refactor Plan

**Decision:** ADR-002 — Transactional Outbox + Cursor Pull + LWW
**Prerequisite:** ADR-001 (UUIDv7 PKs) — entity IDs must be UUIDv7 strings before this plan begins
**Status:** Planning
**Date:** 2026-02-25

---

## Overview

Replace the current `SyncEngine` (ad-hoc queue, full-table pulls, broken deletion detection) with a
**Transactional Outbox** for push and **Cursor-based incremental pull** for inbound sync.

**What is deleted:**
- `SyncedCodeRepository`, `SyncedCategoryRepository`, etc. — all `synced_repositories.py`
- `SyncEngine._outbound_sync_loop()` — replaced by outbox drain loop
- `SyncEngine.pull()` — replaced by cursor pull
- `SyncEngine.queue_change()` — removed; outbox is written by command handlers directly
- `SyncEngine.on_remote_change()` / `_change_listeners` — replaced by pull loop applying changes
- `_pending_outbound` sets in `SyncedRepository` classes — replaced by `sync_outbox` query

**What is retained/adapted:**
- `SyncEngine` class (slimmed down to: push loop + pull loop + online/offline state)
- `SyncState`, `SyncStatus` enums
- `src/shared/core/sync/` domain (pure entities, derivers, invariants) — kept as-is

---

## Phase 1 — Outbox and Meta Tables

**Effort:** Low | **Risk:** Low

Add two new SQLite tables to the shared sync infrastructure.

### `sync_outbox` (replaces `sync_queue`)

```sql
CREATE TABLE IF NOT EXISTS sync_outbox (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,  -- row PK for safe deletion
    entity           TEXT    NOT NULL,                   -- 'code', 'segment', 'source', etc.
    entity_id        TEXT    NOT NULL,                   -- UUIDv7 of the entity
    op               TEXT    NOT NULL,                   -- 'upsert' | 'delete'
    payload          TEXT    NOT NULL,                   -- JSON of full entity data (or {} for delete)
    idempotency_key  TEXT    NOT NULL UNIQUE,            -- stable key: '{entity}:{op}:{entity_id}'
    attempts         INTEGER NOT NULL DEFAULT 0,
    last_error       TEXT,
    created_at       TEXT    NOT NULL                    -- HLC timestamp ISO string
);
CREATE INDEX IF NOT EXISTS idx_outbox_pending
    ON sync_outbox (entity, attempts) WHERE attempts < 5;
```

Note: `id` is an `INTEGER PRIMARY KEY` (the internal row ID). The `entity_id` is a UUIDv7 string. Deletion uses `WHERE id = :row_id`, not `WHERE entity_id = :entity_id`.

### `sync_meta` (replaces nothing — new)

```sql
CREATE TABLE IF NOT EXISTS sync_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Pre-populated rows:
-- key='last_pull_cursor', value='0'
-- key='hlc_state',        value='{"ms": 0, "seq": 0}'
```

**File:** `src/shared/infra/sync/engine.py` — update `_ensure_sync_table()` to create both tables.

**Acceptance criteria:**
- [ ] Both tables created on `SyncEngine.__init__`
- [ ] `sync_queue` table creation removed (keep reading it during a transition period for backward compat, then drop)
- [ ] `make test-all` passes

---

## Phase 2 — Hybrid Logical Clock

**Effort:** Low | **Risk:** Low

The HLC ensures monotonically increasing timestamps across devices even with clock skew. It is used as the `created_at` for outbox entries and as the LWW comparison value during pull.

**File:** `src/shared/common/hlc.py`

```python
"""
Hybrid Logical Clock (HLC) — monotonically increasing timestamps.

HLC = max(physical_ms, logical_counter)
Ensures causal ordering even when device clocks drift or run backwards.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection


@dataclass
class HLCState:
    ms: int = 0    # last known physical ms
    seq: int = 0   # logical counter for same-ms events

    def to_str(self) -> str:
        """Produce a sortable ISO-like string: '{ms:016d}-{seq:08d}'."""
        return f"{self.ms:016d}-{self.seq:08d}"

    def to_json(self) -> str:
        return json.dumps({"ms": self.ms, "seq": self.seq})

    @classmethod
    def from_json(cls, s: str) -> HLCState:
        d = json.loads(s)
        return cls(ms=d["ms"], seq=d["seq"])


class HybridLogicalClock:
    """Thread-safe HLC backed by sync_meta table."""

    def __init__(self, conn: Connection, lock: threading.Lock) -> None:
        self._conn = conn
        self._lock = lock
        self._state = self._load()

    def _load(self) -> HLCState:
        from sqlalchemy import text
        with self._lock:
            row = self._conn.execute(
                text("SELECT value FROM sync_meta WHERE key = 'hlc_state'")
            ).fetchone()
        return HLCState.from_json(row[0]) if row else HLCState()

    def now(self) -> str:
        """Advance clock and return sortable HLC timestamp string."""
        from sqlalchemy import text
        physical_ms = int(time.time() * 1000)
        with self._lock:
            if physical_ms > self._state.ms:
                self._state = HLCState(ms=physical_ms, seq=0)
            else:
                self._state = HLCState(ms=self._state.ms, seq=self._state.seq + 1)
            ts = self._state.to_str()
            self._conn.execute(
                text("INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('hlc_state', :v)"),
                {"v": self._state.to_json()},
            )
            self._conn.commit()
        return ts

    def update(self, remote_ts: str) -> None:
        """Advance clock on receiving a remote timestamp (ensures causality)."""
        if not remote_ts:
            return
        parts = remote_ts.split("-")
        if len(parts) < 2:
            return
        remote_ms = int(parts[0])
        with self._lock:
            if remote_ms > self._state.ms:
                self._state = HLCState(ms=remote_ms, seq=0)
```

**Acceptance criteria:**
- [ ] `HybridLogicalClock.now()` returns a string sortable as a timestamp
- [ ] Two calls in the same millisecond return `...00000000-00000000` then `...00000000-00000001`
- [ ] `update(remote_ts)` advances `ms` when remote is ahead of local
- [ ] Unit test: `hlc.now() < hlc.now()` is always true (monotonic)

---

## Phase 3 — OutboxWriter Helper

**Effort:** Low | **Risk:** Low

A thin helper that command handlers use to write outbox entries. Keeps sync concerns out of domain code while making the dependency explicit and injectable.

**File:** `src/shared/infra/sync/outbox.py`

```python
"""
OutboxWriter — writes sync outbox entries atomically with domain writes.

Injected into command handlers that mutate entities. The command handler
is responsible for calling write_upsert() or write_delete() inside the
same SQLAlchemy transaction as the domain table write.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Connection
    from src.shared.infra.sync.engine import HybridLogicalClock

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


class OutboxWriter:
    """Writes entries to sync_outbox inside the caller's transaction."""

    def __init__(self, conn: Connection, hlc: HybridLogicalClock) -> None:
        self._conn = conn
        self._hlc = hlc

    def write_upsert(self, entity: str, entity_id: str, data: dict[str, Any]) -> None:
        """Queue an upsert. Call inside the same transaction as the domain write."""
        from sqlalchemy import text
        key = f"{entity}:upsert:{entity_id}"
        self._conn.execute(
            text("""
                INSERT INTO sync_outbox (entity, entity_id, op, payload, idempotency_key, created_at)
                VALUES (:entity, :entity_id, 'upsert', :payload, :key, :ts)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    payload = excluded.payload,
                    attempts = 0,
                    last_error = NULL,
                    created_at = excluded.created_at
            """),
            {
                "entity": entity,
                "entity_id": entity_id,
                "payload": json.dumps(data),
                "key": key,
                "ts": self._hlc.now(),
            },
        )

    def write_delete(self, entity: str, entity_id: str) -> None:
        """Queue a delete. Call inside the same transaction as the domain delete."""
        from sqlalchemy import text
        key = f"{entity}:delete:{entity_id}"
        self._conn.execute(
            text("""
                INSERT OR IGNORE INTO sync_outbox
                    (entity, entity_id, op, payload, idempotency_key, created_at)
                VALUES (:entity, :entity_id, 'delete', '{}', :key, :ts)
            """),
            {
                "entity": entity,
                "entity_id": entity_id,
                "key": key,
                "ts": self._hlc.now(),
            },
        )

    def get_pending_ids(self, entity: str) -> frozenset[str]:
        """Return entity IDs with pending outbound changes (thread-safe via WAL)."""
        from sqlalchemy import text
        rows = self._conn.execute(
            text("""
                SELECT DISTINCT entity_id FROM sync_outbox
                WHERE entity = :e AND attempts < :max
            """),
            {"e": entity, "max": MAX_ATTEMPTS},
        ).fetchall()
        return frozenset(row[0] for row in rows)
```

**Acceptance criteria:**
- [ ] `OutboxWriter` created and unit-tested
- [ ] `write_upsert` / `write_delete` work inside an open transaction
- [ ] `get_pending_ids` reads from `sync_outbox` (not in-memory set)
- [ ] Duplicate upserts for same entity update the row, not insert a second row

---

## Phase 4 — Wire OutboxWriter into Command Handlers

**Effort:** Medium | **Risk:** Medium

Each command handler that creates, updates, or deletes domain data must write an outbox entry **in the same transaction**.

**Pattern:**

```python
# src/contexts/coding/core/commandHandlers/create_code.py

def create_code(
    command: CreateCodeCommand,
    code_repo: SQLiteCodeRepository,
    event_bus: EventBus,
    outbox: OutboxWriter | None = None,   # None when sync is disabled
) -> OperationResult:
    # ... invariant checks ...

    code = Code(id=CodeId.new(), name=command.name, ...)

    # Single transaction: domain write + outbox entry
    with code_repo.conn.begin():
        code_repo.save(code)
        if outbox:
            outbox.write_upsert("code", code.id.value, {
                "name": code.name,
                "color": code.color.to_hex(),
                "memo": code.memo,
                "catid": code.category_id.value if code.category_id else None,
                "owner": code.owner,
            })

    event_bus.publish(CodeCreated(...))
    return OperationResult(success=True, data={"id": code.id.value})
```

`outbox=None` when cloud sync is disabled — the handler works identically without sync.

**Command handlers to update:**
- `coding`: `create_code`, `update_code`, `delete_code`, `create_category`, `update_category`, `delete_category`, `apply_code_to_segment`, `remove_code_from_segment`
- `sources`: `add_source`, `update_source`, `delete_source`
- `folders`: `create_folder`, `rename_folder`, `delete_folder`, `move_source_to_folder`
- `cases`: `create_case`, `update_case`, `delete_case`, `save_attribute`, `link_source`, `remove_source_link`

**Wiring in `AppContext`:**

```python
# When project opens with sync enabled:
outbox_writer = OutboxWriter(conn=sync_engine._sync_connection, hlc=sync_engine.hlc)
self.coding.code_repo = SQLiteCodeRepository(conn)  # plain repo, no wrapper
# OutboxWriter injected into command handlers via partial or factory
```

**Acceptance criteria:**
- [ ] All listed command handlers accept `outbox: OutboxWriter | None`
- [ ] `SyncedRepository` classes are no longer instantiated anywhere
- [ ] Creating a code with sync enabled: `sync_outbox` gains a row in the same transaction
- [ ] Creating a code with sync disabled: `sync_outbox` gains no row
- [ ] `make test-all` passes (E2E tests use `outbox=None`)

---

## Phase 5 — Push Loop (Outbox Drain)

**Effort:** Medium | **Risk:** Medium

Replace `SyncEngine._outbound_sync_loop()` with an outbox drain loop.

```python
def _outbound_sync_loop(self) -> None:
    """Drain sync_outbox — send pending rows to Convex."""
    while self._running:
        if not self.is_online:
            time.sleep(1.0)
            continue

        try:
            rows = self._fetch_pending_batch()
            if not rows:
                time.sleep(1.0)
                continue

            for row in rows:
                row_id, entity, entity_id, op, payload_json = (
                    row.id, row.entity, row.entity_id, row.op, row.payload
                )
                result = self._push_row(entity, entity_id, op, payload_json)

                if result == "success":
                    self._delete_outbox_row(row_id)   # by row PK
                elif result == "error":
                    self._increment_attempts(row_id)

        except Exception:
            logger.exception("Error in push loop")
            time.sleep(5.0)

def _fetch_pending_batch(self) -> list:
    from sqlalchemy import text
    with self._sync_db_lock:
        return self._sync_connection.execute(
            text("""
                SELECT id, entity, entity_id, op, payload
                FROM sync_outbox
                WHERE attempts < :max
                ORDER BY id
                LIMIT :batch
            """),
            {"max": MAX_ATTEMPTS, "batch": self.BATCH_SIZE},
        ).fetchall()

def _delete_outbox_row(self, row_id: int) -> None:
    """Delete by row PK — never by entity_id."""
    from sqlalchemy import text
    with self._sync_db_lock:
        self._sync_connection.execute(
            text("DELETE FROM sync_outbox WHERE id = :id"),
            {"id": row_id},
        )
        self._sync_connection.commit()
```

**Mutation dispatch:**

```python
MUTATION_MAP = {
    ("code",     "upsert"): "codes:upsert",
    ("code",     "delete"): "codes:remove",
    ("category", "upsert"): "categories:upsert",
    ("category", "delete"): "categories:remove",
    ("segment",  "upsert"): "segments:upsert",
    ("segment",  "delete"): "segments:remove",
    ("source",   "upsert"): "sources:upsert",
    ("source",   "delete"): "sources:remove",
    ("folder",   "upsert"): "folders:upsert",
    ("folder",   "delete"): "folders:remove",
    ("case",     "upsert"): "cases:upsert",
    ("case",     "delete"): "cases:remove",
    ("attribute","upsert"): "cases:saveAttribute",
    ("attribute","delete"): "cases:removeAttribute",
    ("source_link","upsert"): "cases:linkSource",
    ("source_link","delete"): "cases:removeSourceLink",
}
```

Note: Convex mutations now use `upsert` (create-or-update by `localId`) instead of separate `create`/`update`. This is enabled by the `localId` field from ADR-001.

**Acceptance criteria:**
- [ ] Push loop reads from `sync_outbox`, not from an in-memory queue
- [ ] Successful push deletes by `id` (row PK)
- [ ] Failed push increments `attempts` and sets `last_error`
- [ ] Row with `attempts >= MAX_ATTEMPTS` is never retried (left in table for debugging)
- [ ] No `_translate_fk_ids`, `deferred` result, or `consecutive_deferrals` logic
- [ ] `make test-all` passes

---

## Phase 6 — Convex Cursor API

**Effort:** Medium | **Risk:** Medium

Add a `getChangesSince(cursor)` query to all Convex tables. The cursor is a Convex `_creationTime`-based token or a sequential version number.

### Schema changes (`convex/schema.ts`)

Each table needs a `updatedAt` field for cursor-based queries:

```typescript
codes: defineTable({
  localId: v.string(),    // UUIDv7 from client (ADR-001)
  name: v.string(),
  color: v.string(),
  memo: v.optional(v.string()),
  catid: v.optional(v.string()),
  owner: v.optional(v.string()),
  updatedAt: v.number(),  // server timestamp (Date.now()) — set by server on every write
  _deleted: v.optional(v.boolean()),  // tombstone for deletes
})
.index("by_local_id", ["localId"])
.index("by_updated_at", ["updatedAt"])
```

### Shared sync query (`convex/sync.ts`)

```typescript
export const getChangesSince = query({
  args: {
    cursor: v.number(),     // last updatedAt seen by client (0 = first pull)
    entities: v.array(v.string()),  // which entity types to include
  },
  handler: async (ctx, { cursor, entities }) => {
    const results: Record<string, any[]> = {};

    if (entities.includes("code")) {
      results.code = await ctx.db.query("codes")
        .withIndex("by_updated_at", q => q.gt("updatedAt", cursor))
        .collect();
    }
    // ... repeat for each entity type

    const nextCursor = Math.max(
      ...Object.values(results).flat().map(r => r.updatedAt ?? 0),
      cursor,
    );

    return { items: results, nextCursor };
  },
});
```

### Upsert mutations (`convex/codes.ts`)

```typescript
// Replace separate create + update with a single upsert by localId
export const upsert = mutation({
  args: {
    localId: v.string(),
    name: v.string(),
    color: v.string(),
    memo: v.optional(v.string()),
    catid: v.optional(v.string()),
    owner: v.optional(v.string()),
    idempotencyKey: v.string(),
  },
  handler: async (ctx, { localId, idempotencyKey, ...fields }) => {
    const existing = await ctx.db.query("codes")
      .withIndex("by_local_id", q => q.eq("localId", localId))
      .unique();

    const data = { localId, ...fields, updatedAt: Date.now(), _deleted: false };

    if (existing) {
      await ctx.db.patch(existing._id, data);
      return existing._id;
    } else {
      return await ctx.db.insert("codes", data);
    }
  },
});

export const remove = mutation({
  args: { localId: v.string() },
  handler: async (ctx, { localId }) => {
    const doc = await ctx.db.query("codes")
      .withIndex("by_local_id", q => q.eq("localId", localId))
      .unique();
    if (doc) {
      // Tombstone, not hard delete (preserves cursor history)
      await ctx.db.patch(doc._id, { _deleted: true, updatedAt: Date.now() });
    }
  },
});
```

**Acceptance criteria:**
- [ ] `getChangesSince(0)` returns all entities
- [ ] `getChangesSince(cursor)` returns only entities changed since cursor
- [ ] `_deleted: true` tombstones are returned (not filtered out)
- [ ] `upsert` is idempotent — calling twice with same `localId` updates, not duplicates
- [ ] `convex dev` starts without errors

---

## Phase 7 — Pull Loop (Cursor-based)

**Effort:** Medium | **Risk:** Medium

Replace `SyncEngine.pull()` (full table scan) with cursor-based incremental pull.

```python
def pull(self) -> dict[str, int]:
    """
    Pull changes from Convex since last cursor.

    Returns dict of entity_type -> count applied.
    """
    if not self._convex:
        raise RuntimeError("Not connected to Convex")

    self._state.status = SyncStatus.SYNCING

    # Load cursor
    cursor = self._load_pull_cursor()

    try:
        result = self._convex.query("sync:getChangesSince", {
            "cursor": cursor,
            "entities": ["code", "category", "segment", "source", "folder",
                         "case", "attribute", "source_link"],
        })
    except Exception as e:
        self._state.status = SyncStatus.ERROR
        self._state.error_message = str(e)
        raise

    counts: dict[str, int] = {}
    pending_ids: dict[str, frozenset[str]] = {
        entity: self._outbox_writer.get_pending_ids(entity)
        for entity in result["items"]
    }

    for entity_type, items in result["items"].items():
        applied = self._apply_entity_changes(entity_type, items, pending_ids[entity_type])
        counts[entity_type] = applied

    # Advance cursor
    self._save_pull_cursor(result["nextCursor"])
    self._state.status = SyncStatus.SYNCED
    self._state.last_sync = datetime.now(UTC)

    return counts

def _apply_entity_changes(
    self,
    entity_type: str,
    items: list[dict],
    pending_ids: frozenset[str],
) -> int:
    """Apply remote changes using conflict resolution policy."""
    applied = 0
    for item in items:
        local_id = item.get("localId")
        if not local_id:
            continue

        # Skip if we have a pending outbound change for this entity
        if local_id in pending_ids:
            continue

        if item.get("_deleted"):
            self._apply_remote_delete(entity_type, local_id)
        else:
            self._apply_remote_upsert(entity_type, local_id, item)
            applied += 1

    return applied
```

**Conflict resolution dispatch in `_apply_remote_upsert`:**

```python
ADDITIVE_ENTITIES = {"segment"}   # Never silently overwrite researcher annotations

def _apply_remote_upsert(self, entity_type: str, local_id: str, item: dict) -> None:
    if entity_type in ADDITIVE_ENTITIES:
        # Additive: only insert if not already present locally
        self._notify_listeners(entity_type, [item], strategy="additive")
    else:
        # LWW: remote wins if no pending local change
        self._notify_listeners(entity_type, [item], strategy="lww")
```

**Acceptance criteria:**
- [ ] Pull fetches only changes since last cursor (not full tables)
- [ ] Tombstoned items (`_deleted: true`) trigger local deletion
- [ ] Items with pending outbound changes are skipped
- [ ] Segments use additive policy (existing local segment not deleted by remote upsert)
- [ ] Cursor advances after each successful pull
- [ ] `make test-all` passes

---

## Phase 8 — Delete SyncedRepositories

**Effort:** High | **Risk:** High

Once Phases 4-7 are validated end-to-end, remove all `SyncedRepository` wrappers.

**Files to delete:**
- `src/shared/infra/sync/synced_repositories.py`
- `src/shared/infra/sync/sync_helpers.py` (used only by synced repos)

**Files to update:**
- `src/shared/infra/sync/__init__.py` — remove all `SyncedXxxRepository` exports
- `src/shared/infra/app_context/bounded_contexts.py` — replace `SyncedCodeRepository(...)` with plain `SQLiteCodeRepository(...)`
- `src/shared/infra/app_context/context.py` — remove wiring of SyncedRepos

**Acceptance criteria:**
- [ ] No import of any `Synced*Repository` anywhere in `src/`
- [ ] `SyncEngine.on_remote_change()` / `_change_listeners` removed (pull loop applies changes directly)
- [ ] `SyncEngine.queue_change()` removed
- [ ] `make test-all` passes

---

## Phase 9 — Conflict Resolution Completeness

**Effort:** High | **Risk:** Medium

Implement per-field LWW for metadata entities using the HLC timestamp.

Each entity stored locally gains an `updated_at TEXT` column (HLC string). During pull:

```python
def _apply_lww(local_row: dict | None, remote_item: dict) -> dict:
    """Last-write-wins: remote wins if its HLC timestamp is newer."""
    if local_row is None:
        return remote_item  # new entity

    local_ts = local_row.get("updated_at", "0")
    remote_ts = remote_item.get("updatedAt", "0")

    return remote_item if remote_ts > local_ts else local_row
```

**Schema changes:** Add `updated_at TEXT DEFAULT '0'` to all entity tables.
**Repository changes:** Set `updated_at = hlc.now()` on every `save()`.
**HLC update on pull:** Call `hlc.update(remote_ts)` for each remote item received.

**Acceptance criteria:**
- [ ] All entity tables have `updated_at TEXT`
- [ ] Repositories set `updated_at` on every write
- [ ] Pull handler calls `hlc.update(remote_ts)` for each remote item
- [ ] LWW test: create code locally, modify on server with older timestamp → local version kept
- [ ] LWW test: create code locally, modify on server with newer timestamp → server version applied

---

## Files Changed Summary

| File | Action |
|------|--------|
| `src/shared/infra/sync/engine.py` | Major rewrite — outbox drain loop + cursor pull |
| `src/shared/infra/sync/synced_repositories.py` | **Deleted** |
| `src/shared/infra/sync/sync_helpers.py` | **Deleted** |
| `src/shared/infra/sync/id_map.py` | **Deleted** (see ADR-001) |
| `src/shared/infra/sync/outbox.py` | **New** — OutboxWriter |
| `src/shared/common/hlc.py` | **New** — HybridLogicalClock |
| `src/shared/common/uuid7.py` | **New** (see ADR-001) |
| `src/contexts/*/core/commandHandlers/*.py` | Updated — inject OutboxWriter, atomic writes |
| `convex/schema.ts` | Updated — add `localId`, `updatedAt`, `_deleted` |
| `convex/sync.ts` | **New** — `getChangesSince` query |
| `convex/codes.ts` (and all entity files) | Updated — upsert + tombstone mutations |

---

## References

- ADR: `docs/decisions/ADR-002-sync-engine-pattern.md`
- Prerequisite ADR: `docs/decisions/ADR-001-uuidv7-primary-keys.md`
- Prerequisite plan: `docs/ai/UUIDV7_MIGRATION_PLAN.md`
