---
id: decision-006
title: SQLite Version Control - sqlite-diffable
status: Accepted
date: '2026-02-04'
deciders: []
labels:
  - infrastructure
  - projects
  - version-control
  - sqlite
related_task: QC-047
---

## Context

QualCoder stores all project data (codes, segments, sources, cases, memos) in a SQLite database. Researchers need:

1. **Change tracking** - See what codes/segments changed over time
2. **Rollback capability** - Restore to previous states after mistakes
3. **Collaboration** - Merge work from multiple coders
4. **Auditability** - Full history of research data evolution

SQLite databases are binary files, making them opaque to Git:
- `git diff` shows nothing useful
- `git merge` fails on binary conflicts
- Repository bloats with each commit (no delta compression)

We need a solution that makes SQLite databases **diffable** in Git.

## Decision

**Accepted: sqlite-diffable as the primary tool for SQLite version control.**

[sqlite-diffable](https://github.com/simonw/sqlite-diffable) by Simon Willison converts SQLite databases to a directory of JSON files that Git can diff and merge effectively.

### Why sqlite-diffable

| Criteria | sqlite-diffable | Rating |
|----------|-----------------|--------|
| **Python native** | `pip install sqlite-diffable` | Essential for QualCoder |
| **Cross-platform** | Works on Windows, macOS, Linux | Essential |
| **Active maintenance** | Simon Willison (Datasette creator) | High confidence |
| **Format** | JSON (human-readable) | Excellent for diffs |
| **Roundtrip** | dump → load preserves data | Required |
| **License** | Apache 2.0 | Compatible |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    QualCoder Project Folder                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  project.qda/                                                │
│  ├── data.sqlite          ← Working database (binary)        │
│  ├── .git/                ← Git repository                   │
│  └── .qualcoder-vcs/      ← Diffable snapshot directory      │
│      ├── source.metadata.json                                │
│      ├── source.ndjson                                       │
│      ├── code_name.metadata.json                             │
│      ├── code_name.ndjson                                    │
│      ├── code_text.metadata.json                             │
│      ├── code_text.ndjson                                    │
│      └── ...                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Workflow:
                    ┌─────────────┐
                    │ User edits  │
                    │ in QualCoder│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ data.sqlite │  (binary, working copy)
                    └──────┬──────┘
                           │
         User clicks "Create Snapshot"
                           │
                           ▼
              ┌────────────────────────┐
              │ sqlite-diffable dump   │
              │ data.sqlite            │
              │ .qualcoder-vcs/ --all  │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ .qualcoder-vcs/        │
              │ ├── code_name.ndjson   │  (JSON, diffable)
              │ ├── code_text.ndjson   │
              │ └── ...                │
              └────────────┬───────────┘
                           │
                     git add + commit
                           │
                           ▼
              ┌────────────────────────┐
              │ Git repository         │
              │ (line-by-line diffs)   │
              └────────────────────────┘
```

### Output Format

**Metadata file** (`table_name.metadata.json`):
```json
{
  "name": "code_name",
  "columns": ["cid", "name", "memo", "owner", "date", "color"],
  "schema": "CREATE TABLE code_name (cid INTEGER PRIMARY KEY, name TEXT, ...)"
}
```

**Data file** (`table_name.ndjson`):
```
[1, "Theme A", "Main theme identified", "default", "2026-02-04", "#FF5733"]
[2, "Theme B", "Secondary theme", "default", "2026-02-04", "#33FF57"]
```

**Git diff example** (adding a new code):
```diff
--- a/.qualcoder-vcs/code_name.ndjson
+++ b/.qualcoder-vcs/code_name.ndjson
@@ -1,2 +1,3 @@
 [1, "Theme A", "Main theme identified", "default", "2026-02-04", "#FF5733"]
 [2, "Theme B", "Secondary theme", "default", "2026-02-04", "#33FF57"]
+[3, "Theme C", "Emerging theme", "default", "2026-02-04", "#5733FF"]
```

## Options Considered

### Option 1: git-sqlite (Rejected)

Custom diff/merge driver using `sqldiff` utility.

| Pros | Cons |
|------|------|
| Uses official sqldiff | **No Windows support** |
| SQL-based diffs | Shell scripts only |
| Merge driver included | Dormant since Aug 2021 |
| | No trigger/view diffs |

**Rejected because:** No Windows support is a deal-breaker for QualCoder's cross-platform requirement.

### Option 2: Git clean/smudge filters (Rejected)

Store database as SQL dump text, reconstruct on checkout.

```
[filter "sqlite3"]
    clean = sqlite3 %f .dump
    smudge = sqlite3 %f
```

| Pros | Cons |
|------|------|
| Native Git mechanism | Complex temp file handling |
| SQL text diffs | Errors on clone without filters |
| No extra tools | Schema-dependent ordering |
| | Rebuild time on checkout |

**Rejected because:** Filter setup is error-prone, and users cloning without filters configured get errors.

### Option 3: sqldiff only (Rejected)

Official SQLite utility for comparing databases.

| Pros | Cons |
|------|------|
| Official SQLite tool | Requires two databases to compare |
| SQL output | No Git integration |
| | No trigger/view support |
| | Must build from source on some systems |

**Rejected because:** sqldiff compares two databases, not suitable for Git storage directly. Useful as a complementary viewing tool.

### Option 4: sqlite-diffable (Accepted)

Python tool exporting to JSON directory structure.

| Pros | Cons |
|------|------|
| Python native (pip install) | Extra disk space for JSON copy |
| Cross-platform | Explicit dump/load steps |
| Human-readable JSON | No automatic Git hooks |
| Line-by-line diffs | |
| Active maintainer | |
| Roundtrip fidelity | |

**Accepted because:** Best fit for QualCoder's Python/Qt stack with cross-platform support.

### Option 5: Litestream (Complementary)

Continuous WAL streaming for backup/recovery.

| Pros | Cons |
|------|------|
| Point-in-time recovery | Not version control |
| Cloud backup (S3/Azure) | Requires cloud setup |
| No explicit snapshots | No diff viewing |

**Deferred:** Excellent for backup but doesn't solve version control. Could complement sqlite-diffable for disaster recovery.

## Consequences

### Positive

- **Human-readable diffs**: JSON changes are clear in Git log/diff
- **Cross-platform**: Works on Windows, macOS, Linux
- **Python integration**: Easy to call from QualCoder
- **Selective export**: Can exclude system tables or large blobs
- **Merge support**: Standard Git merge on JSON files
- **No filter complexity**: Explicit dump/load is predictable

### Negative

- **Disk space**: JSON copy alongside SQLite database
- **Manual workflow**: User must trigger snapshot (not automatic)
- **Large tables**: ndjson files can be large for big datasets
- **Binary blobs**: Images/media stored as base64 may bloat

### Mitigations

| Issue | Mitigation |
|-------|------------|
| Disk space | Compress old snapshots, .gitignore binary media |
| Manual workflow | Auto-snapshot on project close (opt-in) |
| Large tables | Exclude `source.fulltext` for text-heavy sources |
| Binary blobs | Store media references only, not content |

## Implementation

### Dependencies

```toml
[project.dependencies]
sqlite-diffable = ">=1.0"  # Apache 2.0
```

### Python API Usage

```python
import subprocess
from pathlib import Path

def create_snapshot(db_path: Path, output_dir: Path, exclude: list[str] = None):
    """Dump database to diffable format."""
    cmd = ["sqlite-diffable", "dump", str(db_path), str(output_dir), "--all"]
    if exclude:
        for table in exclude:
            cmd.extend(["--exclude", table])
    subprocess.run(cmd, check=True)

def restore_snapshot(db_path: Path, snapshot_dir: Path, replace: bool = True):
    """Load database from diffable format."""
    cmd = ["sqlite-diffable", "load", str(db_path), str(snapshot_dir)]
    if replace:
        cmd.append("--replace")
    subprocess.run(cmd, check=True)
```

### Directory Structure

```
src/contexts/projects/
├── infra/
│   ├── sqlite_diffable_adapter.py   # Wrapper for sqlite-diffable CLI
│   └── git_repository.py            # Git operations (init, commit, log)
├── core/
│   └── commandHandlers/
│       ├── create_snapshot.py       # Dump + git commit
│       ├── list_snapshots.py        # Git log parsing
│       └── restore_snapshot.py      # Git checkout + load
└── presentation/
    ├── version_history_panel.py     # List commits, view diffs
    └── snapshot_dialog.py           # Commit message input
```

### Excluded Tables (Default)

```python
EXCLUDE_TABLES = [
    "sqlite_sequence",      # Auto-increment tracking
    "source_fulltext_fts",  # FTS index (regenerable)
    "source_fulltext_data", # FTS data (regenerable)
]
```

### MCP Tools

```python
@mcp_tool
def create_snapshot(message: str) -> SnapshotCreated:
    """Create a version control snapshot of the current database state."""

@mcp_tool
def list_snapshots(limit: int = 20) -> list[Snapshot]:
    """List recent snapshots with commit messages and dates."""

@mcp_tool
def view_diff(from_ref: str = "HEAD~1", to_ref: str = "HEAD") -> DiffResult:
    """View changes between two snapshots."""

@mcp_tool
def restore_snapshot(ref: str) -> SnapshotRestored:
    """Restore database to a previous snapshot state."""
```

## References

- [sqlite-diffable GitHub](https://github.com/simonw/sqlite-diffable)
- [sqlite-diffable Datasette page](https://datasette.io/tools/sqlite-diffable)
- [Using sqlite-diffable as a Python module](https://blog.pesky.moe/posts/2024-07-06-sqlite-diffable/)
- [Simon Willison on tracking data in Git](https://fedi.simonwillison.net/@simon/109331617858051125)
- [Tracking SQLite Database Changes in Git (HN)](https://news.ycombinator.com/item?id=38110286)
- Related task: [QC-047 - SQLite Database Version Control](../tasks/qc-047%20-%20SQLite-Database-Version-Control.md)
