---
id: QC-048
title: SQLite Database Version Control with Git
status: Done
created_date: '2026-02-04'
labels: [infrastructure, projects, feature, P1]
dependencies: []
decision: decision-006
---

## Description

As a Researcher, I want my project database to be automatically version controlled so that every change is tracked and I can rollback mistakes without manual effort.

## Acceptance Criteria

- [x] #1 I can initialize version control for my project
- [x] #2 Every mutation (create code, apply segment, etc.) auto-commits
- [x] #3 I can view the history of all changes
- [x] #4 I can see what changed between two points in time
- [x] #5 I can restore my project to a previous state
- [ ] #6 I can create branches for different analysis approaches
- [ ] #7 I can merge changes from different branches

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-048.01 | Git repository initialization | Done |
| QC-048.02 | sqlite-diffable adapter | Done |
| QC-048.03 | Git operations service | Done |
| QC-048.04 | VersionControlListener with debounce | Done |
| QC-048.05 | Restore snapshot command | Done |
| QC-048.06 | Version history UI | Done |
| QC-048.07 | Diff viewer dialog | Done |
| QC-048.08 | MCP tools | Done |
| QC-048.09 | User documentation | Done |

## References

- [decision-006](../decisions/decision-006%20sqlite-version-control-sqlite-diffable.md) - Architecture decision record
