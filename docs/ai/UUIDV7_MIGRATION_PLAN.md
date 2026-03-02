# UUIDv7 Primary Key Migration Plan

**Decision:** ADR-001 — UUIDv7 as Primary Keys for All Entities
**Status:** Planning
**Date:** 2026-02-25

---

## Overview

This plan migrates all SQLite integer primary keys to UUIDv7 string keys across all bounded contexts. The migration eliminates the `SyncIdMap` mapping table and all FK-translation logic from the sync engine.

**Affected entity types:**

| Entity | Table | Current PK column | FK references from |
|--------|-------|-------------------|--------------------|
| Category | `cod_category` | `catid INTEGER` | `cod_code.catid`, `cod_category.supercatid` |
| Code | `cod_code` | `cid INTEGER` | `cod_segment.cid` |
| Segment | `cod_segment` | `ctid INTEGER` | — |
| Source | `src_source` | `id INTEGER` | `cod_segment.fid`, `cas_source_link.source_id`, `src_source.av_text_id` |
| Folder | `src_folder` | `id INTEGER` | `src_source.folder_id`, `src_folder.parent_id` |
| Case | `cas_case` | `id INTEGER` | `cas_attribute.case_id`, `cas_source_link.case_id` |

---

## Phase 0 — Add Dependency

**Effort:** Trivial | **Risk:** Low

Python's `uuid` stdlib gains `uuid7()` in 3.13+. The `uuid-utils` library provides it for earlier versions with a Rust-backed implementation matching the stdlib API.

```toml
# pyproject.toml
[tool.uv.dependencies]
uuid-utils = ">=0.9"
```

**Create shared utility** at `src/shared/common/uuid7.py`:

```python
"""UUIDv7 generation — time-ordered, globally unique."""
try:
    from uuid import uuid7  # Python 3.13+
except ImportError:
    from uuid_utils import uuid7  # Fallback: uuid-utils package

def new_uuid7() -> str:
    """Generate a new UUIDv7 string (canonical hyphenated form)."""
    return str(uuid7())
```

**Acceptance criteria:**
- [ ] `uuid-utils` added to `pyproject.toml` and lock file updated
- [ ] `src/shared/common/uuid7.py` exists with `new_uuid7() -> str`
- [ ] `uv run python -c "from src.shared.common.uuid7 import new_uuid7; print(new_uuid7())"` prints a UUIDv7

---

## Phase 1 — Typed Identifiers

**Effort:** Medium | **Risk:** Medium (313 `.value` usages, caught by mypy)

Change all typed ID classes in `src/shared/common/types.py` from `value: int` to `value: str`.

**Before:**
```python
@dataclass(frozen=True)
class CodeId:
    value: int

    @classmethod
    def new(cls) -> CodeId:
        return cls(value=int(uuid4().int % 1_000_000))  # BROKEN: collision-prone
```

**After:**
```python
@dataclass(frozen=True)
class CodeId:
    value: str

    @classmethod
    def new(cls) -> CodeId:
        return cls(value=new_uuid7())

    @classmethod
    def from_str(cls, s: str) -> CodeId:
        return cls(value=s)
```

Apply to: `CodeId`, `SegmentId`, `SourceId`, `CategoryId`, `CaseId`, `FolderId`.

**Fix type errors after changing:**
- Any comparison `id.value == 42` → comparison against string
- Any function accepting `int` that receives `id.value`
- Repository columns casting `int(row["id"])` → `str(row["id"])`
- Error message strings `f"Code with id {self.code_id.value}"` — no change needed (str works)

**Acceptance criteria:**
- [ ] All 6 typed ID classes use `value: str`
- [ ] `mypy src/` passes with no type errors in `types.py` or its consumers
- [ ] `CodeId.new()` generates a UUIDv7 (starts with time-encoded prefix, 36 chars)
- [ ] `make test-all` passes

---

## Phase 2 — SQLite Schemas

**Effort:** Medium | **Risk:** Medium

Change all `Integer` primary key and FK columns to `String(36)` in the four schema files.

### `src/contexts/coding/infra/schema.py`

```python
# Before
Column("catid", Integer, primary_key=True),
Column("supercatid", Integer),   # FK → cod_category.catid

Column("cid", Integer, primary_key=True),
Column("catid", Integer),        # FK → cod_category.catid

Column("ctid", Integer, primary_key=True),
Column("cid", Integer, nullable=False),   # FK → cod_code.cid
Column("fid", Integer, nullable=False),   # FK → src_source.id

# After
Column("catid", String(36), primary_key=True),
Column("supercatid", String(36)),

Column("cid", String(36), primary_key=True),
Column("catid", String(36)),

Column("ctid", String(36), primary_key=True),
Column("cid", String(36), nullable=False),
Column("fid", String(36), nullable=False),
```

### `src/contexts/sources/infra/schema.py`

```python
# Before
Column("id", Integer, primary_key=True),    # src_folder
Column("parent_id", Integer),

Column("id", Integer, primary_key=True),    # src_source
Column("folder_id", Integer),
Column("av_text_id", Integer),

# After
Column("id", String(36), primary_key=True),
Column("parent_id", String(36)),

Column("id", String(36), primary_key=True),
Column("folder_id", String(36)),
Column("av_text_id", String(36)),
```

### `src/contexts/cases/infra/schema.py`

```python
# Before
Column("id", Integer, primary_key=True),    # cas_case
Column("id", Integer, primary_key=True),    # cas_attribute
Column("case_id", Integer, nullable=False),
Column("id", Integer, primary_key=True),    # cas_source_link
Column("case_id", Integer, nullable=False),
Column("source_id", Integer, nullable=False),

# After
Column("id", String(36), primary_key=True),
Column("id", String(36), primary_key=True),
Column("case_id", String(36), nullable=False),
Column("id", String(36), primary_key=True),
Column("case_id", String(36), nullable=False),
Column("source_id", String(36), nullable=False),
```

### `src/contexts/folders/infra/schema.py`

```python
# Before
Column("id", Integer, primary_key=True),
Column("parent_id", Integer),

# After
Column("id", String(36), primary_key=True),
Column("parent_id", String(36)),
```

**Acceptance criteria:**
- [ ] All four schema files changed
- [ ] `create_all_contexts(engine)` creates tables with `TEXT` columns (check via SQLite `PRAGMA table_info`)
- [ ] `make test-all` passes (E2E tests recreate the database from scratch, so no migration needed in tests)

---

## Phase 3 — Repositories

**Effort:** Medium | **Risk:** Medium

Update all SQLite repository `save()`, `get_by_id()`, `delete()`, and query methods to treat the `id` column as a string.

**Key changes per repository:**

1. **`get_by_id(id: XxxId)`** — `WHERE id = :id` with `{"id": xxx_id.value}` already works; just confirm `str` binding
2. **`save(entity)`** — `INSERT OR REPLACE` with `id=entity.id.value` — works with str
3. **Row → entity mapping** — change `int(row["id"])` to `str(row["id"])` everywhere
4. **FK columns** — `catid=code.category_id.value if code.category_id else None` — works with str

**Files to update:**
- `src/contexts/coding/infra/repositories.py` (SQLiteCodeRepository, SQLiteCategoryRepository, SQLiteSegmentRepository)
- `src/contexts/sources/infra/source_repository.py`
- `src/contexts/folders/infra/folder_repository.py`
- `src/contexts/cases/infra/case_repository.py`

**Acceptance criteria:**
- [ ] All repositories map `id` column as `str`, not `int`
- [ ] `mypy src/` clean
- [ ] `make test-all` passes

---

## Phase 4 — Sync Layer Simplification

**Effort:** High | **Risk:** High (core sync logic)

This is the payoff phase: delete the mapping table and all translation logic.

### 4a. Delete `src/shared/infra/sync/id_map.py`

The `SyncIdMap` class and `FK_DEPENDENCIES` dict are deleted entirely.

### 4b. Simplify `SyncEngine`

Remove from `engine.py`:
- `self._id_map = SyncIdMap(...)` initialization
- `_translate_fk_ids()` method
- `id_map` property
- All `self._id_map.put(...)`, `self._id_map.get_convex_id(...)`, `self._id_map.remove(...)` calls
- `sync_id_map` table creation

**New `_sync_to_convex` logic for CREATE:**
```python
# Before: needed FK translation + id_map.put
convex_doc_id = self._convex.mutation(mutation, **translated)
if convex_doc_id:
    self._id_map.put(change.entity_type, str(change.entity_id), str(convex_doc_id))

# After: entity_id IS the canonical ID, no mapping
self._convex.mutation(mutation, local_id=change.entity_id, **data)
# No mapping needed — local ID is sent as localId to Convex
```

**New `_sync_to_convex` logic for UPDATE/DELETE:**
```python
# Before: looked up Convex ID via id_map
convex_id = self._id_map.get_convex_id(change.entity_type, str(change.entity_id))

# After: query Convex by localId field
# Convex mutation accepts localId as the selector
self._convex.mutation(mutation, local_id=change.entity_id, **data)
```

### 4c. Remove deferred-retry FK logic from `_outbound_sync_loop`

```python
# Delete: result == "deferred" branch and consecutive_deferrals counter
# The only results are "success" and "error"
```

### 4d. Update `SyncedRepositories`

In `synced_repositories.py`, the `SyncChange` data dicts currently pass integer FK values:
```python
data={"catid": code.category_id.value if code.category_id else None, ...}
```
With UUIDv7, these are now strings — no `_translate_fk_ids` needed. The Convex mutation receives the UUID string directly.

**Acceptance criteria:**
- [ ] `id_map.py` deleted
- [ ] `SyncEngine` has no reference to `SyncIdMap`, `FK_DEPENDENCIES`, or `_translate_fk_ids`
- [ ] `_outbound_sync_loop` has no "deferred" case
- [ ] `make test-all` passes
- [ ] Manual sync test: create code offline, go online, confirm it appears in Convex with correct `localId`

---

## Phase 5 — Convex Schema Update

**Effort:** Medium | **Risk:** Medium

Add `localId` field to all Convex tables and update mutations to accept it.

### Schema changes (`convex/schema.ts`)

```typescript
// Before
codes: defineTable({
  name: v.string(),
  color: v.string(),
  // ...
})

// After
codes: defineTable({
  localId: v.string(),   // UUIDv7 from client
  name: v.string(),
  color: v.string(),
  // ...
}).index("by_local_id", ["localId"])
```

Apply to: `codes`, `categories`, `segments`, `sources`, `folders`, `cases`, `attributes`, `source_links`.

### Mutation changes (`convex/codes.ts`, etc.)

```typescript
// create mutation — accept localId from client
export const create = mutation({
  args: { localId: v.string(), name: v.string(), color: v.string(), ... },
  handler: async (ctx, { localId, name, color, ... }) => {
    return await ctx.db.insert("codes", { localId, name, color, ... });
  },
});

// update/delete — find by localId instead of _id
export const update = mutation({
  args: { localId: v.string(), name: v.optional(v.string()), ... },
  handler: async (ctx, { localId, ...updates }) => {
    const doc = await ctx.db.query("codes")
      .withIndex("by_local_id", q => q.eq("localId", localId))
      .unique();
    if (!doc) throw new Error(`Code ${localId} not found`);
    await ctx.db.patch(doc._id, updates);
  },
});
```

**Acceptance criteria:**
- [ ] All 6 Convex tables have `localId: v.string()` with `by_local_id` index
- [ ] All create/update/delete mutations accept `localId`
- [ ] `convex dev` starts without errors
- [ ] Integration test: create a code in SQLite, sync, query Convex by `localId`, confirm match

---

## Phase 6 — Database Migration for Existing `.qda` Files

**Effort:** High | **Risk:** High (data integrity)

Projects created before this migration have integer PKs. The migration must:
1. Add UUID columns alongside integer columns
2. Generate UUIDv7 values for every existing row
3. Update all FK columns to reference the new UUID values
4. Rename UUID columns to become the new PK
5. Drop old integer PK columns

**Location:** `src/contexts/projects/infra/migrations/migrate_001_uuidv7.py`

**Algorithm:**

```python
def migrate_to_uuidv7(conn):
    """
    One-time migration: convert all integer PKs to UUIDv7 strings.
    Runs inside a single SQLite transaction for atomicity.
    """
    with conn.begin():
        # Step 1: Add uuid columns to all tables
        conn.execute("ALTER TABLE cod_code ADD COLUMN uuid TEXT")
        conn.execute("ALTER TABLE cod_category ADD COLUMN uuid TEXT")
        # ... all tables

        # Step 2: Generate UUIDs for all existing rows
        rows = conn.execute("SELECT cid FROM cod_code").fetchall()
        id_map = {}
        for (cid,) in rows:
            new_uuid = new_uuid7()
            id_map[cid] = new_uuid
            conn.execute("UPDATE cod_code SET uuid = ? WHERE cid = ?", (new_uuid, cid))
        # ... repeat for all tables

        # Step 3: Update FK columns using the maps
        for old_catid, new_catid in category_map.items():
            conn.execute(
                "UPDATE cod_code SET catid_uuid = ? WHERE catid = ?",
                (new_catid, old_catid)
            )
        # ... all FK relationships

        # Step 4: Recreate tables with uuid as PK (SQLite doesn't support ALTER COLUMN)
        conn.execute("""
            CREATE TABLE cod_code_new (
                cid TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#999999',
                catid TEXT,
                ...
            )
        """)
        conn.execute("""
            INSERT INTO cod_code_new SELECT uuid, name, color, catid_uuid, ...
            FROM cod_code
        """)
        conn.execute("DROP TABLE cod_code")
        conn.execute("ALTER TABLE cod_code_new RENAME TO cod_code")
```

**Migration trigger:** Run automatically when `AppContext.open_project()` detects the schema version is below 2.

**Schema version tracking:** Add `schema_version` key to `prj_settings` table.

**Acceptance criteria:**
- [ ] Migration runs without error on a test `.qda` file with real data
- [ ] All row counts match before and after
- [ ] All FK references are valid (no orphaned FKs)
- [ ] Migration is idempotent (safe to run twice)
- [ ] Original `.qda` file backed up before migration runs (copy to `{name}.qda.bak`)

---

## Phase 7 — Tests and Fixtures

**Effort:** Medium | **Risk:** Low

Update all E2E test fixtures to use UUIDv7 IDs.

**Key changes:**
- Test factories that create `CodeId(value=42)` change to `CodeId(value=new_uuid7())`
- Assertions like `assert code.id.value == 42` change to check UUID format: `assert len(code.id.value) == 36`
- Fixtures that directly insert rows with integer IDs must use string UUIDs

**Location:** `src/tests/e2e/` — all fixture files and test helpers.

**Acceptance criteria:**
- [ ] `make test-all` passes with 0 failures
- [ ] No test file contains `value=42` or any integer literal for entity IDs

---

## Execution Order and Dependencies

```
Phase 0 (dependency)
    ↓
Phase 1 (typed IDs)        ← mypy validates all downstream consumers
    ↓
Phase 2 (SQLite schemas)
    ↓
Phase 3 (repositories)
    ↓
Phase 5 (Convex schema)    ← can run in parallel with Phase 3
    ↓
Phase 4 (sync layer)       ← requires Phase 3 + Phase 5
    ↓
Phase 6 (DB migration)     ← requires Phase 4 complete and tested
    ↓
Phase 7 (tests)            ← ongoing through all phases, final pass here
```

---

## Rollback Plan

- Phases 0-3 are independently reversible (typed IDs and schemas can be reverted).
- Phase 4 (sync layer) should be done on a separate git branch (`feature/uuidv7-migration`).
- Phase 6 (DB migration) is irreversible for a given `.qda` file. The `.qda.bak` backup enables recovery.
- The branch is merged only after all phases pass `make test-all` and a manual sync test confirms Convex sync works end-to-end.

---

## Files To Delete After Migration

| File | Reason |
|------|--------|
| `src/shared/infra/sync/id_map.py` | Replaced by direct UUID identity |
| `sync_id_map` SQLite table | No longer needed |
| `sync_id_map` entries in `engine.py` | All references removed |
| `FK_DEPENDENCIES` constant | No FK translation needed |
| `_translate_fk_ids()` method | Deleted |

---

## References

- ADR: `docs/decisions/ADR-001-uuidv7-primary-keys.md`
- Research: `docs/ai/SYNC_ENGINE_RESEARCH.md` (sync engine pattern analysis)
- UUID RFC: https://www.rfc-editor.org/rfc/rfc9562
- `uuid-utils` library: https://pypi.org/project/uuid-utils/
