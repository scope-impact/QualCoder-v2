---
id: QC-054
title: Thread-Safe AI & Human Collaboration Infrastructure
status: Done
assignee: [@myself]
created_date: '2026-03-14'
updated_date: '2026-03-14'
labels: [infra, core, agent-tools, P0]
dependencies: []
parent_task_id: ''
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Thread-safe database infrastructure that enables simultaneous AI agent (MCP) and human (Qt UI) access to the same project database. When an AI agent applies codes via `asyncio.to_thread` while a human is browsing sources in the Qt main thread, both must safely read/write without corruption or deadlocks.

**Why this matters:** QualCoder v2 is agent-first — AI and human researchers collaborate on the same project concurrently. The MCP server runs in async worker threads while the Qt UI runs on the main thread. Without proper connection pooling and thread isolation, concurrent access causes SQLite "database is locked" errors or silent data corruption.

**Solution:** SQLAlchemy `SingletonThreadPool` gives each thread its own cached connection with `busy_timeout` for contention, and a `connection_factory` callable that repositories use instead of raw engine access.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Engine uses `SingletonThreadPool` and `connection_factory` returns same connection on same thread
- [x] #2 Repositories can be accessed from worker threads (not just Qt main thread)
- [x] #3 Concurrent repo access from multiple threads does not corrupt data or deadlock
- [x] #4 MCP `asyncio.to_thread` integration works with thread-safe repos
- [x] #5 Connection pool cleans up properly on project close
<!-- AC:END -->

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-054.01 | SingletonThreadPool connection factory | Done |
| QC-054.02 | Repo worker thread access | Done |
| QC-054.03 | Concurrent repo access stress test | Done |
| QC-054.04 | MCP asyncio.to_thread integration | Done |
| QC-054.05 | Pool cleanup on project close | Done |

## Implementation

### Test file

```
src/tests/e2e/test_thread_safe_repos_e2e.py  # (was QC-INF)
```

### Architecture

```
Qt Main Thread (UI)          Worker Thread (MCP)
     │                            │
     ▼                            ▼
 connection_factory()         connection_factory()
     │                            │
     ▼                            ▼
 Connection A (cached)        Connection B (cached)
     │                            │
     └────── SingletonThreadPool ──┘
                    │
                    ▼
              SQLite DB (busy_timeout=5000ms)
```

The `SingletonThreadPool` ensures each thread gets its own connection, cached for reuse within that thread. The `busy_timeout` PRAGMA prevents "database is locked" errors during brief write contention.
