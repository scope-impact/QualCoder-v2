# ADR-002: Transactional Outbox + Cursor Pull + LWW as Sync Engine Pattern

**Status:** Superseded — Convex sync infrastructure removed (QC-050). Storage now uses S3 + DVC.
**Date:** 2026-02-25
**Deciders:** Sathish Narayanan
**Scope:** `shared/infra/sync/` — outbound push, inbound pull, conflict resolution

---

## Context

QualCoder is an offline-first desktop app. Data is stored locally in SQLite and optionally synced to Convex cloud. Three sync patterns were evaluated:

| Pattern | Fit | Reason |
|---------|-----|--------|
| Transactional Outbox + Cursor Pull + LWW | ✅ Best | Single-researcher primary use, existing DDD architecture, no real-time collaboration required |
| Replicache-style optimistic mutations | ⚠️ Good | Better multi-user conflict resolution but requires server-side mutators and significantly more server work |
| CRDTs (Automerge + Convex) | ❌ Overkill | Designed for collaborative text editing; high storage overhead; poor fit for relational data with business invariants |

### Problems with the current `SyncEngine` implementation

The current implementation has multiple correctness issues that the chosen pattern directly resolves:

**1. Outbox write and domain write are not atomic**

```python
# Current — two separate operations, not one transaction
self._repo.save(code)        # writes domain table
self._sync.queue_change(...) # inserts sync_queue row separately
```

If the app crashes between these two lines, the sync queue entry is lost and the change never syncs to Convex. The outbox pattern requires both writes to be in a single SQLite transaction.

**2. Deletion detection is a broken stub**

`_get_local_ids()` in `pull_handler.py` returns an empty `frozenset()`, meaning `is_deletion_candidate()` is never triggered. Remote deletes are silently ignored.

**3. `_remove_persisted_change` deletes wrong rows**

```python
DELETE FROM sync_queue WHERE entity_type = :entity_type AND entity_id = :entity_id
```

This deletes *all* queued changes for an entity (e.g., both a CREATE and a subsequent UPDATE), not just the row that was just confirmed. The delete should use the row's own integer PK.

**4. `_pending_outbound` sets are not thread-safe**

Each `SyncedRepository` maintains a `set[str]` modified from the Qt main thread (on `save()`/`delete()`) and read from the sync background thread (via `get_pending_ids()`). No lock guards these accesses.

**5. No server cursor — pull fetches everything every time**

`engine.pull()` calls `get_all_codes()`, `get_all_sources()`, etc. — a full table scan on every pull. At scale this is expensive and produces no information about what actually changed.

---

## Decision

**Adopt the Transactional Outbox + Cursor Pull + LWW pattern.**

### Push path: Transactional Outbox

Every command handler that mutates domain data writes both the domain change and an outbox row in a **single SQLite transaction**:

```python
# Inside a command handler — one transaction, two tables
with conn.begin():
    conn.execute("INSERT OR REPLACE INTO cod_code ...", {...})
    conn.execute(
        "INSERT INTO sync_outbox (entity, entity_id, op, payload, idempotency_key, created_at) "
        "VALUES (:entity, :entity_id, :op, :payload, :key, :ts)",
        {
            "entity": "code",
            "entity_id": code.id.value,   # UUIDv7 (see ADR-001)
            "op": "upsert",               # or "delete"
            "payload": json.dumps(code_dict),
            "key": f"code:upsert:{code.id.value}",   # stable idempotency key
            "ts": hlc_now(),              # Hybrid Logical Clock timestamp
        },
    )
```

A background **push loop** drains the outbox:
1. Read a batch of pending rows from `sync_outbox` (ordered by `id`)
2. Call the corresponding Convex mutation with the idempotency key
3. On success, `DELETE FROM sync_outbox WHERE id = :row_id` (by row PK, not entity ID)
4. On transient failure, increment `attempts`; drop after `MAX_ATTEMPTS`

The idempotency key on the Convex side deduplicates retries.

### Pull path: Cursor-based incremental pull

Replace full-table pulls with a cursor-based approach:

```python
# sync_meta table
# key='last_pull_cursor', value='{timestamp or version token}'

cursor = conn.execute(
    "SELECT value FROM sync_meta WHERE key = 'last_pull_cursor'"
).scalar() or "0"

changes = convex.query("sync:getChangesSince", {"cursor": cursor})

for change in changes["items"]:
    if change.get("_deleted"):
        # Explicit tombstone from server — safe to delete locally
        _apply_delete(change["localId"], change["entityType"])
    else:
        _apply_upsert(change)

conn.execute(
    "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_pull_cursor', :cursor)",
    {"cursor": changes["nextCursor"]},
)
```

Deletions are server-driven via explicit tombstone records (`_deleted: true`). The client does not need to maintain a full local ID set and diff it against the remote — the broken `_get_local_ids()` stub is eliminated by design.

### Conflict resolution: LWW for metadata, Additive for annotations

| Entity field type | Policy | Reason |
|------------------|--------|--------|
| Code name, color, memo | Last-Write-Wins (LWW) | Low-stakes metadata; researcher intent is the most recent edit |
| Source name, memo, folder | LWW | Same rationale |
| Coded segments | **Additive** — never delete a remote segment unless an explicit server-side delete tombstone exists | Silently discarding another researcher's annotation is a data integrity violation in qualitative research |
| Case attributes | LWW per field | Structured data; last edit wins |

LWW comparison uses a **Hybrid Logical Clock (HLC)** timestamp, not a wall clock. HLC = `max(physical_ms, logical_counter)`, ensuring monotonically increasing timestamps that also capture causality regardless of clock skew between devices.

```python
# sync_meta key='hlc_state' — persisted HLC state
def hlc_now(conn) -> str:
    """Return current HLC timestamp and advance the clock."""
    ...  # see implementation plan
```

### Pending outbound conflict skip

Rather than per-repo `set[str]` (thread-unsafe), derive pending IDs directly from the `sync_outbox` table:

```python
def get_pending_ids(entity_type: str) -> frozenset[str]:
    rows = conn.execute(
        "SELECT DISTINCT entity_id FROM sync_outbox WHERE entity = :e AND attempts < :max",
        {"e": entity_type, "max": MAX_ATTEMPTS},
    ).fetchall()
    return frozenset(row[0] for row in rows)
```

This is thread-safe because SQLite WAL mode allows concurrent readers while the push loop writes.

---

## Consequences

### Positive

- **Atomicity guaranteed.** A crash between the domain write and the outbox insert is impossible — they are one transaction.
- **No more lost sync entries.** The outbox persists across restarts; the push loop picks up where it left off.
- **Deletion detection works.** Server tombstones replace the broken `_get_local_ids()` stub.
- **`_remove_persisted_change` fixed.** Deletion by row PK, not entity ID.
- **Thread-safety.** `_pending_outbound` sets replaced by a `sync_outbox` query (WAL-safe).
- **Efficient pull.** Cursor-based pull fetches only changes since the last pull, not full tables.
- **Research data integrity.** Additive policy for segments means no annotation is silently lost.
- **Idempotent push.** The idempotency key on Convex deduplicates retries transparently.

### Negative / Trade-offs

- **Convex must expose a `getChangesSince(cursor)` query.** This requires adding a server-side cursor mechanism to all Convex tables. The current `getAll` queries are replaced by cursor-aware queries.
- **HLC state must be persisted.** Adds a `sync_meta` table row for the HLC state. Requires care on clock initialization (especially on first install or database migration).
- **Outbox write inside command handlers couples sync to domain.** Command handlers must know about the outbox table. Mitigation: a thin `OutboxWriter` helper is injected into handlers, keeping the coupling explicit and testable.
- **The `SyncedRepository` decorator pattern is retired.** The current `SyncedCodeRepository` (wrapping SQLiteCodeRepository and calling `engine.queue_change()`) is replaced by direct outbox writes in command handlers. This is a structural change.

---

## Alternatives Considered

### Keep the current `SyncEngine.queue_change()` approach

**Rejected.** The non-atomic write is a correctness bug. The approach could be patched but the structural problems (full-table pulls, broken deletion, thread-unsafe pending sets) all require the same changes the outbox pattern already provides.

### Replicache-style optimistic mutations

**Rejected** for the initial implementation. Replicache requires writing every mutation twice (client + server mutator) and server-side conflict resolution logic. For QualCoder's primary use case (single researcher, offline-capable), the added complexity is not justified. The pattern can be adopted later if multi-user real-time collaboration becomes a requirement.

### Real-time subscriptions (Convex subscribe)

**Rejected** as the primary sync mechanism due to PyO3 GIL threading constraints documented in `engine.py:52-57`. Subscriptions can remain as an optional add-on once the outbox + cursor pull foundation is solid.

---

## Implementation Plan

Implementation plan has been completed and the planning document archived.

**Summary of phases:**

| Phase | Scope | Risk |
|-------|-------|------|
| 1 — Outbox table | Add `sync_outbox` + `sync_meta` tables | Low |
| 2 — HLC | Implement Hybrid Logical Clock utility | Low |
| 3 — OutboxWriter | Thin helper injected into command handlers | Medium |
| 4 — Command handlers | Write outbox entry inside each handler (atomic) | Medium |
| 5 — Push loop | Replace `_outbound_sync_loop` with outbox drain | Medium |
| 6 — Convex cursor API | Add `getChangesSince(cursor)` to all Convex tables | Medium |
| 7 — Pull loop | Replace `engine.pull()` with cursor pull | Medium |
| 8 — Delete SyncedRepos | Remove `SyncedRepository` wrappers | High |
| 9 — Conflict resolution | Implement LWW + additive policy per entity type | High |

---

## Relationship to Other Decisions

| ADR | Relationship |
|-----|-------------|
| [ADR-001](ADR-001-uuidv7-primary-keys.md) | UUIDv7 PKs are a prerequisite — the outbox stores entity UUIDs as the canonical ID, eliminating the FK-translation complexity that plagues the current engine |

---

## References

- [Transactional Outbox Pattern — microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)
- [Local-first software — Ink & Switch](https://www.inkandswitch.com/essay/local-first/)
- [A Map of Sync — Convex](https://stack.convex.dev/a-map-of-sync)
- [How Replicache Works](https://doc.replicache.dev/concepts/how-it-works)
- [WatermelonDB Sync Implementation](https://watermelondb.dev/docs/Implementation/SyncImpl)
- [Hybrid Logical Clocks — Martin Fowler](https://martinfowler.com/articles/patterns-of-distributed-systems/hybrid-clock.html)
- [SQLite WAL Mode](https://sqlite.org/wal.html)
- [Offline sync & conflict resolution patterns](https://www.sachith.co.uk/offline-sync-conflict-resolution-patterns-architecture-trade%E2%80%91offs-practical-guide-feb-19-2026/)
