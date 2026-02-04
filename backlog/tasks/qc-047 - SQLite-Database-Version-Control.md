---
id: QC-047
title: SQLite Database Version Control with Git
status: To Do
created_date: '2026-02-04'
labels: [infrastructure, projects, feature, P1]
dependencies: []
---

## Description

Implement version control for QualCoder SQLite databases using Git, enabling users to track changes, view diffs, rollback to previous states, and merge database changes.

This allows researchers to:
- Track all changes to their qualitative research data over time
- Rollback to any previous state if mistakes are made
- View meaningful diffs showing what codes/segments/sources changed
- Collaborate with merge capabilities for multi-coder workflows

## Research Summary

### Available Approaches

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Git clean/smudge filters** | Line-by-line diffs, stores as SQL text | Setup complexity | **Primary choice** |
| **sqldiff (Official SQLite)** | Official tool, SQL output | No triggers/views | Use for diff display |
| **git-sqlite** | Full merge support | Shell scripts, extra deps | Consider for merging |
| **sqlite-diffable** | Python, JSON export | Different format | Good for archival |
| **Git textconv** | Simple setup | Display only, no merge | Fallback option |
| **Litestream** | Continuous backup, PITR | Not version control | Complementary backup |

### Recommended Implementation Stack

1. **Git clean/smudge filters** - Store database as SQL text in Git
   - Clean: `sqlite3 .dump` on commit (binary -> SQL)
   - Smudge: Reconstruct binary on checkout (SQL -> binary)
   - Enables meaningful line-by-line diffs

2. **sqldiff integration** - For viewing changes between versions
   - Official SQLite utility (included in Debian 9+)
   - Outputs SQL script to transform db1 -> db2

3. **Optional: Litestream** - Complementary continuous backup
   - WAL streaming to S3/Azure for disaster recovery
   - Point-in-time recovery capability

### Key Tools & References

- [git-sqlite](https://github.com/cannadayr/git-sqlite) - Custom diff/merge driver
- [sqlite-diffable](https://datasette.io/tools/sqlite-diffable) - Python tool by Datasette
- [sqldiff](https://www.sqlite.org/sqldiff.html) - Official SQLite utility
- [gitsqlite](https://github.com/danielsiegl/gitsqlite) - Smudge/clean filters
- [Litestream](https://litestream.io/) - Streaming SQLite replication

### Technical Considerations

1. **Repository Size**: Storing as SQL text is more efficient than binary blobs
2. **Binary Changes**: SQLite files change even when content is identical (need canonical rebuild)
3. **Merge Conflicts**: Domain-specific - may need custom resolution for QualCoder schema
4. **Filter Setup**: Users without filters configured will see errors on clone

## Acceptance Criteria

- [ ] Git repository initialization for QualCoder projects
- [ ] Clean/smudge filter configuration for SQLite files
- [ ] sqldiff integration for viewing database changes
- [ ] UI for viewing version history and diffs
- [ ] Rollback/restore functionality to previous commits
- [ ] Branch and merge support for database states
- [ ] User documentation for Git-based version control

## Subtasks

| ID | Subtask | Status | Layer |
|----|---------|--------|-------|
| QC-047.01 | Git repository initialization in project folder | To Do | infrastructure |
| QC-047.02 | Clean/smudge filter scripts for SQLite | To Do | infrastructure |
| QC-047.03 | sqldiff wrapper for viewing changes | To Do | infrastructure |
| QC-047.04 | Version history query service | To Do | core |
| QC-047.05 | Commit/snapshot command handler | To Do | core |
| QC-047.06 | Rollback/restore command handler | To Do | core |
| QC-047.07 | Version history UI panel | To Do | presentation |
| QC-047.08 | Diff viewer dialog | To Do | presentation |
| QC-047.09 | MCP tools for version control | To Do | interface |
| QC-047.10 | User documentation | To Do | documentation |

## Implementation Notes

### Git Filter Configuration

```bash
# .gitattributes in project folder
*.sqlite filter=sqlite3 diff=sqlite3

# Git config (per-repo or global)
[filter "sqlite3"]
    clean = sqlite3 %f .dump
    smudge = sqlite3 %f

[diff "sqlite3"]
    textconv = sqlite3 %f .dump
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
│   ├── sqlite_filter.py
│   └── sqldiff_adapter.py
├── interface/
│   └── version_control_tools.py  # MCP tools
└── presentation/
    ├── version_history_panel.py
    └── diff_viewer_dialog.py
```

### MCP Tool Schemas

```python
# Planned MCP tools
- create_snapshot(message: str) -> SnapshotCreated
- list_snapshots(limit: int) -> List[Snapshot]
- view_diff(from_ref: str, to_ref: str) -> DiffResult
- restore_snapshot(ref: str) -> SnapshotRestored
- get_version_status() -> VersionStatus
```
