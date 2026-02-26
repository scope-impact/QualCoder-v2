# ADR-001: UUIDv7 as Primary Keys for All Entities

**Status:** Accepted
**Date:** 2026-02-25
**Deciders:** Sathish Narayanan
**Scope:** All bounded contexts (`coding`, `sources`, `cases`, `folders`)

---

## Context

### The problem we are solving

QualCoder stores data locally in SQLite (offline-first) and optionally syncs to Convex cloud. SQLite uses **auto-increment integer** primary keys. Convex uses **opaque string** document IDs. Keeping these two ID spaces in sync requires a mapping table (`sync_id_map`) with significant complexity:

1. Every outbound sync must look up the Convex ID for each entity.
2. Every inbound sync must translate Convex IDs back to local integer IDs.
3. Foreign key references (e.g., `segment.code_id`) must also be translated, introducing ordering dependencies that cause "FK not mapped yet — deferring" errors.
4. If the mapping table is lost or out of sync, the entire sync state is corrupted.

### The current ID generation is broken

The typed identifiers in `src/shared/common/types.py` use this pattern:

```python
@classmethod
def new(cls) -> CodeId:
    return cls(value=int(uuid4().int % 1_000_000))
```

This generates a random integer in the range `[0, 999_999]`. By the birthday paradox, a 50% collision probability is reached at approximately **1,183 entities** — well within the scale of a real research project. This is a latent correctness bug.

### The two-ID problem is the root cause of sync complexity

The `SyncEngine._translate_fk_ids()`, `SyncEngine._sync_to_convex()`, `SyncIdMap`, and all deferred-retry logic in the outbound sync loop exist solely to bridge integer local IDs and Convex string IDs. Eliminating the mismatch eliminates this entire layer.

---

## Decision

**Use UUIDv7 string values as primary keys for all entities across SQLite and Convex.**

- Local SQLite `id` columns change from `Integer` to `String(36)` (storing the UUID as a canonical hyphenated string).
- Typed identifiers (`CodeId`, `SegmentId`, `SourceId`, `CategoryId`, `CaseId`, `FolderId`) change their internal `value` from `int` to `str`.
- The Convex document `_id` field continues to be Convex's own ID; the UUID is stored as a separate `localId` field in Convex documents (or the mutation accepts the client UUID as the canonical record ID where Convex supports custom IDs).
- The `SyncIdMap` table and `id_map.py` module are **deleted** once migration is complete.
- The `FK_DEPENDENCIES` translation logic in `SyncEngine._translate_fk_ids()` is **deleted**.

### Why UUIDv7 specifically

| Property | UUIDv4 | UUIDv7 |
|----------|--------|--------|
| Globally unique | Yes | Yes |
| Time-ordered | No | Yes — first 48 bits = millisecond timestamp |
| B-tree index friendly | Poor (random, causes page splits) | Good (monotonically increasing) |
| Sortable by creation time | No | Yes |
| Available in Python | `uuid.uuid4()` | `uuid-utils` library (Rust-backed, fast) |

UUIDv7's time-ordering means SQLite B-tree indexes for the `id` column remain append-friendly, preserving the locality that makes integer auto-increment performant. Pure random UUIDv4 causes index fragmentation on every insert.

### Why not keep integers

- Integer PKs require the mapping table, which is the source of the majority of sync complexity.
- The current `uuid4() % 1_000_000` hack is unsound; moving to UUIDv7 fixes correctness at the same time.
- Integers require server coordination for global uniqueness (e.g., Convex ID must be authoritative). UUIDv7 allows offline-first creation with no coordination.

### Why not UUIDv4

- Index fragmentation degrades SQLite read performance on large projects.
- Not sortable by time, which breaks any "show me recently added codes" query that relies on ID ordering.

---

## Consequences

### Positive

- **Sync ID mapping eliminated.** `SyncIdMap`, `FK_DEPENDENCIES`, `_translate_fk_ids`, deferred-retry FK logic — all deleted.
- **Offline entity creation is safe.** A new code created offline is given its canonical global ID immediately, without needing a server round-trip.
- **Collision probability eliminated.** UUIDv7 collision probability is negligible (2^122 random bits plus time component).
- **SQLite index performance preserved.** Monotonically increasing IDs prevent B-tree fragmentation.
- **Simpler sync boundary.** The outbound sync sends the entity's own UUID; the server stores it. No translation required.

### Negative / Trade-offs

- **Migration required for existing `.qda` files.** Projects created before this change have integer PKs. A one-time migration must convert all IDs and update all FK references. Existing files cannot be opened without running the migration.
- **String IDs are larger than integers** — approximately 36 bytes vs 4-8 bytes per PK. At the scale of QualCoder projects (tens of thousands of segments at most), this is negligible.
- **Python dependency.** Python's built-in `uuid` module gains `uuid7()` only in Python 3.13+. Until then, the `uuid-utils` library (`pip install uuid-utils`) provides a fast Rust-backed implementation with an identical API.
- **All 313 `.value` usages must change type** — any code that compares `id.value` to an integer literal or passes it to a function expecting `int` will fail at type-check time. This is a one-time cost, caught by `mypy`.
- **Convex schema change.** Convex documents currently use Convex's own `_id` as the authoritative ID. We add a `localId: v.string()` field (storing the UUIDv7) and use that for all cross-system references.

---

## Alternatives Considered

### Keep integer PKs + improve SyncIdMap

**Rejected.** The mapping table is inherently stateful and can desync. Adding a `localId TEXT UNIQUE` column to each table (PowerSync dual-ID pattern) solves offline creation but still requires FK translation. Complexity reduction is partial.

### UUIDv4 instead of UUIDv7

**Rejected.** Same collision safety as UUIDv7 but loses time-ordering, causing SQLite B-tree fragmentation and removing natural sort-by-creation ordering.

### Convex-issued IDs as the canonical ID

**Rejected.** This requires a network round-trip to create any entity, breaking offline-first operation entirely.

---

## Implementation Plan

See [`docs/ai/UUIDV7_MIGRATION_PLAN.md`](../ai/UUIDV7_MIGRATION_PLAN.md) for the full phased implementation plan.

**Summary of phases:**

| Phase | Scope | Risk |
|-------|-------|------|
| 0 — Dependency | Add `uuid-utils` to `pyproject.toml` | Low |
| 1 — Typed IDs | Change `value: int → str` in `types.py` | Medium (313 usages) |
| 2 — SQLite schemas | Change `Integer` PKs to `String(36)` | Medium |
| 3 — Repositories | Update all repo `save()`/`get_by_id()` | Medium |
| 4 — Sync layer | Remove `SyncIdMap`, `_translate_fk_ids`, deferred-retry logic | High |
| 5 — Convex schema | Add `localId` field to all Convex tables | Medium |
| 6 — DB migration | Write SQLite migration for existing `.qda` files | High |
| 7 — Tests | Update all E2E fixtures and assertions | Medium |

---

## References

- [UUIDv7 RFC 9562](https://www.rfc-editor.org/rfc/rfc9562)
- [Goodbye Sequential Integers, Hello UUIDv7 — Buildkite](https://buildkite.com/resources/blog/goodbye-integers-hello-uuids/)
- [uuid-utils Python library](https://pypi.org/project/uuid-utils/)
- [PowerSync Sequential ID Mapping](https://docs.powersync.com/tutorials/client/data/sequential-id-mapping) — the problem we are solving by not needing this
- [The Two ID Problem — Dan Lew](https://blog.danlew.net/2017/03/09/the-two-id-problem/) — the root cause
- Research session that led to this decision: `docs/ai/SYNC_ENGINE_RESEARCH.md`
