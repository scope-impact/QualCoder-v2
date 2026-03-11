# Session Architecture Plan

> Replaces `ThreadSafeConnectionProxy`, `UnitOfWork`, and simplifies `_create_contexts`.
> Incremental migration — each step is independently shippable and testable.

## Problem Statement

Three separate mechanisms solve overlapping concerns:

| Mechanism | What it does | Problem |
|-----------|-------------|---------|
| `ThreadSafeConnectionProxy` | Per-thread connections for repos | Repos capture a connection at construction, hold it forever |
| `UnitOfWork` | Monkey-patches `conn.commit` with no-op for multi-repo atomicity | Fragile, can't nest, repos don't know they're in a UoW |
| Per-repo `commit()` | Every repo method calls `self._conn.commit()` | Command handler has no control over transaction boundary |

Additionally, `_create_contexts()` is a 100-line method mixing network I/O, sync engine lifecycle, and bounded context wiring.

## Solution: Session + SyncContext extraction

### Session class

One object per open project. Shared between UI (main thread) and MCP (worker threads).

```python
class Session:
    """
    Project-scoped database session.

    Provides thread-local connections via SingletonThreadPool.
    Owns the commit — repos never commit, command handlers do.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._local = threading.local()

    @property
    def connection(self) -> Connection:
        """Thread-local connection. Same thread always gets the same one."""
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = self._engine.connect()
            conn.execute(text("PRAGMA busy_timeout = 5000"))
            self._local.conn = conn
        return conn

    @property
    def engine(self) -> Engine:
        return self._engine

    def commit(self) -> None:
        """Commit the current transaction. Called by command handlers."""
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.connection.rollback()

    def close(self) -> None:
        """Close all connections and dispose the engine."""
        # Thread-local cleanup handled by engine.dispose()
        self._engine.dispose()
```

### How it replaces UnitOfWork

The Session *is* the unit of work. Repos never commit; command handlers call `session.commit()`.

**Before (UoW monkey-patches commit):**
```python
def merge_codes(command, code_repo, segment_repo, event_bus):
    with UnitOfWork(code_repo._conn) as uow:
        segment_repo.reassign_code(source_id, target_id)  # suppressed commit
        code_repo.delete(source_id)                        # suppressed commit
        uow.commit()                                       # real commit
    event_bus.publish(event)
```

**After (session owns commit):**
```python
def merge_codes(command, session, code_repo, segment_repo, event_bus):
    segment_repo.reassign_code(source_id, target_id)  # execute only
    code_repo.delete(source_id)                        # execute only
    session.commit()                                   # single commit point
    event_bus.publish(event)
```

**Single-repo handlers:**
```python
# Before: commit buried inside repo.save()
def create_code(command, code_repo, event_bus):
    code_repo.save(code)  # execute + commit
    event_bus.publish(event)

# After: explicit commit
def create_code(command, session, code_repo, event_bus):
    code_repo.save(code)   # execute only
    session.commit()        # explicit
    event_bus.publish(event)
```

### How it replaces ThreadSafeConnectionProxy

Session provides thread-local connections natively. No proxy needed.

```
open_project()
  ├── creates Engine (SingletonThreadPool + WAL mode)
  ├── creates Session (wraps engine)
  │
  ├── UI (main thread)
  │   └── session.connection → main thread's connection
  │
  └── MCP (worker threads via asyncio.to_thread)
      └── session.connection → worker thread's connection
```

### Repo changes

Repos receive Session instead of Connection. Never call commit.

```python
class SQLiteCodeRepository:
    def __init__(self, session: Session, outbox: OutboxWriter | None = None):
        self._session = session
        self._outbox = outbox

    def save(self, code: Code) -> None:
        self._session.connection.execute(upsert_stmt)
        if self._outbox:
            self._outbox.write_upsert("code", code.id.value, {...})
        # NO commit — command handler decides when

    def get_all(self) -> list[Code]:
        result = self._session.connection.execute(select_stmt)
        return [self._map(row) for row in result]
```

OutboxWriter already follows this pattern — it never commits. No changes needed there.

### SyncContext extraction

Pull sync wiring out of `_create_contexts` into its own bounded context.

```python
@dataclass
class SyncContext:
    """Cloud sync bounded context — optional."""
    engine: SyncEngine

    @classmethod
    def create(
        cls,
        session: Session,
        convex_client: ConvexClientWrapper,
    ) -> SyncContext:
        sync_engine = SyncEngine(session.connection, convex_client)
        return cls(engine=sync_engine)

    def start(self) -> None:
        self.engine.start()

    def stop(self) -> None:
        self.engine.stop()
```

`_create_contexts` becomes clean domain wiring only:

```python
def _create_contexts(self, session, project_path):
    self.sources_context = SourcesContext.create(session=session, ...)
    self.coding_context = CodingContext.create(session=session, ...)
    self.cases_context = CasesContext.create(session=session, ...)
    self.folders_context = FoldersContext.create(session=session, ...)
    self.projects_context = ProjectsContext.create(session=session, ...)
```

Sync wiring happens separately in `open_project`:

```python
if self._is_convex_reachable(url):
    self.sync_context = SyncContext.create(session=session, convex_client=client)
    self.sync_context.start()
```

### Enable WAL mode

One pragma eliminates most SQLite multi-connection deadlocks:

```python
# In ProjectLifecycle.open_database(), after creating the engine:
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.commit()
```

With WAL mode, the `commit()` after SELECT pattern (3 locations in sync code) becomes unnecessary. Readers no longer block writers.

## Comparison: UnitOfWork vs Session

| Concern | UnitOfWork (current) | Session (proposed) |
|---------|---------------------|--------------------|
| Who commits? | UoW after monkey-patching | Command handler via `session.commit()` |
| Multi-repo atomicity | Suppress individual commits | Repos never commit — naturally atomic |
| Thread safety | Separate concern (proxy) | Built in (thread-local connections) |
| Rollback on error | Auto-rollback in `__exit__` | `session.rollback()` or framework-level |
| Monkey-patching | Yes (`conn.commit = noop`) | None |
| Nesting | Broken | Not needed |
| OutboxWriter | Already compatible | No changes needed |

**Verdict: UnitOfWork is deleted once Session is in place.**

## Schema isolation (future)

Each context uses prefixed tables (`cod_`, `src_`, `cas_`, `prj_`). Currently in one SQLite file, but the schema boundaries are clean enough to split into separate databases if needed. The Session abstraction doesn't prevent this — a future `MultiDbSession` could route by context prefix.

## Migration steps

Each step is independently shippable. Tests verify each step.

### Step 1: Create Session class
- New file: `src/shared/infra/session.py`
- Wraps engine + thread-local connections
- No behavior change yet — existing code unchanged

### Step 2: Enable WAL mode
- Add `PRAGMA journal_mode=WAL` in `ProjectLifecycle.open_database()`
- Remove `commit()` after SELECT in sync code (3 locations)
- Eliminates reader-blocks-writer deadlocks

### Step 3: Add `session.commit()` to command handlers
- Pass Session to command handlers alongside repos
- Add `session.commit()` after repo operations
- Repos still commit too (double commit is safe, no behavior change)

### Step 4: Remove `self._conn.commit()` from repos
- One repo at a time
- Tests verify each repo's command handlers still work
- Repos become pure execute-only

### Step 5: Delete UnitOfWork
- The 4 command handlers that use it (`delete_code`, `delete_category`, `merge_codes`, `remove_source`) just use `session.commit()`
- Delete `src/shared/infra/unit_of_work.py`

### Step 6: Delete ThreadSafeConnectionProxy
- Session replaces it
- Delete `src/shared/infra/connection_provider.py`
- Update `_create_contexts` to pass Session instead of proxy

### Step 7: Extract SyncContext
- New dataclass: `SyncContext` with `create()`, `start()`, `stop()`
- Move Convex reachability check, client creation, SyncEngine wiring out of `_create_contexts`
- `_create_contexts` becomes pure domain context wiring

## Files affected

| File | Change |
|------|--------|
| `src/shared/infra/session.py` | **New** — Session class |
| `src/shared/infra/lifecycle.py` | Creates Session instead of raw connection + factory |
| `src/shared/infra/app_context/context.py` | Uses Session, extracts SyncContext |
| `src/shared/infra/app_context/bounded_contexts.py` | `create()` methods take Session instead of Connection |
| `src/shared/infra/connection_provider.py` | **Deleted** |
| `src/shared/infra/unit_of_work.py` | **Deleted** |
| `src/contexts/*/infra/*_repository.py` | Receive Session, remove `commit()` calls |
| `src/contexts/*/core/commandHandlers/*.py` | Add `session` param, call `session.commit()` |
| `src/shared/infra/sync/engine.py` | Remove commit-after-SELECT (WAL makes it unnecessary) |
| `src/shared/infra/sync/id_map.py` | Remove commit-after-SELECT |
