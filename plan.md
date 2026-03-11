# Plan: Consolidate Session Commit, Fix Import Duplication, Async Reachability

Three architectural issues from `/simplify` review.

---

## Issue 1: Consolidate `if session: session.commit()` (28 handlers)

### Approach: Auto-commit in `@metered_command` decorator

The decorator wraps every mutation handler. After a successful result, it can commit the session automatically.

### Step 1: Add auto-commit to `@metered_command` (`src/shared/infra/metrics.py`)

After `func(*args, **kwargs)` succeeds (i.e., `result.is_success`), extract `session` from kwargs and call `session.commit()`:

```python
def wrapper(*args, **kwargs):
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        attrs = {"command": command_name}
        if hasattr(result, "is_success"):
            if result.is_success:
                session = kwargs.get("session")
                if session:
                    session.commit()
            else:
                command_failures.add(1, attrs)
        command_total.add(1, attrs)
        return result
    # ... rest unchanged
```

This is safe for nested calls (e.g., `import_code_list` → `create_code`): each sub-handler commits its own work, and the parent handler's commit is a no-op if nothing new was written since.

### Step 2: Remove `if session: session.commit()` from all 28 command handlers

All handlers in:
- `coding/core/commandHandlers/` (12 files)
- `cases/core/commandHandlers/` (7 files)
- `sources/core/commandHandlers/` (5 files)
- `folders/core/commandHandlers/` (4 files)

### Step 3: Keep explicit commits in exchange import handlers for direct `repo.save()`

`import_refi_qda`, `import_rqda`, `import_survey_csv` do direct `repo.save()` for sources/segments/cases (bypassing command handlers). These explicit `session.commit()` calls must stay because the decorator only commits at the import handler level, not after each direct save.

However, since these import handlers are NOT decorated with `@metered_command`, we should:
- Add `@metered_command` to all 4 exchange import handlers
- Their final `session.commit()` will then be handled by the decorator
- Keep intermediate commits for direct `repo.save()` calls within loops

### Step 4: Fix `open_source` bug

`file_manager_viewmodel.py:706` passes `session=self._session` to `open_source()` which doesn't accept it → `TypeError` at runtime. Remove it.

### Step 5: Fix `_import_sources_async` commit

The viewmodel's `_import_sources_async` calls `self._source_repo.save(source)` + `self._session.commit()` directly. Keep this as-is since it bypasses command handlers.

### Step 6: Run tests, fix broken mocks

---

## Issue 2: `_import_sources_async` duplicates `import_file_source` logic

### Approach: Call `import_file_source` from the async batch method

Currently `_import_sources_async` reimplements: type detection, uniqueness check, text extraction, entity creation, persistence, event publishing — all of which already exist in `import_file_source`.

### Step 1: Run `import_file_source` in the executor

`import_file_source` is synchronous and does blocking I/O (text extraction). Wrap the entire call in `run_in_executor`:

```python
async def _import_sources_async(self, file_paths, origin, memo):
    loop = asyncio.get_running_loop()
    self._suppress_reloads += 1
    try:
        for idx, raw_path in enumerate(file_paths):
            if self._import_cancelled:
                break
            command = ImportFileSourceCommand(
                path=raw_path, origin=origin, memo=memo
            )
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    import_file_source,
                    command=command,
                    state=self._state,
                    source_repo=self._source_repo,
                    event_bus=self._event_bus,
                    session=self._session,
                ),
            )
            if result.is_success:
                imported += 1
                imported_paths.append(raw_path)
            else:
                failed += 1
            self.batch_import_progress.emit(idx + 1, total, Path(raw_path).name)
    finally:
        self._suppress_reloads = max(0, self._suppress_reloads - 1)
    self.batch_import_finished.emit(imported, failed, imported_paths)
    self.sources_changed.emit()
    self.summary_changed.emit()
```

This is thread-safe because:
- `SingletonThreadPool` gives each thread its own SQLite connection
- `session.commit()` (via decorator) commits the thread-local connection
- `EventBus.publish()` is thread-safe (uses locks)

### Step 2: Handle uniqueness check efficiency

`import_file_source` calls `source_repo.get_all()` for each file (uniqueness check). For batch import this is O(n × m) where m is total sources.

Accept this for now — SQLite queries are fast for typical batch sizes (< 1000 files). If perf becomes an issue later, add a `known_names` parameter to the command.

### Step 3: Remove duplicated logic from `_import_sources_async`

Remove:
- `detect_source_type()` call
- Inline uniqueness check
- `extract_text()` call
- `Source(...)` entity construction
- `source_repo.save()` call
- `SourceAdded.create()` event publishing

### Step 4: Verify the `ImportFileSourceCommand` has all needed fields

Check that the command supports `origin` and `memo` parameters needed by batch import.

---

## Issue 3: `_is_convex_reachable` blocks main thread up to 2s

### Approach: Reduce timeout (quick fix) + background check (follow-up)

### Step 1 (quick, do now): Reduce timeout from 2.0s to 0.5s

In `src/shared/infra/app_context/sync_context.py`:

```python
with socket.create_connection((host, port), timeout=0.5):
```

If Convex can't connect in 500ms on localhost/LAN, it's effectively unreachable. This reduces worst-case UI block from 2s to 0.5s.

### Step 2 (follow-up, skip for now): Move to background thread

Would require:
- `SyncEngine.set_convex_client()` method for deferred client injection
- Background thread for reachability check + client creation
- Status callback to update UI sync indicator

This is a larger refactor touching SyncEngine internals. Not worth the risk for a 0.5s improvement over Step 1.

---

## Summary of Changes

| File | Change |
|------|--------|
| `src/shared/infra/metrics.py` | Add auto-commit after successful handler |
| 28 command handler files | Remove `if session: session.commit()` |
| 4 exchange import handlers | Add `@metered_command` decorator |
| `file_manager_viewmodel.py` | Remove `session=` from `open_source()` call; refactor `_import_sources_async` to use `import_file_source` |
| `sync_context.py` | Reduce socket timeout to 0.5s |
| `test_mcp_tools.py` + other tests | Update as needed |

## Risks

- **Nested decorator commits:** Sub-handlers (called from import handlers) will commit after each item. This is actually fine — SQLite commits are cheap and data is safer.
- **Thread safety of `import_file_source` in executor:** Safe with `SingletonThreadPool` — each executor thread gets its own connection.
- **`import_file_source` uniqueness check:** O(n²) for batch but acceptable for typical sizes.
