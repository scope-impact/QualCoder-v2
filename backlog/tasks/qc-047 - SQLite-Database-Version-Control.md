---
id: QC-047
title: SQLite Database Version Control with Git
status: To Do
created_date: '2026-02-04'
labels: [infrastructure, projects, feature, P1]
dependencies: []
decision: decision-006
---

## Description

Implement version control for QualCoder SQLite databases using Git, enabling users to track changes, view diffs, rollback to previous states, and merge database changes.

This allows researchers to:
- Track all changes to their qualitative research data over time
- Rollback to any previous state if mistakes are made
- View meaningful diffs showing what codes/segments/sources changed
- Collaborate with merge capabilities for multi-coder workflows

## Decision

**sqlite-diffable** selected as the primary tool. See [decision-006](../decisions/decision-006%20sqlite-version-control-sqlite-diffable.md) for full rationale.

### Why sqlite-diffable

| Criteria | sqlite-diffable | Alternatives |
|----------|-----------------|--------------|
| Python native | `pip install` | git-sqlite: shell only |
| Cross-platform | Win/Mac/Linux | git-sqlite: no Windows |
| Active maintainer | Simon Willison | git-sqlite: dormant |
| Format | JSON (diffable) | SQL text (ordering issues) |
| Integration | CLI + Python | Shell scripts |

### Architecture

```
project.qda/
├── data.sqlite           ← Working database (binary)
├── .git/                 ← Git repository
└── .qualcoder-vcs/       ← Diffable snapshots
    ├── code_name.metadata.json
    ├── code_name.ndjson
    ├── code_text.metadata.json
    ├── code_text.ndjson
    └── ...
```

### Workflow

1. User works in QualCoder (edits `data.sqlite`)
2. User clicks "Create Snapshot"
3. `sqlite-diffable dump` exports to `.qualcoder-vcs/`
4. Git commits the JSON files
5. Git diff shows meaningful line-by-line changes
6. Restore: Git checkout + `sqlite-diffable load`

## Acceptance Criteria

- [ ] Git repository initialization for QualCoder projects
- [ ] sqlite-diffable integration for dump/load operations
- [ ] Snapshot creation (dump + git commit)
- [ ] UI for viewing version history and diffs
- [ ] Rollback/restore functionality to previous commits
- [ ] Branch and merge support for database states
- [ ] User documentation for Git-based version control

## Subtasks

| ID | Subtask | Status | Layer |
|----|---------|--------|-------|
| QC-047.01 | Git repository initialization in project folder | To Do | infrastructure |
| QC-047.02 | sqlite-diffable adapter (dump/load wrapper) | To Do | infrastructure |
| QC-047.03 | Git operations service (commit, log, checkout) | To Do | infrastructure |
| QC-047.04 | Version history query service | To Do | core |
| QC-047.05 | Create snapshot command handler | To Do | core |
| QC-047.06 | Restore snapshot command handler | To Do | core |
| QC-047.07 | Version history UI panel | To Do | presentation |
| QC-047.08 | Diff viewer dialog | To Do | presentation |
| QC-047.09 | MCP tools for version control | To Do | interface |
| QC-047.10 | User documentation | To Do | documentation |

## Implementation Notes

### Dependencies

```toml
[project.dependencies]
sqlite-diffable = ">=1.0"  # Apache 2.0
```

### Excluded Tables

```python
EXCLUDE_TABLES = [
    "sqlite_sequence",       # Auto-increment tracking
    "source_fulltext_fts",   # FTS index (regenerable)
    "source_fulltext_data",  # FTS data (regenerable)
]
```

### Directory Structure

```
src/contexts/projects/
├── core/
│   └── commandHandlers/
│       ├── init_version_control.py
│       ├── create_snapshot.py
│       └── restore_snapshot.py
├── infra/
│   ├── git_repository.py
│   └── sqlite_diffable_adapter.py
├── interface/
│   └── version_control_tools.py  # MCP tools
└── presentation/
    ├── version_history_panel.py
    └── diff_viewer_dialog.py
```

### Python API

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

def restore_snapshot(db_path: Path, snapshot_dir: Path):
    """Load database from diffable format."""
    cmd = ["sqlite-diffable", "load", str(db_path), str(snapshot_dir), "--replace"]
    subprocess.run(cmd, check=True)
```

### MCP Tool Schemas

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

@mcp_tool
def get_version_status() -> VersionStatus:
    """Get current version control status (dirty/clean, current commit)."""
```

## References

- [sqlite-diffable GitHub](https://github.com/simonw/sqlite-diffable)
- [Decision Record](../decisions/decision-006%20sqlite-version-control-sqlite-diffable.md)
